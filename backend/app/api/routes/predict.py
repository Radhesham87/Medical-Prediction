"""Prediction routes: run a prediction (saved to history) and download its PDF."""
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_approved_user
from app.api.module_guard import ensure_module_allowed, log_usage
from app.core.branding import pdf_headline_for, pdf_letterhead_for
from app.db.session import get_db
from app.models.prediction import Prediction
from app.models.user import User
from app.schemas.prediction import PredictionRequest, PredictionResponse
from app.services.pdf_generator import build_prediction_pdf
from app.services.prediction_engine import predict as run_engine

router = APIRouter(prefix="/predict", tags=["prediction"])


@router.post("", response_model=PredictionResponse)
def make_prediction(
    payload: PredictionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_approved_user),
):
    ensure_module_allowed(db, user, "maharashtra")
    log_usage(db, user, "maharashtra")
    results = run_engine(
        mode=payload.mode,
        score=payload.score,
        air=payload.air,
        sml=payload.sml,
        degrees=payload.degrees,
        gender=payload.gender,
        category=payload.category,
    )
    show_rank = payload.category.upper() != "OPEN"

    record = Prediction(
        user_id=user.id,
        student_name=payload.student_name,
        mode=payload.mode,
        score=payload.score,
        air=payload.air,
        sml=payload.sml,
        gender=payload.gender,
        category=payload.category,
        degrees=json.dumps(payload.degrees),
        result_json=json.dumps(results),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return PredictionResponse(
        student_name=payload.student_name,
        mode=payload.mode,
        score=payload.score,
        air=payload.air,
        sml=payload.sml,
        gender=payload.gender,
        category=payload.category,
        show_category_rank=show_rank,
        generated_at=record.created_at,
        results=results,
    )


@router.get("/{prediction_id}/pdf")
def download_pdf(
    prediction_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_approved_user),
):
    record = db.get(Prediction, prediction_id)
    if not record or (record.user_id != user.id and user.role.value != "admin"):
        raise HTTPException(status_code=404, detail="Prediction not found")

    pdf = build_prediction_pdf(
        student_name=record.student_name,
        mode=record.mode,
        score=record.score,
        air=record.air,
        sml=record.sml,
        gender=record.gender,
        brand_headline=pdf_headline_for(user.email),
        letterhead=pdf_letterhead_for(user.email),
        category=record.category,
        results=record.results,
        show_category_rank=record.category.upper() != "OPEN",
    )
    record.downloads += 1
    db.commit()

    filename = f"NEET_Prediction_{record.student_name.replace(' ', '_')}_{record.id}.pdf"
    return StreamingResponse(
        iter([pdf]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
