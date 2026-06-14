from pathlib import Path

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
    # GALLERY THUMBNAIL (images + video static fallback)
    # -------------------------
    def get_gallery_pixmap(self, media, password: str) -> QPixmap:

        category = classify_extension(
            media.display_media_type
        )

        if category == "image":
            return self.get_image_pixmap(
                media.encrypted_path,
                password
            )

        static_pixmap = self.get_video_static_pixmap(
            media.encrypted_path,
            password
        )

        if static_pixmap is not None:
            return static_pixmap

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
    # VIDEO STATIC PREVIEW FRAME
    # -------------------------
    def get_video_static_pixmap(
        self,
        encrypted_path: str,
        password: str
    ):
        """
        Returns the decrypted static preview frame as a QPixmap,
        or None if no preview file exists / decryption fails.
        """

        static_path = encrypted_path + "_static.enc"

        if not Path(static_path).exists():
            return None

        try:
            image_bytes = self.encryption.decrypt_bytes(
                static_path,
                password
            )

            pixmap = QPixmap()
            pixmap.loadFromData(image_bytes)

            if pixmap.isNull():
                return None

            return pixmap

        except Exception:
            return None

    # -------------------------
    # VIDEO ANIMATED PREVIEW (GIF bytes)
    # -------------------------
    def get_video_preview_gif_bytes(
        self,
        encrypted_path: str,
        password: str
    ):
        """
        Returns the decrypted preview GIF as raw bytes, or None
        if no preview file exists / decryption fails. The caller
        loads these bytes into a QMovie via a QBuffer.
        """

        preview_path = encrypted_path + "_preview.enc"

        if not Path(preview_path).exists():
            return None

        try:
            return self.encryption.decrypt_bytes(
                preview_path,
                password
            )

        except Exception:
            return None

    def has_video_preview(self, encrypted_path: str) -> bool:

        return Path(
            encrypted_path + "_preview.enc"
        ).exists()

    # -------------------------
    # VIDEO PLACEHOLDER (no preview available)
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