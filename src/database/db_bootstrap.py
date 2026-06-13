from sqlalchemy import inspect

from src.database.db_manager import (
    engine,
    Base
)


class DBBootstrap:

    def __init__(self):

        self.inspector = inspect(engine)

    def ensure_tables(self):

        existing_tables = (
            self.inspector.get_table_names()
        )

        if not existing_tables:

            print(
                "[DB] Creating tables..."
            )

            Base.metadata.create_all(
                bind=engine
            )

        else:

            # opcional: asegurar columnas futuras
            Base.metadata.create_all(
                bind=engine
            )

            print(
                "[DB] OK"
            )