from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # GitHub OAuth App
    github_client_id: str
    github_client_secret: str

    # Server PAT for creating PRs (fine-grained, scoped to repo)
    github_pat: str

    # Target repository
    github_repo: str = "JELambert/pax-market"

    # Session signing
    secret_key: str

    # URLs
    base_url: str = "https://submit.pax-market.com"
    main_site_url: str = "https://pax-market.com"

    # Upload limits
    max_upload_bytes: int = 10 * 1024 * 1024  # 10MB
    max_file_bytes: int = 5 * 1024 * 1024  # 5MB
    max_file_count: int = 20

    # Rate limiting
    rate_limit_per_hour: int = 5
    rate_limit_global_per_hour: int = 100

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
