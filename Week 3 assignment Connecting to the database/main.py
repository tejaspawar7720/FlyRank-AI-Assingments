import os

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import HTTPException as FastAPIHTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:dev@localhost:5432/tasks")


# Adding a function to get a database connection
def get_db():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            done BOOLEAN DEFAULT FALSE
        )
    """)
    cur.execute("SELECT COUNT(*) AS count FROM tasks")
    count = cur.fetchone()["count"]
    if count == 0:
        cur.execute("INSERT INTO tasks (title, done) VALUES (%s, %s)", ("Buy groceries", False))
        cur.execute("INSERT INTO tasks (title, done) VALUES (%s, %s)", ("Read a book", False))
        cur.execute("INSERT INTO tasks (title, done) VALUES (%s, %s)", ("Go for a walk", True))
        conn.commit()
    cur.close()
    conn.close()


init_db()

app = FastAPI()


# error shape: {"error": "..."} instead of FastAPI's default {"detail": "..."}
@app.exception_handler(FastAPIHTTPException)
async def http_exception_handler(request, exc: FastAPIHTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


# models for request bodies
class TaskInput(BaseModel):
    title: str


class TaskUpdate(BaseModel):
    title: str = None
    done: bool = None


# adding a root endpoint to provide basic information about the API
@app.get("/")
def root():
    return {"name": "Task API", "version": "3.0", "endpoints": ["/tasks"]}


@app.get("/health")
def health():
    conn = get_db()
    conn.cursor().execute("SELECT 1")
    conn.close()
    return {"status": "ok", "db": "ok"}


@app.get("/tasks")
def get_all_tasks():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks")
    tasks = cur.fetchall()
    conn.close()
    return [dict(t) for t in tasks]


# to get a specific task by id
@app.get("/tasks/{id}")
def get_task(id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE id = %s", (id,))
    task = cur.fetchone()
    conn.close()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return dict(task)


# to create a new task
@app.post("/tasks", status_code=201)
def create_task(task_input: TaskInput):
    if not task_input.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING *",
        (task_input.title, False),
    )
    task = cur.fetchone()
    conn.commit()
    conn.close()
    return dict(task)


# to update an existing task
@app.put("/tasks/{id}")
def update_task(id: int, task_update: TaskUpdate):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE id = %s", (id,))
    task = cur.fetchone()
    if task is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")
    task = dict(task)
    new_title = task_update.title if task_update.title is not None else task["title"]
    new_done = task_update.done if task_update.done is not None else task["done"]
    if not new_title.strip():
        conn.close()
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    cur.execute(
        "UPDATE tasks SET title = %s, done = %s WHERE id = %s RETURNING *",
        (new_title, new_done, id),
    )
    updated = cur.fetchone()
    conn.commit()
    conn.close()
    return dict(updated)


# to delete a task
@app.delete("/tasks/{id}", status_code=204)
def delete_task(id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE id = %s", (id,))
    task = cur.fetchone()
    if task is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")
    cur.execute("DELETE FROM tasks WHERE id = %s", (id,))
    conn.commit()
    conn.close()
