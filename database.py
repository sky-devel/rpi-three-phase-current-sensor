from sqlalchemy import create_engine, text
from config import settings

engine = create_engine(url=settings.database_url)


with engine.connect() as connection:
    result = connection.execute(text("SELECT VERSION()"))
    print(result.first())
