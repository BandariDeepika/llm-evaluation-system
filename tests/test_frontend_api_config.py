git status
git add frontend/__init__.py frontend/app.py frontend/api_config.py tests/test_frontend_api_config.py
git commit -m "Fix Streamlit frontend API config import path"
git push origin <your-branch-name>import ast
from pathlib import Path

import pytest

import frontend.api_config as api_config
from frontend.api_config import (
    DEFAULT_API_BASE_URL,
    DEFAULT_API_TIMEOUT_SECONDS,
    LOCAL_API_BASE_URL,
    get_api_base_url,
    get_api_timeout,
)


def test_frontend_api_config_imports_from_project_package():
    assert Path(api_config.__file__).resolve() == (
        Path(__file__).resolve().parents[1] / "frontend" / "api_config.py"
    )


def test_app_imported_api_config_names_exist():
    project_root = Path(__file__).resolve().parents[1]
    app_tree = ast.parse((project_root / "frontend" / "app.py").read_text(encoding="utf-8"))
    imported_names = {
        alias.name
        for node in ast.walk(app_tree)
        if isinstance(node, ast.ImportFrom) and node.module == "frontend.api_config"
        for alias in node.names
    }

    assert imported_names
    assert imported_names <= vars(api_config).keys()


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


def test_api_url_defaults_to_render_when_streamlit_secrets_are_unavailable():
    class MissingSecrets:
        def get(self, key):
            raise FileNotFoundError("No secrets.toml found")

    assert get_api_base_url(MissingSecrets(), {}) == DEFAULT_API_BASE_URL


def test_api_url_falls_back_when_secret_is_blank():
    assert get_api_base_url(
        {"API_BASE_URL": "  "},
        {},
    ) == DEFAULT_API_BASE_URL


@pytest.mark.parametrize(
    "secret_value",
    [None, 123, ""],
)
def test_invalid_secret_values_do_not_break_deployed_fallback(secret_value):
    assert get_api_base_url({"API_BASE_URL": secret_value}, {}) == DEFAULT_API_BASE_URL


def test_local_api_can_be_selected_with_environment_override():
    assert get_api_base_url(
        {},
        {"AEGISEVAL_API_URL": LOCAL_API_BASE_URL},
    ) == LOCAL_API_BASE_URL


def test_api_timeout_defaults_to_a_long_read_timeout():
    assert get_api_timeout({}, {}) == DEFAULT_API_TIMEOUT_SECONDS


def test_api_timeout_uses_valid_environment_override():
    assert get_api_timeout(
        {},
        {"AEGISEVAL_API_TIMEOUT_SECONDS": "240"},
    ) == 240


def test_invalid_api_timeout_uses_default():
    assert get_api_timeout(
        {},
        {"AEGISEVAL_API_TIMEOUT_SECONDS": "not-a-timeout"},
    ) == DEFAULT_API_TIMEOUT_SECONDS
