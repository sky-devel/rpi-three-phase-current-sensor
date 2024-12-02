from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    DB_HOSTNAME: str
    DB_PORT: int
    DB_PASSWORD: str
    DB_NAME: str
    DB_USERNAME: str

    SERIAL_PORT_LIST: List[str]
    BAUD_RATE: int
    SLAVE_ID: int

    class Config:
        env_file = ".env"


settings = Settings()
