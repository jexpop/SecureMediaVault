from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QSizePolicy
)

from PySide6.QtGui import QMovie, QPixmap
from PySide6.QtCore import Qt, QSize, QByteArray, QBuffer


class VideoThumbnailWidget(QWidget):
    """
    Gallery thumbnail for a video:
      - Shows a static frame by default.
      - On hover (or while selected), plays a short looping GIF
        preview decrypted in memory.
      - Shows the tag list below the thumbnail, matching the
        layout used for image items (so video items line up with
        image items in the grid).

    The GIF bytes are decrypted on hover and discarded on
    mouseleave (the QMovie/QBuffer are dropped), so the decrypted
    animated preview is never written to disk and is not kept in
    memory longer than needed for display.
    """

    def __init__(
        self,
        static_pixmap: QPixmap,
        gif_bytes_provider,
        thumbnail_size: QSize,
        tags_text: str,
        parent=None
    ):

        super().__init__(parent)

        self._static_pixmap = static_pixmap
        self._gif_bytes_provider = gif_bytes_provider
        self._thumbnail_size = thumbnail_size

        self._movie = None
        self._movie_buffer = None
        self._movie_data = None

        self._selected = False

        self.setAttribute(
            Qt.WA_Hover,
            True
        )

        # -------------------------
        # THUMBNAIL LABEL
        # -------------------------
        self.image_label = QLabel()

        self.image_label.setFixedSize(
            thumbnail_size
        )

        self.image_label.setAlignment(
            Qt.AlignCenter
        )

        self.image_label.setSizePolicy(
            QSizePolicy.Fixed,
            QSizePolicy.Fixed
        )

        # -------------------------
        # TAGS LABEL
        # -------------------------
        self.tags_label = QLabel(
            tags_text
        )

        self.tags_label.setAlignment(
            Qt.AlignHCenter | Qt.AlignTop
        )

        self.tags_label.setWordWrap(
            True
        )

        self.tags_label.setSizePolicy(
            QSizePolicy.Preferred,
            QSizePolicy.Preferred
        )

        # -------------------------
        # LAYOUT
        # -------------------------
        layout = QVBoxLayout()

        layout.setAlignment(
            Qt.AlignHCenter
        )

        layout.addWidget(
            self.image_label,
            alignment=Qt.AlignHCenter
        )

        layout.addWidget(
            self.tags_label
        )

        self.setLayout(layout)

        self._show_static()

    # -------------------------
    # STATIC / ANIMATED SWITCHING
    # -------------------------
    def _show_static(self):

        self._stop_movie()

        if self._static_pixmap and not self._static_pixmap.isNull():

            scaled = self._static_pixmap.scaled(
                self._thumbnail_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )

            self.image_label.setPixmap(scaled)

    def _show_animated(self):

        if self._movie is not None:
            return  # already playing

        gif_bytes = self._gif_bytes_provider()

        if not gif_bytes:
            return

        self._movie_data = QByteArray(gif_bytes)

        self._movie_buffer = QBuffer(self)
        self._movie_buffer.setData(self._movie_data)
        self._movie_buffer.open(QBuffer.ReadOnly)

        self._movie = QMovie(self)
        self._movie.setDevice(self._movie_buffer)
        self._movie.setScaledSize(self._thumbnail_size)
        self._movie.setCacheMode(QMovie.CacheAll)

        self.image_label.setMovie(self._movie)

        self._movie.start()

    def _stop_movie(self):

        if self._movie is not None:
            self._movie.stop()
            self.image_label.setMovie(None)
            self._movie.deleteLater()

        if self._movie_buffer is not None:
            self._movie_buffer.close()

        self._movie = None
        self._movie_buffer = None
        self._movie_data = None

    # -------------------------
    # SELECTION (kept animated while selected)
    # -------------------------
    def set_selected(self, selected: bool):

        self._selected = selected

        if selected:
            self._show_animated()
        elif not self.underMouse():
            self._show_static()

    # -------------------------
    # HOVER EVENTS
    # -------------------------
    def enterEvent(self, event):

        self._show_animated()
        super().enterEvent(event)

    def leaveEvent(self, event):

        if not self._selected:
            self._show_static()

        super().leaveEvent(event)