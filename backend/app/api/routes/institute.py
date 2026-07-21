"""Routes for the AIIMS / All-India / Deemed prediction modules.

Stateless: predictions are returned directly and the PDF is generated from the
posted results, so these modules don't touch the prediction-history table.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_approved_user
from app.api.module_guard import ensure_module_allowed, log_usage
from app.core.branding import pdf_headline_for
from app.db.session import get_db
from app.models.user import User
from app.schemas.institute import (
    InstituteOptions,
    InstitutePdfRequest,
    InstitutePredictRequest,
    InstitutePredictResponse,
)
from app.services.institute_engine import MODULES, module_options, predict_institute
from app.services.institute_pdf import build_institute_pdf

router = APIRouter(prefix="/institute", tags=["institute"])

_VALID = set(MODULES.keys())


def _require_module(module: str):
    if module not in _VALID:
        raise HTTPException(status_code=404, detail=f"Unknown module '{module}'")
    return MODULES[module]


@router.get("/{module}/options", response_model=InstituteOptions)
def options(
    module: str = Path(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_approved_user),
):
    _require_module(module)
    ensure_module_allowed(db, user, module)
    return module_options(module)


@router.post("/{module}/predict", response_model=InstitutePredictResponse)
def predict(
    payload: InstitutePredictRequest,
    module: str = Path(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_approved_user),
):
    cfg = _require_module(module)
    ensure_module_allowed(db, user, module)
    log_usage(db, user, module)
    results = predict_institute(
        module=module,
        mode=payload.mode,
        score=payload.score,
        air=payload.air,
        degrees=payload.degrees,
        categories=payload.categories,
        states=payload.states,
    )
    return InstitutePredictResponse(
        module=module,
        student_name=payload.student_name,
        mode=payload.mode,
        score=payload.score,
        air=payload.air,
        generated_at=datetime.now(timezone.utc),
        show_degree=cfg.has_degree,
        show_category=cfg.has_category,
        results=results,
    )


@router.post("/{module}/pdf")
def pdf(
    payload: InstitutePdfRequest,
    module: str = Path(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_approved_user),
):
    _require_module(module)
    ensure_module_allowed(db, user, module)
    log_usage(db, user, module, kind="download")
    data = build_institute_pdf(
        module=module,
        student_name=payload.student_name,
        mode=payload.mode,
        score=payload.score,
        air=payload.air,
        show_degree=payload.show_degree,
        show_category=payload.show_category,
        brand_headline=pdf_headline_for(user.email),
        results=[r.model_dump() for r in payload.results],
    )
    fname = f"{module}_prediction_{payload.student_name.replace(' ', '_')}.pdf"
    return StreamingResponse(
        iter([data]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={fname}"},
    )
