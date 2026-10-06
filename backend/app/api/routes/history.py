"""User + admin prediction history routes."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, defer

from app.api.deps import get_approved_user, get_current_admin
from app.db.session import get_db
from app.models.prediction import Prediction
from app.models.user import User
from app.schemas.prediction import PredictionHistoryOut

router = APIRouter(tags=["history"])


def _count_expr():
    """Number of result rows, counted inside the database.

    The history LIST used to load and JSON-parse every saved prediction's full
    result list just to show a count - with many saved predictions that is
    slow and memory-hungry on the server (and a crash there shows up in the
    browser as a CORS / "Failed to fetch" error). Counting the '"sr_no"'
    markers in SQL keeps the list request small and fast. Hidden
    "No Data" rows are subtracted so the count matches what is shown.
    """
    rj = Prediction.result_json
    sr = '"sr_no"'
    nd = '"No Data"'
    return (
        (func.length(rj) - func.length(func.replace(rj, sr, ""))) / len(sr)
        - (func.length(rj) - func.length(func.replace(rj, nd, ""))) / len(nd)
    ).label("result_count")


def _list_query(db: Session):
    return db.query(Prediction, _count_expr()).options(defer(Prediction.result_json))


def _to_out(p: Prediction, result_count: int | None = None) -> PredictionHistoryOut:
    return PredictionHistoryOut(
        id=p.id,
        student_name=p.student_name,
        mode=p.mode,
        score=p.score,
        air=p.air,
        gender=p.gender,
        category=p.category,
        degrees=p.degrees_list,
        result_count=int(result_count) if result_count is not None else len(p.results),
        created_at=p.created_at,
    )


@router.get("/history", response_model=list[PredictionHistoryOut])
def my_history(db: Session = Depends(get_db), user: User = Depends(get_approved_user)):
    rows = (
        _list_query(db)
        .filter(Prediction.user_id == user.id)
        .order_by(Prediction.created_at.desc())
        .all()
    )
    return [_to_out(p, n) for p, n in rows]


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
    q = _list_query(db)
    if search:
        like = f"%{search}%"
        q = q.filter(or_(Prediction.student_name.ilike(like), Prediction.category.ilike(like)))
    q = q.order_by(Prediction.created_at.asc() if sort == "asc" else Prediction.created_at.desc())
    return [_to_out(p, n) for p, n in q.all()]
