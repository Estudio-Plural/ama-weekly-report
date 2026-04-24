# AMA Weekly Report

Reporte semanal automático del bot AMA: genera un Excel con la actividad de la semana anterior, arma una narrativa con LLM y lo envía por correo.

Corre cada martes 8:00 AM Bogotá vía GitHub Actions (`.github/workflows/weekly-report.yml`).

## Secrets del workflow

Configurados en GitHub Actions del repo:

- `DATABASE_URL` — Postgres de Supabase (pooler 6543)
- `BOT_START_DATE` — fecha de lanzamiento del bot (`YYYY-MM-DD`)
- `OPENROUTER_API_KEY` — para la narrativa del LLM
- `GMAIL_USER` — cuenta que envía (requiere App Password)
- `GMAIL_APP_PASSWORD` — App Password de 16 chars (sin espacios)
- `REPORT_RECIPIENTS` — emails destino separados por coma
