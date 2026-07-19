"""Admin dashboard routes: stats, user management, exports."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.core.security import hash_password
from app.db.session import get_db
from app.models.access import ModuleAccess, PredictionUsage
from app.models.prediction import Prediction
from app.models.session import LoginSession
from app.models.user import Role, Status, User
from app.schemas.user import AdminStats, DeviceOut, ModuleAccessIn, ModuleStatsOut, PasswordReset, UserOut
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

    # Maharashtra: its full history lives in the predictions table.
    mah_total = db.query(func.count(Prediction.id)).scalar() or 0
    mah_today = (
        db.query(func.count(Prediction.id))
        .filter(Prediction.created_at >= start_of_day)
        .scalar()
        or 0
    )
    mah_dl = int(db.query(func.coalesce(func.sum(Prediction.downloads), 0)).scalar() or 0)

    # AIIMS / All India / Deemed: counted from usage events.
    inst_total: dict[str, int] = {}
    inst_today: dict[str, int] = {}
    for key in ("aiims", "all-india", "deemed", "veterinary"):
        base = db.query(func.count(PredictionUsage.id)).filter(
            PredictionUsage.module == key, PredictionUsage.kind == "predict"
        )
        inst_total[key] = base.scalar() or 0
        inst_today[key] = (
            base.filter(PredictionUsage.created_at >= start_of_day).scalar() or 0
        )
    inst_dl = (
        db.query(func.count(PredictionUsage.id))
        .filter(PredictionUsage.kind == "download")
        .scalar()
        or 0
    )

    todays_by_module = {
        "aiims": inst_today["aiims"],
        "all-india": inst_today["all-india"],
        "maharashtra": mah_today,
        "deemed": inst_today["deemed"],
        "veterinary": inst_today["veterinary"],
    }

    return AdminStats(
        total_users=count(),
        pending_users=count(status=Status.PENDING),
        approved_users=count(status=Status.APPROVED),
        rejected_users=count(status=Status.REJECTED),
        prediction_count=mah_total + sum(inst_total.values()),
        todays_predictions=mah_today + sum(inst_today.values()),
        total_downloads=mah_dl + int(inst_dl),
        todays_by_module=todays_by_module,
    )


@router.get("/users", response_model=list[UserOut])
def list_users(status_filter: str | None = None, db: Session = Depends(get_db)):
    q = db.query(User).filter(User.role == Role.USER)
    if status_filter in {s.value for s in Status}:
        q = q.filter(User.status == Status(status_filter))
    users = q.order_by(User.registration_date.desc()).all()
    return [_serialize_user(db, u) for u in users]


def _get_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if not user or user.role == Role.ADMIN:
        raise HTTPException(status_code=404, detail="User not found")
    return user


_MODULE_KEYS = ["aiims", "all-india", "maharashtra", "deemed", "veterinary"]


def _usage_counts(db: Session, u: User) -> dict:
    """Per-module prediction counts for one user (all four modules)."""
    usage = {k: 0 for k in _MODULE_KEYS}
    rows = (
        db.query(PredictionUsage.module, func.count(PredictionUsage.id))
        .filter(PredictionUsage.user_id == u.id, PredictionUsage.kind == "predict")
        .group_by(PredictionUsage.module)
        .all()
    )
    for mod, cnt in rows:
        if mod in usage:
            usage[mod] = int(cnt)
    # Maharashtra predictions predate usage logging; its history table is the full record.
    usage["maharashtra"] = u.prediction_count
    return usage


def _serialize_user(db: Session, u: User) -> dict:
    access = db.get(ModuleAccess, u.id)
    modules = {
        "aiims": bool(access and access.aiims),
        "all-india": bool(access and access.all_india),
        "maharashtra": bool(access and access.maharashtra),
        "deemed": bool(access and access.deemed),
        "veterinary": bool(access and getattr(access, "veterinary", False)),
    }
    usage = _usage_counts(db, u)
    return {
        "id": u.id, "name": u.name, "email": u.email, "mobile": u.mobile,
        "college": u.college, "city": u.city, "state": u.state,
        "role": u.role.value, "status": u.status.value, "is_active": u.is_active,
        "registration_date": u.registration_date, "last_login": u.last_login,
        "prediction_count": sum(usage.values()),
        "active_device_count": u.active_device_count,
        "modules": modules, "usage": usage,
    }


@router.put("/users/{user_id}/modules", response_model=UserOut)
def set_modules(user_id: int, payload: ModuleAccessIn, db: Session = Depends(get_db)):
    user = _get_user(db, user_id)
    access = db.get(ModuleAccess, user.id)
    if access is None:
        access = ModuleAccess(user_id=user.id)
        db.add(access)
    access.aiims = payload.aiims
    access.all_india = payload.all_india
    access.maharashtra = payload.maharashtra
    access.deemed = payload.deemed
    access.veterinary = payload.veterinary
    db.commit()
    return _serialize_user(db, user)


_ACCESS_FIELD = {
    "aiims": "aiims",
    "all-india": "all_india",
    "maharashtra": "maharashtra",
    "deemed": "deemed",
    "veterinary": "veterinary",
}

_MODULE_TITLES = {
    "aiims": "AIIMS",
    "all-india": "All India (15%)",
    "maharashtra": "Maharashtra (85%)",
    "deemed": "Deemed",
    "veterinary": "Veterinary",
}


@router.get("/module-stats", response_model=list[ModuleStatsOut])
def module_stats(db: Session = Depends(get_db)):
    """One dashboard block per prediction module, mirroring the overall stats."""
    start_of_day = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    out: list[dict] = []
    for key in _MODULE_KEYS:
        field = _ACCESS_FIELD[key]
        users_with_access = (
            db.query(func.count(ModuleAccess.user_id))
            .filter(getattr(ModuleAccess, field).is_(True))
            .scalar()
            or 0
        )
        if key == "maharashtra":
            # Full history lives in the predictions table (predates usage logging).
            predictions = db.query(func.count(Prediction.id)).scalar() or 0
            todays = (
                db.query(func.count(Prediction.id))
                .filter(Prediction.created_at >= start_of_day)
                .scalar()
                or 0
            )
            unique_users = db.query(func.count(func.distinct(Prediction.user_id))).scalar() or 0
            downloads = int(
                db.query(func.coalesce(func.sum(Prediction.downloads), 0)).scalar() or 0
            )
        else:
            base = db.query(PredictionUsage).filter(
                PredictionUsage.module == key, PredictionUsage.kind == "predict"
            )
            predictions = base.count()
            todays = base.filter(PredictionUsage.created_at >= start_of_day).count()
            unique_users = (
                db.query(func.count(func.distinct(PredictionUsage.user_id)))
                .filter(PredictionUsage.module == key, PredictionUsage.kind == "predict")
                .scalar()
                or 0
            )
            downloads = (
                db.query(func.count(PredictionUsage.id))
                .filter(PredictionUsage.module == key, PredictionUsage.kind == "download")
                .scalar()
                or 0
            )
        out.append(
            {
                "key": key,
                "label": _MODULE_TITLES[key],
                "users_with_access": int(users_with_access),
                "unique_users": int(unique_users),
                "predictions": int(predictions),
                "todays_predictions": int(todays),
                "downloads": int(downloads),
            }
        )
    return out


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
    totals = {u.id: sum(_usage_counts(db, u).values()) for u in users}
    data = registered_users_xlsx(users, totals)
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


@router.get("/users/{user_id}/devices", response_model=list[DeviceOut])
def list_devices(user_id: int, db: Session = Depends(get_db)):
    """Devices currently/previously logged in for this account (newest first)."""
    _get_user(db, user_id)
    return (
        db.query(LoginSession)
        .filter(LoginSession.user_id == user_id)
        .order_by(LoginSession.last_seen_at.desc())
        .all()
    )


@router.delete("/users/{user_id}/devices/{session_id}", status_code=204)
def revoke_device(user_id: int, session_id: int, db: Session = Depends(get_db)):
    """Remove a device record (forces that device to log in again)."""
    _get_user(db, user_id)
    sess = db.get(LoginSession, session_id)
    if not sess or sess.user_id != user_id:
        raise HTTPException(status_code=404, detail="Device not found")
    db.delete(sess)
    db.commit()
