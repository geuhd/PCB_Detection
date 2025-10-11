from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    database_hostname: str
    database_port: str
    database_password: str
    database_name: str
    database_username: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes:int
    #DATABASE_URL: str = os.environ.get("DATABASE_URL")

    class Config:
        env_file =".env"



settings = Settings()

