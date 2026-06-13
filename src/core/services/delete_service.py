import os
from pathlib import Path
from src.database.db_manager import SessionLocal
from src.database.models.media_model import Media


class DeleteService:
    """
    Service for permanently deleting media files.
    Handles:
    - Deletion of encrypted file
    - Removal from database
    - Cleanup of tag associations
    """

    def __init__(self):
        self.session = SessionLocal()

    # -------------------------
    # DELETE MEDIA PERMANENTLY
    # -------------------------
    def delete_media(
        self,
        media
    ) -> bool:
        """
        Completely delete a media file:
        1. Delete encrypted file from storage
        2. Remove all tag associations
        3. Delete database record

        Args:
            media: Media object to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get managed media object
            managed_media = (
                self.session
                .query(Media)
                .filter_by(
                    id=media.id
                )
                .first()
            )

            if not managed_media:
                return False

            # 1. Delete encrypted file
            encrypted_path = (
                managed_media
                .encrypted_path
            )

            if encrypted_path and os.path.exists(
                encrypted_path
            ):
                try:
                    os.remove(
                        encrypted_path
                    )
                except Exception as e:
                    print(
                        f"Error deleting file: {e}"
                    )
                    return False

            # 2. Clear tag associations
            managed_media.tags.clear()

            # 3. Delete database record
            self.session.delete(
                managed_media
            )

            self.session.commit()

            return True

        except Exception as e:
            self.session.rollback()
            print(
                f"Error deleting media: {e}"
            )
            return False

    # -------------------------
    # CLEANUP EMPTY FOLDERS
    # -------------------------
    def cleanup_empty_folders(self):
        """
        Remove empty folders in vault/media
        after file deletion
        """
        base_path = Path("vault/media")

        if not base_path.exists():
            return

        try:
            # Remove empty directories
            for folder in sorted(
                base_path.rglob("*"),
                key=lambda p: len(
                    p.parts
                ),
                reverse=True
            ):
                if (
                    folder.is_dir() and
                    not list(
                        folder.iterdir()
                    )
                ):
                    folder.rmdir()

        except Exception as e:
            print(
                f"Error cleaning up folders: {e}"
            )
