


import json
import os

MEMORY_DIR = "channel_memory"


def _memory_path(channel_id):
    os.makedirs(MEMORY_DIR, exist_ok=True)
    return os.path.join(MEMORY_DIR, f"{channel_id}.json")


def load_channel_history(channel_id):
    path = _memory_path(channel_id)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return []


def save_channel_history(channel_id, history):
    path = _memory_path(channel_id)
    with open(path, "w") as f:
        json.dump(history, f, indent=2)