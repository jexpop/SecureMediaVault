import os

from src.core.config.vault_config import VaultConfig
from src.core.config.vault_session import VaultSession

from src.core.crypto.encryption_service import EncryptionService
from src.core.crypto.string_crypto_service import StringCryptoService
from src.core.crypto.key_manager import KeyManager

from src.database.db_manager import SessionLocal
from src.database.models.media_model import Media
from src.database.models.tag_models import Tag


class PasswordChangeService:
    """
    Re-encrypts the whole vault (media files + DB metadata + tags)
    under a new master password.

    Strategy ("best effort atomic"):
      1. Verify the current password.
      2. Derive old/new metadata keys.
      3. Re-encrypt every media file to a "<path>.tmp" file
         (originals untouched so far).
      4. Decrypt+re-encrypt filenames/media_type/tag names in memory
         (DB session NOT committed yet).
      5. POINT OF NO RETURN:
         a. Rename all .tmp files over the originals.
         b. Commit DB changes.
         c. Update config.json (password hash + metadata salt).
         d. Update VaultSession.

    A failure before step 5 leaves the vault completely untouched
    (only orphan .tmp files to clean up). A failure during step 5
    can leave a partially-updated vault - hence the recommendation
    to back up `vault/` before running this.
    """

    def __init__(self):

        self.vault_config = VaultConfig()
        self.encryption_service = EncryptionService()
        self.string_crypto = StringCryptoService()
        self.key_manager = KeyManager()

    def change_password(
        self,
        old_password: str,
        new_password: str,
        progress_callback=None
    ):
        """
        progress_callback(current, total) is called after each
        media file is re-encrypted, so the UI can show progress.
        """

        # -------------------------
        # 1. VERIFY OLD PASSWORD
        # -------------------------
        if not self.vault_config.verify_password(old_password):
            raise Exception("Current password is incorrect")

        # -------------------------
        # 2. DERIVE KEYS
        # -------------------------
        old_metadata_salt = (
            self.vault_config.get_metadata_salt()
        )

        old_metadata_key = self.key_manager.derive_key(
            password=old_password,
            salt=old_metadata_salt
        )

        new_metadata_salt = os.urandom(
            VaultConfig.METADATA_SALT_SIZE
        )

        new_metadata_key = self.key_manager.derive_key(
            password=new_password,
            salt=new_metadata_salt
        )

        session = SessionLocal()

        # list of (tmp_path, final_path) pending rename
        pending_renames = []

        try:
            # -------------------------
            # 3 & 4. RE-ENCRYPT MEDIA + METADATA (not committed yet)
            # -------------------------
            media_items = session.query(Media).all()
            total = len(media_items)

            for i, media in enumerate(media_items):

                # --- re-encrypt the media file to a temp path ---
                tmp_path = media.encrypted_path + ".tmp"

                data = self.encryption_service.decrypt_bytes(
                    source_path=media.encrypted_path,
                    password=old_password
                )

                self.encryption_service.encrypt_bytes(
                    data=data,
                    target_path=tmp_path,
                    password=new_password
                )

                pending_renames.append(
                    (tmp_path, media.encrypted_path)
                )

                # --- re-encrypt filename / media_type ---
                filename_plain = self.string_crypto.decrypt(
                    media.original_filename,
                    old_metadata_key
                )

                type_plain = self.string_crypto.decrypt(
                    media.media_type,
                    old_metadata_key
                )

                media.original_filename = self.string_crypto.encrypt(
                    filename_plain,
                    new_metadata_key
                )

                media.media_type = self.string_crypto.encrypt(
                    type_plain,
                    new_metadata_key
                )

                if progress_callback:
                    progress_callback(i + 1, total)

            # --- re-encrypt tag names + recompute hashes ---
            tags = session.query(Tag).all()

            for tag in tags:

                name_plain = self.string_crypto.decrypt(
                    tag.name_encrypted,
                    old_metadata_key
                )

                tag.name_encrypted = self.string_crypto.encrypt(
                    name_plain,
                    new_metadata_key
                )

                tag.name_hash = self.string_crypto.hash_value(
                    name_plain,
                    new_metadata_key
                )

            # =====================================================
            # 5. POINT OF NO RETURN
            # =====================================================

            # 5a. Rename re-encrypted files over the originals
            for tmp_path, final_path in pending_renames:
                os.replace(tmp_path, final_path)

            # 5b. Commit DB changes
            session.commit()

            # 5c. Update config.json (password hash + metadata salt)
            self.vault_config.update_credentials(
                new_password=new_password,
                new_metadata_salt=new_metadata_salt
            )

            # 5d. Update in-memory session
            VaultSession.set_password(new_password)
            VaultSession.set_metadata_key(new_metadata_key)

            return True

        except Exception:

            # Rollback DB changes (safe if not committed yet)
            session.rollback()

            # Clean up any temp files created so far.
            # NOTE: if the exception happened during step 5a
            # (mid-rename), some originals may already be
            # encrypted with the NEW password while config.json
            # still has the OLD one. This is the "best effort"
            # risk window - hence the backup recommendation.
            for tmp_path, _ in pending_renames:
                if os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass

            raise

        finally:
            session.close()