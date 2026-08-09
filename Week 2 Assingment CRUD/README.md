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