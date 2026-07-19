"""Institute-based prediction engines for AIIMS, All-India and Deemed modules.

These three datasets are simpler than the Maharashtra one: each row is a single
institute (+ optional degree) with a closing AIR and Score for a category/quota.
A cutoff row = the last admitted candidate, so:
  - by SCORE: candidate at/above the cutoff score is safer.
  - by AIR:   candidate with a lower (better) rank than the cutoff is safer.

One config-driven engine serves all three modules; the differences (which columns
exist, whether degree/category/state filters apply) live in MODULES below.
"""
from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional

import pandas as pd

from app.core.config import settings, PROJECT_ROOT
from app.core.logging import get_logger

logger = get_logger("institute_engine")

# Same interpretable bands used by the Maharashtra engine.
SCORE_HIGH_MARGIN = 10
SCORE_MODERATE_FLOOR = -5
SCORE_LOW_FLOOR = -20
AIR_HIGH_RATIO = 0.85
AIR_MODERATE_RATIO = 1.05
AIR_LOW_RATIO = 1.25
_BAND_ORDER = {"High": 0, "Moderate": 1, "Low": 2}


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


class ModuleConfig:
    """Describes how to load and filter one institute dataset."""

    def __init__(
        self,
        key: str,
        label: str,
        filename: str,
        sheet: str,
        col_institute: str,
        col_state: str,
        col_air: str,
        col_score: str,
        col_degree: Optional[str] = None,
        col_category: Optional[str] = None,
        degrees: Optional[List[str]] = None,
    ) -> None:
        self.key = key
        self.label = label
        self.filename = filename
        self.sheet = sheet
        self.col_institute = col_institute
        self.col_state = col_state
        self.col_air = col_air
        self.col_score = col_score
        self.col_degree = col_degree
        self.col_category = col_category
        self.degrees = degrees or []

    @property
    def path(self) -> str:
        return str(PROJECT_ROOT / "data" / self.filename)

    @property
    def has_degree(self) -> bool:
        return self.col_degree is not None

    @property
    def has_category(self) -> bool:
        return self.col_category is not None


MODULES: Dict[str, ModuleConfig] = {
    "aiims": ModuleConfig(
        key="aiims", label="AIIMS",
        filename="AIIMS_Cutoff.xlsx", sheet="AIIMS Cutoff",
        col_institute="Institute Name", col_state="State Name",
        col_air="AIR", col_score="Score", col_category="Category",
    ),
    "all-india": ModuleConfig(
        key="all-india", label="All India (15%)",
        filename="All_India_Cutoff.xlsx", sheet="MBBS + BDS Cutoff",
        col_institute="Institute Name", col_state="State Name",
        col_air="AIR", col_score="Score", col_degree="Degree", col_category="Category",
        degrees=["MBBS", "BDS"],
    ),
    "deemed": ModuleConfig(
        key="deemed", label="Deemed",
        filename="Deemed_Cutoff.xlsx", sheet="Deemed MBBS + BDS",
        col_institute="Institute Name", col_state="State",
        col_air="Gen Rank", col_score="Gen Score", col_degree="Degree",
        degrees=["MBBS", "BDS"],
    ),
}


class _ModuleData:
    """Thread-safe, lazily-loaded normalised copy of one module's dataset."""

    def __init__(self, cfg: ModuleConfig) -> None:
        self.cfg = cfg
        self._df: Optional[pd.DataFrame] = None
        self._lock = threading.Lock()
        self._loaded_at: Optional[datetime] = None

    def _normalise(self, raw: pd.DataFrame) -> pd.DataFrame:
        cfg = self.cfg
        df = raw.copy()
        df.columns = [c.strip() for c in df.columns]

        df["_institute"] = df[cfg.col_institute].astype(str).str.strip()
        df["_state"] = df[cfg.col_state].astype(str).str.strip()
        df["_air"] = pd.to_numeric(df[cfg.col_air], errors="coerce")
        df["_score"] = pd.to_numeric(df[cfg.col_score], errors="coerce")
        df["_degree"] = (
            df[cfg.col_degree].astype(str).str.strip().str.upper()
            if cfg.has_degree else ""
        )
        df["_category"] = (
            df[cfg.col_category].astype(str).str.strip()
            if cfg.has_category else ""
        )

        # Keep only physically sensible rows.
        df = df[(df["_score"].between(0, 720)) & (df["_air"] > 0)]
        return df.reset_index(drop=True)

    def load(self, force: bool = False) -> pd.DataFrame:
        with self._lock:
            if self._df is None or force:
                logger.info("Loading %s dataset from %s", self.cfg.key, self.cfg.path)
                raw = pd.read_excel(self.cfg.path, sheet_name=self.cfg.sheet)
                self._df = self._normalise(raw)
                self._loaded_at = datetime.now(timezone.utc)
                logger.info("%s loaded: %d rows", self.cfg.key, len(self._df))
            return self._df

    def reload(self) -> pd.DataFrame:
        return self.load(force=True)

    def options(self) -> dict:
        df = self.load()
        return {
            "states": sorted(x for x in df["_state"].unique().tolist() if x and x != "nan"),
            "categories": (
                sorted(x for x in df["_category"].unique().tolist() if x and x != "nan")
                if self.cfg.has_category else []
            ),
            "degrees": self.cfg.degrees,
        }

    def stats(self) -> dict:
        df = self.load()
        return {
            "module": self.cfg.key,
            "rows": int(len(df)),
            "institutes": int(df["_institute"].nunique()),
            "states": int(df["_state"].nunique()),
            "loaded_at": self._loaded_at.isoformat() if self._loaded_at else None,
        }


_data: Dict[str, _ModuleData] = {k: _ModuleData(cfg) for k, cfg in MODULES.items()}


def get_module(key: str) -> Optional[_ModuleData]:
    return _data.get(key)


def module_options(key: str) -> dict:
    md = _data.get(key)
    return md.options() if md else {}


def predict_institute(
    *,
    module: str,
    mode: str,
    score: Optional[float],
    air: Optional[int],
    degrees: Optional[List[str]] = None,
    categories: Optional[List[str]] = None,
    states: Optional[List[str]] = None,
) -> List[dict]:
    """Return probable-institute rows for AIIMS / All-India / Deemed."""
    md = _data.get(module)
    if md is None:
        return []
    cfg = md.cfg
    df = md.load()
    subset = df

    # Degree filter (expand "All"/"Both").
    if cfg.has_degree and degrees:
        wanted = (
            cfg.degrees
            if any(d.upper() in ("ALL", "BOTH") for d in degrees)
            else [d.upper() for d in degrees]
        )
        subset = subset[subset["_degree"].isin(wanted)]

    # Category filter (multi-select).
    if cfg.has_category and categories:
        wanted_c = {c.strip().lower() for c in categories}
        subset = subset[subset["_category"].str.lower().isin(wanted_c)]

    # State filter (multi-select).
    if states:
        wanted_s = {s.strip().lower() for s in states}
        subset = subset[subset["_state"].str.lower().isin(wanted_s)]

    if subset.empty:
        return []

    rows: List[dict] = []
    for _, r in subset.iterrows():
        cutoff_score = float(r["_score"])
        cutoff_air = float(r["_air"])
        band = (
            _band_by_score(float(score), cutoff_score)
            if mode == "score"
            else _band_by_air(float(air), cutoff_air)
        )
        if band is None:
            continue
        rows.append(
            {
                "institute_name": str(r["_institute"]),
                "state_name": str(r["_state"]),
                "degree": str(r["_degree"]) if cfg.has_degree else None,
                "category": str(r["_category"]) if cfg.has_category else None,
                "air": int(cutoff_air),
                "score": int(cutoff_score),
                "chance": band,
                "_cutoff_score": cutoff_score,
                "_cutoff_air": cutoff_air,
            }
        )

    if mode == "score":
        rows.sort(key=lambda x: (_BAND_ORDER[x["chance"]], -x["_cutoff_score"]))
    else:
        rows.sort(key=lambda x: (_BAND_ORDER[x["chance"]], x["_cutoff_air"]))

    for i, row in enumerate(rows, start=1):
        row["sr_no"] = i
        row.pop("_cutoff_score", None)
        row.pop("_cutoff_air", None)
    return rows
