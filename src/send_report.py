"""
send_report.py
Genera el reporte semanal del bot AMA y lo envía por correo.

Rango: lunes a domingo de la semana anterior al día en que se ejecute.
Pensado para correr en GitHub Actions cada martes 8am Bogota.

Envs requeridas:
    DATABASE_URL, BOT_START_DATE, OPENROUTER_API_KEY
    GMAIL_USER, GMAIL_APP_PASSWORD
    REPORT_RECIPIENTS  (lista separada por comas)

Uso local (dry-run, no envía):
    python3 src/send_report.py --dry-run
"""

from __future__ import annotations

import argparse
import os
import smtplib
import sys
from datetime import date, timedelta
from email.message import EmailMessage
from pathlib import Path
from typing import Optional

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv

import db
import report_bot
from agent_report import build_prompt, call_llm, DEFAULT_MODEL

load_dotenv()

REPORTS_DIR = Path("data/reports")
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465


def previous_week_range(today: Optional[date] = None) -> tuple[str, str]:
    """Lunes-domingo de la semana anterior a `today` (por defecto hoy)."""
    today = today or date.today()
    monday_this = today - timedelta(days=today.weekday())
    monday_prev = monday_this - timedelta(days=7)
    sunday_prev = monday_prev + timedelta(days=6)
    return monday_prev.isoformat(), sunday_prev.isoformat()


def generate(fecha_inicio: str, fecha_fin: str, model: str = DEFAULT_MODEL) -> tuple[Path, str]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[send_report] Generando Excel {fecha_inicio} → {fecha_fin}...")
    excel_path, summary = report_bot.generate_report(fecha_inicio, fecha_fin, str(REPORTS_DIR))

    evo_df = db.get_weekly_evolution(fecha_fin)
    evolucion_lines = [
        f"Semana del {row['semana']}: {row['usuarios']} usuarios"
        for _, row in evo_df.iterrows()
    ]
    evolucion = "\n".join(evolucion_lines) if evolucion_lines else "Sin datos de evolución."

    print(f"[send_report] Generando narrativa con {model}...")
    prompt = build_prompt(summary, fecha_inicio, fecha_fin, evolucion)
    narrativa = call_llm(prompt, model)

    md_path = REPORTS_DIR / f"reporte_bot_{fecha_inicio}_{fecha_fin}.md"
    md_path.write_text(
        f"# Reporte Bot AMA — {fecha_inicio} al {fecha_fin}\n\n{narrativa}",
        encoding="utf-8",
    )

    return Path(excel_path), narrativa


def build_message(
    fecha_inicio: str,
    fecha_fin: str,
    narrativa: str,
    xlsx_path: Path,
    sender: str,
    recipients: list,
) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = f"Reporte Bot AMA - {fecha_inicio} al {fecha_fin}"
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg.set_content(f"Saludos equipo, les envío el informe:\n\n{narrativa}")

    with xlsx_path.open("rb") as f:
        msg.add_attachment(
            f.read(),
            maintype="application",
            subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=xlsx_path.name,
        )
    return msg


def send(msg: EmailMessage, sender: str, password: str) -> None:
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.login(sender, password)
        smtp.send_message(msg)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="Genera el reporte y prepara el mensaje, pero no envía.")
    parser.add_argument("--from", dest="fecha_inicio", default=None,
                        help="Override del rango (por defecto: semana anterior).")
    parser.add_argument("--to", dest="fecha_fin", default=None)
    args = parser.parse_args()

    if args.fecha_inicio and args.fecha_fin:
        fecha_inicio, fecha_fin = args.fecha_inicio, args.fecha_fin
    else:
        fecha_inicio, fecha_fin = previous_week_range()

    sender = os.environ.get("GMAIL_USER")
    password = os.environ.get("GMAIL_APP_PASSWORD")
    recipients_raw = os.environ.get("REPORT_RECIPIENTS", "")
    recipients = [r.strip() for r in recipients_raw.split(",") if r.strip()]

    if not args.dry_run:
        missing = [k for k, v in {
            "GMAIL_USER": sender,
            "GMAIL_APP_PASSWORD": password,
            "REPORT_RECIPIENTS": recipients_raw,
        }.items() if not v]
        if missing:
            raise SystemExit(f"[send_report] Faltan envs: {', '.join(missing)}")

    print(f"[send_report] Rango: {fecha_inicio} → {fecha_fin}")
    print(f"[send_report] Destinatarios: {recipients or '(ninguno)'}")

    xlsx_path, narrativa = generate(fecha_inicio, fecha_fin)

    if args.dry_run:
        print(f"[send_report] DRY-RUN. Excel: {xlsx_path}")
        print("[send_report] Asunto: Reporte Bot AMA - "
              f"{fecha_inicio} al {fecha_fin}")
        print("[send_report] Cuerpo:\n")
        print(f"Saludos equipo, les envío el informe:\n\n{narrativa}")
        return 0

    msg = build_message(fecha_inicio, fecha_fin, narrativa, xlsx_path, sender, recipients)
    send(msg, sender, password)
    print(f"[send_report] Enviado a {len(recipients)} destinatarios.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
