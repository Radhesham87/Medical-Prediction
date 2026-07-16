"""Reusable FastAPI dependencies for authentication and authorization."""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import Role, Status, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/login")

_CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise _CREDENTIALS_ERROR
    user = db.get(User, int(payload["sub"]))
    if not user:
        raise _CREDENTIALS_ERROR
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled. Contact the administrator.")
    return user


def get_current_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user


def get_approved_user(user: User = Depends(get_current_user)) -> User:
    if user.role == Role.ADMIN:
        return user
    if user.status != Status.APPROVED:
        raise HTTPException(
            status_code=403,
            detail="Your account is awaiting admin approval." if user.status == Status.PENDING
            else "Your account has been rejected.",
        )
    return user
