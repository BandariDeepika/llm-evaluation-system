import pytest

from frontend.api_config import LOCAL_API_BASE_URL, get_api_base_url


def test_api_url_prefers_streamlit_secret_and_removes_trailing_slash():
    assert get_api_base_url(
        {"API_BASE_URL": "https://aegiseval-api.example.com/"},
        {"AEGISEVAL_API_URL": "http://localhost:8000"},
    ) == "https://aegiseval-api.example.com"


def test_api_url_uses_existing_environment_override_when_secret_is_missing():
    assert get_api_base_url(
        {},
        {"AEGISEVAL_API_URL": "https://api-from-env.example.com/"},
    ) == "https://api-from-env.example.com"


def test_api_url_falls_back_to_local_when_streamlit_secrets_are_unavailable():
    class MissingSecrets:
        def get(self, key):
            raise FileNotFoundError("No secrets.toml found")

    assert get_api_base_url(MissingSecrets(), {}) == LOCAL_API_BASE_URL


def test_api_url_falls_back_when_secret_is_blank():
    assert get_api_base_url(
        {"API_BASE_URL": "  "},
        {},
    ) == LOCAL_API_BASE_URL


@pytest.mark.parametrize(
    "secret_value",
    [None, 123, ""],
)
def test_invalid_secret_values_do_not_break_local_fallback(secret_value):
    assert get_api_base_url({"API_BASE_URL": secret_value}, {}) == LOCAL_API_BASE_URL
