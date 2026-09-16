"""
Wires the working participant-agent logic into a real Slack workspace via
Socket Mode. Channel history now persists to disk (memory.py) instead of
living only in memory - survives script restarts.
"""


import os
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

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
        # tag this message as deliberately not addressed, so if the agent
    # later runs (triggered by a different message nearby), it doesn't
    # try to retroactively answer something we chose to skip
        history[-1]["content"] += " [not addressed - off-topic or not directed at agent]"
        save_channel_history(channel, history)
        return

    try:
        result = agent.invoke({"messages": history},{"recursion_limit":10})
        reply = result["messages"][-1].content
        if isinstance(reply, list):
           reply = reply[0]["text"]

    except GraphRecursionError:
        reply = "I tried looking into this but couldn't find a clear answer in the docs — you may want to check manually."

    history.append({"role": "assistant", "content": reply})
    history = trim(history)
    save_channel_history(channel, history)

    say(reply)


if __name__ == "__main__":
    handler = SocketModeHandler(slack_app, os.getenv("SLACK_APP_TOKEN"))
    print("ambient-agent is running. Go send it a message in Slack.")
    handler.start()