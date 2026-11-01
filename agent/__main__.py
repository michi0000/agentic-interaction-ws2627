import os

from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("MODEL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
DATA_BASE_URL = os.getenv("DATA_BASE_URL")

print(MODEL)
print(OPENAI_BASE_URL)
print(DATA_BASE_URL)