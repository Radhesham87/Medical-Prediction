"""Request/response schemas for the AIIMS, All-India and Deemed modules."""
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, model_validator


class InstitutePredictRequest(BaseModel):
    student_name: str = Field(min_length=1, max_length=150)
    mode: Literal["score", "air"]
    score: Optional[float] = Field(default=None, ge=0, le=720)
    air: Optional[int] = Field(default=None, ge=1)
    degrees: Optional[List[str]] = None      # All-India / Deemed
    categories: Optional[List[str]] = None   # AIIMS / All-India
    states: Optional[List[str]] = None       # all three

    @model_validator(mode="after")
    def _check(self):
        if self.mode == "score" and self.score is None:
            raise ValueError("score is required when mode is 'score'")
        if self.mode == "air" and self.air is None:
            raise ValueError("air is required when mode is 'air'")
        return self


class InstituteResult(BaseModel):
    sr_no: int
    institute_name: str
    state_name: str
    degree: Optional[str] = None
    category: Optional[str] = None
    air: int
    score: int
    chance: str


class InstitutePredictResponse(BaseModel):
    module: str
    student_name: str
    mode: str
    score: Optional[float]
    air: Optional[int]
    generated_at: datetime
    show_degree: bool
    show_category: bool
    results: List[InstituteResult]


class InstituteOptions(BaseModel):
    states: List[str]
    categories: List[str]
    degrees: List[str]


class InstitutePdfRequest(BaseModel):
    module: str
    student_name: str
    mode: str
    score: Optional[float] = None
    air: Optional[int] = None
    show_degree: bool = False
    show_category: bool = False
    results: List[InstituteResult]
