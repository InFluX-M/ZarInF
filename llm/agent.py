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
Respond with function calls when possible.

Devices:
- Lamps: kitchen, bathroom, room1, room2
- AC units: room1, kitchen
- Cooler: on/off based on weather (e.g., >30°C)
- TV: on/off based on news (e.g., football)

Fields:
- `description`: context like news or weather
- `time_description`: scheduling, e.g., "in 2 hours"
"""),
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