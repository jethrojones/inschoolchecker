import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass
class Settings:
    database_url: str
    redis_url: str
    object_storage_bucket: str
    object_storage_endpoint: str
    object_storage_access_key: str
    object_storage_secret_key: str
    app_base_url: str
    api_base_url: str
    user_agent_string: str
    openai_api_key: str | None
    max_fetches_per_domain: int
    max_crawl_depth: int
    fetch_timeout_seconds: int
    snapshot_dir: str
    cors_allowed_origins: str

    @property
    def snapshot_path(self) -> Path:
        return Path(self.snapshot_dir)


@lru_cache
def get_settings() -> Settings:
    return Settings(
        database_url=os.getenv("DATABASE_URL", "sqlite:///./inschoolchecker.db"),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        object_storage_bucket=os.getenv("OBJECT_STORAGE_BUCKET", "inschoolchecker"),
        object_storage_endpoint=os.getenv("OBJECT_STORAGE_ENDPOINT", "http://localhost:9000"),
        object_storage_access_key=os.getenv("OBJECT_STORAGE_ACCESS_KEY", "minioadmin"),
        object_storage_secret_key=os.getenv("OBJECT_STORAGE_SECRET_KEY", "minioadmin"),
        app_base_url=os.getenv("APP_BASE_URL", "http://localhost:3000"),
        api_base_url=os.getenv("API_BASE_URL", "http://localhost:8000"),
        user_agent_string=os.getenv("USER_AGENT_STRING", "DistrictStatusChecker/0.1 (+contact: ops@example.com)"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        max_fetches_per_domain=int(os.getenv("MAX_FETCHES_PER_DOMAIN", "20")),
        max_crawl_depth=int(os.getenv("MAX_CRAWL_DEPTH", "2")),
        fetch_timeout_seconds=int(os.getenv("FETCH_TIMEOUT_SECONDS", "10")),
        snapshot_dir=os.getenv("SNAPSHOT_DIR", "apps/api/data/snapshots"),
        cors_allowed_origins=os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000,https://jethrojones.github.io"),
    )
