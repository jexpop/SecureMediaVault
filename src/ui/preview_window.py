from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtCore import Qt, QPoint

from src.core.services.thumbnail_service import ThumbnailService


class PreviewWindow(QWidget):

    def __init__(self, media_list, current_index, password):

        super().__init__()

        self.setWindowTitle("Preview")
        self.setMouseTracking(True)

        # -------------------------
        # DATA
        # -------------------------
        self.media_list = media_list
        self.index = current_index
        self.password = password

        # -------------------------
        # SERVICE
        # -------------------------
        self.thumbnail_service = ThumbnailService()

        # -------------------------
        # STATE (ZOOM + PAN)
        # -------------------------
        self._pixmap = None

        self._scale = 1.0
        self._min_scale = 0.2
        self._max_scale = 5.0

        self._offset = QPoint(0, 0)

        self._dragging = False
        self._last_pos = QPoint()

        self.showMaximized()

        self.load_image()

    # -------------------------
    # CURRENT MEDIA
    # -------------------------
    def current_media(self):
        return self.media_list[self.index]

    # -------------------------
    # LOAD IMAGE
    # -------------------------
    def load_image(self):

        media = self.current_media()

        self._pixmap = self.thumbnail_service.get_image_pixmap(
            encrypted_path=media.encrypted_path,
            password=self.password
        )

        self._scale = 1.0
        self._offset = QPoint(0, 0)

        self.update()

    # -------------------------
    # PAINT ENGINE (NO QT LOOP BUGS)
    # -------------------------
    def paintEvent(self, event):

        if not self._pixmap:
            return

        painter = QPainter(self)

        scaled = self._pixmap.scaled(
            self._pixmap.size() * self._scale,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        x = (self.width() - scaled.width()) // 2 + self._offset.x()
        y = (self.height() - scaled.height()) // 2 + self._offset.y()

        painter.fillRect(self.rect(), Qt.black)
        painter.drawPixmap(x, y, scaled)

    # -------------------------
    # ZOOM PRO (CURSOR-BASED)
    # -------------------------
    def wheelEvent(self, event):

        if not self._pixmap:
            return

        old_scale = self._scale

        # zoom factor
        if event.angleDelta().y() > 0:
            new_scale = self._scale * 1.1
        else:
            new_scale = self._scale * 0.9

        new_scale = max(self._min_scale, min(new_scale, self._max_scale))

        # cursor position
        cursor = event.position().toPoint()
        center = self.rect().center()

        rel_x = cursor.x() - center.x()
        rel_y = cursor.y() - center.y()

        factor = new_scale / old_scale

        # adjust offset so zoom locks under cursor
        self._offset = QPoint(
            int(self._offset.x() - rel_x * (factor - 1)),
            int(self._offset.y() - rel_y * (factor - 1))
        )

        self._scale = new_scale
        self.update()

    # -------------------------
    # PAN START
    # -------------------------
    def mousePressEvent(self, event):

        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._last_pos = event.position().toPoint()

    # -------------------------
    # PAN MOVE
    # -------------------------
    def mouseMoveEvent(self, event):

        if self._dragging:

            pos = event.position().toPoint()
            delta = pos - self._last_pos

            self._offset += delta
            self._last_pos = pos

            self.update()

    # -------------------------
    # PAN END
    # -------------------------
    def mouseReleaseEvent(self, event):

        if event.button() == Qt.LeftButton:
            self._dragging = False

    # -------------------------
    # NAV + SHORTCUTS
    # -------------------------
    def keyPressEvent(self, event):

        if event.key() == Qt.Key_Escape:
            self.close()

        elif event.key() == Qt.Key_Right:
            if self.index < len(self.media_list) - 1:
                self.index += 1
                self.load_image()

        elif event.key() == Qt.Key_Left:
            if self.index > 0:
                self.index -= 1
                self.load_image()

        elif event.key() == Qt.Key_R:
            self._scale = 1.0
            self._offset = QPoint(0, 0)
            self.update()