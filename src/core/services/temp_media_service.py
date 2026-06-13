import os
import secrets
import uuid
from pathlib import Path

from src.core.crypto.encryption_service import EncryptionService


class TempMediaService:
    """
    Handles temporary decrypted copies of media files (used for
    video playback, since QMediaPlayer's FFmpeg backend is not
    reliable when streaming from an in-memory QBuffer).

    Files are written to vault/.tmp/ with random names, and
    securely "shredded" (overwritten with random bytes before
    being deleted) as soon as they are no longer needed.

    Note: on SSDs, wear-leveling means overwriting does not
    guarantee the original bytes are unrecoverable at the
    hardware level - this is a best-effort measure on top of
    normal deletion.
    """

    TEMP_DIR = Path("vault/.tmp")

    def __init__(self):

        self.encryption_service = EncryptionService()

        self.TEMP_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

    # -------------------------
    # DECRYPT TO TEMP FILE
    # -------------------------
    def decrypt_to_temp(
        self,
        encrypted_path: str,
        password: str,
        extension: str = ""
    ) -> str:

        data = self.encryption_service.decrypt_bytes(
            encrypted_path,
            password
        )

        suffix = f".{extension}" if extension else ""

        temp_path = self.TEMP_DIR / f"{uuid.uuid4().hex}{suffix}"

        with open(temp_path, "wb") as f:
            f.write(data)

        return str(temp_path)

    # -------------------------
    # SECURE DELETE (best effort)
    # -------------------------
    def secure_delete(self, path) -> bool:
        """
        Overwrites the file with random bytes, then deletes it.
        Returns True on success, False if the file could not be
        deleted (e.g. still locked by another process).
        """

        path = Path(path)

        if not path.exists():
            return True

        try:
            size = path.stat().st_size

            with open(path, "r+b") as f:

                remaining = size
                chunk_size = 1024 * 1024

                while remaining > 0:

                    chunk = min(chunk_size, remaining)

                    f.write(
                        secrets.token_bytes(chunk)
                    )

                    remaining -= chunk

                f.flush()
                os.fsync(f.fileno())

        except Exception:
            # If we can't even open/overwrite it, fall through
            # and try to unlink anyway.
            pass

        try:
            path.unlink()
            return True

        except Exception:
            return False

    # -------------------------
    # CLEANUP STALE TEMP FILES
    # -------------------------
    def cleanup_stale(self):
        """
        Removes any leftover temp files from a previous session
        (e.g. if the app crashed without cleaning up).
        """

        if not self.TEMP_DIR.exists():
            return

        for f in self.TEMP_DIR.iterdir():

            if f.is_file():
                self.secure_delete(f)