from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_HOSTNAME: str
    DB_PORT: int
    DB_PASSWORD: str
    DB_NAME: str
    DB_USERNAME: str

    @property
    def database_url(self):
        return f'postgresql://{self.DB_USERNAME}:{self.DB_PASSWORD}@{self.DB_HOSTNAME}:{self.DB_PORT}/{self.DB_NAME}'

    class Config:
        env_file = ".env"


settings = Settings()
