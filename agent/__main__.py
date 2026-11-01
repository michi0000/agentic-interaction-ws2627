import os

from dotenv import load_dotenv

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

print(MODEL)