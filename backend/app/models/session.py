"""Login session / device tracking.

Each distinct device (approximated by user-agent + IP) that logs in for a user
gets one row here. Re-logging in from the same device updates last_seen_at
instead of creating a duplicate, so the admin panel can show an accurate
"how many devices" count per account.
"""
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class LoginSession(Base):
    __tablename__ = "login_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    device_label: Mapped[str] = mapped_column(String(120), default="Unknown device")
    browser: Mapped[str] = mapped_column(String(60), default="Unknown")
    os: Mapped[str] = mapped_column(String(60), default="Unknown")
    ip: Mapped[str] = mapped_column(String(64), default="")
    user_agent: Mapped[str] = mapped_column(Text, default="")

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    user = relationship("User", back_populates="sessions")
