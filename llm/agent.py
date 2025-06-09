import os
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from langchain.tools import tool

@tool
def control_tv(action: str, description: str = "", time_description: str = ""):
    """Turn on/off the TV with optional context like football news or weather."""
    return f"TV will be turned {action}. Reason: {description}. Time: {time_description}"

@tool
def control_cooler(action: str, description: str = "", time_description: str = ""):
    """Turn on/off the cooler with weather condition logic."""
    return f"Cooler will be turned {action}. Condition: {description}. Time: {time_description}"

@tool
def control_ac(room: str, action: str, time_description: str = ""):
    """Turn on/off the AC in a specific room."""
    return f"AC in {room} will be turned {action}. Time: {time_description}"

@tool
def control_lamp(room: str, action: str, time_description: str = ""):
    """Turn on/off the lamp in a specific room."""
    return f"Lamp in {room} will be turned {action}. Time: {time_description}"

chat = ChatOpenAI(
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
    base_url="https://api.together.xyz/v1",
    api_key=os.getenv("TOGETHER_API_KEY")
)

tools = [control_tv, control_cooler, control_ac, control_lamp]
chat_with_tools = chat.bind_tools(tools)

messages = [
    SystemMessage(content="""
You are a smart home assistant.
- When the user requests multiple actions, respond with a list of function calls.
- Use fields like `description` for news/weather reasons.
- Use `time_description` for any scheduled times (e.g., 'in 2 hours', 'at 6pm', 'on April 15').

Available devices:
- Lamps: kitchen, bathroom, room1, room2
- AC units: room1, kitchen
- Cooler: can be turned on/off based on weather conditions (e.g., forecast > 30°C)
- TV: can be turned on/off with description like 'football news'

Always respond with function calls if possible.
"""),
    HumanMessage(content="If there’s football news, turn on the TV in 1 hour and  also i want turn on kitchen lamp now.")
]

response = chat_with_tools.invoke(messages)

if response.tool_calls:
    for call in response.tool_calls:
        function_name = call["name"]
        arguments = call["args"]

        match function_name:
            case "control_tv":
                result = control_tv.invoke(arguments)
            case "control_cooler":
                result = control_cooler.invoke(arguments)
            case "control_ac":
                result = control_ac.invoke(arguments)
            case "control_lamp":
                result = control_lamp.invoke(arguments)
            case _:
                result = f"Unknown function: {function_name}"

        print(f"✅ Tool `{function_name}` called with {arguments} → {result}")
else:
    print("🤖 Assistant replied (no tool calls):", response.content)
