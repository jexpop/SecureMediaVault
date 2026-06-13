from pathlib import Path

from src.core.crypto.encryption_service import EncryptionService
from src.core.storage.media_storage import MediaStorage

from src.database.repositories.media_repository import MediaRepository
from src.database.models.media_model import Media


class ImportService:

    def __init__(self):

        self.storage = MediaStorage()
        self.encryption_service = EncryptionService()
        self.repository = MediaRepository()

    def import_file(self, source_file: str, password: str):

        source = Path(source_file)

        if not source.exists():
            raise Exception("File not found")

        media_uuid, target_path = self.storage.create_encrypted_path()

        self.encryption_service.encrypt_file(
            source_path=str(source),
            target_path=target_path,
            password=password
        )

        media = Media(
            uuid=media_uuid,
            encrypted_path=target_path,
            original_filename=source.name,
            media_type=source.suffix.replace(".", "")
        )

        saved = self.repository.save(media)

        return {
            "id": saved.id,
            "uuid": saved.uuid,
            "encrypted_path": saved.encrypted_path,
            "original_filename": saved.original_filename
        }