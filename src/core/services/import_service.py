from pathlib import Path

from src.core.crypto.encryption_service import EncryptionService
from src.core.crypto.string_crypto_service import StringCryptoService
from src.core.storage.media_storage import MediaStorage
from src.core.config.vault_session import VaultSession

from src.database.repositories.media_repository import MediaRepository
from src.database.models.media_model import Media


class ImportService:

    def __init__(self):

        self.storage = MediaStorage()
        self.encryption_service = EncryptionService()
        self.string_crypto = StringCryptoService()
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

        metadata_key = VaultSession.get_metadata_key()

        encrypted_filename = self.string_crypto.encrypt(
            source.name,
            metadata_key
        )

        encrypted_media_type = self.string_crypto.encrypt(
            source.suffix.replace(".", ""),
            metadata_key
        )

        media = Media(
            uuid=media_uuid,
            encrypted_path=target_path,
            original_filename=encrypted_filename,
            media_type=encrypted_media_type
        )

        saved = self.repository.save(media)

        return {
            "id": saved.id,
            "uuid": saved.uuid,
            "encrypted_path": saved.encrypted_path,
            "original_filename": source.name
        }