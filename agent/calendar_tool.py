import time

import requests

from .config import DATA_BASE_URL
from .event_logger import log_event


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
                "message": (
                    "Calendar data could not be retrieved. Therefore, it "
                    "cannot be determined whether any appointments exist "
                    "(404 File not found)."
                ),
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
