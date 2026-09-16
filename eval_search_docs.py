"""
Labeled eval for search_docs - checks whether it retrieves the correct
topic for a set of known questions, using the same topic-metadata
accuracy pattern from Project 1.
"""

from setup import collection, vo

test_set = [
    {"query": "How can I make responses appear word by word instead of all at once?", "expected_topic": 3},
    {"query": "How do I make the model call a real function in my code?", "expected_topic": 0},
    {"query": "How can I reduce cost when sending the same long system prompt repeatedly?", "expected_topic": 1},
    {"query": "How do I get the model to answer using my own private documents?", "expected_topic": 6},
    {"query": "What happens if my conversation gets too long for the model to handle?", "expected_topic": 5},
    {"query": "How can I force the model to return data in a specific format?", "expected_topic": 4},
    {"query": "How do I process thousands of requests without doing them one by one?", "expected_topic": 8},
    {"query": "How can I check that the model's answer is actually backed by the source document?", "expected_topic": 9},
]


def evaluate_search_docs(test_set, n_results=2):
    queries = [item["query"] for item in test_set]
    query_embeddings = vo.embed(queries, model="voyage-4", input_type="query").embeddings

    correct = 0
    results_log = []

    for item, query_embedding in zip(test_set, query_embeddings):
        results = collection.query(query_embeddings=[query_embedding], n_results=n_results)
        retrieved_topics = [m["topic"] for m in results["metadatas"][0]]

        found = item["expected_topic"] in retrieved_topics
        correct += found

        results_log.append({
            "query": item["query"],
            "expected_topic": item["expected_topic"],
            "retrieved_topics": retrieved_topics,
            "found": found
        })

    accuracy = correct / len(test_set)
    return accuracy, results_log


if __name__ == "__main__":
    accuracy, log = evaluate_search_docs(test_set)
    print(f"search_docs accuracy: {accuracy * 100:.0f}%\n")
    for r in log:
        status = "✅" if r["found"] else "❌"
        print(f"{status} {r['query']} (expected {r['expected_topic']}, got {r['retrieved_topics']})")