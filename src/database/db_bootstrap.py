from sqlalchemy import inspect, text

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

        # Import models so SQLAlchemy registers them with Base
        # before create_all. Order matters: TagCategory must be
        # registered before Tag (which references it via FK).
        from src.database.models.tag_category_model import TagCategory  # noqa
        from src.database.models.tag_models import Tag  # noqa
        from src.database.models.media_model import Media  # noqa

        if not existing_tables:

            print("[DB] Creating tables...")

            Base.metadata.create_all(
                bind=engine
            )

        else:

            # create_all creates new tables but does NOT alter
            # existing ones — so we run explicit column migrations
            # first, then let create_all handle any brand-new tables.
            self._migrate(existing_tables)

            Base.metadata.create_all(
                bind=engine
            )

            print("[DB] OK")

    # -------------------------
    # MIGRATIONS
    # -------------------------
    def _migrate(self, existing_tables):
        """
        Applies incremental schema changes to an existing database.
        Each migration is idempotent (checks before applying).
        """

        with engine.connect() as conn:

            # ------------------------------------------------
            # Migration 001: add category_id to tags table
            # ------------------------------------------------
            if "tags" in existing_tables:

                existing_cols = [
                    col["name"]
                    for col in self.inspector.get_columns("tags")
                ]

                if "category_id" not in existing_cols:

                    conn.execute(text(
                        "ALTER TABLE tags "
                        "ADD COLUMN category_id INTEGER "
                        "REFERENCES tag_categories(id)"
                    ))

                    conn.commit()

                    print(
                        "[DB] Migration: added category_id to tags"
                    )
