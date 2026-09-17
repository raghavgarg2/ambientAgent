"""
Wires the working participant-agent logic into a real Slack workspace via
Socket Mode. Channel history now persists to disk (memory.py) instead of
living only in memory - survives script restarts. Long-term memory
extracts durable facts separately, so they survive even after old
messages get trimmed out of channel history.
"""

import os
from health_check import run_startup_checks
from setup import groq_client, vo
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from reliability import call_with_retry
from long_term_memory import load_memory, save_fact, extract_fact

from langgraph.errors import GraphRecursionError

from setup import agent
from week1_participant import should_respond, trim
from memory import load_channel_history, save_channel_history

load_dotenv()

slack_app = App(token=os.getenv("SLACK_BOT_TOKEN"))


@slack_app.event("message")
def handle_slack_message(event, say):
    if event.get("bot_id"):
        return

    channel = event["channel"]
    sender = event.get("user", "unknown")
    text = event.get("text", "")

    history = load_channel_history(channel)
    history.append({"role": "user", "content": f"{sender}: {text}"})
    history = trim(history)

    if not should_respond(text, sender):
        history[-1]["content"] += " [not addressed - off-topic or not directed at agent]"
        save_channel_history(channel, history)
        return

    fact = extract_fact(groq_client, sender, text)
    print(f"[long-term memory check] extracted: {fact}")
    if fact:
        save_fact(channel, fact)

    facts = load_memory(channel)
    messages_for_agent = list(history)
    if facts:
        facts_text = "\n".join(f"- {f}" for f in facts)
        messages_for_agent.insert(0, {
            "role": "user",
            "content": f"[Remembered facts about this channel:\n{facts_text}]"
        })

    def _invoke_agent():
        result = agent.invoke({"messages": messages_for_agent}, {"recursion_limit": 10})
        reply = result["messages"][-1].content
        if isinstance(reply, list):
            reply = reply[0]["text"]
        return reply

    try:
        reply = call_with_retry(
            _invoke_agent,
            max_retries=3,
            fallback="Sorry, I am having trouble connecting right now — please try again in a moment."
        )
    except GraphRecursionError:
        reply = "I tried looking into this but couldn't find a clear answer in the docs — you may want to check manually."

    history.append({"role": "assistant", "content": reply})
    history = trim(history)
    save_channel_history(channel, history)

    say(reply)


if __name__ == "__main__":
    run_startup_checks(groq_client, vo)
    handler = SocketModeHandler(slack_app, os.getenv("SLACK_APP_TOKEN"))
    print("ambient-agent is running. Go send it a message in Slack.")
    handler.start()