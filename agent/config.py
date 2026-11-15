import os

from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

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

client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL,
)
