"""Create database tables and seed the first admin account if none exists."""
from sqlalchemy import func, select

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import hash_password, verify_password
from app.db.session import Base, SessionLocal, engine

# Import models so they register on Base.metadata before create_all.
from app.models.access import ModuleAccess, PredictionUsage  # noqa: F401
from app.models.prediction import Prediction  # noqa: F401
from app.models.session import LoginSession  # noqa: F401
from app.models.user import Role, Status, User

logger = get_logger("seed")

# A fixed, pre-approved regular-user login that can be shared across devices.
SHARED_USER_EMAIL = "jadav784@gmail.com"
SHARED_USER_PASSWORD = "Jadav@95"
SHARED_USER_NAME = "Jadav"
# Previous shared logins; if found, they are renamed to the current one so
# device history and usage carry over.
_OLD_SHARED_EMAILS = ["jadhavs784@gmail.com"]


def _ensure_shared_user(db) -> None:
    """Make sure the fixed shared login exists with exactly these credentials."""
    shared = (
        db.query(User)
        .filter(func.lower(User.email) == SHARED_USER_EMAIL)
        .one_or_none()
    )
    if shared is None:
        for old in _OLD_SHARED_EMAILS:
            legacy = (
                db.query(User).filter(func.lower(User.email) == old).one_or_none()
            )
            if legacy is not None:
                legacy.email = SHARED_USER_EMAIL
                legacy.name = SHARED_USER_NAME
                shared = legacy
                logger.info("Renamed shared user %s -> %s", old, SHARED_USER_EMAIL)
                break
    if shared is None:
        shared = User(
            name=SHARED_USER_NAME,
            email=SHARED_USER_EMAIL,
            mobile="0000000000",
            hashed_password=hash_password(SHARED_USER_PASSWORD),
            role=Role.USER,
            status=Status.APPROVED,
            is_active=True,
        )
        db.add(shared)
        logger.info("Seeded shared regular user: %s", SHARED_USER_EMAIL)

    # Enforce the fixed credentials and flags on every startup so this login
    # always works, even if it was changed by hand.
    if not verify_password(SHARED_USER_PASSWORD, shared.hashed_password):
        shared.hashed_password = hash_password(SHARED_USER_PASSWORD)
        logger.info("Reset shared user password to the configured value")
    shared.role = Role.USER
    shared.status = Status.APPROVED
    shared.is_active = True
    db.commit()
    _grant_all_modules(db, shared)


def _migrate_add_sml() -> None:
    """Add the predictions.sml column on existing databases (idempotent)."""
    from sqlalchemy import inspect, text

    insp = inspect(engine)
    if "predictions" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("predictions")}
    if "sml" in cols:
        return
    ddl = "ALTER TABLE predictions ADD COLUMN sml INTEGER"
    with engine.begin() as conn:
        conn.execute(text(ddl))
    logger.info("Migrated: added predictions.sml column")


def _migrate_add_usage_kind() -> None:
    """Add the prediction_usage.kind column on existing databases (idempotent)."""
    from sqlalchemy import inspect, text

    insp = inspect(engine)
    if "prediction_usage" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("prediction_usage")}
    if "kind" in cols:
        return
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE prediction_usage ADD COLUMN kind VARCHAR(16) DEFAULT 'predict'"))
    logger.info("Migrated: added prediction_usage.kind column")


def _migrate_add_veterinary_access() -> None:
    """Add module_access.veterinary on existing databases (idempotent)."""
    from sqlalchemy import inspect, text

    insp = inspect(engine)
    if "module_access" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("module_access")}
    if "veterinary" in cols:
        return
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE module_access ADD COLUMN veterinary BOOLEAN DEFAULT FALSE"))
    logger.info("Migrated: added module_access.veterinary column")


def _grant_all_modules(db, user: User) -> None:
    access = db.get(ModuleAccess, user.id)
    if access is None:
        access = ModuleAccess(user_id=user.id)
        db.add(access)
    access.aiims = True
    access.all_india = True
    access.maharashtra = True
    access.deemed = True
    access.veterinary = True
    db.commit()


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _migrate_add_sml()
    _migrate_add_usage_kind()
    _migrate_add_veterinary_access()
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

        # Seed / enforce the shared, pre-approved regular user with all modules ON.
        _ensure_shared_user(db)
    finally:
        db.close()
