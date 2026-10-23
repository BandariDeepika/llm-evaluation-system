import hashlib
import hmac
import json
import os
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BASE_DIR / "data" / "aegiseval.db"
DB_PATH = Path(os.getenv("APP_DATABASE_PATH", str(DEFAULT_DB_PATH)))
PASSWORD_HASH_ITERATIONS = 600_000


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _format_timestamp(value: Optional[datetime] = None) -> str:
    dt = value or _utc_now()
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def get_db_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(DB_PATH))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database() -> None:
    with get_db_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token_hash TEXT NOT NULL UNIQUE,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);

            CREATE TABLE IF NOT EXISTS evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                question TEXT NOT NULL,
                response TEXT NOT NULL,
                reference_answer TEXT,
                verdict TEXT,
                overall_score REAL,
                metrics_json TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_evaluations_user_id ON evaluations(user_id);
            """
        )


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_HASH_ITERATIONS,
    )
    return f"pbkdf2_sha256${PASSWORD_HASH_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    if password_hash.startswith("pbkdf2_sha256$"):
        try:
            algorithm, iterations, salt_hex, digest_hex = password_hash.split("$")
            if algorithm != "pbkdf2_sha256":
                return False
            iteration_count = int(iterations)
            if not 100_000 <= iteration_count <= 2_000_000:
                return False
            expected = bytes.fromhex(digest_hex)
            actual = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                bytes.fromhex(salt_hex),
                iteration_count,
            )
            return hmac.compare_digest(actual, expected)
        except (ValueError, TypeError):
            return False

    # Verify and upgrade hashes created by the earlier fixed-salt implementation.
    legacy_salt = os.getenv("PASSWORD_SALT", "aegiseval-default-salt").encode("utf-8")
    legacy_digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        legacy_salt,
        100_000,
    ).hex()
    return hmac.compare_digest(legacy_digest, password_hash)


def update_user_password_hash(user_id: int, password: str) -> None:
    with get_db_connection() as connection:
        connection.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (hash_password(password), user_id),
        )


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_user(full_name: str, email: str, username: str, password: str) -> dict[str, Any]:
    normalized_email = email.strip().lower()
    normalized_username = username.strip().lower()
    normalized_full_name = full_name.strip()

    if not normalized_full_name or not normalized_email or not normalized_username:
        raise ValueError("Full name, email, and username are required.")

    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")

    with get_db_connection() as connection:
        existing_email = connection.execute(
            "SELECT id FROM users WHERE lower(email) = lower(?)",
            (normalized_email,),
        ).fetchone()
        if existing_email:
            raise ValueError("An account with that email already exists.")

        existing_username = connection.execute(
            "SELECT id FROM users WHERE lower(username) = lower(?)",
            (normalized_username,),
        ).fetchone()
        if existing_username:
            raise ValueError("That username is already in use.")

        cursor = connection.execute(
            """
            INSERT INTO users (full_name, email, username, password_hash, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                normalized_full_name,
                normalized_email,
                normalized_username,
                hash_password(password),
                _format_timestamp(),
            ),
        )

        user_id = cursor.lastrowid
        user = connection.execute(
            "SELECT id, full_name, email, username, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        return dict(user)


def get_user_by_id(user_id: int) -> Optional[dict[str, Any]]:
    with get_db_connection() as connection:
        row = connection.execute(
            "SELECT id, full_name, email, username, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        return dict(row) if row else None


def get_user_by_username_or_email(username_or_email: str) -> Optional[dict[str, Any]]:
    lookup = username_or_email.strip()
    if not lookup:
        return None

    with get_db_connection() as connection:
        row = connection.execute(
            """
            SELECT id, full_name, email, username, password_hash, created_at
            FROM users
            WHERE lower(username) = lower(?) OR lower(email) = lower(?)
            LIMIT 1
            """,
            (lookup, lookup),
        ).fetchone()
        return dict(row) if row else None


def issue_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    expiry = _utc_now() + timedelta(days=7)

    with get_db_connection() as connection:
        connection.execute(
            "INSERT INTO sessions (user_id, token_hash, expires_at, created_at) VALUES (?, ?, ?, ?)",
            (user_id, hash_token(token), _format_timestamp(expiry), _format_timestamp()),
        )

    return token


def verify_session_token(token: str) -> Optional[dict[str, Any]]:
    if not token:
        return None

    token_hash = hash_token(token)
    now = _format_timestamp()

    with get_db_connection() as connection:
        row = connection.execute(
            """
            SELECT s.user_id, s.expires_at, u.id, u.full_name, u.email, u.username, u.created_at
            FROM sessions s
            JOIN users u ON u.id = s.user_id
            WHERE s.token_hash = ? AND s.expires_at > ?
            LIMIT 1
            """,
            (token_hash, now),
        ).fetchone()

        if not row:
            return None

        return {
            "id": row["id"],
            "full_name": row["full_name"],
            "email": row["email"],
            "username": row["username"],
            "created_at": row["created_at"],
        }


def revoke_session(token: str) -> None:
    if not token:
        return
    with get_db_connection() as connection:
        connection.execute(
            "DELETE FROM sessions WHERE token_hash = ?",
            (hash_token(token),),
        )


def save_evaluation(user_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    question = str(payload.get("question", "")).strip()
    response = str(payload.get("response", "")).strip()
    reference_answer = payload.get("reference_answer")
    verdict = payload.get("verdict")
    overall_score = payload.get("overall_score")
    metrics_json = json.dumps(payload, default=str)

    with get_db_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO evaluations (
                user_id, question, response, reference_answer, verdict, overall_score, metrics_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                question,
                response,
                reference_answer,
                verdict,
                overall_score,
                metrics_json,
                _format_timestamp(),
            ),
        )

        row = connection.execute(
            "SELECT * FROM evaluations WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()

    if row:
        return dict(row)

    raise ValueError("Evaluation record could not be saved.")


def get_user_evaluations(user_id: int, limit: Optional[int] = None) -> list[dict[str, Any]]:
    query = """
        SELECT id, user_id, question, response, reference_answer, verdict, overall_score, metrics_json, created_at
        FROM evaluations
        WHERE user_id = ?
        ORDER BY created_at DESC
    """
    params: list[Any] = [user_id]
    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)

    with get_db_connection() as connection:
        rows = connection.execute(query, params).fetchall()

    return [dict(row) for row in rows]


def get_dashboard_summary(user_id: int) -> dict[str, Any]:
    evaluations = get_user_evaluations(user_id)
    total = len(evaluations)
    verdict_counts = {"PASS": 0, "NEEDS IMPROVEMENT": 0, "FAIL": 0}
    scores: list[float] = []

    for item in evaluations:
        verdict = str(item.get("verdict") or "").strip().upper()
        if verdict in verdict_counts:
            verdict_counts[verdict] += 1

        value = item.get("overall_score")
        try:
            if value is not None:
                scores.append(float(value))
        except (TypeError, ValueError):
            continue

    avg_score = sum(scores) / len(scores) if scores else 0.0
    return {
        "total_evaluations": total,
        "pass_count": verdict_counts["PASS"],
        "needs_improvement_count": verdict_counts["NEEDS IMPROVEMENT"],
        "fail_count": verdict_counts["FAIL"],
        "average_score": round(avg_score, 2),
        "evaluations": evaluations,
    }
