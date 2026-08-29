import os
from functools import lru_cache

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.exceptions import HTTPException as FastAPIHTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field
from supabase import Client, create_client

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:dev@localhost:5432/tasks")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


# ---------- database (same as A3) ----------
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


# ---------- supabase (auth) ----------
@lru_cache
def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(creds: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    """The guard. Add Depends(get_current_user) to any route that needs a logged-in user."""
    if not creds or not creds.credentials:
        raise HTTPException(status_code=401, detail="Access token required")
    try:
        resp = get_supabase().auth.get_user(creds.credentials)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    if not resp or not resp.user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return resp.user


app = FastAPI()


# error shape everywhere: {"error": "..."}
@app.exception_handler(FastAPIHTTPException)
async def http_exception_handler(request, exc: FastAPIHTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    first = exc.errors()[0]
    field = first["loc"][-1]
    return JSONResponse(status_code=400, content={"error": f"{field}: {first['msg']}"})


# ---------- models ----------
class TaskInput(BaseModel):
    title: str


class TaskUpdate(BaseModel):
    title: str = None
    done: bool = None


class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


# ---------- basic info ----------
@app.get("/")
def root():
    return {"name": "Task API", "version": "4.0", "endpoints": ["/tasks", "/auth", "/protected", "/public"]}


@app.get("/health")
def health():
    conn = get_db()
    conn.cursor().execute("SELECT 1")
    conn.close()
    return {"status": "ok", "db": "ok"}


# ---------- tasks CRUD (unchanged since A3) ----------
@app.get("/tasks")
def get_all_tasks():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks")
    tasks = cur.fetchall()
    conn.close()
    return [dict(t) for t in tasks]


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


# ---------- auth (new in A4) ----------
@app.post("/auth/signup", status_code=201)
def signup(payload: Credentials):
    try:
        result = get_supabase().auth.sign_up(
            {"email": payload.email, "password": payload.password}
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"user": result.user}


@app.post("/auth/login")
def login(payload: Credentials):
    try:
        result = get_supabase().auth.sign_in_with_password(
            {"email": payload.email, "password": payload.password}
        )
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid login credentials")
    return {
        "access_token": result.session.access_token,
        "refresh_token": result.session.refresh_token,
    }


@app.post("/auth/logout", status_code=204)
def logout(user=Depends(get_current_user)):
    get_supabase().auth.sign_out()


# ---------- public & protected demo routes ----------
@app.get("/public/info")
def public_info():
    return {"message": "Welcome stranger! This info is public."}


@app.get("/protected/profile")
def profile(user=Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "created_at": user.created_at}


@app.get("/protected/dashboard")
def dashboard(user=Depends(get_current_user)):
    return {"message": f"Welcome back, {user.email}"}
