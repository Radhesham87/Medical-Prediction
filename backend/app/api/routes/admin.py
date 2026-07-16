"""Admin dashboard routes: stats, user management, exports."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.core.security import hash_password
from app.db.session import get_db
from app.models.prediction import Prediction
from app.models.user import Role, Status, User
from app.schemas.user import AdminStats, PasswordReset, UserOut
from app.services.excel_export import predictions_xlsx, registered_users_xlsx

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(get_current_admin)])


@router.get("/stats", response_model=AdminStats)
def stats(db: Session = Depends(get_db)):
    def count(**kw):
        q = db.query(func.count(User.id)).filter(User.role == Role.USER)
        for k, v in kw.items():
            q = q.filter(getattr(User, k) == v)
        return q.scalar() or 0

    start_of_day = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    todays = db.query(func.count(Prediction.id)).filter(Prediction.created_at >= start_of_day).scalar() or 0
    total_pred = db.query(func.count(Prediction.id)).scalar() or 0
    total_dl = db.query(func.coalesce(func.sum(Prediction.downloads), 0)).scalar() or 0

    return AdminStats(
        total_users=count(),
        pending_users=count(status=Status.PENDING),
        approved_users=count(status=Status.APPROVED),
        rejected_users=count(status=Status.REJECTED),
        prediction_count=total_pred,
        todays_predictions=todays,
        total_downloads=int(total_dl),
    )


@router.get("/users", response_model=list[UserOut])
def list_users(status_filter: str | None = None, db: Session = Depends(get_db)):
    q = db.query(User).filter(User.role == Role.USER)
    if status_filter in {s.value for s in Status}:
        q = q.filter(User.status == Status(status_filter))
    return q.order_by(User.registration_date.desc()).all()


def _get_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if not user or user.role == Role.ADMIN:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/users/{user_id}/approve", response_model=UserOut)
def approve(user_id: int, db: Session = Depends(get_db)):
    user = _get_user(db, user_id)
    user.status = Status.APPROVED
    db.commit()
    db.refresh(user)
    return user


@router.post("/users/{user_id}/reject", response_model=UserOut)
def reject(user_id: int, db: Session = Depends(get_db)):
    user = _get_user(db, user_id)
    user.status = Status.REJECTED
    db.commit()
    db.refresh(user)
    return user


@router.post("/users/{user_id}/disable", response_model=UserOut)
def disable(user_id: int, db: Session = Depends(get_db)):
    user = _get_user(db, user_id)
    user.is_active = False
    db.commit()
    db.refresh(user)
    return user


@router.post("/users/{user_id}/enable", response_model=UserOut)
def enable(user_id: int, db: Session = Depends(get_db)):
    user = _get_user(db, user_id)
    user.is_active = True
    db.commit()
    db.refresh(user)
    return user


@router.post("/users/{user_id}/reset-password", response_model=UserOut)
def reset_password(user_id: int, payload: PasswordReset, db: Session = Depends(get_db)):
    user = _get_user(db, user_id)
    user.hashed_password = hash_password(payload.new_password)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = _get_user(db, user_id)
    db.delete(user)
    db.commit()


@router.get("/export/users.xlsx")
def export_users(db: Session = Depends(get_db)):
    users = db.query(User).filter(User.role == Role.USER).order_by(User.id).all()
    data = registered_users_xlsx(users)
    return StreamingResponse(
        iter([data]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=Registered_Users.xlsx"},
    )


@router.get("/export/predictions.xlsx")
def export_predictions(db: Session = Depends(get_db)):
    preds = db.query(Prediction).order_by(Prediction.created_at.desc()).all()
    data = predictions_xlsx(preds)
    return StreamingResponse(
        iter([data]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=Predictions.xlsx"},
    )
