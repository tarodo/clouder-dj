import base64
import hashlib
import os
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from cryptography.fernet import Fernet

from app.core.settings import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/callback")

fernet = Fernet(settings.ENCRYPTION_KEY.encode())


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a new access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGO
    )
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create a new refresh token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGO
    )
    return encoded_jwt


def verify_token(token: str) -> dict[str, Any]:
    """Verify the token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGO])
        return payload
    except JWTError as err:
        raise credentials_exception from err


def create_pkce_challenge() -> tuple[str, str]:
    """Create a PKCE code verifier and challenge pair."""
    code_verifier = (
        base64.urlsafe_b64encode(os.urandom(32)).rstrip(b"=").decode("utf-8")
    )
    code_challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode("utf-8")).digest())
        .rstrip(b"=")
        .decode("utf-8")
    )
    return code_verifier, code_challenge


def encrypt_data(data: str) -> str:
    """Encrypts a string."""
    return fernet.encrypt(data.encode()).decode()


def decrypt_data(encrypted_data: str) -> str:
    """Decrypts a string."""
    return fernet.decrypt(encrypted_data.encode()).decode()
