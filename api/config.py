"""应用配置（环境变量）。"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    jwt_secret_key: str = "change-me-in-production-use-long-random-string"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    database_url: str = "sqlite:///./data/app.db"
    storage_root: str = "./storage"
    # 开发：启动时 create_all + 种子用户（生产请仅用 Alembic 并关闭 auto_create_tables）
    auto_create_tables: bool = True
    seed_demo_users: bool = True
    dev_admin_password: str = "admin123"
    dev_annotator_password: str = "anno123"
    dev_viewer_password: str = "view123"

    # P2 推理：YOLO classify 权重（留空则 /infer 仅返回演示 top-k）
    classify_weights_path: str = ""
    tonguesam_root: str = "./tongue_sam"
    infer_device: str = "cpu"
    infer_imgsz: int = 224
    infer_sam_timeout_sec: int = 600


@lru_cache
def get_settings() -> Settings:
    return Settings()
