import os
from pathlib import Path
import httpx
from dotenv import load_dotenv

# Always load .env from current file's directory
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

api_key = os.getenv("WELLSAID_API_KEY")
base_url = "https://api.wellsaidlabs.com/v1/tts"

if not api_key:
    raise ValueError("WELLSAID_API_KEY environment variable is required")

client = httpx.Client(
    base_url=base_url,
    headers={
        "X-Api-Key": api_key,
        "User-Agent": "WellSaid-MCP/1.0.0",
    }
)