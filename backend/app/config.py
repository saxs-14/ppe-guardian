import os
import json
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "PPE Guardian"
    database_url: str = "sqlite:///./ppeguardian.db"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    upload_dir: str = "./uploads"
    max_upload_mb: int = 100
    default_zone: str = "construction"
    zone_rules_json: str = '{"construction": ["helmet", "vest"], "mining": ["helmet"], "warehouse": ["vest"]}'
    api_key: str = "dev-local-key-change-me"

    class Config:
        env_file = ".env"

    @property
    def zone_rules(self) -> dict:
        return json.loads(self.zone_rules_json)


settings = Settings()
os.makedirs(settings.upload_dir, exist_ok=True)
