from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3

# Adding a function to get a database connection
def get_db():
    conn = sqlite3.connect("tasks.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done INTEGER DEFAULT 0
        )
    """)
    count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    if count == 0:
        conn.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", ("Buy groceries", 0))
        conn.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", ("Read a book", 0))
        conn.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", ("Go for a walk", 1))
        conn.commit()
    conn.close()

init_db()

app = FastAPI()

# models for request bodies
class TaskInput(BaseModel):
    title: str

class TaskUpdate(BaseModel):
    title: str = None
    done: bool = None

# adding a root endpoint to provide basic information about the API
@app.get("/")
def root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/tasks")
def get_all_tasks():
    conn = get_db()
    tasks = conn.execute("SELECT * FROM tasks").fetchall()
    conn.close()
    return [dict(t) for t in tasks]

#to get a specific task by id
@app.get("/tasks/{id}")
def get_task(id: int):
    conn = get_db()
    task = conn.execute("SELECT * FROM tasks WHERE id = ?", (id,)).fetchone()
    conn.close()
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {id} not found")
    return dict(task)

#to create a new task
@app.post("/tasks", status_code=201)
def create_task(task_input: TaskInput):
    if not task_input.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO tasks (title, done) VALUES (?, ?)",
        (task_input.title, 0)
    )
    conn.commit()
    new_id = cursor.lastrowid
    task = conn.execute("SELECT * FROM tasks WHERE id = ?", (new_id,)).fetchone()
    conn.close()
    return dict(task)

#to update an existing task
@app.put("/tasks/{id}")
def update_task(id: int, task_update: TaskUpdate):
    conn = get_db()
    task = conn.execute("SELECT * FROM tasks WHERE id = ?", (id,)).fetchone()
    if task is None:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Task {id} not found")
    task = dict(task)
    new_title = task_update.title if task_update.title is not None else task["title"]
    new_done = int(task_update.done) if task_update.done is not None else task["done"]
    if not new_title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    conn.execute(
        "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
        (new_title, new_done, id)
    )
    conn.commit()
    updated = conn.execute("SELECT * FROM tasks WHERE id = ?", (id,)).fetchone()
    conn.close()
    return dict(updated)

#to delete a task
@app.delete("/tasks/{id}", status_code=204)
def delete_task(id: int):
    conn = get_db()
    task = conn.execute("SELECT * FROM tasks WHERE id = ?", (id,)).fetchone()
    if task is None:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Task {id} not found")
    conn.execute("DELETE FROM tasks WHERE id = ?", (id,))
    conn.commit()
    conn.close()