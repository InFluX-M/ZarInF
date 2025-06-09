import os
import requests
from langchain.schema import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from newsapi import NewsApiClient
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from langchain_huggingface import HuggingFaceEmbeddings

evaluator_llm = ChatOpenAI(
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
    base_url="https://api.together.xyz/v1",
    api_key=os.getenv("TOGETHER_API_KEY")
)

def fetch_today_headlines(api_key: str, query=""):
    newsapi = NewsApiClient(api_key=api_key)
    top_headlines = newsapi.get_top_headlines(language='en', page_size=50, q=query or None)
    return [article['title'] for article in top_headlines['articles'] if article.get("title")]

def create_vector_store_from_headlines(headlines: list[str]):
    docs = [Document(page_content=h) for h in headlines]
    embedding_model = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    vector_store = FAISS.from_documents(docs, embedding_model)
    return vector_store

def retrieve_relevant_headlines(description: str, vector_store, k=5):
    return [doc.page_content for doc in vector_store.similarity_search(description, k=k)]

def fetch_weather_forecast(api_key: str, id: str = "418863"):
    url = f"http://api.openweathermap.org/data/2.5/forecast?id={id}&appid={api_key}&units=metric"
    resp = requests.get(url)
    data = resp.json()
    hourly_forecast = []
    for entry in data.get("list", [])[:16]:  # 48 hours, 3h intervals
        time = entry['dt_txt']
        temp = entry['main']['temp']
        description = entry['weather'][0]['description']
        hourly_forecast.append(f"{time}: {temp}°C, {description}")
    return "\n".join(hourly_forecast)

def evaluate_condition_llm(description: str, context: dict) -> bool:
    messages = [
        SystemMessage(content="""
You are an AI condition evaluator for a smart home.
The user gives a conditional description (e.g., "if football news exists", "if avg temp > 30").
You're also given external data like news or weather.
Decide whether the condition is currently satisfied.
Reply only `True` or `False`.
"""),
        HumanMessage(content=f"""
Condition: {description}

News Summary:
{'\n'.join(f"- {n}" for n in context['news_summary'])}

Weather Forecast (next 48 hours):
{context['weather_forecast']}
""")
    ]

    result = evaluator_llm.invoke(messages).content.strip().lower()
    return "true" in result

def handle_conditional_description(conditional_description: str):
    headlines = fetch_today_headlines(os.getenv('NEWS_API_KEY'))
    vector_store = create_vector_store_from_headlines(headlines)
    relevant_news = retrieve_relevant_headlines(conditional_description, vector_store)

    weather_forecast = fetch_weather_forecast(os.getenv('OPENWEATHER_API_KEY'), "418863")

    context = {
        "news_summary": relevant_news,
        "weather_forecast": weather_forecast
    }

    return evaluate_condition_llm(conditional_description, context)

if __name__ == "__main__":
    description = "if football news exists or if average temperature in next 6 hours > 30°C"
    print("✅ Condition Satisfied?" if handle_conditional_description(description) else "❌ Condition Not Met.")
