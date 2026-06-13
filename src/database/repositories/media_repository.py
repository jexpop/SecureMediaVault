from src.database.db_manager import (
    SessionLocal
)

from src.database.models.media_model import (
    Media
)


class MediaRepository:

    def save(
        self,
        media: Media
    ):

        session = SessionLocal()

        try:

            session.add(media)
            session.commit()
            session.refresh(media)

            return media

        finally:

            session.close()

    def get_all(self):

        session = SessionLocal()

        try:

            return (
                session.query(Media)
                .order_by(
                    Media.imported_at.desc()
                )
                .all()
            )

        finally:

            session.close()