# AMA Weekly Report — CLAUDE.md

Repo hermano de [`Bot_monitoring`](https://github.com/Rodato/ama-bot-monitoring) (dashboard Streamlit). Este repo solo contiene la automatización de **envío semanal del reporte por correo** vía GitHub Actions.

## Relación con Bot_monitoring

Los archivos `src/{send_report,report_bot,agent_report,db}.py` están **duplicados a mano** entre los dos repos. Cambios al prompt del LLM, a las queries de DB, o al armado del Excel hay que copiarlos a ambos.

- `Bot_monitoring` usa esos archivos para el botón de descarga manual del dashboard.
- `ama-weekly-report` los usa para el cron de email.

No hay submodule ni package compartido — se sincroniza con `cp`.

## Estructura

```
ama-weekly-report/
├── .github/workflows/weekly-report.yml   # cron lunes 13:00 UTC (8am Bogotá)
├── requirements.txt                       # pg8000, sqlalchemy, pandas, openpyxl, openai, python-dotenv
└── src/
    ├── send_report.py    # entry point: rango semana anterior, arma email, SMTP Gmail 465 SSL
    ├── report_bot.py     # genera Excel con 4 hojas (leyenda + Ciudad + Colegio + Salón)
    ├── agent_report.py   # build_prompt + call_llm (OpenRouter, default x-ai/grok-4)
    └── db.py             # SQLAlchemy + pg8000, queries al schema ama de Supabase
```

## Comandos

```bash
pip3 install -r requirements.txt
python3 src/send_report.py --dry-run                             # genera sin enviar
python3 src/send_report.py                                        # envía (usa REPORT_RECIPIENTS)
python3 src/send_report.py --from 2026-04-13 --to 2026-04-19     # override rango
```

Por defecto el rango es **lunes a domingo de la semana anterior a hoy**.

## Secrets (GitHub Actions)

6 secrets necesarios en el repo. Ver README para detalles. Valores sensibles viven en el `.env` del repo hermano `Bot_monitoring` (local) y en los secrets del repo (cloud).

## Estilo de narrativa del LLM

Reporte **puramente descriptivo**. 5-7 párrafos cortos, prosa continua, sin markdown. Orden: resumen general → ciudad → colegios → evolución semanal desde lanzamiento.

**NO incluir** párrafos de "punto de atención", interpretaciones, hipótesis, ni sugerencias de seguimiento. Si los datos son planos, el reporte termina plano.

Fecha de lanzamiento del bot: **2026-03-03** (usada por `db.get_weekly_evolution`).

## Base de datos

Postgres de Supabase (pooler, puerto 6543). Schema `ama` (minúsculas), no expuesto vía REST — solo acceso directo.

Tablas relevantes:
- `ama.ama_session_start_table` — eventos de inicio de sesión
- `ama.ama_sessions_responses` — respuestas por día (JSON)
- `ama.ama_user_info_table_v1` — perfil (nombre, género, ciudad, colegio, curso)

Filtro de país aplicado en todas las queries: `client_number ~ '^(57|59)'` (Colombia + Bolivia).

## Lecciones técnicas

- **`gh secret set`**: `--body -` pasa el literal `-`, NO lee stdin. Usar `--body "$VAR"`.
- Para cambiar driver en SQLAlchemy: `make_url(url).set(drivername="postgresql+pg8000")` — NO string replace (genera bugs tipo `ostgresql`).
- pg8000 devuelve columnas `DATE` como `datetime` — castear `::text` en SQL cuando importa el formato.
- El workflow usa Python 3.12 en runner Ubuntu; local puede ser 3.9+.

## Convenciones del usuario

- Siempre `python3` (no `python`).
- **NO crear `.env.example`** ni archivos equivalentes. Si hay que documentar envs, va en el README.
- Remoto del repo: org `Estudio-Plural` (público). El repo hermano sí está bajo `Rodato` personal.

## Flujo de cambios

1. Editar archivo local.
2. Si el cambio toca código compartido con `Bot_monitoring` (db/report_bot/agent_report/send_report), copiar también allá.
3. Commit + push → el workflow corre solo los lunes, o manual desde Actions → `Weekly AMA Bot Report` → `Run workflow`.
