from src.database.db_manager import SessionLocal

from src.database.models.tag_models import Tag
from src.database.models.media_model import Media

from src.core.crypto.string_crypto_service import StringCryptoService
from src.core.config.vault_session import VaultSession


class TagService:

    def __init__(self):

        self.session = SessionLocal()
        self.string_crypto = StringCryptoService()

    # -------------------------
    # INTERNAL HELPERS
    # -------------------------
    def _metadata_key(self):
        return VaultSession.get_metadata_key()

    def _hash(self, tag_name: str) -> str:
        return self.string_crypto.hash_value(
            tag_name,
            self._metadata_key()
        )

    def _attach_display_name(self, tag: Tag):

        try:
            tag.display_name = (
                self.string_crypto.decrypt(
                    tag.name_encrypted,
                    self._metadata_key()
                )
            )
        except Exception:
            tag.display_name = "[unreadable]"

        return tag

    # -------------------------
    # ADD TAG TO MEDIA
    # -------------------------
    def add_tag_to_media(
        self,
        media,
        tag_name: str
    ):

        tag_name = (
            tag_name
            .strip()
            .lower()
        )

        if not tag_name:
            return

        name_hash = self._hash(tag_name)

        tag = (
            self.session.query(Tag)
            .filter_by(
                name_hash=name_hash
            )
            .first()
        )

        if not tag:

            tag = Tag(
                name_hash=name_hash,
                name_encrypted=(
                    self.string_crypto.encrypt(
                        tag_name,
                        self._metadata_key()
                    )
                )
            )

            self.session.add(tag)
            self.session.commit()

        managed_media = (
            self.session
            .query(Media)
            .filter_by(
                id=media.id
            )
            .first()
        )

        if not managed_media:
            return

        if tag not in managed_media.tags:

            managed_media.tags.append(
                tag
            )

            self.session.commit()

    # -------------------------
    # REMOVE TAG FROM MEDIA
    # -------------------------
    def remove_tag_from_media(
        self,
        media,
        tag_name: str
    ):

        tag_name = (
            tag_name
            .strip()
            .lower()
        )

        name_hash = self._hash(tag_name)

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

        tag = (
            self.session
            .query(Tag)
            .filter_by(
                name_hash=name_hash
            )
            .first()
        )

        if not tag:
            return False

        if tag in managed_media.tags:

            managed_media.tags.remove(
                tag
            )

            self.session.commit()

            return True

        return False

    # -------------------------
    # CHECK IF TAG HAS MEDIA
    # -------------------------
    def tag_has_media(
        self,
        tag_name: str
    ) -> bool:

        tag_name = (
            tag_name
            .strip()
            .lower()
        )

        name_hash = self._hash(tag_name)

        media_count = (
            self.session
            .query(Media)
            .join(Media.tags)
            .filter(
                Tag.name_hash == name_hash
            )
            .count()
        )

        return media_count > 0

    # -------------------------
    # DELETE TAG GLOBALLY
    # -------------------------
    def delete_tag(
        self,
        tag_name: str
    ):

        tag_name = (
            tag_name
            .strip()
            .lower()
        )

        name_hash = self._hash(tag_name)

        tag = (
            self.session.query(Tag)
            .filter_by(
                name_hash=name_hash
            )
            .first()
        )

        if not tag:
            return False

        self.session.delete(tag)
        self.session.commit()

        return True

    # -------------------------
    # GET ALL TAGS
    # -------------------------
    def get_all_tags(self):

        tags = (
            self.session
            .query(Tag)
            .all()
        )

        for tag in tags:
            self._attach_display_name(tag)

        tags.sort(
            key=lambda t: t.display_name
        )

        return tags

    # -------------------------
    # FILTER BY TAG
    # -------------------------
    def get_media_by_tag(
        self,
        tag_name: str
    ):

        tag_name = (
            tag_name
            .strip()
            .lower()
        )

        name_hash = self._hash(tag_name)

        return (
            self.session
            .query(Media)
            .join(Media.tags)
            .filter(
                Tag.name_hash == name_hash
            )
            .all()
        )

    # -------------------------
    # GET TAGS FOR MEDIA
    # -------------------------
    def get_tags_for_media(
        self,
        media_id: int
    ):

        media = (
            self.session
            .query(Media)
            .filter_by(
                id=media_id
            )
            .first()
        )

        if not media:
            return []

        tags = media.tags

        for tag in tags:
            self._attach_display_name(tag)

        return tags