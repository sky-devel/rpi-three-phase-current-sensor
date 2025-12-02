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

    @property
    def database_url(self):
        return f"postgresql://{self.DB_USERNAME}:{self.DB_PASSWORD}@{self.DB_HOSTNAME}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        env_file = ".env"


settings = Settings()
