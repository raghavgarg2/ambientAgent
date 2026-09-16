"""
Startup dependency health check - confirms Groq and Voyage are actually
reachable before the bot starts listening, instead of only discovering
a dead dependency mid-conversation.
"""


def check_groq(groq_client):
    try:
        groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=5
        )
        return True
    except Exception as e:
        print(f"[health check] Groq unreachable: {e}")
        return False


def check_voyage(vo):
    try:
        vo.embed(["ping"], model="voyage-4", input_type="query")
        return True
    except Exception as e:
        print(f"[health check] Voyage unreachable: {e}")
        return False


def run_startup_checks(groq_client, vo):
    print("Running startup dependency checks...")
    groq_ok = check_groq(groq_client)
    voyage_ok = check_voyage(vo)

    print(f"  Groq:   {'OK' if groq_ok else 'DEGRADED'}")
    print(f"  Voyage: {'OK' if voyage_ok else 'DEGRADED'}")

    if not groq_ok:
        print("  WARNING: agent responses will fail until Groq is reachable.")
    if not voyage_ok:
        print("  WARNING: search_docs will fail until Voyage is reachable.")

    return groq_ok, voyage_ok