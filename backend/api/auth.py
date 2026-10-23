from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr, Field, field_validator

from backend.database import (
    create_user,
    get_dashboard_summary,
    get_user_by_username_or_email,
    get_user_evaluations,
    issue_session,
    revoke_session,
    update_user_password_hash,
    verify_password,
    verify_session_token,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=1)
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)

    @field_validator("full_name", "username")
    @classmethod
    def strip_and_validate(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("This field is required.")
        return cleaned

    @field_validator("confirm_password")
    @classmethod
    def validate_confirm_password(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Please confirm your password.")
        return value


class LoginRequest(BaseModel):
    username_or_email: str = Field(..., min_length=1)
    password: str = Field(..., min_length=8)


def _set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key="aegiseval_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
        secure=os.getenv("AEGISEVAL_COOKIE_SECURE", "false").lower() == "true",
    )


def _request_token(request: Request) -> str | None:
    authorization = request.headers.get("authorization", "")
    if authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()
    return request.cookies.get("aegiseval_token")


@router.post("/register")
def register_user(payload: RegisterRequest, response: Response) -> dict:
    if payload.password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match.")

    try:
        user = create_user(
            full_name=payload.full_name,
            email=str(payload.email),
            username=payload.username,
            password=payload.password,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    token = issue_session(user["id"])
    _set_auth_cookie(response, token)
    return {"token": token, "user": user}


@router.post("/login")
def login_user(payload: LoginRequest, response: Response) -> dict:
    user = get_user_by_username_or_email(payload.username_or_email)
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username/email or password.")

    if not user["password_hash"].startswith("pbkdf2_sha256$"):
        update_user_password_hash(user["id"], payload.password)

    token = issue_session(user["id"])
    _set_auth_cookie(response, token)
    return {
        "token": token,
        "user": {
            "id": user["id"],
            "full_name": user["full_name"],
            "email": user["email"],
            "username": user["username"],
            "created_at": user["created_at"],
        },
    }


@router.post("/logout")
def logout_user(request: Request, response: Response) -> dict:
    token = _request_token(request)
    if token:
        revoke_session(token)
    response.delete_cookie("aegiseval_token")
    return {"message": "Logged out successfully."}


def get_authenticated_user(request: Request) -> dict:
    token = _request_token(request)
    user = verify_session_token(token) if token else None
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required.")
    return user


@router.get("/me")
def get_current_user(request: Request) -> dict:
    return get_authenticated_user(request)


@router.get("/dashboard")
def get_dashboard(request: Request) -> dict:
    user = get_authenticated_user(request)
    return get_dashboard_summary(user["id"])


@router.get("/history")
def get_user_history(request: Request) -> dict:
    user = get_authenticated_user(request)
    return {"evaluations": get_user_evaluations(user["id"])}
