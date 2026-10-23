import sqlite3

from backend import database


def test_password_hashes_are_salted_and_verifiable():
    first_hash = database.hash_password("correct horse battery staple")
    second_hash = database.hash_password("correct horse battery staple")

    assert first_hash != second_hash
    assert database.verify_password("correct horse battery staple", first_hash)
    assert not database.verify_password("wrong password", first_hash)
    assert not database.verify_password("password", "pbkdf2_sha256$999999999$00$00")


def test_evaluation_history_and_dashboard_are_isolated_by_user(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "accounts.sqlite3")
    database.initialize_database()

    alice = database.create_user(
        full_name="Alice Example",
        email="Alice@example.com",
        username="Alice",
        password="alice-password",
    )
    bob = database.create_user(
        full_name="Bob Example",
        email="bob@example.com",
        username="bob",
        password="bob-password",
    )
    assert database.get_user_by_username_or_email("ALICE")["id"] == alice["id"]

    database.save_evaluation(
        alice["id"],
        {
            "question": "Question for Alice",
            "response": "Alice's response",
            "verdict": "PASS",
            "overall_score": 9.2,
            "metrics": {"relevance": {"score": 9}},
        },
    )
    database.save_evaluation(
        bob["id"],
        {
            "question": "Question for Bob",
            "response": "Bob's response",
            "verdict": "FAIL",
            "overall_score": 2.1,
            "metrics": {},
        },
    )

    alice_history = database.get_user_evaluations(alice["id"])
    alice_dashboard = database.get_dashboard_summary(alice["id"])
    assert len(alice_history) == 1
    assert alice_history[0]["question"] == "Question for Alice"
    assert alice_dashboard["total_evaluations"] == 1
    assert alice_dashboard["pass_count"] == 1
    assert alice_dashboard["fail_count"] == 0
    assert len(database.get_user_evaluations(bob["id"])) == 1

    with sqlite3.connect(database.DB_PATH) as connection:
        stored_hash = connection.execute(
            "SELECT password_hash FROM users WHERE id = ?",
            (alice["id"],),
        ).fetchone()[0]
    assert stored_hash != "alice-password"
    assert database.verify_password("alice-password", stored_hash)
