import os
from dotenv import load_dotenv


load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

assert GEMINI_API_KEY, "GEMINI_API_KEY environment variable is not set"