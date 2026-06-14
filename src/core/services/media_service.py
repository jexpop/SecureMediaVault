from src.database.repositories.media_repository import (
    MediaRepository
)

from src.core.crypto.string_crypto_service import (
    StringCryptoService
)

from src.core.config.vault_session import (
    VaultSession
)

from src.database.repositories.media_repository import (
    MediaRepository
)

from src.core.crypto.string_crypto_service import (
    StringCryptoService
)

from src.core.config.vault_session import (
    VaultSession
)


class MediaService:

    def __init__(self):

        self.repository = (
            MediaRepository()
        )

        self.string_crypto = (
            StringCryptoService()
        )

    def get_all_media(self):

        media_items = (
            self.repository.get_all()
        )

        return self.decorate_media_list(
            media_items
        )

    # -------------------------
    # DECRYPT DISPLAY FIELDS
    # -------------------------
    def decorate_media_list(self, media_items):
        """
        Attaches transient `display_filename` and
        `display_media_type` attributes to each Media
        object, decrypted with the current metadata key.
        These are NOT persisted to the database.
        """

        metadata_key = (
            VaultSession.get_metadata_key()
        )

        for media in media_items:
            self._attach_display_fields(
                media,
                metadata_key
            )

        return media_items

    def _attach_display_fields(self, media, metadata_key):

        try:
            media.display_filename = (
                self.string_crypto.decrypt(
                    media.original_filename,
                    metadata_key
                )
            )
        except Exception:
            media.display_filename = "[unreadable]"

        try:
            media.display_media_type = (
                self.string_crypto.decrypt(
                    media.media_type,
                    metadata_key
                )
            )
        except Exception:
            media.display_media_type = ""

        return media

class MediaService:

    def __init__(self):

        self.repository = (
            MediaRepository()
        )

        self.string_crypto = (
            StringCryptoService()
        )

    def get_all_media(self):

        media_items = (
            self.repository.get_all()
        )

        return self.decorate_media_list(
            media_items
        )

    # -------------------------
    # DECRYPT DISPLAY FIELDS
    # -------------------------
    def decorate_media_list(self, media_items):

        metadata_key = (
            VaultSession.get_metadata_key()
        )

        for media in media_items:
            self._attach_display_fields(
                media,
                metadata_key
            )

        return media_items

    def _attach_display_fields(self, media, metadata_key):

        try:
            media.display_filename = (
                self.string_crypto.decrypt(
                    media.original_filename,
                    metadata_key
                )
            )
        except Exception:
            media.display_filename = "[unreadable]"

        try:
            media.display_media_type = (
                self.string_crypto.decrypt(
                    media.media_type,
                    metadata_key
                )
            )
        except Exception:
            media.display_media_type = ""

        return media

    # -------------------------
    # CHECK FOR DUPLICATE FILENAME
    # -------------------------
    def filename_exists(self, filename: str) -> bool:
        """
        Returns True if a media item with the same original
        filename (case-insensitive) already exists in the vault.

        Filenames are stored encrypted, so each one is decrypted
        and compared in memory.
        """

        metadata_key = (
            VaultSession.get_metadata_key()
        )

        media_items = (
            self.repository.get_all()
        )

        target = filename.strip().lower()

        for media in media_items:

            try:
                existing_name = (
                    self.string_crypto.decrypt(
                        media.original_filename,
                        metadata_key
                    )
                )
            except Exception:
                continue

            if existing_name.strip().lower() == target:
                return True

        return False