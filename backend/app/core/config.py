from functools import lru_cache
import json
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "TXT Reader API"
    app_version: str = "0.1.0"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    api_v1_prefix: str = "/api/v1"
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: [
            "http://localhost:24412",
            "http://127.0.0.1:24412",
        ]
    )
    data_dir: Path = BACKEND_DIR / "data"
    upload_dir: Path = BACKEND_DIR / "uploads"
    database_url: str | None = None
    secret_key: str = "change-this-in-production"
    access_token_expire_minutes: int = 60 * 24 * 7
    default_admin_username: str = "admin"
    default_admin_password: str = "admin123"
    default_txt_encoding: str = "utf-8"
    online_request_timeout_seconds: int = 15
    online_response_size_limit_bytes: int = 2 * 1024 * 1024
    online_default_user_agent: str = "TXT-Reader/Phase1"
    online_follow_redirects: bool = True

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return []
            if value.startswith("["):
                parsed = json.loads(value)
                if not isinstance(parsed, list):
                    raise ValueError("cors_origins JSON value must be a list")
                return [str(item).strip() for item in parsed if str(item).strip()]
            return [item.strip() for item in value.split(",") if item.strip()]
        if isinstance(value, (list, tuple, set)):
            return [str(item).strip() for item in value if str(item).strip()]
        return value

    @field_validator("data_dir", "upload_dir", mode="before")
    @classmethod
    def normalize_path(cls, value: object) -> Path:
        if isinstance(value, Path):
            return value
        return Path(str(value))

    @model_validator(mode="after")
    def finalize_paths(self) -> "Settings":
        self.data_dir = self._to_absolute_path(self.data_dir)
        self.upload_dir = self._to_absolute_path(self.upload_dir)
        if not self.database_url:
            self.database_url = f"sqlite:///{(self.data_dir / 'app.db').as_posix()}"
        return self

    @staticmethod
    def _to_absolute_path(path: Path) -> Path:
        return path if path.is_absolute() else (BACKEND_DIR / path).resolve()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
