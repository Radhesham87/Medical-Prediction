"""Per-module access permissions and per-module usage logging.

- ModuleAccess: one row per user; four booleans decide which of the four
  prediction modules that user is allowed to open. Missing row = all off.
- PredictionUsage: one row per prediction run (any module), so the admin panel
  can show which module a user used and how many times.
"""
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ModuleAccess(Base):
    __tablename__ = "module_access"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    aiims: Mapped[bool] = mapped_column(Boolean, default=False)
    all_india: Mapped[bool] = mapped_column(Boolean, default=False)
    maharashtra: Mapped[bool] = mapped_column(Boolean, default=False)
    deemed: Mapped[bool] = mapped_column(Boolean, default=False)
    veterinary: Mapped[bool] = mapped_column(Boolean, default=False)

    user = relationship("User", back_populates="module_access")


class PredictionUsage(Base):
    __tablename__ = "prediction_usage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    module: Mapped[str] = mapped_column(String(32), index=True)  # aiims|all-india|maharashtra|deemed
    kind: Mapped[str] = mapped_column(String(16), default="predict", index=True)  # predict|download
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    user = relationship("User", back_populates="usage_events")
