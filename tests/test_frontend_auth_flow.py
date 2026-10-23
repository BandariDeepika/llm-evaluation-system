from unittest.mock import patch

from streamlit.testing.v1 import AppTest


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code
        self.ok = status_code < 400
        self.text = ""

    def json(self):
        return self.payload

    def raise_for_status(self):
        if not self.ok:
            raise RuntimeError(self.text)


def test_registration_returns_to_login_without_authenticating():
    registered_user = {"id": 1, "full_name": "New User"}
    with patch(
        "requests.post",
        return_value=FakeResponse({"token": "registration-token", "user": registered_user}),
    ) as post:
        app = AppTest.from_file("frontend/app.py", default_timeout=30).run()
        app.radio[0].set_value("Register").run()
        for field, value in zip(
            app.text_input,
            [
                "New User",
                "new@example.com",
                "newuser",
                "new-user-password",
                "new-user-password",
            ],
        ):
            field.set_value(value)
        app.button[0].click().run()

    assert not app.exception
    assert post.call_args.args[0].endswith("/auth/register")
    assert "auth_token" not in app.session_state
    assert app.session_state["auth_mode"] == "Login"
    assert app.radio[0].value == "Login"
    assert any("Registration successful. Please log in" in item.value for item in app.success)
    assert not any(item.label == "Navigation" for item in app.radio)


def test_login_opens_protected_app_and_logout_returns_to_login():
    user = {
        "id": 2,
        "full_name": "Existing User",
        "email": "existing@example.com",
        "username": "existing",
    }

    def fake_post(url, **kwargs):
        if url.endswith("/auth/login"):
            return FakeResponse({"token": "valid-session-token", "user": user})
        if url.endswith("/auth/logout"):
            return FakeResponse({"message": "Logged out successfully."})
        raise AssertionError(f"Unexpected POST endpoint: {url}")

    def fake_get(url, **kwargs):
        if url.endswith("/auth/me"):
            return FakeResponse(user)
        if url.endswith("/auth/dashboard"):
            return FakeResponse(
                {
                    "total_evaluations": 0,
                    "pass_count": 0,
                    "needs_improvement_count": 0,
                    "fail_count": 0,
                    "evaluations": [],
                }
            )
        raise AssertionError(f"Unexpected GET endpoint: {url}")

    with patch("requests.post", side_effect=fake_post), patch(
        "requests.get", side_effect=fake_get
    ):
        app = AppTest.from_file("frontend/app.py", default_timeout=30).run()
        app.text_input[0].set_value("existing")
        app.text_input[1].set_value("existing-password")
        next(button for button in app.button if button.label == "Login").click().run()

        assert not app.exception
        assert app.session_state["auth_token"] == "valid-session-token"
        assert any(item.label == "Navigation" for item in app.radio)
        assert any("AegisEval Dashboard" in item.value for item in app.markdown)

        next(button for button in app.button if button.label == "Log out").click().run()

    assert not app.exception
    assert "auth_token" not in app.session_state
    assert app.session_state["auth_mode"] == "Login"
    assert app.radio[0].value == "Login"
    assert any(item.label == "Username or email" for item in app.text_input)
