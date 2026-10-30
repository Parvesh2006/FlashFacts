"""
Security and authentication utilities for FlashFacts.
Implements dependency-free JWT (HS256) and PBKDF2-HMAC-SHA256 password hashing.
"""
import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db

SECRET_KEY = getattr(settings, "SECRET_KEY", "flashfacts_secure_exam_portal_key_2026")
ALGORITHM = "HS256"
TOKEN_EXPIRE_SECONDS = 86400 * 30  # 30 days

security = HTTPBearer(auto_error=False)


def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def base64url_decode(data: str) -> bytes:
    padding = 4 - (len(data) % 4)
    if padding < 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data.encode("utf-8"))


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000
    )
    return f"{salt}:{key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        salt, key_hex = hashed_password.split(":")
        new_key = hashlib.pbkdf2_hmac(
            "sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 100000
        )
        return hmac.compare_digest(new_key.hex(), key_hex)
    except Exception:
        return False


def create_access_token(payload: Dict[str, Any], expires_in: int = TOKEN_EXPIRE_SECONDS) -> str:
    header = {"alg": ALGORITHM, "typ": "JWT"}
    payload_data = dict(payload)
    payload_data["exp"] = int(time.time()) + expires_in
    payload_data["iat"] = int(time.time())

    h_b64 = base64url_encode(json.dumps(header).encode("utf-8"))
    p_b64 = base64url_encode(json.dumps(payload_data).encode("utf-8"))
    signing_input = f"{h_b64}.{p_b64}".encode("utf-8")
    signature = hmac.new(SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
    s_b64 = base64url_encode(signature)

    return f"{h_b64}.{p_b64}.{s_b64}"


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        h_b64, p_b64, s_b64 = parts
        signing_input = f"{h_b64}.{p_b64}".encode("utf-8")
        expected_sig = hmac.new(SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
        if not hmac.compare_digest(base64url_encode(expected_sig), s_b64):
            return None
        payload = json.loads(base64url_decode(p_b64).decode("utf-8"))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


def get_current_user_optional(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
):
    """
    Returns the authenticated User or None if not supplied.
    Raises 401 if a token was supplied but is invalid or expired.
    """
    from app.models.user import User

    if not auth or not auth.credentials:
        return None

    payload = decode_access_token(auth.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload["sub"]
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
):
    """
    Returns the authenticated User (registered student or initialized guest with a valid token).
    Raises 401 Unauthorized if no credentials are provided or if the token is invalid/expired.
    Prevents accidental guest row creation on unauthenticated requests.
    """
    user = get_current_user_optional(auth, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
