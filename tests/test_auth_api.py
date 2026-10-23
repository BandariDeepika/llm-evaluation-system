import hashlib
import os
import sqlite3

from fastapi.testclient import TestClient

from backend import database
from backend.main import app


def test_registration_evaluation_history_and_logout(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "auth-api.sqlite3")

    with TestClient(app) as alice_client:
        registration = alice_client.post(
            "/auth/register",
            json={
                "full_name": "Alice Example",
                "email": "alice@example.com",
                "username": "alice",
                "password": "alice-password",
                "confirm_password": "alice-password",
            },
        )
        assert registration.status_code == 200
        alice_token = registration.json()["token"]
        assert "password" not in registration.json()["user"]

        evaluation = alice_client.post(
            "/evaluate",
            headers={"Authorization": f"Bearer {alice_token}"},
            json={
                "question": "What is the capital of France?",
                "response": "Paris is the capital of France.",
                "source_document": "Paris is the capital of France.",
                "use_knowledge_base": False,
            },
        )
        assert evaluation.status_code == 200
        assert evaluation.json()["verdict"] in {
            "PASS",
            "NEEDS IMPROVEMENT",
            "FAIL",
        }

        alice_history = alice_client.get(
            "/auth/history",
            headers={"Authorization": f"Bearer {alice_token}"},
        )
        assert alice_history.status_code == 200
        assert len(alice_history.json()["evaluations"]) == 1
        assert alice_history.json()["evaluations"][0]["question"] == (
            "What is the capital of France?"
        )

        login = alice_client.post(
            "/auth/login",
            json={
                "username_or_email": "ALICE",
                "password": "alice-password",
            },
        )
        assert login.status_code == 200

        logout = alice_client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {alice_token}"},
        )
        assert logout.status_code == 200
        assert alice_client.get("/auth/me").status_code == 401

    with TestClient(app) as bob_client:
        bob_registration = bob_client.post(
            "/auth/register",
            json={
                "full_name": "Bob Example",
                "email": "bob@example.com",
                "username": "bob",
                "password": "bob-password",
                "confirm_password": "bob-password",
            },
        )
        assert bob_registration.status_code == 200
        bob_history = bob_client.get("/auth/history")
        assert bob_history.status_code == 200
        assert bob_history.json()["evaluations"] == []


def test_login_upgrades_existing_fixed_salt_hash(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "legacy-auth.sqlite3")
    monkeypatch.setenv("PASSWORD_SALT", "legacy-test-salt")

    with TestClient(app) as client:
        user = database.create_user(
            full_name="Legacy Example",
            email="legacy@example.com",
            username="legacy",
            password="legacy-password",
        )
        legacy_hash = hashlib.pbkdf2_hmac(
            "sha256",
            b"legacy-password",
            os.environ["PASSWORD_SALT"].encode("utf-8"),
            100_000,
        ).hex()
        with sqlite3.connect(database.DB_PATH) as connection:
            connection.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (legacy_hash, user["id"]),
            )

        login = client.post(
            "/auth/login",
            json={
                "username_or_email": "legacy",
                "password": "legacy-password",
            },
        )
        assert login.status_code == 200
        with sqlite3.connect(database.DB_PATH) as connection:
            upgraded_hash = connection.execute(
                "SELECT password_hash FROM users WHERE id = ?",
                (user["id"],),
            ).fetchone()[0]
        assert upgraded_hash.startswith("pbkdf2_sha256$")
        assert database.verify_password("legacy-password", upgraded_hash)
