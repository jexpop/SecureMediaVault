from PySide6.QtGui import (
    QPixmap,
    QPainter,
    QColor,
    QPolygon
)

from PySide6.QtCore import (
    Qt,
    QPoint,
    QSize
)

from src.core.crypto.encryption_service import (
    EncryptionService
)

from src.core.services.media_category import (
    classify_extension
)


class ThumbnailService:

    def __init__(self):

        self.encryption = (
            EncryptionService()
        )

    # -------------------------
    # GALLERY THUMBNAIL
    # -------------------------
    def get_gallery_pixmap(self, media, password: str) -> QPixmap:
        """
        Returns the pixmap to show in the gallery:
          - Images: decrypted and loaded directly.
          - Videos: a generic placeholder icon. The video
            content is NEVER decrypted just to build a thumbnail.
        """

        category = classify_extension(
            media.display_media_type
        )

        if category == "image":
            return self.get_image_pixmap(
                media.encrypted_path,
                password
            )

        return self._video_placeholder_pixmap()

    # -------------------------
    # FULL IMAGE (used by gallery and preview)
    # -------------------------
    def get_image_pixmap(
        self,
        encrypted_path: str,
        password: str
    ) -> QPixmap:

        image_bytes = self.encryption.decrypt_bytes(
            encrypted_path,
            password
        )

        pixmap = QPixmap()

        pixmap.loadFromData(
            image_bytes
        )

        return pixmap

    # -------------------------
    # VIDEO PLACEHOLDER
    # -------------------------
    def _video_placeholder_pixmap(self) -> QPixmap:

        size = QSize(180, 180)

        pixmap = QPixmap(size)
        pixmap.fill(QColor("#202020"))

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.setBrush(QColor("#e0e0e0"))
        painter.setPen(Qt.NoPen)

        cx, cy = size.width() // 2, size.height() // 2
        triangle_size = 40

        points = [
            QPoint(cx - triangle_size // 2, cy - triangle_size),
            QPoint(cx - triangle_size // 2, cy + triangle_size),
            QPoint(cx + triangle_size, cy)
        ]

        painter.drawPolygon(QPolygon(points))

        painter.end()

        return pixmap