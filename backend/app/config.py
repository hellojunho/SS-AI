from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "mysql+pymysql://ss_ai:ss_ai@db:3306/ss_ai"
    database_connect_max_retries: int = 10
    database_connect_retry_seconds: float = 1.0
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30
    jwt_refresh_expire_minutes: int = 30
    openai_api_key: str | None = None
    cors_allow_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    cors_allow_origin_regex: str | None = None

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
