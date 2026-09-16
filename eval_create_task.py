"""
Labeled eval for create_task - checks whether varied phrasings of a
task request correctly trigger the tool AND produce a sensible task
description, not just an exact one format.
"""

from setup import agent
from langgraph.errors import GraphRecursionError
import setup

test_set = [
    "remind me to review the PR after lunch",
    "don't let me forget to check the deploy tomorrow",
    "can you track that we need to update the docs",
    "make a note to follow up with Sara about the budget",
    "I need a reminder to submit the report by Friday",
]


def evaluate_create_task(test_set):
    setup.TASKS.clear()  # reset before the eval run
    results_log = []

    for text in test_set:
        try:
            result = agent.invoke(
                {"messages": [{"role": "user", "content": text}]},
                {"recursion_limit": 10}
            )
            reply = result["messages"][-1].content
            if isinstance(reply, list):
                reply = reply[0]["text"]
        except GraphRecursionError:
            reply = "[recursion limit hit]"

        results_log.append({"input": text, "reply": reply})

    return results_log, list(setup.TASKS)


if __name__ == "__main__":
    log, tasks_created = evaluate_create_task(test_set)

    print(f"Tasks created: {len(tasks_created)} / {len(test_set)}\n")
    for r in log:
        print(f"Input: {r['input']}")
        print(f"Reply: {r['reply']}\n")

    print("Actual TASKS list contents:")
    for t in tasks_created:
        print(f"  - {t}")