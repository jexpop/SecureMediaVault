import uuid
from pathlib import Path


class MediaStorage:

    BASE_PATH = Path("vault/media")

    def generate_uuid(self) -> str:
        return str(uuid.uuid4())

    def build_storage_path(
        self,
        media_uuid: str
    ) -> Path:

        first = media_uuid[:2]
        second = media_uuid[2:4]

        folder = (
            self.BASE_PATH /
            first /
            second
        )

        folder.mkdir(
            parents=True,
            exist_ok=True
        )

        filename = (
            f"{media_uuid}.enc"
        )

        return folder / filename

    def create_encrypted_path(
        self
    ) -> tuple[str, str]:

        media_uuid = (
            self.generate_uuid()
        )

        path = self.build_storage_path(
            media_uuid
        )

        return (
            media_uuid,
            str(path)
        )