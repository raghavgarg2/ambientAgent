"""
Long-term memory: extracts durable facts (preferences, recurring topics)
from a conversation and persists them separately from channel history,
so they survive trimming instead of aging out with old messages.
"""

import json
import os
from reliability import call_with_retry

MEMORY_FILE = "long_term_memory.json"


def load_memory(channel_id):
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            all_memory = json.load(f)
        return all_memory.get(channel_id, [])
    return []


def save_fact(channel_id, fact):
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            all_memory = json.load(f)
    else:
        all_memory = {}

    all_memory.setdefault(channel_id, [])
    if fact not in all_memory[channel_id]:
        all_memory[channel_id].append(fact)

    with open(MEMORY_FILE, "w") as f:
        json.dump(all_memory, f, indent=2)


def extract_fact(groq_client, sender, message):
    """
    Asks the model: is there a durable fact worth remembering here?
    Returns None if not - most messages have nothing worth keeping.
    """
    prompt = f"""A message just arrived from {sender}: "{message}"

Does this contain a durable fact worth remembering long-term (a stated
preference, a recurring responsibility, something that would still be
useful to know weeks from now)? Examples: "I prefer short answers",
"I'm the one who handles deploys".

If yes, respond with ONLY the fact in one short sentence.
If no, respond with ONLY the word "none"."""

    def _call():
        response = groq_client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()

    result = call_with_retry(_call, fallback="none")
    return None if result.lower() == "none" else result