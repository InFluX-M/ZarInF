# --- agent.py ---
import os
import logging
from datetime import datetime
import dateparser

from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from langchain.tools import tool

from conditional_agent import handle_condition, fetch_headlines, fetch_weather

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
def control_tv(action: str, weather_description: str = "", news_description: str = "", time_description: str = ""):
    """Turn on/off the TV with optional context like football news or weather."""
    logger.info(f"✅ TV will be turned {action}. News: {news_description}. Weather: {weather_description}. Time: {time_description}")

@tool
def control_cooler(action: str, weather_description: str = "", news_description: str = "", time_description: str = ""):
    """Turn on/off the cooler based on weather logic."""
    logger.info(f"✅ Cooler will be turned {action}. Weather: {weather_description}. News: {news_description}. Time: {time_description}")

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
You are a smart home assistant. Your job is to turn user commands into tool calls for smart devices.

Tools you can use:
- control_lamp(room, action, time_description)
- control_ac(room, action, time_description)
- control_cooler(action, weather_description, news_description, time_description)
- control_tv(action, weather_description, news_description, time_description)

Rules:
- Use one tool call per action.
- Set `weather_description` only for weather logic (e.g. "hot", "30°C", "avg > 50 in 5h").
- Set `news_description` only for news/events (e.g. "football match", "war").
- Use both if both apply.
- Use `time_description` if there's a schedule (e.g. "in 2 hours").

Examples:
1. If it's hot, turn on the cooler.
→ control_cooler(action='on', weather_description='hot', news_description='', time_description='now')

2. Turn off the kitchen lamp in 1 hour.
→ control_lamp(room='kitchen', action='off', time_description='in 1 hour')

3. If avg weather in next 5 hours is above 50, turn on the cooler.
→ control_cooler(action='on', weather_description='avg > 50 in next 5 hours', news_description='', time_description='now')

4. If there's important war news, turn on the TV.
→ control_tv(action='on', weather_description='', news_description='important war news', time_description='now')

5. If it's hot and there's a football match, turn on the cooler in 1 hour.
→ control_cooler(action='on', weather_description='hot', news_description='football match', time_description='in 1 hour')
"""),
        HumanMessage(content=prompt)
    ]

    logger.info(f"Processing user prompt: {prompt}")

    response = chat_with_tools.invoke(messages)
    actions = []

    news_api_key = os.getenv("NEWS_API_KEY")
    weather_api_key = os.getenv("OPENWEATHER_API_KEY")

    headlines = fetch_headlines(news_api_key)
    if not headlines:
        logger.warning("No headlines fetched, condition may be inaccurate")

    weather_report = fetch_weather(weather_api_key)
    if weather_report == "No weather data available.":
        logger.warning("Weather data unavailable, condition may be inaccurate")

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

        weather_desc = args.get("weather_description", "")
        news_desc = args.get("news_description", "")

        condition_met = [True, True]
        if fn_name in {"control_tv", "control_cooler"}:
            condition_met = handle_condition(weather_desc, news_desc, headlines, weather_report)
            logger.info(f"Weather condition '{weather_desc}' evaluated to {condition_met[0]}")
            logger.info(f"News condition '{news_desc}' evaluated to {condition_met[1]}")

        if fn_name in {"control_tv", "control_cooler"}:
            weather_required = bool(weather_desc.strip())
            news_required = bool(news_desc.strip())

            # Only check conditions if a condition string is provided
            weather_ok, news_ok = condition_met

            if (weather_required and not weather_ok) or (news_required and not news_ok):
                desc = " or ".join(
                    f"{'weather' if i == 0 else 'news'} condition '{weather_desc if i == 0 else news_desc}' not met"
                    for i, met, req in zip(range(2), condition_met, [weather_required, news_required]) if req and not met
                )
                logger.info(f"Skipping {fn_name} due to unmet condition: {desc}")
                continue

        logger.info(f"Scheduling {fn_name} at {run_time.isoformat()} with args: {args}")

        actions.append({
            "function": fn_name,
            "args": args,
            "scheduled_for": run_time,
        })

    return actions
