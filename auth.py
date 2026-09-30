import os
from datetime import datetime, timedelta, timezone

from fastapi import Request, HTTPException
from passlib.context import CryptContext
from jose import jwt, JWTError
from dotenv import load_dotenv

from database import get_user_by_id

load_dotenv()

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "development-secret-change-me"
)

ALGORITHM = "HS256"

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str):
    return pwd_context.verify(
        password,
        password_hash
    )


def create_access_token(user_id: int):
    expire = (
        datetime.now(timezone.utc)
        + timedelta(hours=12)
    )

    token = jwt.encode(
        {
            "sub": str(user_id),
            "exp": expire
        },
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return token


def get_current_user(request: Request):
    token = request.cookies.get("access_token")

    if not token:
        return None

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = int(payload["sub"])

        return get_user_by_id(user_id)

    except (
        JWTError,
        ValueError,
        TypeError,
        KeyError
    ):
        return None


def require_user(request: Request):
    user = get_current_user(request)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Please login first."
        )

    return user