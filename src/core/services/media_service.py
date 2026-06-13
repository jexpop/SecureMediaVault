from src.database.repositories.media_repository import (
    MediaRepository
)


class MediaService:

    def __init__(self):

        self.repository = (
            MediaRepository()
        )

    def get_all_media(self):

        return (
            self.repository.get_all()
        )