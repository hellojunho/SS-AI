from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "mysql+pymysql://ss_ai:ss_ai@db:3306/ss_ai"
    database_connect_max_retries: int = 10
    database_connect_retry_seconds: float = 1.0
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 15
    jwt_refresh_expire_minutes: int = 43200
    openai_model: str = "gpt-4o-mini"
    openai_token_budget: int = 128000
    openai_usage_endpoint: str = "https://api.openai.com/v1/usage"
    openai_api_key: str | None = None
    gemini_api_key: str | None = None
    # gemini_model: str = "gemini-2.5-pro"
    gemini_model: str = "gemini-2.5-flash" # gemini-flash-latest
    cors_allow_origins: list[str] = []
    cors_allow_origin_regex: str | None = r"^https?://(localhost|127\\.0\\.0\\.1)(:\\d+)?$"
    cors_allow_credentials: bool = False

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
