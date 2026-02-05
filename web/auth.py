"""
Simple authentication system
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import RedirectResponse
from jose import JWTError, jwt

from .config import USERNAME, PASSWORD, SECRET_KEY, SESSION_EXPIRE_HOURS

ALGORITHM = "HS256"


def verify_credentials(username: str, password: str) -> bool:
    """Verify username and password against config"""
    return username == USERNAME and password == PASSWORD


def create_session_token(username: str) -> str:
    """Create a JWT token for the session"""
    expire = datetime.utcnow() + timedelta(hours=SESSION_EXPIRE_HOURS)
    to_encode = {
        "sub": username,
        "exp": expire
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_session_token(token: str) -> Optional[str]:
    """Verify JWT token and return username if valid"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return username
    except JWTError:
        return None


def get_current_user(request: Request) -> Optional[str]:
    """Get current user from session cookie"""
    token = request.cookies.get("session_token")
    if not token:
        return None
    return verify_session_token(token)


def require_auth(request: Request) -> str:
    """Dependency to require authentication"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return user


def login_required(request: Request):
    """Check if user is logged in, redirect to login if not"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    return None
