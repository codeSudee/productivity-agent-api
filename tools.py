import json
import os
from datetime import datetime

TASKS_FILE = "tasks.json"


def _load_tasks():
    """Read all tasks from the JSON file."""
    if not os.path.exists(TASKS_FILE):
        return []
    with open(TASKS_FILE, "r") as f:
        return json.load(f)


def _save_tasks(tasks):
    """Write all tasks back to the JSON file."""
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=2)


def add_task(title, due_date=None, notes=None):
    """Add a new task."""
    tasks = _load_tasks()
    new_task = {
        "id": len(tasks) + 1,
        "title": title,
        "due_date": due_date,
        "notes": notes,
        "status": "pending",
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    tasks.append(new_task)
    _save_tasks(tasks)
    return {"success": True, "task": new_task}


def list_tasks(status=None):
    """List tasks, optionally filtered by status ('pending' or 'done')."""
    tasks = _load_tasks()
    if status:
        tasks = [t for t in tasks if t["status"] == status]
    return {"tasks": tasks}


def complete_task(task_id):
    """Mark a task as done by its id."""
    tasks = _load_tasks()
    for t in tasks:
        if t["id"] == task_id:
            t["status"] = "done"
            _save_tasks(tasks)
            return {"success": True, "task": t}
    return {"success": False, "error": f"No task found with id {task_id}"}


def delete_task(task_id):
    """Delete a task by its id."""
    tasks = _load_tasks()
    filtered = [t for t in tasks if t["id"] != task_id]
    if len(filtered) == len(tasks):
        return {"success": False, "error": f"No task found with id {task_id}"}
    _save_tasks(filtered)
    return {"success": True, "deleted_id": task_id}