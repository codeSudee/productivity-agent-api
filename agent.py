import json
import os
from datetime import date, timedelta
from openai import OpenAI
from dotenv import load_dotenv

from tool_schemas import TOOLS
from tools import add_task, list_tasks, complete_task, delete_task

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Maps tool names (as the model sees them) to the real Python functions
AVAILABLE_FUNCTIONS = {
    "add_task": add_task,
    "list_tasks": list_tasks,
    "complete_task": complete_task,
    "delete_task": delete_task,
}

def get_system_prompt():
    today = date.today()
    upcoming_days = []
    for i in range(8):
        d = today + timedelta(days=i)
        label = "Today" if i == 0 else d.strftime("%A")
        upcoming_days.append(f"{label}: {d.isoformat()}")
    date_reference = "\n".join(upcoming_days)

    return f"""You are a helpful personal productivity assistant.
You help the user manage their tasks: adding, listing, completing, and deleting them.

Today is {today.strftime("%A, %Y-%m-%d")}. Here are the next 7 days for reference:
{date_reference}

When the user mentions a relative date (e.g., "Friday", "tomorrow", "next week"), look up the exact YYYY-MM-DD date from the reference above instead of calculating it yourself. If they say "next Friday" and today is not Friday, use the Friday listed above.
When the user refers to a task by description rather than id, use list_tasks first to find the right id.
Be concise and conversational in your replies."""


def run_agent(user_input, conversation_history):
    conversation_history.append({"role": "user", "content": user_input})

    messages = [{"role": "system", "content": get_system_prompt()}] + conversation_history

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=TOOLS,
    )

    response_message = response.choices[0].message

    # If the model wants to call one or more tools
    if response_message.tool_calls:
        conversation_history.append(response_message)

        for tool_call in response_message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            function_to_call = AVAILABLE_FUNCTIONS[function_name]
            function_result = function_to_call(**function_args)

            conversation_history.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(function_result),
            })

        # Call the model again so it can respond using the tool results
        second_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": get_system_prompt()}] + conversation_history,
        )
        final_message = second_response.choices[0].message
        conversation_history.append({"role": "assistant", "content": final_message.content})
        return final_message.content

    # No tool call needed, just a direct reply
    conversation_history.append({"role": "assistant", "content": response_message.content})
    return response_message.content

        
        