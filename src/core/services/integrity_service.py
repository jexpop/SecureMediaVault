import os

from src.core.crypto.encryption_service import (
    EncryptionService
)


class IntegrityService:

    def __init__(self):

        self.crypto = EncryptionService()

    def check_media(
        self,
        media,
        password: str
    ):

        # 1. archivo existe
        if not os.path.exists(media.encrypted_path):

            return "missing"

        # 2. intentar decrypt (sin guardar)
        try:

            self.crypto.decrypt_bytes(
                source_path=media.encrypted_path,
                password=password
            )

            return "ok"

        except Exception:

            return "corrupt"