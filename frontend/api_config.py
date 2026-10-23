"""Frontend API endpoint configuration."""

import os
from typing import Mapping, Optional


LOCAL_API_BASE_URL = "http://localhost:8000"


def get_api_base_url(
    secrets: Mapping[str, object],
    environment: Optional[Mapping[str, str]] = None,
) -> str:
    """Resolve the API URL from Streamlit secrets, then local dev settings."""
    try:
        secret_url = secrets.get("API_BASE_URL")
    except (FileNotFoundError, KeyError):
        secret_url = None

    env = environment if environment is not None else os.environ
    candidates = (secret_url, env.get("AEGISEVAL_API_URL"), LOCAL_API_BASE_URL)
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip().rstrip("/")
    return LOCAL_API_BASE_URL
