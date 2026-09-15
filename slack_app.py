"""
Wires the working participant-agent logic (from week1_participant.py) into
a real Slack workspace via Socket Mode.

Key change from the terminal version: CHANNEL_HISTORIES is now a dict
keyed by channel ID, not a single global list - each channel needs its
own independent memory, since a real workspace has multiple channels.
"""

import os
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from setup import agent
from week1_participant import should_respond, trim

load_dotenv()

slack_app = App(token=os.getenv("SLACK_BOT_TOKEN"))

CHANNEL_HISTORIES = {}


@slack_app.event("message")
def handle_slack_message(event, say):
    # ignore messages sent BY the bot itself
    if event.get("bot_id"):
        return

    channel = event["channel"]
    sender = event.get("user", "unknown")
    text = event.get("text", "")

    if channel not in CHANNEL_HISTORIES:
        CHANNEL_HISTORIES[channel] = []

    history = CHANNEL_HISTORIES[channel]
    history.append({"role": "user", "content": f"{sender}: {text}"})
    history = trim(history)

    if not should_respond(text, sender):
        CHANNEL_HISTORIES[channel] = history
        return

    result = agent.invoke({"messages": history})
    reply = result["messages"][-1].content
    if isinstance(reply, list):
        reply = reply[0]["text"]

    history.append({"role": "assistant", "content": reply})
    CHANNEL_HISTORIES[channel] = trim(history)

    say(reply)


if __name__ == "__main__":
    handler = SocketModeHandler(slack_app, os.getenv("SLACK_APP_TOKEN"))
    print("ambient-agent is running. Go send it a message in Slack.")
    handler.start()