"""首次启动：演示用户与默认项目。"""
import bcrypt
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.config import Settings
from db.models import Project, User, UserRole
from db.session import get_engine


def _hash(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def ensure_demo_seed(db: Session, settings: Settings) -> None:
    if not settings.seed_demo_users:
        return
    default_project = db.scalar(select(Project).where(Project.name == "default"))
    if not default_project:
        db.add(Project(name="default"))
        db.commit()

    for username, full_name, role, pwd in (
        ("admin", "系统管理员", UserRole.admin.value, settings.dev_admin_password),
        ("annotator", "标注员", UserRole.annotator.value, settings.dev_annotator_password),
        ("viewer", "只读访客", UserRole.viewer.value, settings.dev_viewer_password),
    ):
        existing = db.scalar(select(User).where(User.username == username))
        if existing:
            continue
        db.add(
            User(
                username=username,
                full_name=full_name,
                role=role,
                password_hash=_hash(pwd),
                is_active=True,
            )
        )
    db.commit()


def init_db_schema_and_seed(settings: Settings) -> None:
    from db.base import Base
    from db.sqlite_util import ensure_sqlite_dirs
    from sqlalchemy.orm import sessionmaker

    ensure_sqlite_dirs(settings.database_url)
    engine = get_engine()
    if settings.auto_create_tables:
        Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    with SessionLocal() as db:
        ensure_demo_seed(db, settings)
