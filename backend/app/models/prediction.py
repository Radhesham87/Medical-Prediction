"""Prediction history model. Inputs and result rows are stored as JSON text."""
import json
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    student_name: Mapped[str] = mapped_column(String(150))
    mode: Mapped[str] = mapped_column(String(10))  # "score" | "air" | "sml"
    score: Mapped[float | None] = mapped_column(nullable=True)
    air: Mapped[int | None] = mapped_column(nullable=True)
    sml: Mapped[int | None] = mapped_column(nullable=True)
    gender: Mapped[str] = mapped_column(String(10))
    category: Mapped[str] = mapped_column(String(20))
    degrees: Mapped[str] = mapped_column(Text)  # JSON list
    result_json: Mapped[str] = mapped_column(Text)  # JSON list of result rows
    downloads: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)

    user = relationship("User", back_populates="predictions")

    @property
    def degrees_list(self) -> list[str]:
        return json.loads(self.degrees or "[]")

    @property
    def results(self) -> list[dict]:
        return json.loads(self.result_json or "[]")
