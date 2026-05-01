from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/harvesterflow"
    app_name: str = "HarvesterFlow"
    debug: bool = False

    class Config:
        env_file = ".env"


settings = Settings()
