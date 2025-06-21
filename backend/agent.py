# --- agent.py ---
import os
import logging
from datetime import datetime
import dateparser

from langchain.schema import SystemMessage, HumanMessage
from langchain.tools import tool
from langchain_openai import ChatOpenAI

from conditional_agent import handle_condition, fetch_headlines, fetch_weather, build_vector_store, get_similar

from dotenv import load_dotenv
load_dotenv()

import httpx

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

_cached_headlines = []
_cached_weather_report = ""

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

@tool
def get_news(filter: str = "") -> list[str]:
    """Return news headlines filtered by the given topic. Empty filter returns all."""
    headlines = _cached_headlines
    if filter:
        vector_store = build_vector_store(headlines)
        relevant_news = get_similar(filter, vector_store)
        logger.info(f"Filtered news by '{filter}': {relevant_news}")
        return relevant_news
    else:
        logger.info(f"Returning all news headlines")
        return headlines

@tool
def get_weather(description: str = "") -> str:
    """Return weather info matching the description query."""
    weather_report = _cached_weather_report
    logger.info(f"Fetching weather info for description: '{description}'")
    return weather_report 

# === Tool Map and Required Args ===

TOOL_MAP = {
    "control_tv": control_tv,
    "control_cooler": control_cooler,
    "control_ac": control_ac,
    "control_lamp": control_lamp,
    "get_news": get_news,
    "get_weather": get_weather
}

REQUIRED_ARGS = {
    "control_tv": ["action"],
    "control_cooler": ["action"],
    "control_ac": ["room", "action"],
    "control_lamp": ["room", "action"],
    "get_news": [], 
    "get_weather": []
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

client = httpx.Client(proxies="socks5://127.0.0.1:2080")

llm = ChatOpenAI(
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
    base_url="https://api.together.xyz/v1",
    api_key=os.getenv("TOGETHER_API_KEY"),
    http_client=client
)

"""
llm = ChatOpenAI(
    model="llama3-70b-8192",
    base_url="https://api.groq.com/openai/v1",
    api_key="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",
    http_client=client
)
"""

tools = list(TOOL_MAP.values())
chat_with_tools = llm.bind_tools(tools)

# === Main User Request Handler ===

def handle_user_request(prompt: str):
    global _cached_headlines, _cached_weather_report

    messages = [
SystemMessage(content="""
You are a smart home assistant. Your job is to turn user commands into tool calls for smart devices or info retrieval.

Available tools and valid arguments:
- control_lamp(room, action, time_description)
  - Valid rooms: kitchen, bathroom, room1, room2
- control_ac(room, action, time_description)
  - Valid rooms: room1, kitchen
- control_tv(action, weather_description, news_description, time_description)
  - Only one TV in living room
- control_cooler(action, weather_description, news_description, time_description)
  - Only one cooler, no room

- get_news(filter)
- get_weather(description)

Rules:
- Use one tool call per action.
- Set `weather_description` only for weather logic (e.g. "hot", "30°C", "avg > 50 in 5h").
- Set `news_description` only for news/events (e.g. "football match", "war").
- Use both if both apply.
- Use `time_description` if there's a schedule (e.g. "in 2 hours").
- Never refer to rooms or devices not listed above. E.g., there's no AC in the living room.
- If user asks for an invalid device/room (e.g., “lamp in hallway”), respond: “Sorry, there is no such device in that room.”
- Always match your responses and tool calls to the exact valid values above.

Examples:

1. If it's hot, turn on the cooler.
→ control_cooler(action='on', weather_description='hot', news_description='', time_description='now')

2. Turn off the kitchen lamp in 1 hour.
→ control_lamp(room='kitchen', action='off', time_description='in 1 hour')
"""),
        HumanMessage(content=prompt)
    ]

    logger.info(f"Processing user prompt: {prompt}")

    response = chat_with_tools.invoke(messages)
    actions = []

    news_api_key = os.getenv("NEWS_API_KEY")
    weather_api_key = os.getenv("OPENWEATHER_API_KEY")

    _cached_headlines = fetch_headlines(news_api_key)
    if not _cached_headlines:
        logger.warning("No headlines fetched, condition may be inaccurate")

    _cached_weather_report = fetch_weather(weather_api_key)
    if _cached_weather_report == "No weather data available.":
        logger.warning("Weather data unavailable, condition may be inaccurate")

    for call in response.tool_calls:
        fn_name = call.get("name")
        args = call.get("args", {})

        if fn_name not in TOOL_MAP:
            logger.warning(f"Unknown tool function requested: {fn_name}. Skipping.")
            continue

        missing_args = [arg for arg in REQUIRED_ARGS[fn_name] if arg not in args]
        if missing_args:
            logger.warning(f"Missing required args for {fn_name}: {missing_args}. Skipping this call.")
            continue

        if fn_name in ['get_news', 'get_weather']:
            logger.info(f"Running {fn_name} immediately with args: {args}")
            input_str = ""
            if fn_name == "get_news":
                input_str = args.get("filter", "")
            elif fn_name == "get_weather":
                input_str = args.get("description", "")

            result = TOOL_MAP[fn_name].invoke(input_str)
            logger.info(f"result {fn_name} immediately with args: {args} = {result}")
            actions.append({
                "function": fn_name,
                "args": args,
                "scheduled_for": "Now",
                "result": result
            })
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
            condition_met = handle_condition(weather_desc, news_desc, _cached_headlines, _cached_weather_report)
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
            "result": ''
        })

    return actions
