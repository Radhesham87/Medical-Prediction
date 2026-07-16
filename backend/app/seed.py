"""Create database tables and seed the first admin account if none exists."""
from sqlalchemy import select

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import hash_password
from app.db.session import Base, SessionLocal, engine

# Import models so they register on Base.metadata before create_all.
from app.models.prediction import Prediction  # noqa: F401
from app.models.user import Role, Status, User

logger = get_logger("seed")


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        admin = db.execute(select(User).where(User.role == Role.ADMIN)).scalar_one_or_none()
        if admin is None:
            admin = User(
                name=settings.FIRST_ADMIN_NAME,
                email=settings.FIRST_ADMIN_EMAIL.lower(),
                mobile="0000000000",
                hashed_password=hash_password(settings.FIRST_ADMIN_PASSWORD),
                role=Role.ADMIN,
                status=Status.APPROVED,
                is_active=True,
            )
            db.add(admin)
            db.commit()
            logger.info("Seeded first admin: %s", admin.email)
        else:
            logger.info("Admin already present: %s", admin.email)
    finally:
        db.close()
