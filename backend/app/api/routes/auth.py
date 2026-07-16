"""Authentication routes: registration and login."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.user import Role, Status, User
from app.schemas.user import Token, UserRegister

router = APIRouter(prefix="/auth", tags=["auth"])
logger = get_logger("auth")


@router.post("/register", status_code=201)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    exists = db.query(User).filter(func.lower(User.email) == payload.email.lower()).first()
    if exists:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        name=payload.name,
        email=payload.email.lower(),
        mobile=payload.mobile,
        hashed_password=hash_password(payload.password),
        college=payload.college,
        city=payload.city,
        state=payload.state,
        role=Role.USER,
        status=Status.PENDING,
    )
    db.add(user)
    db.commit()
    logger.info("New registration pending approval: %s", user.email)
    return {"message": "Registration successful. Awaiting admin approval.", "status": "pending"}


@router.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # OAuth2 form uses 'username'; we treat it as the email.
    user = db.query(User).filter(func.lower(User.email) == form.username.lower()).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled. Contact the administrator.")
    if user.role != Role.ADMIN and user.status != Status.APPROVED:
        detail = (
            "Your account is awaiting admin approval."
            if user.status == Status.PENDING
            else "Your account has been rejected."
        )
        raise HTTPException(status_code=403, detail=detail)

    user.last_login = datetime.now(timezone.utc)
    db.commit()
    token = create_access_token(subject=user.id, role=user.role.value)
    return Token(access_token=token, role=user.role.value, name=user.name)
