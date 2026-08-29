# Task API — A3: Containerize your stack

FastAPI + SQLAlchemy task API, backed by PostgreSQL in Docker. Same routes as A1 (memory) and A2 (SQLite) — only storage changed.

## Run it

```bash
cp .env.example .env
docker compose up
```

API on `http://localhost:3000`. Table is created and seeded (3 tasks) on first run only.

## Endpoints

| Method | Path          | Body                          | Success | Errors        |
|--------|---------------|--------------------------------|---------|---------------|
| GET    | /tasks        | —                               | 200     | —             |
| GET    | /tasks/{id}   | —                               | 200     | 404           |
| POST   | /tasks        | `{"title": str, "done": bool}` | 201     | 400           |
| PUT    | /tasks/{id}   | `{"title": str, "done": bool}` | 200     | 400, 404      |
| DELETE | /tasks/{id}   | —                               | 204     | 404           |
| GET    | /health       | —                               | 200     | —             |

## Example

```bash
curl -i http://localhost:3000/tasks
```

## Persistence

Data survives `docker compose down` + `up` — kept in the `taskdata` named volume.

## AI vs me

<!-- Fill in after Stage 6: your prompt, what the AI got right/wrong, what your prompt missed. -->
