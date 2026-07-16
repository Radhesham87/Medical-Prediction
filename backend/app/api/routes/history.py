"""User + admin prediction history routes."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import get_approved_user, get_current_admin
from app.db.session import get_db
from app.models.prediction import Prediction
from app.models.user import User
from app.schemas.prediction import PredictionHistoryOut

router = APIRouter(tags=["history"])


def _to_out(p: Prediction) -> PredictionHistoryOut:
    return PredictionHistoryOut(
        id=p.id,
        student_name=p.student_name,
        mode=p.mode,
        score=p.score,
        air=p.air,
        gender=p.gender,
        category=p.category,
        degrees=p.degrees_list,
        result_count=len(p.results),
        created_at=p.created_at,
    )


@router.get("/history", response_model=list[PredictionHistoryOut])
def my_history(db: Session = Depends(get_db), user: User = Depends(get_approved_user)):
    preds = (
        db.query(Prediction)
        .filter(Prediction.user_id == user.id)
        .order_by(Prediction.created_at.desc())
        .all()
    )
    return [_to_out(p) for p in preds]


@router.get("/history/{prediction_id}")
def history_detail(
    prediction_id: int, db: Session = Depends(get_db), user: User = Depends(get_approved_user)
):
    p = db.get(Prediction, prediction_id)
    if not p or (p.user_id != user.id and user.role.value != "admin"):
        raise HTTPException(status_code=404, detail="Prediction not found")
    return {
        **_to_out(p).model_dump(),
        "results": p.results,
        "show_category_rank": p.category.upper() != "OPEN",
    }


@router.delete("/history/{prediction_id}", status_code=204)
def delete_history(
    prediction_id: int, db: Session = Depends(get_db), user: User = Depends(get_approved_user)
):
    p = db.get(Prediction, prediction_id)
    if not p or (p.user_id != user.id and user.role.value != "admin"):
        raise HTTPException(status_code=404, detail="Prediction not found")
    db.delete(p)
    db.commit()


@router.get("/admin/history", response_model=list[PredictionHistoryOut],
            dependencies=[Depends(get_current_admin)])
def admin_history(
    db: Session = Depends(get_db),
    search: str | None = Query(default=None),
    sort: str = Query(default="desc"),
):
    q = db.query(Prediction)
    if search:
        like = f"%{search}%"
        q = q.filter(or_(Prediction.student_name.ilike(like), Prediction.category.ilike(like)))
    q = q.order_by(Prediction.created_at.asc() if sort == "asc" else Prediction.created_at.desc())
    return [_to_out(p) for p in q.all()]
