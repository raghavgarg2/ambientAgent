"""
Persistent task storage - same load/save JSON pattern as memory.py,
applied to tasks instead of channel history.
"""

import json
import os

TASKS_FILE = "tasks.json"


def load_tasks():
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, "r") as f:
            return json.load(f)
    return []


def save_tasks(tasks):
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=2)


def add_task(description):
    tasks = load_tasks()
    tasks.append(description)
    save_tasks(tasks)
    return tasks