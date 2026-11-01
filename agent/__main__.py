import os
import sys
import requests

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

#Loads all appointments for a specific calendar day.
def get_calendar(date: str):
    """
    Reads one calendar day from the mock endpoint.
    """
    url = f"{DATA_BASE_URL}/calendar/{date}.json"
    response = requests.get(url)
    if response.status_code == 404:
        return {"error":"No calendar data found"}
    response.raise_for_status()
    return response.json()

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

print(
    get_calendar("2026-11-02")
)

# read user task from command line
user_task = sys.argv[1]
