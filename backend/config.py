import os

from dotenv import load_dotenv


load_dotenv()


def get_openai_api_key() -> Optional[str]:
    """Return the configured API key without exposing it through the API."""
    return os.getenv("OPENAI_API_KEY")