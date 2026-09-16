

from setup import agent, groq_client
from langgraph.errors import GraphRecursionError
from reliability import call_with_retry

CHANNEL_HISTORY = []

MAX_MESSAGES = 20

def trim(messages, max_messages=MAX_MESSAGES):
    if len(messages) > max_messages:
        return messages[-max_messages:]
    return messages



def handle_message(sender, text):
    global CHANNEL_HISTORY
    CHANNEL_HISTORY.append({"role": "user", "content": f"{sender}: {text}"})
    CHANNEL_HISTORY = trim(CHANNEL_HISTORY)

    if not should_respond(text, sender):
        print(f"[{sender}]: {text}")
        print("  -> (agent stays silent)\n")
        return

    def _invoke_agent():
        result = agent.invoke({"messages": CHANNEL_HISTORY}, {"recursion_limit": 10})
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
        reply = "I tried looking into this but could not find a clear answer in the docs - you may want to check manually."



    CHANNEL_HISTORY.append({"role": "assistant", "content": reply})
    CHANNEL_HISTORY = trim(CHANNEL_HISTORY)

    print(f"[{sender}]: {text}")
    print(f"  -> agent responds: {reply}\n")



def should_respond(message, sender):
    """
    A separate, lightweight, cheap check - NOT the full agent - deciding
    only whether to engage at all. Note: this has NO access to search_docs,
    so its "yes" decision is a surface-level judgment, not a verified one.
    """
    prompt = f"""You are monitoring a team chat channel as a helpful AI participant.
A new message just arrived from {sender}: "{message}"

Should you respond to this message? Respond with ONLY "yes" or "no".

Respond "yes" ONLY if one of these is true:
- You are directly mentioned or addressed (e.g. "@agent", "does the bot know...", "can you...")
- Someone asks a genuine technical/work-related question that isn't clearly directed at other humans in the channel
- Someone explicitly asks you to remember, track, or remind them of something

Respond "no" if:
- It's casual conversation between coworkers, even if phrased as a question
  (e.g. "does anyone know when standup is" is a question FOR THE GROUP, not for you)
- The question is unrelated to work, technology, or the team's tools
  (e.g. sports, weather, restaurants, general chit-chat)
- It's a reaction, acknowledgment, or filler message ("thanks", "lol", "nvm")

Important: a message being phrased as a question is NOT enough on its own -
many questions in a work chat are directed at teammates, not at you. Only
say yes if the question is genuinely work/technical in nature AND not
clearly addressed to the human group.

explicitly stating that group-phrased questions should still get a "yes" if the topic is clearly technical/tooling-related, overriding the group-phrasing signal in that specific case.

"If search_docs does not contain information that directly confirms or "
"denies a specific claim after 2-3 attempts, say so explicitly rather "
"than answering from general knowledge or continuing to search."

"""

    def _call_groq():
      
      response = groq_client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}]
        )
      return response.choices[0].message.content.strip().lower()

    decision = call_with_retry(_call_groq, fallback="no")
    return "yes" in decision




if __name__ == "__main__":
    handle_message("Priya", "hey does anyone know what time the standup is today")
    handle_message("Raghav", "9:30 as usual I think")
    handle_message("Priya", "cool thanks")
    handle_message("Amit", "@agent can you remind me to review the PR after lunch")
    handle_message("Sara", "@agent how does prompt caching work?")
    handle_message("Raghav", "does anyone know how tool use actually works under the hood")



