import os
import requests
import logging
from typing import List

from langchain.schema import Document, SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from newsapi import NewsApiClient
from sentence_transformers import SentenceTransformer

from dotenv import load_dotenv
load_dotenv()

import httpx
client = httpx.Client(proxies="socks5://127.0.0.1:2080")

# Setup logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("log/conditional_agent.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

"""
evaluator_llm = ChatOpenAI(
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
    base_url="https://api.together.xyz/v1",
    api_key=os.getenv("TOGETHER_API_KEY"),
    http_client=client
)
"""

evaluator_llm = ChatOpenAI(
    model="llama3-70b-8192",
    base_url="https://api.groq.com/openai/v1",
    api_key="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",
    http_client=client
)

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def fetch_headlines(api_key: str, query: str = "") -> List[str]:
    try:
        logger.debug(f"Fetching news headlines with query: '{query}'")
        client = NewsApiClient(api_key=api_key)
        articles = client.get_top_headlines(language="en", page_size=50, q=query or None).get("articles", [])
        headlines = [a["title"] for a in articles if a.get("title")]
        logger.info(f"Fetched {len(headlines)} headlines")
        return headlines
    except Exception as e:
        logger.error(f"Failed to fetch headlines: {e}")
        return []

def fetch_weather(api_key: str, city_id: str = "418863") -> str:
    try:
        logger.debug(f"Fetching weather for city_id={city_id}")
        res = requests.get("http://api.openweathermap.org/data/2.5/forecast", params={
            "id": city_id, "appid": api_key, "units": "metric"
        }).json()
        if "list" not in res:
            logger.warning("No weather data found in response")
            return "No weather data available."
        weather_report = "\n".join(
            f"{e['dt_txt']}: {e['main']['temp']}°C, {e['weather'][0]['description']}"
            for e in res["list"][:16]
        )
        logger.info("Fetched weather data successfully")
        return weather_report
    except Exception as e:
        logger.error(f"Failed to fetch weather data: {e}")
        return "No weather data available."

def build_vector_store(texts: List[str]):
    logger.debug(f"Building vector store for {len(texts)} documents")
    docs = [Document(page_content=text) for text in texts]
    store = FAISS.from_documents(docs, embeddings)
    logger.info("Vector store created")
    return store

def get_similar(query: str, store, k: int = 5) -> List[str]:
    logger.debug(f"Searching for top {k} documents similar to: '{query}'")
    results = [doc.page_content for doc in store.similarity_search(query, k=k)]
    logger.info(f"Found {len(results)} similar documents")
    return results

def evaluate_condition(weather_description: str, news_description: str, news: List[str], weather: str) -> tuple[bool, bool]:
    logger.debug(f"Evaluating conditions: weather='{weather_description}', news='{news_description}'")

    messages = [
        SystemMessage(content="""
You are an AI condition evaluator for a smart home system.

You will receive two independent conditions:
1. A weather-related condition (e.g. "if temperature > 30°C")
2. A news-related condition (e.g. "if football match is happening")

You will also receive:
- A list of recent news headlines
- A weather forecast report

❗Your task:
Evaluate each condition separately.
Return exactly two lines:
- `WeatherCondition: True` or `WeatherCondition: False`
- `NewsCondition: True` or `NewsCondition: False`

⚠️ Do NOT explain anything.
"""),
        HumanMessage(content=f"""Weather condition: {weather_description or 'none'}
News condition: {news_description or 'none'}

News headlines:
{chr(10).join(f"- {n}" for n in news)}

Weather forecast:
{weather}
""")
    ]

    try:
        reply = evaluator_llm.invoke(messages).content.strip().lower()
        logger.debug(f"Raw model reply:\n{reply}")

        weather_result = "weathercondition: true" in reply
        news_result = "newscondition: true" in reply

        logger.info(f"Weather condition result: {weather_result}")
        logger.info(f"News condition result: {news_result}")

        return weather_result, news_result
    except Exception as e:
        logger.error(f"Error during condition evaluation: {e}")
        return False, False

def handle_condition(weather_description: str, news_description: str, headlines, weather_report) -> tuple[bool, bool]:
    logger.info(f"Handling condition — weather: '{weather_description}', news: '{news_description}'")

    relevant_news = []
    if len(news_description) > 0:
        vector_store = build_vector_store(headlines)
        relevant_news = get_similar(news_description, vector_store)

    cond = True
    if len(weather_report) > 0 or len(relevant_news) > 0:
        cond = evaluate_condition(weather_description, news_description, relevant_news, weather_report)

    return cond
