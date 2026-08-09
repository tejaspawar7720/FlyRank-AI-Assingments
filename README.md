# Task CRUD API

A simple Todo API built with FastAPI.

## How to run
pip install fastapi uvicorn
uvicorn main:app --reload

## Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /tasks | Get all tasks |
| GET | /tasks/{id} | Get one task |
| POST | /tasks | Create task |
| PUT | /tasks/{id} | Update task |
| DELETE | /tasks/{id} | Delete task |

## Swagger UI
Visit http://localhost:8000/docs

# Task CRUD API — Week 3: SQLite Database

A Todo CRUD API built with FastAPI and SQLite.

## How to run
pip install fastapi uvicorn
uvicorn main:app --reload

## Why SQLite?
SQLite is a lightweight, serverless database stored in a single file (tasks.db).
No setup required — the database and table are created automatically on first run.
Data survives server restarts unlike in-memory storage.

## Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | / | API info |
| GET | /health | Health check |
| GET | /tasks | Get all tasks |
| GET | /tasks/{id} | Get one task |
| POST | /tasks | Create task |
| PUT | /tasks/{id} | Update task |
| DELETE | /tasks/{id} | Delete task |

## Database
- File: tasks.db (auto-created on first run)
- Table: tasks (id, title, done)
- 3 example tasks seeded on first run only

## Example SQL query
SELECT * FROM tasks WHERE done = 1;
-- Returns all completed tasks

## Swagger UI
Visit http://localhost:8000/docs
