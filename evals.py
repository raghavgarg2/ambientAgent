"""
Labeled eval for should_respond: measures how often the engagement-decision
logic gets it right, instead of eyeballing a handful of example messages.
"""

from setup import groq_client
from week1_participant import should_respond

test_set = [
    {"sender": "Priya", "text": "does anyone know when standup is", "expected": False},
    {"sender": "Raghav", "text": "9:30 I think", "expected": False},
    {"sender": "Priya", "text": "thanks!", "expected": False},
    {"sender": "Raghav", "text": "lol yeah that meeting ran long", "expected": False},
    {"sender": "Sara", "text": "what's everyone working on today", "expected": False},
    {"sender": "Amit", "text": "@agent remind me to review the PR after lunch", "expected": True},
    {"sender": "Sara", "text": "@agent how does prompt caching work?", "expected": True},
    {"sender": "Raghav", "text": "does anyone know how tool use actually works under the hood", "expected": True},
    {"sender": "Amit", "text": "can someone explain what embeddings are", "expected": True},
    {"sender": "Priya", "text": "can you remind me to check the deploy tomorrow", "expected": True},
    {"sender": "Sara", "text": "does the bot know anything about streaming?", "expected": True},
    {"sender": "Raghav", "text": "anyone free for lunch", "expected": False},
    {"sender": "Amit", "text": "the deploy failed again ugh", "expected": False},
    {"sender": "Priya", "text": "can you remind everyone that Sara is out tomorrow", "expected": True},
    {"sender": "Sara", "text": "nvm figured it out", "expected": False},

    # general-knowledge questions - answerable without search_docs at all,
    # testing whether should_respond captures "helpable" beyond doc lookups
    {"sender": "Amit", "text": "what's a REST API anyway", "expected": True},
    {"sender": "Priya", "text": "quick question, what does JSON stand for", "expected": True},

    # off-domain questions - genuine questions, but clearly outside scope,
    # a different failure mode than casual banter
    {"sender": "Raghav", "text": "who won the match last night", "expected": False},
    {"sender": "Sara", "text": "any good restaurant recommendations nearby", "expected": False},
    {"sender": "Amit", "text": "what's the weather like today", "expected": False},


    # adversarial round 2: testing the NEW rule's blind spots

{"sender": "Amit", "text": "does anyone know why this keeps timing out", "expected": True},
# genuinely technical-sounding, group-phrased - tests whether vague-but-plausible
# technical topics correctly get picked up, not just clean keyword matches

{"sender": "Priya", "text": "does anyone know if Raghav finished the deploy script", "expected": False},
# contains a technical word ("deploy") but is actually asking about a
# COLLEAGUE's work status, not something the agent could answer

{"sender": "Sara", "text": "@agent what's a good name for our new mascot", "expected": True},
# explicit mention, but genuinely off-topic/silly - tests whether explicit
# addressing alone is enough to trigger a response, independent of topic relevance

{"sender": "Raghav", "text": "lol anyway does anyone know how tool use works, kind of curious", "expected": True},
# casual tone wrapped around a real technical question - tests whether
# informal phrasing accidentally suppresses a genuine question

{"sender": "Amit", "text": "does anyone know why my streaming service keeps buffering", "expected": False},
# "streaming" is literally a topic in the dataset, but this is about
# Netflix/personal streaming, not the docs - tests keyword-overlap false positives
]


def evaluate_should_respond(test_set):
    import time
    correct = 0
    results_log = []

    for i, item in enumerate(test_set):
        predicted = should_respond(item["text"], item["sender"])
        is_correct = predicted == item["expected"]
        correct += is_correct

        results_log.append({
            "sender": item["sender"],
            "text": item["text"],
            "expected": item["expected"],
            "predicted": predicted,
            "correct": is_correct
        })

        if (i + 1) % 4 == 0:  # pause every 4 requests to stay under the per-minute cap
            time.sleep(15)

    accuracy = correct / len(test_set)
    return accuracy, results_log


if __name__ == "__main__":
    accuracy, log = evaluate_should_respond(test_set)
    print(f"should_respond accuracy: {accuracy * 100:.0f}%\n")

    for r in log:
        status = "✅" if r["correct"] else "❌"
        print(f"{status} [{r['sender']}]: {r['text']}")
        print(f"    expected={r['expected']}, predicted={r['predicted']}")





