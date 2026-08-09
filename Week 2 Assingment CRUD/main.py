from fastapi import FastAPI
from fastapi import FastAPI, HTTPException
app = FastAPI()

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


#task id to get a specific task
@app.get("/tasks/{id}")
def get_task(id: int):
    for task in tasks:
        if task["id"] == id:
            return task
    raise HTTPException(status_code=404, detail=f"Task {id} not found")