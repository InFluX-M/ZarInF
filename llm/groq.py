import json
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
)

tools = [
    {
        "type": "function",
        "function": {
            "name": "turn_on_device",
            "description": "Turns on a specific home device.",
            "parameters": {
                "type": "object",
                "properties": {
                    "device": {
                        "type": "string",
                        "enum": [
                            "lamp_kitchen", "lamp_bathroom", "lamp_room1", "lamp_room2",
                            "ac_room1", "ac_kitchen", "tv_livingroom"
                        ]
                    }
                },
                "required": ["device"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "turn_off_device",
            "description": "Turns off a specific home device.",
            "parameters": {
                "type": "object",
                "properties": {
                    "device": {
                        "type": "string",
                        "enum": [
                            "lamp_kitchen", "lamp_bathroom", "lamp_room1", "lamp_room2",
                            "ac_room1", "ac_kitchen", "tv_livingroom"
                        ]
                    }
                },
                "required": ["device"]
            }
        }
    }
]

# Send request to Groq's LLM
response = client.chat.completions.create(
    model="llama3-70b-8192",  # or another supported Groq model
    messages=[
        {"role": "system", "content": "You are a smart home assistant. Respond with a function call when appropriate."},
        {"role": "user", "content": "Turn on the kitchen light"}
    ],
    tools=tools,
    tool_choice="auto"
)

# Extract and handle function call
call = response.choices[0].message.tool_calls[0]
function_name = call.function.name
arguments = json.loads(call.function.arguments)

if function_name == "turn_on_device":
    device = arguments['device']
    print(f"Turning on {device}...")
elif function_name == "turn_off_device":
    device = arguments['device']
    print(f"Turning off {device}...")
else:
    print(f"Unknown function: {function_name}")
