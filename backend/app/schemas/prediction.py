"""Schemas for the prediction request and its output rows."""
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, model_validator

# Categories accepted from the UI (map cleanly onto the dataset's Quota-Gender prefixes).
Category = Literal[
    "OPEN", "OBC", "SEBC", "EWS", "VJA", "NTB", "NTC", "NTD", "SC", "ST", "D1", "D2", "D3"
]
Gender = Literal["Male", "Female"]
Degree = Literal["MBBS", "BDS", "BAMS", "BHMS", "BUMS", "BPTH"]


class PredictionRequest(BaseModel):
    student_name: str = Field(min_length=1, max_length=150)
    mode: Literal["score", "air"]
    score: Optional[float] = Field(default=None, ge=0, le=720)
    air: Optional[int] = Field(default=None, ge=1)
    degrees: List[str] = Field(min_length=1)  # "All" allowed; expanded server-side
    gender: Gender
    category: Category

    @model_validator(mode="after")
    def _check_mode_value(self):
        if self.mode == "score" and self.score is None:
            raise ValueError("score is required when mode is 'score'")
        if self.mode == "air" and self.air is None:
            raise ValueError("air is required when mode is 'air'")
        return self


class CollegeResult(BaseModel):
    sr_no: int
    college_code: str
    college_name: str
    status: str
    degree: str
    neet_score: Optional[float]
    neet_sml: Optional[float]
    air: Optional[int]
    category_rank: Optional[str]
    chance: str  # "High" | "Moderate" | "Low"


class PredictionResponse(BaseModel):
    student_name: str
    mode: str
    score: Optional[float]
    air: Optional[int]
    gender: str
    category: str
    show_category_rank: bool
    generated_at: datetime
    results: List[CollegeResult]


class PredictionHistoryOut(BaseModel):
    id: int
    student_name: str
    mode: str
    score: Optional[float]
    air: Optional[int]
    gender: str
    category: str
    degrees: List[str]
    result_count: int
    created_at: datetime
