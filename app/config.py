from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/harvesterflow"
    app_name: str = "HarvesterFlow"
    debug: bool = False

    whatsapp_verify_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_access_token: str = ""
    redis_url: str = "redis://localhost:6379/1"

    class Config:
        env_file = ".env"


settings = Settings()
