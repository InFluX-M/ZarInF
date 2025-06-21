import os
import logging
import json
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

from dotenv import load_dotenv
load_dotenv()

import httpx
client = httpx.Client(proxies="socks5://127.0.0.1:2080")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("log/response_agent.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

"""
llm = ChatOpenAI(
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
    base_url="https://api.together.xyz/v1",
    api_key=os.getenv("TOGETHER_API_KEY"),
    temperature=0,
    http_client=client
)
"""

llm = ChatOpenAI(
    model="llama3-70b-8192",
    base_url="https://api.groq.com/openai/v1",
    api_key="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",
    temperature=0,
    http_client=client
)

def make_response(actions: list[dict]) -> str:
    system_content = """
You are a friendly and concise Smart Home Assistant.

- For control actions (lamp, AC, cooler, TV), reply with a natural, grouped sentence. 
- Avoid robotic repetition. Group similar device statuses into a single line.
- Example: Say "Lamps in kitchen and bathroom are on" instead of listing each one separately.
- If all lamps or ACs are on/off, mention them collectively.
- For scheduled actions, include the time naturally and briefly: e.g., "will turn on in 2 hours".
- For weather: give one short sentence summarizing average temperature and main condition.
- For news: respond with a brief headline-style summary. Use 1-2 sentences max.
- Use only 'result' field for news/weather.
- If 'result' is missing or empty, say: “Sorry, I don't have any updates right now.”
- No filler, no preambles like "Here's your update". Just respond directly.
- Ask clarifying questions ONLY if the data is ambiguous or incomplete.
- Use a natural, human-like tone, as if chatting.
"""

    # Get current date and time as a formatted string
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    actions_json = json.dumps(actions, indent=2)

    prompt = f"""
Current date and time: {now_str}

You have these actions performed or scheduled:

{actions_json}

Based on the above, generate a concise, clear, and friendly summary reply.

Examples:

1) Input:
- control_lamp: room=kitchen, action=on, scheduled in 2 hours

Output:
"The kitchen lamp will turn on in 2 hours."

2) Input:
- get_weather with result about temperature and conditions

Output:
"The average temperature today is around 25°C with clear skies."

3) Input:
- get_news with result including news headlines

Output:
"Here are the latest basketball news headlines: NBA Finals kicked off, U.S. Open underway with surprising results."

4) Input:
- get_news with missing or empty result

Output:
"Sorry, I don't have any news updates right now."

Now generate the response.
"""

    messages = [
        SystemMessage(content=system_content),
        HumanMessage(content=prompt)
    ]

    response = llm.invoke(messages)
    logger.info(f"LLM response: {response.content}")

    return response.content
