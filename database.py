from sqlalchemy import create_engine, text
from config import settings

engine = create_engine(url=settings.database_url)


def execute_query(query: str, fetchall: bool = False):
    with engine.connect() as connection:
        result = connection.execute(text(query))
        connection.commit()
        return result.all() if fetchall else None
