# oee-line-monitor (monorepo)

Monorepo fullstack para monitoramento OEE industrial com operação por cliques, correções administrativas com auditoria e dashboard em tempo real (polling).

## Stack
- **Backend**: Python 3.12, Flask, SQLAlchemy, Flask-Migrate, JWT, RBAC.
- **Banco**: PostgreSQL local via docker-compose e compatível com Neon via `DATABASE_URL`.
- **Frontend**: React + Vite + TypeScript, TailwindCSS, React Router, TanStack Query, Recharts.

## Estrutura
```
apps/
  api/   # Flask API
  web/   # React app
```

## Rodar local com Docker
1. Copie envs:
   - `cp .env.example .env`
   - `cp apps/api/.env.example apps/api/.env`
   - `cp apps/web/.env.example apps/web/.env`
2. Suba tudo:
   - `make dev` (ou `docker compose up --build`)
3. URLs:
   - Web: http://localhost:5173
   - API: http://localhost:5000

## Migrations
No container da API:
- `flask db init`
- `flask db migrate -m "init"`
- `flask db upgrade`

## Seed inicial
`python seed.py` cria:
- Turnos padrão (diurno/noturno)
- Motivos planejados e não planejados (setup/troca/falta material etc)
- Admin padrão usando `ADMIN_EMAIL`/`ADMIN_PASSWORD`

## Neon / produção
Basta configurar `DATABASE_URL` com string do Neon. Exemplo:
`postgresql+psycopg://<user>:<pass>@<host>/<db>?sslmode=require`

## Deploy sugerido
- **Web**: Vercel apontando para `apps/web`
- **API**: Render/Fly/Railway apontando para `apps/api`
- Definir envs: `DATABASE_URL`, `JWT_SECRET`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `VITE_API_URL`.

## Autenticação e perfis
- Roles: `ADMIN`, `LEADER`, `VIEWER`.
- Login retorna JWT em `/api/auth/login`.

## Endpoints principais
- Auth: `/api/auth/login`, `/api/auth/me`
- Cadastros: `/api/lines`, `/api/machines`, `/api/shifts`, `/api/products`, `/api/downtime-reasons`
- Plano diário: `/api/daily-plan`, `/api/daily-plan/{id}/status`
- Operações: `/api/runs/open`, `/api/segments/start`, `/api/segments/switch`, `/api/downtime/start`, `/api/downtime/stop`, `/api/runs/close`
- Auditoria/correções: `/api/segments/{id}`, `/api/downtime/{id}`, `/api/audit`
- Status: `/api/status/overview`, `/api/status/machines/{machine_id}`
- Relatórios: `/api/reports/run/{run_id}/oee`, `/api/reports/machine/{machine_id}`, `/api/reports/monthly`, `/api/reports/yearly`
- Branding: `/api/public/settings`, `/api/settings`

## Testes mínimos
- API smoke tests com pytest:
  - login
  - abrir run + iniciar segmento
  - iniciar/finalizar parada + validar `machine_state`

Rodar:
`docker compose run --rm api pytest -q`
