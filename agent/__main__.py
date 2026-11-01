import os
import sys
import requests
import json
import time
import uuid

from datetime import datetime, timezone
from dotenv import load_dotenv
from openai import OpenAI

# ------------------------------------------------------------------
# Load configuration from environment
# ------------------------------------------------------------------
# Environment variables must take precedence over .env values
load_dotenv(override=False)

MODEL = os.getenv("MODEL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
DATA_BASE_URL = os.getenv("DATA_BASE_URL")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not set")
if not OPENAI_BASE_URL:
    raise ValueError("OPENAI_BASE_URL not set")
if not MODEL:
    raise ValueError("MODEL not set")
if not DATA_BASE_URL:
    raise ValueError("DATA_BASE_URL not set")

# ------------------------------------------------------------------
# OpenAI Client
# ------------------------------------------------------------------
client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL,
)

# ------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------
RUN_ID = str(uuid.uuid4())
os.makedirs("logs", exist_ok=True)
LOG_FILE = os.path.join("logs", f"{RUN_ID}.log")

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def log_event(
    event: str,
    ok: bool = True,
    tool: str | None = None,
    args: dict | None = None,
    duration_ms: int | None = None,
):
    entry = {
        "ts": now_iso(),
        "run_id": RUN_ID,
        "event": event,
        "tool": tool,
        "args": args,
        "ok": ok,
        "model": MODEL,
        "duration_ms": duration_ms,
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

# ------------------------------------------------------------------
# Tool
# ------------------------------------------------------------------

#Loads all appointments for a specific calendar day.
def get_calendar(date: str):
    """
    Reads one calendar day from the mock endpoint.
    """
    start = time.time()
    url = f"{DATA_BASE_URL}/calendar/{date}.json"
    try:
        response = requests.get(url, timeout=10)
        duration_ms = int((time.time() - start) * 1000)
        if response.status_code == 404:
            result = {
                    "date": date,
                    "found": False,
                    "message": "No calendar data available."
                }
            log_event(
                event="tool_result",
                tool="get_calendar",
                args={"date": date},
                ok=True,
                duration_ms=duration_ms,
            )
            return result
        response.raise_for_status()
        result = response.json()
        log_event(
                event="tool_result",
                tool="get_calendar",
                args={"date": date},
                ok=True,
                duration_ms=duration_ms,
            )
        return result
    except Exception as e:
        duration_ms = int((time.time() - start) * 1000)
        log_event(
            event="tool_result",
            tool="get_calendar",
            args={"date": date},
            ok=False,
            duration_ms=duration_ms,
        )
        return {
            "error": str(e)
        }

# ------------------------------------------------------------------
# Tool Definition
# ------------------------------------------------------------------
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_calendar",
            "description": (
                "Read appointments from the calendar "
                "for a specific day. "
                "Use this whenever the user asks about "
                "events, appointments, meetings or plans "
                "for a date."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date in format YYYY-MM-DD"
                    }
                },
                "required": ["date"]
            }
        }
    }
]

# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------
def main():
    # check command line arguments
    if len(sys.argv) < 2:
        print("Usage: python -m agent \"your question\"")
        sys.exit(1)

    # read user task from command line
    user_task = sys.argv[1]

    log_event(
        event="user_task",
        args={"task": user_task},
        ok=True,
    )
    # messages for the first model call
    messages = [
        {
            "role": "system",
            "content": ("""
                You answer questions about a calendar. 
                If a user asks about a specific day, 
                use the available tool.
                You ONLY know information that is obtained through tool calls.
                You may:
                - summarize tool results
                - compare tool results with the user's question
                - explain why a requested event cannot be found
                You may not:
                - invent appointments
                - invent dates
                - invent participants
                - invent locations
                Never use general knowledge.
                Never make assumptions.
                """
            ),
        },
        {
            "role": "user",
            "content": user_task
        }
    ]

    try:
        start = time.time()
        # first model call
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            temperature=0
        )
        duration_ms = int((time.time() - start) * 1000)
        # extract tool call from model response
        assistant_message = response.choices[0].message

        # ----------------------------------------------------------
        # Tool Call
        # ----------------------------------------------------------
        if assistant_message.tool_calls:
            tool_call = assistant_message.tool_calls[0]
            tool_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            
            log_event(
                event="tool_call",
                tool=tool_name,
                args=args,
                ok=True,
                duration_ms=duration_ms,
            )
            if tool_name == "get_calendar":
                result = get_calendar(args["date"])
            else:
                result = {"error": "Unknown tool"}

            # Return tool result to the model
            # Add the tool call to the messages list
            messages.append(assistant_message) 
            # Add the tool result to the messages list
            messages.append(
                {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result)
                }
            )
            start = time.time()

            # Second model call with tool result 
            final_response = client.chat.completions.create(
                model=MODEL,
                messages=messages
            )    
            duration_ms = int((time.time() - start) * 1000)       

            # Extract the final answer from the model response
            answer = final_response.choices[0].message.content
        else:
            # No tool call was made, just return the model's response
            answer = assistant_message.content
        print(answer)
        log_event(
            event="final",
            args={"answer": answer},
            ok=True,
            duration_ms=duration_ms,
        )
    except Exception as e:
        log_event(
            event="error",
            args={"message": str(e)},
            ok=False,
        )
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()