"""JWT Authentication module for Resume Job Matcher AI."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
from sqlalchemy.orm import Session
from backend.config import get_settings
from backend.database import get_db
from backend.models import User

settings = get_settings()
security = HTTPBearer()


def create_access_token(user_id: int) -> str:
    """Create a JWT access token for the given user ID."""
    payload = {"sub": str(user_id)}
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
    return token


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Validate JWT token and return the current user."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        user_id = int(payload.get("sub"))
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
