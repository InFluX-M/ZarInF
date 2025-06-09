import os
import requests
import logging
from typing import List

from langchain.schema import Document, SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from newsapi import NewsApiClient

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

evaluator_llm = ChatOpenAI(
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
    base_url="https://api.together.xyz/v1",
    api_key=os.getenv("TOGETHER_API_KEY")
)

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
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    store = FAISS.from_documents(docs, embeddings)
    logger.info("Vector store created")
    return store

def get_similar(query: str, store, k: int = 5) -> List[str]:
    logger.debug(f"Searching for top {k} documents similar to: '{query}'")
    results = [doc.page_content for doc in store.similarity_search(query, k=k)]
    logger.info(f"Found {len(results)} similar documents")
    return results

def evaluate_condition(description: str, news: List[str], weather: str) -> bool:
    logger.debug(f"Evaluating condition: '{description}'")
    messages = [
        SystemMessage(content="""
You are an AI condition evaluator for a smart home.
Given a condition like "if football news exists" or "if avg temp > 30",
and current news and weather data, respond only with `True` or `False`.
Do not explain anything.
"""),
        HumanMessage(content=f"Condition: {description}\n\nNews:\n" +
                     "\n".join(f"- {n}" for n in news) +
                     f"\n\nWeather:\n{weather}")
    ]
    try:
        reply = evaluator_llm.invoke(messages).content.strip().lower()
        result = "true" in reply
        logger.info(f"Condition evaluation result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error during condition evaluation: {e}")
        return False

def handle_condition(description: str) -> bool:
    logger.info(f"Handling condition: '{description}'")
    news_api_key = os.getenv("NEWS_API_KEY")
    weather_api_key = os.getenv("OPENWEATHER_API_KEY")

    headlines = fetch_headlines(news_api_key)
    if not headlines:
        logger.warning("No headlines fetched, condition may be inaccurate")

    vector_store = build_vector_store(headlines)
    relevant_news = get_similar(description, vector_store)

    weather_report = fetch_weather(weather_api_key)
    if weather_report == "No weather data available.":
        logger.warning("Weather data unavailable, condition may be inaccurate")

    return evaluate_condition(description, relevant_news, weather_report)
