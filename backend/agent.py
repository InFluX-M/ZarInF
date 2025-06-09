# --- agent.py ---
import os
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from langchain.tools import tool
import dateparser
from conditional_agent import handle_condition

def parse_time_description(text: str, base: datetime = None) -> datetime | None:
    return dateparser.parse(text, settings={"PREFER_DATES_FROM": "future", "RELATIVE_BASE": base or datetime.now()})

@tool
def control_tv(action: str, description: str = "", time_description: str = ""):
    """Turn on/off the TV with optional context like football news or weather."""
    print(f"✅ TV will be turned {action}. Reason: {description}. Time: {time_description}")

@tool
def control_cooler(action: str, description: str = "", time_description: str = ""):
    """Turn on/off the cooler based on weather logic."""
    print(f"✅ Cooler will be turned {action}. Condition: {description}. Time: {time_description}")

@tool
def control_ac(room: str, action: str, time_description: str = ""):
    """Turn on/off the AC in a room."""
    print(f"✅ AC in {room} will be turned {action}. Time: {time_description}")

@tool
def control_lamp(room: str, action: str, time_description: str = ""):
    """Turn on/off the lamp in a room."""
    print(f"✅ Lamp in {room} will be turned {action}. Time: {time_description}")

llm = ChatOpenAI(
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
    base_url="https://api.together.xyz/v1",
    api_key=os.getenv("TOGETHER_API_KEY")
)

tools = [control_tv, control_cooler, control_ac, control_lamp]
chat_with_tools = llm.bind_tools(tools)

def handle_user_request(prompt: str):
    messages = [
        SystemMessage(content="""
You are a smart home assistant.

When the user gives an instruction, your task is to extract and execute the correct function calls for controlling smart home devices.

✅ Always use tool calls when actions are required.
✅ If the user gives multiple tasks, handle each one as a separate tool call.
✅ Use the `description` field for any context, such as weather or football matches.
✅ Use the `time_description` field for scheduled tasks like "in 2 hours" or "after 30 seconds".

Available devices and their tools:

- `control_lamp(room, action, time_description)`: Lamps in kitchen, bathroom, room1, room2.
- `control_ac(room, action, time_description)`: AC in room1 or kitchen.
- `control_cooler(action, description, time_description)`: Cooler on/off, typically based on hot weather (>30°C).
- `control_tv(action, description, time_description)`: TV on/off, often triggered by events like football or news.

Examples:

1. If it's hot, turn on the cooler in 10 minutes.
→ tool call: control_cooler(action='on', description='hot weather', time_description='in 10 minutes')

2. Turn off the kitchen lamp now.
→ tool call: control_lamp(room='kitchen', action='off', time_description='now')

3. Turn on the TV if there's El Clasico, and also turn on bathroom lamp in 2 minutes.
→ tool call 1: control_tv(action='on', description='El Clasico', time_description='now')
→ tool call 2: control_lamp(room='bathroom', action='on', time_description='in 2 minutes')
""")
,
        HumanMessage(content=prompt)
    ]

    response = chat_with_tools.invoke(messages)
    actions = []

    for call in response.tool_calls:
        fn_name = call["name"]
        args = call["args"]
        time = parse_time_description(args.get("time_description", "")) or datetime.now()
        condition_met = True

        desc = args.get("description", "")
        if desc:
            condition_met = handle_condition(desc)

        if fn_name in {"control_tv", "control_cooler"} and not condition_met:
            continue

        actions.append((fn_name, args, time))

    return actions