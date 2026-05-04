"""应用配置（环境变量）。"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    jwt_secret_key: str = "change-me-in-production-use-long-random-string"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    # 演示账号口令（生产环境须改为数据库 + 首次强制改密）
    dev_admin_password: str = "admin123"
    dev_annotator_password: str = "anno123"
    dev_viewer_password: str = "view123"


@lru_cache
def get_settings() -> Settings:
    return Settings()
