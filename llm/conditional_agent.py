import os
from langchain.schema import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

evaluator_llm = ChatOpenAI(
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
    base_url="https://api.together.xyz/v1",
    api_key=os.getenv("TOGETHER_API_KEY")
)

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
{chr(10).join(f"- {n}" for n in context['news_summary'])}

Weather Forecast (next 6 hours): {context['weather_forecast']}
""")
    ]
    result = evaluator_llm.invoke(messages).content.strip().lower()
    return "true" in result
