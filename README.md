
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
<img width="1887" height="913" alt="Swagger UI" src="https://github.com/user-attachments/assets/1a35549f-c53b-4b73-b7ee-60b9b300d241" />
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
<img width="1382" height="942" alt="databse count " src="https://github.com/user-attachments/assets/de2a4761-2466-4757-94d8-5b062a8ad88e" />
<img width="1907" height="977" alt="Data by id " src="https://github.com/user-attachments/assets/9f121044-747c-473b-b26f-deec065d3eb8" />
<img width="1902" height="1012" alt="DB1" src="https://github.com/user-attachments/assets/4549afb8-8a94-4b54-b0b5-fe0f1bb5a1e8" />

## Example SQL query
SELECT * FROM tasks WHERE done = 1;
-- Returns all completed tasks

## Swagger UI
Visit http://localhost:8000/docs
