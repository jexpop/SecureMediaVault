import io
from pathlib import Path

from PySide6.QtCore import QEventLoop, QTimer, QUrl, Qt
from PySide6.QtGui import QImage
from PySide6.QtMultimedia import QMediaPlayer, QVideoSink

from PIL import Image

from src.core.crypto.encryption_service import EncryptionService
from src.core.services.temp_media_service import TempMediaService


class VideoPreviewService:
    """
    Generates encrypted preview assets for a video:
      - "<path>_static.enc": a single static frame (PNG, encrypted)
      - "<path>_preview.enc": a short looping GIF (a few seconds,
        encrypted), made of several frames sampled from the start
        of the video.

    Before sampling, probes forward past any black intro/fade-in
    so the preview doesn't end up being a black frame (common with
    videos exported from editing software). See
    BLACK_LUMINANCE_THRESHOLD / _find_non_black_start.

    Frames are captured via QMediaPlayer + QVideoSink (no external
    binaries required). The GIF is assembled in memory with
    Pillow.

    If frame capture fails for any reason (corrupt video, unusual
    codec the bundled FFmpeg plugin can't decode, etc.), both
    preview files are simply not created, and the gallery falls
    back to the generic "play" placeholder.
    """

    PREVIEW_WIDTH = 240
    FRAME_COUNT = 8
    CAPTURE_WINDOW_MS = 3000  # first 3 seconds (once past black frames)
    GIF_FRAME_DURATION_MS = 125  # ~8 fps

    # -------------------------
    # BLACK-FRAME DETECTION
    # -------------------------
    # Mean luminance (0-255) below this is considered "too dark"
    # (pure black intros as well as heavily shadowed/dim frames).
    BLACK_LUMINANCE_THRESHOLD = 40

    # How far into the video we're willing to probe to find the
    # first non-black frame, before giving up and just using
    # whatever we found (even if it's black).
    BLACK_SKIP_MAX_PROBE_MS = 15000  # 15 seconds

    # Step size while probing forward past a black intro.
    BLACK_SKIP_PROBE_STEP_MS = 500

    def __init__(self):

        self.encryption_service = EncryptionService()
        self.temp_media_service = TempMediaService()

    # -------------------------
    # PUBLIC ENTRY POINT
    # -------------------------
    def generate_previews(
        self,
        encrypted_video_path: str,
        password: str,
        extension: str
    ):
        """
        Decrypts the video to a temp file, captures frames, builds
        and encrypts the static + GIF previews, and writes them
        next to encrypted_video_path as "<path>_static.enc" and
        "<path>_preview.enc".

        Returns True on success, False if preview generation
        failed (caller should treat this as "no preview
        available").
        """

        temp_path = None

        try:
            temp_path = self.temp_media_service.decrypt_to_temp(
                encrypted_path=encrypted_video_path,
                password=password,
                extension=extension
            )

            frames = self._capture_frames(temp_path)

            if not frames:
                return False

            static_bytes = self._frame_to_png_bytes(frames[0])

            gif_bytes = self._frames_to_gif_bytes(frames)

            static_path = encrypted_video_path + "_static.enc"
            preview_path = encrypted_video_path + "_preview.enc"

            self.encryption_service.encrypt_bytes(
                data=static_bytes,
                target_path=static_path,
                password=password
            )

            self.encryption_service.encrypt_bytes(
                data=gif_bytes,
                target_path=preview_path,
                password=password
            )

            return True

        except Exception:
            return False

        finally:
            if temp_path:
                self.temp_media_service.secure_delete(temp_path)

    # -------------------------
    # FRAME CAPTURE
    # -------------------------
    def _capture_frames(self, video_path: str):
        """
        Plays the video headlessly and captures FRAME_COUNT frames
        as QImage, sampled evenly across CAPTURE_WINDOW_MS,
        starting from the first non-black frame found (so a black
        intro/fade-in doesn't end up as the preview).

        Uses a local QEventLoop to turn QMediaPlayer's async
        signal-based API into a simple blocking sequence, since
        this runs during import (not on the UI's hot path).
        """

        player = QMediaPlayer()
        sink = QVideoSink()

        player.setVideoSink(sink)
        player.setSource(QUrl.fromLocalFile(video_path))

        frames = []

        # -------------------------
        # Wait until duration is known (or error/timeout)
        # -------------------------
        if not self._wait_for_duration(player):
            player.stop()
            player.setSource(QUrl())
            return frames

        duration = player.duration()

        start_position = self._find_non_black_start(
            player,
            sink,
            duration
        )

        window = min(
            self.CAPTURE_WINDOW_MS,
            max(duration - start_position - 1, 0)
        )

        if window <= 0:
            # Very short video, or nothing left after skipping the
            # black intro: just grab one frame at start_position.
            positions = [start_position]
        else:
            positions = [
                start_position + int(
                    window * i / (self.FRAME_COUNT - 1)
                )
                for i in range(self.FRAME_COUNT)
            ]

        for position in positions:

            image = self._capture_frame_at(
                player,
                sink,
                position
            )

            if image is not None and not image.isNull():
                frames.append(
                    self._scale_image(image)
                )

        player.stop()
        player.setSource(QUrl())

        return frames

    # -------------------------
    # SKIP BLACK INTRO / FADE-IN
    # -------------------------
    def _find_non_black_start(
        self,
        player,
        sink,
        duration_ms: int
    ) -> int:
        """
        Probes forward from position 0 in steps of
        BLACK_SKIP_PROBE_STEP_MS, looking for the first frame
        whose mean luminance is above BLACK_LUMINANCE_THRESHOLD.

        Gives up after BLACK_SKIP_MAX_PROBE_MS (or the video's own
        duration, whichever is smaller) and falls back to the
        brightest frame seen during the probe - so a video that's
        black throughout (or has an unusually long fade-in) still
        gets *some* preview instead of failing outright.
        """

        max_probe = min(
            self.BLACK_SKIP_MAX_PROBE_MS,
            max(duration_ms - 1, 0)
        )

        position = 0

        best_position = 0
        best_luminance = -1.0

        while position <= max_probe:

            image = self._capture_frame_at(
                player,
                sink,
                position
            )

            if image is not None and not image.isNull():

                luminance = self._mean_luminance(image)

                if luminance > best_luminance:
                    best_luminance = luminance
                    best_position = position

                if luminance >= self.BLACK_LUMINANCE_THRESHOLD:
                    return position

            position += self.BLACK_SKIP_PROBE_STEP_MS

        # Nothing bright enough found - use the brightest one we
        # did see (better than an all-black frame chosen blindly).
        return best_position

    def _mean_luminance(self, qimage) -> float:
        """
        Returns the average luminance (0-255) of a downsampled
        version of the frame. Downsampling first keeps this cheap
        even for 4K source video, since we only need a rough
        "is this black" estimate, not a precise measurement.
        """

        sample = qimage.scaled(
            32,
            32,
            Qt.IgnoreAspectRatio,
            Qt.FastTransformation
        )

        sample = sample.convertToFormat(
            QImage.Format_Grayscale8
        )

        width = sample.width()
        height = sample.height()

        if width <= 0 or height <= 0:
            return 0.0

        ptr = sample.constBits()

        buffer = bytes(ptr)[:width * height]

        return sum(buffer) / len(buffer)

    def _wait_for_duration(self, player, timeout_ms=5000) -> bool:

        loop = QEventLoop()

        result = {"ok": False}

        def on_duration_changed(duration):
            if duration > 0:
                result["ok"] = True
                loop.quit()

        def on_error(*_args):
            loop.quit()

        player.durationChanged.connect(on_duration_changed)
        player.errorOccurred.connect(on_error)

        timeout_timer = QTimer()
        timeout_timer.setSingleShot(True)
        timeout_timer.timeout.connect(loop.quit)
        timeout_timer.start(timeout_ms)

        # Trigger loading
        player.play()
        player.pause()

        loop.exec()

        timeout_timer.stop()

        try:
            player.durationChanged.disconnect(on_duration_changed)
            player.errorOccurred.disconnect(on_error)
        except Exception:
            pass

        return result["ok"]

    def _capture_frame_at(
        self,
        player,
        sink,
        position_ms,
        timeout_ms=3000
    ):

        loop = QEventLoop()

        captured = {"image": None}

        def on_frame_changed(frame):

            image = frame.toImage()

            if not image.isNull():
                captured["image"] = image
                loop.quit()

        sink.videoFrameChanged.connect(on_frame_changed)

        timeout_timer = QTimer()
        timeout_timer.setSingleShot(True)
        timeout_timer.timeout.connect(loop.quit)
        timeout_timer.start(timeout_ms)

        player.setPosition(position_ms)
        player.play()
        player.pause()

        loop.exec()

        timeout_timer.stop()

        try:
            sink.videoFrameChanged.disconnect(on_frame_changed)
        except Exception:
            pass

        return captured["image"]

    # -------------------------
    # IMAGE HELPERS
    # -------------------------
    def _scale_image(self, qimage):

        if qimage.width() <= 0:
            return qimage

        target_height = int(
            qimage.height() * (self.PREVIEW_WIDTH / qimage.width())
        )

        return qimage.scaled(
            self.PREVIEW_WIDTH,
            max(target_height, 1)
        )

    def _qimage_to_pil(self, qimage):

        qimage = qimage.convertToFormat(
            QImage.Format_RGBA8888
        )

        width = qimage.width()
        height = qimage.height()

        ptr = qimage.constBits()

        buffer = bytes(ptr)[:width * height * 4]

        return Image.frombuffer(
            "RGBA",
            (width, height),
            buffer,
            "raw",
            "RGBA",
            0,
            1
        ).convert("RGB")

    def _frame_to_png_bytes(self, qimage) -> bytes:

        pil_image = self._qimage_to_pil(qimage)

        output = io.BytesIO()

        pil_image.save(output, format="PNG")

        return output.getvalue()

    def _frames_to_gif_bytes(self, qimages) -> bytes:

        pil_frames = [
            self._qimage_to_pil(img)
            for img in qimages
        ]

        output = io.BytesIO()

        pil_frames[0].save(
            output,
            format="GIF",
            save_all=True,
            append_images=pil_frames[1:],
            duration=self.GIF_FRAME_DURATION_MS,
            loop=0
        )

        return output.getvalue()