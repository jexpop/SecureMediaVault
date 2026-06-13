from PySide6.QtGui import (
    QPixmap
)

from src.core.crypto.encryption_service import (
    EncryptionService
)


class ThumbnailService:

    def __init__(self):

        self.encryption = (
            EncryptionService()
        )

    def get_pixmap(
        self,
        encrypted_path: str,
        password: str
    ):

        image_bytes = (
            self.encryption.decrypt_bytes(
                encrypted_path,
                password
            )
        )

        pixmap = QPixmap()

        pixmap.loadFromData(
            image_bytes
        )

        return pixmap