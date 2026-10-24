"""Frontend API endpoint configuration."""

import math
import os
from typing import Mapping, Optional


LOCAL_API_BASE_URL = "http://localhost:8000"
DEFAULT_API_BASE_URL = "https://llm-evaluation-system-o5uf.onrender.com"
DEFAULT_API_TIMEOUT_SECONDS = 180.0


def _read_secret_value(secrets: Optional[Mapping[str, object]], key: str):
    if secrets is None:
        return None
    try:
        return secrets.get(key)
    except (FileNotFoundError, KeyError):
        return None


def get_api_base_url(
    secrets: Mapping[str, object],
    environment: Optional[Mapping[str, str]] = None,
) -> str:
    """Resolve the API URL from Streamlit secrets, then local dev settings."""
    secret_url = _read_secret_value(secrets, "API_BASE_URL")

    env = environment if environment is not None else os.environ
    candidates = (
        secret_url,
        env.get("AEGISEVAL_API_URL"),
        env.get("API_BASE_URL"),
        DEFAULT_API_BASE_URL,
    )
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip().rstrip("/")
    return LOCAL_API_BASE_URL


def get_api_timeout(
    secrets: Optional[Mapping[str, object]] = None,
    environment: Optional[Mapping[str, str]] = None,
    default: float = DEFAULT_API_TIMEOUT_SECONDS,
) -> float:
    """Resolve the request timeout, allowing deployment overrides without hard-coding 15s."""
    env = environment if environment is not None else os.environ
    secret_map = secrets if secrets is not None else {}

    candidates = (
        _read_secret_value(secret_map, "API_TIMEOUT_SECONDS"),
        env.get("AEGISEVAL_API_TIMEOUT_SECONDS"),
        env.get("API_TIMEOUT_SECONDS"),
        env.get("AEGISEVAL_API_TIMEOUT"),
        env.get("API_TIMEOUT"),
    )
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            try:
                timeout = float(candidate.strip())
            except ValueError:
                continue
        elif isinstance(candidate, (int, float)):
            timeout = float(candidate)
        else:
            continue

        if math.isfinite(timeout) and timeout > 0:
            return timeout

    return float(default)
