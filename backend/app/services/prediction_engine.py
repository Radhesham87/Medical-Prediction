"""Prediction engine.

Loads the last-year cutoff dataset (xlsx), normalises it, and predicts probable
colleges for a candidate given a NEET Score OR All-India-Rank (AIR), plus degree,
gender and category filters.

A cutoff row represents the *last* admitted candidate in a category-gender-degree
bucket last year. So:
  - by SCORE: the higher a candidate's score is above the cutoff, the safer the seat.
  - by AIR:   the lower (better) a candidate's rank vs the cutoff, the safer the seat.

Chance bands are heuristic and tuned to be interpretable, not a guarantee.
"""
from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import List, Optional

import numpy as np
import pandas as pd

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("prediction_engine")

# UI category -> dataset Quota prefix (they already line up, but keep explicit map)
CATEGORY_MAP = {
    "OPEN": "OPEN", "OBC": "OBC", "SEBC": "SEBC", "EWS": "EWS", "VJA": "VJA",
    "NTB": "NTB", "NTC": "NTC", "NTD": "NTD", "SC": "SC", "ST": "ST",
    "D1": "D1", "D2": "D2", "D3": "D3",
}
GENDER_MAP = {"Male": "M", "Female": "F"}
ALL_DEGREES = ["MBBS", "BDS", "BAMS", "BHMS", "BUMS", "BPTH"]

# Score-based bands (points relative to cutoff).
SCORE_HIGH_MARGIN = 10      # >= cutoff + 10  -> High
SCORE_LOW_FLOOR = -20       # cutoff - 20 .. cutoff - 5 -> Low; below that dropped
SCORE_MODERATE_FLOOR = -5

# AIR-based bands (ratio = candidate_air / cutoff_air; lower is better).
AIR_HIGH_RATIO = 0.85
AIR_MODERATE_RATIO = 1.05
AIR_LOW_RATIO = 1.25


class _Dataset:
    """Thread-safe, lazily-loaded, normalised copy of the cutoff data."""

    def __init__(self) -> None:
        self._df: Optional[pd.DataFrame] = None
        self._lock = threading.Lock()
        self._loaded_at: Optional[datetime] = None

    def _normalise(self, raw: pd.DataFrame) -> pd.DataFrame:
        df = raw.copy()
        df.columns = [c.strip() for c in df.columns]

        # Split "OPEN-M" -> category "OPEN", gender "M"
        qg = df["Quota-Gender"].astype(str).str.rsplit("-", n=1, expand=True)
        df["cat"] = qg[0].str.strip().str.upper()
        df["gen"] = qg[1].str.strip().str.upper()

        # Numeric coercion + drop physically impossible NEET scores / ranks.
        df["NEET Score"] = pd.to_numeric(df["NEET Score"], errors="coerce")
        df["AIR"] = pd.to_numeric(df["AIR"], errors="coerce")
        df["SML"] = pd.to_numeric(df["SML"], errors="coerce")
        df = df[(df["NEET Score"].between(0, 720)) & (df["AIR"] > 0)]

        # Extract numeric category rank from the "Category" column (e.g. "SEBC-2710").
        def _rank(val) -> Optional[str]:
            if pd.isna(val):
                return None
            parts = str(val).rsplit("-", 1)
            return parts[1] if len(parts) == 2 and parts[1].isdigit() else None

        df["category_rank"] = df["Category"].apply(_rank)
        df["Degree"] = df["Degree"].astype(str).str.strip().str.upper()
        df["College Code"] = df["College Code"].astype(str).str.replace(r"\.0$", "", regex=True)
        return df.reset_index(drop=True)

    def load(self, force: bool = False) -> pd.DataFrame:
        with self._lock:
            if self._df is None or force:
                logger.info("Loading dataset from %s", settings.DATASET_PATH)
                raw = pd.read_excel(settings.DATASET_PATH, sheet_name=settings.DATASET_SHEET)
                self._df = self._normalise(raw)
                self._loaded_at = datetime.now(timezone.utc)
                logger.info("Dataset loaded: %d valid rows", len(self._df))
            return self._df

    def reload(self) -> pd.DataFrame:
        return self.load(force=True)

    def stats(self) -> dict:
        df = self.load()
        return {
            "valid_rows": int(len(df)),
            "colleges": int(df["College Code"].nunique()),
            "degrees": sorted(df["Degree"].unique().tolist()),
            "loaded_at": self._loaded_at.isoformat() if self._loaded_at else None,
        }


dataset = _Dataset()


def _band_by_score(candidate: float, cutoff: float) -> Optional[str]:
    delta = candidate - cutoff
    if delta >= SCORE_HIGH_MARGIN:
        return "High"
    if delta >= SCORE_MODERATE_FLOOR:
        return "Moderate"
    if delta >= SCORE_LOW_FLOOR:
        return "Low"
    return None


def _band_by_air(candidate: float, cutoff: float) -> Optional[str]:
    if cutoff <= 0:
        return None
    ratio = candidate / cutoff
    if ratio <= AIR_HIGH_RATIO:
        return "High"
    if ratio <= AIR_MODERATE_RATIO:
        return "Moderate"
    if ratio <= AIR_LOW_RATIO:
        return "Low"
    return None


_BAND_ORDER = {"High": 0, "Moderate": 1, "Low": 2}


def predict(
    *,
    mode: str,
    score: Optional[float],
    air: Optional[int],
    degrees: List[str],
    gender: str,
    category: str,
) -> List[dict]:
    """Return a list of probable-college dicts sorted High -> Moderate -> Low."""
    df = dataset.load()

    # Expand "All" and normalise degree list.
    wanted = ALL_DEGREES if any(d.upper() == "ALL" for d in degrees) else [d.upper() for d in degrees]
    cat = CATEGORY_MAP.get(category.upper())
    gen = GENDER_MAP.get(gender)
    if cat is None or gen is None:
        return []

    subset = df[(df["Degree"].isin(wanted)) & (df["cat"] == cat) & (df["gen"] == gen)].copy()
    if subset.empty:
        return []

    rows: list[dict] = []
    for _, r in subset.iterrows():
        cutoff_score = r["NEET Score"]
        cutoff_air = r["AIR"]
        if mode == "score":
            band = _band_by_score(float(score), float(cutoff_score))
        else:
            band = _band_by_air(float(air), float(cutoff_air))
        if band is None:
            continue

        raw_rank = r["category_rank"]
        rank_val = None if pd.isna(raw_rank) else str(raw_rank)
        rows.append(
            {
                "college_code": str(r["College Code"]),
                "college_name": str(r["College Name"]),
                "status": str(r["College Status"]),
                "degree": str(r["Degree"]),
                "neet_score": None if pd.isna(cutoff_score) else float(cutoff_score),
                "neet_sml": None if pd.isna(r["SML"]) else float(r["SML"]),
                "air": None if pd.isna(cutoff_air) else int(cutoff_air),
                "category_rank": rank_val if category.upper() != "OPEN" else None,
                "chance": band,
                "_cutoff_score": float(cutoff_score),
                "_cutoff_air": float(cutoff_air),
            }
        )

    # Sort: best band first; then most-competitive college first within a band.
    if mode == "score":
        rows.sort(key=lambda x: (_BAND_ORDER[x["chance"]], -x["_cutoff_score"]))
    else:
        rows.sort(key=lambda x: (_BAND_ORDER[x["chance"]], x["_cutoff_air"]))

    for i, row in enumerate(rows, start=1):
        row["sr_no"] = i
        row.pop("_cutoff_score", None)
        row.pop("_cutoff_air", None)
    return rows
