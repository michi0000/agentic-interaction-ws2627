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

TODAY = datetime.now().strftime("%Y-%m-%d")

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
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

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
                    "message": "Calendar data could not be retrieved. Therefore, it cannot be determined whether any appointments exist (404 File not found)."
                }
            log_event(
                event="tool_result",
                tool="get_calendar",
                args={"date": date},
                ok=False,
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

MAX_STEPS = 20

# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------
def main():
    # check command line arguments
    if len(sys.argv) != 2:
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
            "content": (f"""
                You are an assistant with access to calendar data.

                Current date: {TODAY}

                Rules:
                - Calendar information may ONLY come from tool results.
                - If calendar data is unavailable, say so.
                - Never invent appointments.
                - Never invent dates.
                - Never invent participants.
                - Never invent locations.
                - Resolve relative dates using the current date.
                - You may call tools multiple times.
                - Continue calling tools until you have enough information.
                - Then provide a final answer.
                Never extrapolate calendar results from one day to another.
                Never claim that a date has no appointments
                unless get_calendar was called for exactly that date.
                
                Never summarize a week unless every day of that
                week was loaded from the tool.If information is missing, ask for additional tool calls.

                - General knowledge questions may be answered normally.
                """
            ),
        },
        {
            "role": "user",
            "content": user_task
        }
    ]

    calendar_results = []
    model_call_count = 0
    limit_summary_pending = False

    def report_step_limit_fallback():
        answer = (
            "Execution stopped because the model-call limit was reached. "
            "Calendar results gathered so far: "
            f"{json.dumps(calendar_results, ensure_ascii=False)}. "
            "Dates not listed were not retrieved; please submit a new "
            "request for them."
        )
        print(answer)
        log_event(
            event="error",
            args={"message": "step_limit_reached", "answer": answer},
            ok=False,
        )
        sys.exit(1)

    try:
        while model_call_count < MAX_STEPS:
            start = time.time()
            model_call_count += 1

            if limit_summary_pending:
                limit_instruction = (
                    "The maximum number of model calls has been reached. "
                    "Generate a user-facing partial result in the language "
                    "of the original request using ONLY these calendar "
                    "results:\n"
                    f"{json.dumps(calendar_results, ensure_ascii=False)}\n\n"
                    "List the retrieved appointments and their details. "
                    "Clearly explain that execution stopped because the "
                    "model-call limit was reached. Dates not listed were not "
                    "retrieved, so do not claim whether they have appointments. "
                    "Ask the user to submit a new request for those dates."
                )
                limit_messages = [
                    messages[0],
                    messages[1],
                    {"role": "user", "content": limit_instruction},
                ]
                final_response = client.chat.completions.create(
                    model=MODEL,
                    messages=limit_messages,
                    temperature=0,
                )
                duration_ms = int((time.time() - start) * 1000)
                answer = final_response.choices[0].message.content
                if answer is None:
                    raise ValueError(
                        "Model returned no partial answer at the step limit"
                    )

                print(answer)
                log_event(
                    event="error",
                    args={
                        "message": "step_limit_reached",
                        "answer": answer,
                    },
                    ok=False,
                    duration_ms=duration_ms,
                )
                sys.exit(1)

            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=TOOLS,
                temperature=0,
            )
            duration_ms = int((time.time() - start) * 1000)
            assistant_message = response.choices[0].message

            if not assistant_message.tool_calls:
                answer = assistant_message.content or ""
                print(answer)
                log_event(
                    event="final",
                    args={"answer": answer},
                    ok=True,
                    duration_ms=duration_ms,
                )
                return

            tool_calls = assistant_message.tool_calls
            messages.append(
                {
                    "role": "assistant",
                    "content": assistant_message.content,
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": tool_call.type,
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments,
                            },
                        }
                        for tool_call in tool_calls
                    ],
                }
            )

            for tool_call in tool_calls:
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
                    calendar_results.append(
                        {"date": args["date"], "result": result}
                    )
                else:
                    result = {"error": "Unknown tool"}

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result),
                    }
                )

            if model_call_count >= MAX_STEPS - 1:
                limit_summary_pending = True

        if limit_summary_pending and model_call_count >= MAX_STEPS:
            report_step_limit_fallback()

    except Exception as e:
        log_event(
            event="error",
            args={"message": str(e)},
            ok=False,
        )
        if limit_summary_pending and model_call_count >= MAX_STEPS:
            report_step_limit_fallback()

        error_message = str(e).lower()

        if (
            "429" in error_message
            or "rate limit" in error_message.lower()
            or "tokens per day" in error_message.lower()
        ):
            answer = (
                "The request could not be completed because the API usage limit "
                "has been reached.\n\n"
                "Please wait a few minutes and try again. "
                "If the problem persists, the API quota may need to be increased."
            )

            print(answer)

            log_event(
                event="error",
                args={
                    "message": "rate_limit_reached",
                    "details": error_message,
                },
                ok=False,
            )

            sys.exit(1)



        if (
            "could not be parsed" in error_message
            or isinstance(e, json.JSONDecodeError)
        ):
            recovery_instruction = (
                "The previous model response could not be processed. "
                "Now generate the final answer in the language of the original request, without calling any tools. "
                "The original request and the calendar calls that were actually executed, together with their results, are:\n"
                f"{json.dumps(calendar_results, ensure_ascii=False)}\n"
                "List the retrieved appointments and their details. Use only the calendar results provided above. "
                "Do not claim either appointments or the absence of appointments for any date for which no calendar call is listed. "
                "Explain that the issue occurred after the last listed calendar call; if no calendar call is listed, it occurred before the first call. "
                "Ask the user to submit a new request for any dates that have not yet been retrieved."
            )
            recovery_messages = [
                messages[0],
                messages[1],
                {"role": "user", "content": recovery_instruction},
            ]
            try:
                if model_call_count >= MAX_STEPS:
                    raise ValueError(
                        "Model-call limit reached before parsing recovery"
                    )
                model_call_count += 1
                start = time.time()
                recovery_response = client.chat.completions.create(
                    model=MODEL,
                    messages=recovery_messages,
                    temperature=0,
                )
                duration_ms = int((time.time() - start) * 1000)
                answer = recovery_response.choices[0].message.content
                if answer is None:
                    raise ValueError(
                        "Model returned no final answer after a parsing error"
                    )
                print(answer)
                log_event(
                    event="final",
                    args={"answer": answer},
                    ok=True,
                    duration_ms=duration_ms,
                )
                return
            except Exception as recovery_error:
                if model_call_count >= MAX_STEPS:
                    report_step_limit_fallback()
                log_event(
                    event="error",
                    args={"message": str(recovery_error)},
                    ok=False,
                )
                print(f"Error: {recovery_error}")
                sys.exit(1)

        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()