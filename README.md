# oee-line-monitor (industrial-oee-tracker)

Sistema full-stack para monitoramento de OEE de linhas e máquinas, com API Flask + Postgres e frontend React/Vite.

## 1) Stack
- **Backend**: Flask, SQLAlchemy, Flask-Migrate, JWT, Flask-CORS
- **Frontend**: React + Vite + TypeScript + Tailwind + TanStack Query + Recharts
- **Infra**: Docker Compose (dev/prod), Gunicorn (API em produção), Nginx (frontend em produção)

## 2) Variáveis de ambiente
Copie os arquivos de exemplo:
```bash
cp .env.example .env
cp apps/api/.env.example apps/api/.env
cp apps/web/.env.example apps/web/.env
```

Principais variáveis:
- `DATABASE_URL`: conexão Postgres (Neon compatível)
- `JWT_SECRET`, `JWT_EXPIRES_HOURS`
- `CORS_ORIGINS`: lista separada por vírgula
- `ADMIN_EMAIL`, `ADMIN_PASSWORD`
- `VITE_API_URL` (frontend)

## 3) Rodar em desenvolvimento com Docker
```bash
docker compose up --build
```
ou
```bash
make dev
```

Serviços:
- Front: http://localhost:5173
- API: http://localhost:5000
- Health API: http://localhost:5000/api/health

## 4) Rodar em desenvolvimento sem Docker
### Backend
```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# aplique migração quando existir diretório migrations
if [ -d migrations ]; then flask db upgrade; fi
python seed.py
flask run --host 0.0.0.0 --port 5000
```

### Frontend
```bash
cd apps/web
npm install
npm run dev
```

## 5) Seed de dados demo (idempotente)
```bash
cd apps/api
python seed.py
```
A seed cria e/ou reconcilia:
- turnos padrão
- motivos de parada
- admin default
- 1 linha + 1 máquina
- 2 produtos
- 3–5 runs do mês atual com segmentos/paradas para dashboards e relatórios

A execução imprime um resumo com `created`, `updated`, `unchanged`. Rodar duas vezes não deve duplicar dados.

## 6) Produção local (Docker)
```bash
docker compose -f docker-compose.prod.yml up --build
```
ou
```bash
make prod
```

- Front servido por Nginx (porta 80)
- API servida por gunicorn (porta 5000)
- DB com healthcheck
- API depende de DB saudável e aplica migrações quando houver `migrations/`

## 7) Qualidade
### Frontend
```bash
cd apps/web
npm run lint
npm run format
npm run build
```

### Backend
```bash
cd apps/api
ruff check .
black --check .
pytest -q
```

## 8) CI (GitHub Actions)
Pipeline em `.github/workflows/ci.yml` roda:
- **web**: install, lint, build
- **api**: Postgres service, ruff, black --check, pytest

## 9) Contratos de autenticação e UX
- Token único no storage: `access_token`
- Axios injeta `Authorization: Bearer <token>`
- Tratamento global de `401`: limpa token e redireciona para `/login`
- Rotas privadas protegidas com `ProtectedRoute`
- Páginas com fetch possuem estados explícitos: **loading**, **erro** e **empty-state**

## 10) Endpoint de health
- `GET /api/health` → valida disponibilidade da API
