# --- agent.py ---
import os
import logging
from datetime import datetime
import dateparser

from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from langchain.tools import tool

from conditional_agent import handle_condition

from dotenv import load_dotenv
load_dotenv()

# Setup logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("log/agent.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# === Tool Definitions ===

@tool
def control_tv(action: str, description: str = "", time_description: str = ""):
    """Turn on/off the TV with optional context like football news or weather."""

    logger.info(f"✅ TV will be turned {action}. Reason: {description}. Time: {time_description}")

@tool
def control_cooler(action: str, description: str = "", time_description: str = ""):
    """Turn on/off the cooler based on weather logic."""
    logger.info(f"✅ Cooler will be turned {action}. Condition: {description}. Time: {time_description}")

@tool
def control_ac(room: str, action: str, time_description: str = ""):
    """Turn on/off the AC in a room."""
    logger.info(f"✅ AC in {room} will be turned {action}. Time: {time_description}")

@tool
def control_lamp(room: str, action: str, time_description: str = ""):
    """Turn on/off the lamp in a room."""
    logger.info(f"✅ Lamp in {room} will be turned {action}. Time: {time_description}")

# === Tool Map and Required Args ===

TOOL_MAP = {
    "control_tv": control_tv,
    "control_cooler": control_cooler,
    "control_ac": control_ac,
    "control_lamp": control_lamp,
}

REQUIRED_ARGS = {
    "control_tv": ["action"],
    "control_cooler": ["action"],
    "control_ac": ["room", "action"],
    "control_lamp": ["room", "action"],
}

# === Time Parsing ===

def parse_time_description(text: str, base: datetime = None) -> datetime | None:
    dt = dateparser.parse(
        text,
        settings={
            "PREFER_DATES_FROM": "future",
            "RELATIVE_BASE": base or datetime.now()
        }
    )
    if dt:
        logger.debug(f"Parsed time '{text}' as {dt.isoformat()}")
    else:
        logger.debug(f"Failed to parse time from '{text}'")
    return dt

# === LLM Setup ===

llm = ChatOpenAI(
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
    base_url="https://api.together.xyz/v1",
    api_key=os.getenv("TOGETHER_API_KEY")
)

tools = list(TOOL_MAP.values())
chat_with_tools = llm.bind_tools(tools)

# === Main User Request Handler ===

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
"""),
        HumanMessage(content=prompt)
    ]

    logger.info(f"Processing user prompt: {prompt}")

    response = chat_with_tools.invoke(messages)
    actions = []

    for call in response.tool_calls:
        fn_name = call.get("name")
        args = call.get("args", {})

        if fn_name not in TOOL_MAP:
            logger.warning(f"Unknown tool function requested: {fn_name}. Skipping.")
            continue

        # Validate required arguments
        missing_args = [arg for arg in REQUIRED_ARGS[fn_name] if arg not in args]
        if missing_args:
            logger.warning(f"Missing required args for {fn_name}: {missing_args}. Skipping this call.")
            continue

        time_str = args.get("time_description", "")
        run_time = parse_time_description(time_str)

        if not run_time:
            logger.warning(f"Could not parse time description '{time_str}', defaulting to now.")
            run_time = datetime.now()

        desc = args.get("description", "")
        condition_met = True
        if desc and fn_name in {"control_tv", "control_cooler"}:
            condition_met = handle_condition(desc)
            logger.info(f"Condition '{desc}' evaluated to {condition_met} for {fn_name}")

        if fn_name in {"control_tv", "control_cooler"} and not condition_met:
            logger.info(f"Skipping {fn_name} due to unmet condition: {desc}")
            continue

        logger.info(f"Scheduling {fn_name} at {run_time.isoformat()} with args: {args}")

        actions.append({
            "function": fn_name,
            "args": args,
            "scheduled_for": run_time,
        })

    return actions
