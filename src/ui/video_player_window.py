from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QSlider,
    QLabel,
    QSizePolicy
)

from PySide6.QtMultimedia import (
    QMediaPlayer,
    QAudioOutput
)

from PySide6.QtMultimediaWidgets import (
    QVideoWidget
)

from PySide6.QtCore import (
    Qt,
    QUrl,
    QTimer
)

from src.core.services.temp_media_service import (
    TempMediaService
)


class VideoPlayerWindow(QWidget):
    """
    Reusable encrypted video player window.

    Since QMediaPlayer's FFmpeg backend is not reliable when
    streaming from an in-memory QIODevice (it can deadlock when
    swapping sources), each video is decrypted to a temporary
    file under vault/.tmp/ and played via QUrl.fromLocalFile().

    Temp files are securely deleted (overwritten + removed):
      - right after switching to a new video (once the player
        has released the previous file), and
      - when the window is closed.

    Any leftover temp files from a crashed session are cleaned
    up on app startup (see TempMediaService.cleanup_stale, called
    from app.py).
    on_close_callback, if provided, is called every time the
    window is closed (e.g. so MainWindow can re-enable the
    Change Password button while no media viewer is open).
    """

    def __init__(self, on_close_callback=None):

        super().__init__()

        self.resize(900, 600)

        self.temp_media_service = TempMediaService()
        self.on_close_callback = on_close_callback

        self._current_temp_path = None
        self._loading = False

        # -------------------------
        # PLAYER (created once, reused)
        # -------------------------
        self.video_widget = QVideoWidget()

        self.video_widget.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        self.audio_output = QAudioOutput()

        self.player = QMediaPlayer()
        self.player.setVideoOutput(self.video_widget)
        self.player.setAudioOutput(self.audio_output)

        self.player.errorOccurred.connect(self._on_error)

        # -------------------------
        # CONTROLS
        # -------------------------
        self.play_button = QPushButton("Pause")

        self.play_button.clicked.connect(
            self.toggle_play
        )

        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 0)

        self.position_slider.sliderMoved.connect(
            self._on_seek
        )

        self.position_slider.valueChanged.connect(
            self._on_value_changed
        )

        self.time_label = QLabel("00:00 / 00:00")

        self.player.positionChanged.connect(
            self._on_position_changed
        )

        self.player.durationChanged.connect(
            self._on_duration_changed
        )

        self.player.playbackStateChanged.connect(
            self._on_playback_state_changed
        )

        # -------------------------
        # LAYOUT
        # -------------------------
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.position_slider)
        controls_layout.addWidget(self.time_label)

        layout = QVBoxLayout()
        layout.addWidget(self.video_widget, stretch=1)
        layout.addLayout(controls_layout)

        self.setLayout(layout)

    # -------------------------
    # LOAD / SWAP MEDIA
    # -------------------------
    def load_media(self, media, password):

        if self._loading:
            return

        self._loading = True

        try:
            self.player.stop()

            # Release the file handle on the previous source
            # (if any) so it can be securely deleted.
            self.player.setSource(QUrl())

            old_temp_path = self._current_temp_path
            self._current_temp_path = None

            extension = media.display_media_type

            new_temp_path = self.temp_media_service.decrypt_to_temp(
                encrypted_path=media.encrypted_path,
                password=password,
                extension=extension
            )

            self.setWindowTitle(
                f"Playing: {media.display_filename}"
            )

            self.position_slider.setRange(0, 0)
            self.time_label.setText("00:00 / 00:00")

            self.player.setSource(
                QUrl.fromLocalFile(new_temp_path)
            )

            self._current_temp_path = new_temp_path

            self.player.play()

            # Clean up the previous temp file now that the player
            # has released it.
            if old_temp_path:
                self._delete_temp_with_retry(old_temp_path)

        finally:
            self._loading = False

    # -------------------------
    # SECURE DELETE WITH RETRY
    # -------------------------
    def _delete_temp_with_retry(
        self,
        path,
        attempts=10,
        delay_ms=300
    ):

        if attempts <= 0:
            return

        if self.temp_media_service.secure_delete(path):
            return

        QTimer.singleShot(
            delay_ms,
            lambda: self._delete_temp_with_retry(
                path,
                attempts - 1,
                delay_ms
            )
        )

    # -------------------------
    # PLAY / PAUSE
    # -------------------------
    def toggle_play(self):

        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def _on_playback_state_changed(self, state):

        if state == QMediaPlayer.PlayingState:
            self.play_button.setText("Pause")
        else:
            self.play_button.setText("Play")

    # -------------------------
    # SEEKING
    # -------------------------
    def _on_seek(self, value):
        self.player.setPosition(value)

    def _on_value_changed(self, value):

        if not self.position_slider.signalsBlocked():
            self.player.setPosition(value)

    # -------------------------
    # POSITION / DURATION
    # -------------------------
    def _on_position_changed(self, position):

        self.position_slider.blockSignals(True)
        self.position_slider.setValue(position)
        self.position_slider.blockSignals(False)

        self._update_time_label(
            position,
            self.player.duration()
        )

    def _on_duration_changed(self, duration):

        self.position_slider.setRange(0, duration)

        self._update_time_label(
            self.player.position(),
            duration
        )

    def _update_time_label(self, position_ms, duration_ms):

        def fmt(ms):
            seconds = ms // 1000
            minutes = seconds // 60
            seconds = seconds % 60
            return f"{minutes:02d}:{seconds:02d}"

        self.time_label.setText(
            f"{fmt(position_ms)} / {fmt(duration_ms)}"
        )

    # -------------------------
    # ERROR HANDLING
    # -------------------------
    def _on_error(self, error, error_string):

        self.time_label.setText(
            f"Error: {error_string}"
        )

    # -------------------------
    # SHORTCUTS
    # -------------------------
    def keyPressEvent(self, event):

        if event.key() == Qt.Key_Escape:
            self.close()

        elif event.key() == Qt.Key_Space:
            self.toggle_play()

    # -------------------------
    # CLOSE: STOP + SECURE DELETE + HIDE
    # -------------------------
    def closeEvent(self, event):

        self.player.pause()
        self.player.stop()

        # Release the file handle so it can be securely deleted.
        self.player.setSource(QUrl())

        event.accept()

        path = self._current_temp_path
        self._current_temp_path = None

        if path:
            self._delete_temp_with_retry(path)

        if self.on_close_callback:
            self.on_close_callback()