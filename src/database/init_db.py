from src.database.db_manager import (
    engine,
    Base
)

from src.database.models.media_model import (
    Media
)

from src.database.models.tag_models import Tag


def init_database():

    Base.metadata.create_all(
        bind=engine
    )

    print(
        "Database initialized"
    )


if __name__ == "__main__":
    init_database()