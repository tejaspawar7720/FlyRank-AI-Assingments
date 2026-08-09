from fastapi import FastAPI
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
app = FastAPI()
#class to define the input model for creating a new task
class TaskInput(BaseModel):
    title: str

# to create a new task
@app.post("/tasks", status_code=201)
def create_task(task_input: TaskInput):
    if not task_input.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    
    new_id = len(tasks) + 1
    new_task = {
        "id": new_id,
        "title": task_input.title,
        "done": False
    }
    tasks.append(new_task)
    return new_task

@app.get("/")
def root():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"]
    }

#to check if the API is running
@app.get("/health")
def health():
    return {"status": "ok"}

#tasks data 
tasks = [
    {"id": 1, "title": "Buy groceries", "done": False},
    {"id": 2, "title": "Read a book", "done": False},
    {"id": 3, "title": "Go for a walk", "done": True}
]

#to get all tasks
@app.get("/tasks")
def get_all_tasks():
    return tasks

#  task id to get a specific task
@app.get("/tasks/{id}")
def get_task(id: int):
    for task in tasks:
        if task["id"] == id:
            return task
    raise HTTPException(status_code=404, detail=f"Task {id} not found")

class TaskUpdate(BaseModel):
    title: str = None
    done: bool = None

@app.put("/tasks/{id}")
def update_task(id: int, task_update: TaskUpdate):
    for task in tasks:
        if task["id"] == id:
            if task_update.title is not None:
                if not task_update.title.strip():
                    raise HTTPException(status_code=400, detail="Title cannot be empty")
                task["title"] = task_update.title
            if task_update.done is not None:
                task["done"] = task_update.done
            return task
    raise HTTPException(status_code=404, detail=f"Task {id} not found")

@app.delete("/tasks/{id}", status_code=204)
def delete_task(id: int):
    for i, task in enumerate(tasks):
        if task["id"] == id:
            tasks.pop(i)
            return
    raise HTTPException(status_code=404, detail=f"Task {id} not found")