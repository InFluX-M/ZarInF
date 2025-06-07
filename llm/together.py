import json
from together import Together

client = Together()

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

response = client.chat.completions.create(
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
    messages=[
        {"role": "system", "content": "You are a smart home assistant. Respond with a function call when appropriate."},
        {"role": "user", "content": "Turn on the kitchen light"}
    ],
    tools=tools,
    tool_choice="auto"
)

call = response.choices[0].message.tool_calls[0]
function_name = call.function.name
arguments = json.loads(call.function.arguments)

# Execute the function call
if function_name == "turn_on_device":
    device = arguments['device']
    print(f"Turning on {device}...")
    # Here you would add the code to actually turn on the device
elif function_name == "turn_off_device":
    device = arguments['device']
    print(f"Turning off {device}...")
else:
    print(f"Unknown function: {function_name}")