from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OUTBOX_DIR: str = "outbox"
    CLOUD_URL: str = "http://127.0.0.1:9000/ingest"

    class Config:
        env_file = ".env"


settings = Settings()
