from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./quiz.db"
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    groq_api_key: str = ""
    cors_origins: str = "http://localhost:8000,http://localhost:5500"
    max_upload_size_mb: int = 10
    domains: str = "General / Other,Data Science,Frontend Development,Backend Development,DevOps,ML Engineering,Cloud Computing,Cybersecurity,Mobile Development,System Design,Database Administration"

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def domain_list(self) -> List[str]:
        return [d.strip() for d in self.domains.split(",") if d.strip()]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
