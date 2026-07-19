"""User model with role + approval-status workflow."""
import enum
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Role(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"


class Status(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    mobile: Mapped[str] = mapped_column(String(20), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    college: Mapped[str] = mapped_column(String(200), default="")
    city: Mapped[str] = mapped_column(String(100), default="")
    state: Mapped[str] = mapped_column(String(100), default="")

    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.USER, nullable=False)
    status: Mapped[Status] = mapped_column(Enum(Status), default=Status.PENDING, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    registration_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    predictions = relationship("Prediction", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("LoginSession", back_populates="user", cascade="all, delete-orphan")
    module_access = relationship(
        "ModuleAccess", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    usage_events = relationship(
        "PredictionUsage", back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def active_device_count(self) -> int:
        return sum(1 for s in self.sessions if s.is_active)

    @property
    def prediction_count(self) -> int:
        return len(self.predictions)
