# LSS Async Core API

API assíncrona da **Lucas Software Solutions (LSS)** para autenticação, autorização e operações de negócio com padrão de produção.

Stack: **Python · FastAPI · SQLAlchemy 2.0 Async · PostgreSQL (ou SQLite) · Redis · JWT + refresh · RBAC · Docker · NGINX · Alembic · pytest**.

Repositório: [github.com/Lucasvduda/lss-async-core-api](https://github.com/Lucasvduda/lss-async-core-api)

## O que resolve

Padroniza APIs internas/externas com:

- autenticação JWT (access + refresh token)
- RBAC por perfil (`admin`, `operator`, `viewer`)
- CRUD de itens com **paginação e filtros**
- **upload/processamento de CSV**
- rate limiting (Redis ou fallback em memória)
- logs com `X-Request-ID` e tratamento centralizado de erros
- Clean Architecture / Repository Pattern
- OpenAPI/Swagger em `/docs`

## Arquitetura

```
app/
  domain/                 # entidades e erros
  application/
    ports/                # interfaces (repositórios, segurança)
    use_cases/            # casos de uso
  adapters/
    inbound/api/v1/       # FastAPI routers + DTOs
    outbound/             # SQLAlchemy, JWT, Redis
  infrastructure/         # config, middleware, logging
```

Domínio não depende do FastAPI. Persistência e HTTP ficam na borda.

## Como rodar (local, sem Docker)

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

- Swagger: http://localhost:8000/docs  
- Health: http://localhost:8000/health  

O default do `.env.example` usa **SQLite** (`aiosqlite`) para subir sem Postgres.

## Como rodar (Docker Compose)

```bash
docker compose up --build
```

- API: http://localhost:8000  
- via NGINX: http://localhost:8080  
- Postgres: localhost:5432  
- Redis: localhost:6379  

## Fluxo rápido (curl)

```bash
# 1) registrar
curl -s -X POST http://localhost:8000/v1/auth/register \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"lucas@lss.dev\",\"password\":\"senhaforte\",\"full_name\":\"Lucas\",\"role\":\"admin\"}"

# 2) login
curl -s -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"lucas@lss.dev\",\"password\":\"senhaforte\"}"

# 3) criar item (troque TOKEN)
curl -s -X POST http://localhost:8000/v1/items \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"Pedido 1\",\"description\":\"demo\",\"status\":\"open\"}"

# 4) listar com filtros
curl -s "http://localhost:8000/v1/items?page=1&page_size=10&status=open&q=Pedido" \
  -H "Authorization: Bearer TOKEN"

# 5) importar CSV
curl -s -X POST http://localhost:8000/v1/items/import/csv \
  -H "Authorization: Bearer TOKEN" \
  -F "file=@scripts/sample_items.csv"

# 6) refresh token
curl -s -X POST http://localhost:8000/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\":\"REFRESH\"}"
```

## Endpoints principais

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/health` | health check |
| POST | `/v1/auth/register` | cadastro |
| POST | `/v1/auth/login` | access + refresh |
| POST | `/v1/auth/refresh` | novo access token |
| GET | `/v1/auth/me` | usuário autenticado |
| GET | `/v1/items` | lista paginada (`page`, `page_size`, `status`, `q`) |
| POST | `/v1/items` | cria item |
| GET | `/v1/items/{id}` | detalhe |
| DELETE | `/v1/items/{id}` | remove |
| POST | `/v1/items/import/csv` | importação CSV |

## RBAC

| Papel | Pode |
|-------|------|
| `admin` | tudo + vê itens de todos |
| `operator` | CRUD/import dos próprios itens |
| `viewer` | só leitura dos próprios itens |

## Testes

```bash
pytest -q
```

## Migrations (Alembic)

Com o banco configurado:

```bash
alembic upgrade head
```

Em desenvolvimento local o `lifespan` também cria as tabelas via `metadata.create_all` para onboarding rápido.

## Variáveis de ambiente

Ver `.env.example`. Principais: `DATABASE_URL`, `SECRET_KEY`, `REDIS_URL`, `RATE_LIMIT_PER_MINUTE`.

## Decisões de design

1. **Access curto + refresh** — reduz janela de abuso se o access vazar.  
2. **Repository + use cases** — troca de adapter (SQLite ↔ Postgres) sem reescrever regra.  
3. **Rate limit com fallback** — Redis em produção/compose; memória no demo local.  
4. **CSV síncrono + BackgroundTasks** — import retorna contagem; log assíncrono do resultado.  
5. **Erros tipados** — `code` + `message` + `request_id` estáveis para o cliente.

## Autor

Lucas Viana Duda — Lucas Software Solutions (LSS)  
github.com/Lucasvduda
