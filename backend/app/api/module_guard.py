"""Per-module access checks and usage logging shared by the predict routes."""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.access import ModuleAccess, PredictionUsage
from app.models.user import Role, User

# module key (used in URLs) -> ModuleAccess boolean attribute
MODULE_FIELDS = {
    "aiims": "aiims",
    "all-india": "all_india",
    "maharashtra": "maharashtra",
    "deemed": "deemed",
}

MODULE_LABELS = {
    "aiims": "AIIMS",
    "all-india": "All India (15%)",
    "maharashtra": "Maharashtra (85%)",
    "deemed": "Deemed",
}


def module_allowed(db: Session, user: User, module_key: str) -> bool:
    if user.role == Role.ADMIN:
        return True
    field = MODULE_FIELDS.get(module_key)
    if field is None:
        return False
    access = db.get(ModuleAccess, user.id)
    return bool(access and getattr(access, field, False))


def ensure_module_allowed(db: Session, user: User, module_key: str) -> None:
    if not module_allowed(db, user, module_key):
        label = MODULE_LABELS.get(module_key, module_key)
        raise HTTPException(
            status_code=403,
            detail=f"You are not approved to use {label}. Please contact the administrator.",
        )


def log_usage(db: Session, user: User, module_key: str, kind: str = "predict") -> None:
    db.add(PredictionUsage(user_id=user.id, module=module_key, kind=kind))
    db.commit()
