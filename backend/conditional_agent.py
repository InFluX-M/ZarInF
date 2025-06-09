import os
import requests
from typing import List
from langchain.schema import Document, SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from newsapi import NewsApiClient

evaluator_llm = ChatOpenAI(
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
    base_url="https://api.together.xyz/v1",
    api_key=os.getenv("TOGETHER_API_KEY")
)

def fetch_headlines(api_key: str, query: str = "") -> List[str]:
    articles = NewsApiClient(api_key=api_key).get_top_headlines(
        language="en", page_size=50, q=query or None
    ).get("articles", [])
    return [a["title"] for a in articles if a.get("title")]

def build_vector_store(texts: List[str]):
    docs = [Document(page_content=t) for t in texts]
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    return FAISS.from_documents(docs, embeddings)

def get_similar(text: str, store, k: int = 5) -> List[str]:
    return [d.page_content for d in store.similarity_search(text, k=k)]

def fetch_weather(api_key: str, city_id: str = "418863") -> str:
    res = requests.get(f"http://api.openweathermap.org/data/2.5/forecast", params={
        "id": city_id, "appid": api_key, "units": "metric"
    }).json()
    return "\n".join(
        f"{e['dt_txt']}: {e['main']['temp']}°C, {e['weather'][0]['description']}"
        for e in res.get("list", [])[:16]
    )

def evaluate_condition(description: str, news: List[str], weather: str) -> bool:
    messages = [
        SystemMessage(content="""
You are an AI condition evaluator for a smart home.
Given a condition like 'if football news exists' or 'if avg temp > 30', and news + weather data,
reply only 'True' or 'False'.
"""),
        HumanMessage(content=f"Condition: {description}\n\nNews:\n" + "\n".join(f"- {n}" for n in news) +
                     f"\n\nWeather:\n{weather}")
    ]
    return "true" in evaluator_llm.invoke(messages).content.strip().lower()

def handle_condition(description: str) -> bool:
    headlines = fetch_headlines(os.getenv("NEWS_API_KEY"))
    vector_store = build_vector_store(headlines)
    news = get_similar(description, vector_store)
    weather = fetch_weather(os.getenv("OPENWEATHER_API_KEY"))
    return evaluate_condition(description, news, weather)
