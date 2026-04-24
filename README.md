# AMA Weekly Report

Reporte semanal automático del bot AMA: genera un Excel con la actividad de la semana anterior, arma una narrativa con LLM y lo envía por correo.

Corre cada martes 8:00 AM Bogotá vía GitHub Actions (`.github/workflows/weekly-report.yml`).

## Correr local

```bash
pip install -r requirements.txt
cp .env.example .env   # completar valores
python3 src/send_report.py --dry-run                 # genera sin enviar
python3 src/send_report.py                            # envía usando REPORT_RECIPIENTS
python3 src/send_report.py --from 2026-04-13 --to 2026-04-19
```

## Secrets del workflow

Configurados en GitHub Actions del repo:

- `DATABASE_URL` — Postgres de Supabase (pooler 6543)
- `BOT_START_DATE` — fecha de lanzamiento del bot (`YYYY-MM-DD`)
- `OPENROUTER_API_KEY` — para la narrativa del LLM
- `GMAIL_USER` — cuenta que envía (requiere App Password)
- `GMAIL_APP_PASSWORD` — App Password de 16 chars (sin espacios)
- `REPORT_RECIPIENTS` — emails destino separados por coma

## Ejecución manual del workflow

`Actions → Weekly AMA Bot Report → Run workflow`.
