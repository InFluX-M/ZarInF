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
"""

def make_response(actions: list[dict]) -> str:
    system_content = """
You are a friendly and concise Smart Home Assistant.

- For scheduled control actions (lamp, AC, cooler, TV): reply with a simple, minimal sentence stating device, action, and time. No extra explanations.
- For weather updates: give a single short sentence summary with average temperature and main condition. No details, no hourly info.
- For news updates: provide a brief but clear summary headline or 2-3 short sentences highlighting main news points.
- Only use info from the 'result' field for weather and news.
- If 'result' missing or empty, say politely no data available.
- Avoid unnecessary explanations or filler.
- Ask clarifying questions ONLY if action data is ambiguous or incomplete.
- Use clear, natural, and warm conversational tone.
- In response don't start with Here's a concise and friendly summary: or sentence like this, just response
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
