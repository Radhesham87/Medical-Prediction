"""Admin dataset management: upload, replace, backup, restore, statistics."""
import shutil
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.api.deps import get_current_admin
from app.core.config import settings
from app.core.logging import get_logger
from app.services.prediction_engine import dataset

router = APIRouter(prefix="/dataset", tags=["dataset"], dependencies=[Depends(get_current_admin)])
logger = get_logger("dataset")

DATASET_PATH = Path(settings.DATASET_PATH)
BACKUP_DIR = DATASET_PATH.parent / "backups"


@router.get("/stats")
def dataset_stats():
    return dataset.stats()


@router.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files are accepted")

    # Backup the current dataset before replacing it.
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    if DATASET_PATH.exists():
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        shutil.copy2(DATASET_PATH, BACKUP_DIR / f"dataset_{ts}.xlsx")

    DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DATASET_PATH.open("wb") as out:
        shutil.copyfileobj(file.file, out)

    try:
        dataset.reload()
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Uploaded dataset failed to load")
        raise HTTPException(status_code=422, detail=f"Dataset could not be parsed: {exc}")

    logger.info("Dataset replaced by admin upload: %s", file.filename)
    return {"message": "Dataset replaced and reloaded", **dataset.stats()}


@router.get("/backups")
def list_backups():
    if not BACKUP_DIR.exists():
        return {"backups": []}
    files = sorted((p.name for p in BACKUP_DIR.glob("*.xlsx")), reverse=True)
    return {"backups": files}


@router.post("/restore/{backup_name}")
def restore_backup(backup_name: str):
    target = BACKUP_DIR / Path(backup_name).name  # prevent path traversal
    if not target.exists():
        raise HTTPException(status_code=404, detail="Backup not found")
    shutil.copy2(target, DATASET_PATH)
    dataset.reload()
    return {"message": f"Restored from {backup_name}", **dataset.stats()}
