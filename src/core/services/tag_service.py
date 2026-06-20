from src.database.db_manager import SessionLocal

from src.database.models.tag_models import Tag
from src.database.models.media_model import Media

from src.core.crypto.string_crypto_service import StringCryptoService
from src.core.config.vault_session import VaultSession

from src.core.services.media_category import (
    SYSTEM_TAG_NAMES,
    IMAGES_TAG_NAME,
    VIDEOS_TAG_NAME
)


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

    def _get_or_create_tag(
        self,
        tag_name: str,
        is_system: bool = False
    ) -> Tag:

        tag_name = tag_name.strip().lower()
        name_hash = self._hash(tag_name)

        tag = (
            self.session.query(Tag)
            .filter_by(name_hash=name_hash)
            .first()
        )

        if not tag:

            tag = Tag(
                name_hash=name_hash,
                name_encrypted=self.string_crypto.encrypt(
                    tag_name,
                    self._metadata_key()
                ),
                is_system=is_system
            )

            self.session.add(tag)
            self.session.commit()

        elif is_system and not tag.is_system:

            # Promote to system tag if it somehow existed already
            tag.is_system = True
            self.session.commit()

        return tag

    # -------------------------
    # SYSTEM TAGS (Images / Videos)
    # -------------------------
    def ensure_system_tags(self):

        return {
            "image": self._get_or_create_tag(
                IMAGES_TAG_NAME, is_system=True
            ),
            "video": self._get_or_create_tag(
                VIDEOS_TAG_NAME, is_system=True
            ),
        }

    def set_media_type_tag(self, media, category: str):
        """
        Assigns the automatic "Images" or "Videos" tag to a media
        item, and makes sure the other one is NOT present
        (mutual exclusivity). Bypasses the normal user-facing
        restrictions - called internally by ImportService.
        """

        system_tags = self.ensure_system_tags()

        target_tag = system_tags[category]

        other_category = (
            "video" if category == "image" else "image"
        )

        other_tag = system_tags[other_category]

        managed_media = (
            self.session.query(Media)
            .filter_by(id=media.id)
            .first()
        )

        if not managed_media:
            return

        if other_tag in managed_media.tags:
            managed_media.tags.remove(other_tag)

        if target_tag not in managed_media.tags:
            managed_media.tags.append(target_tag)

        self.session.commit()

    # -------------------------
    # ADD TAG TO MEDIA
    # -------------------------
    def add_tag_to_media(self, media, tag_name: str) -> bool:

        tag_name = tag_name.strip().lower()

        if not tag_name:
            return False

        if tag_name in SYSTEM_TAG_NAMES:
            # "images"/"videos" are managed automatically
            return False

        tag = self._get_or_create_tag(tag_name)

        managed_media = (
            self.session.query(Media)
            .filter_by(id=media.id)
            .first()
        )

        if not managed_media:
            return False

        if tag not in managed_media.tags:
            managed_media.tags.append(tag)
            self.session.commit()

        return True

    # -------------------------
    # REMOVE TAG FROM MEDIA
    # -------------------------
    def remove_tag_from_media(self, media, tag_name: str) -> bool:

        tag_name = tag_name.strip().lower()
        name_hash = self._hash(tag_name)

        managed_media = (
            self.session.query(Media)
            .filter_by(id=media.id)
            .first()
        )

        if not managed_media:
            return False

        tag = (
            self.session.query(Tag)
            .filter_by(name_hash=name_hash)
            .first()
        )

        if not tag:
            return False

        if tag.is_system:
            return False

        if tag in managed_media.tags:
            managed_media.tags.remove(tag)
            self.session.commit()
            return True

        return False

    # -------------------------
    # CHECK IF TAG HAS MEDIA
    # -------------------------
    def tag_has_media(self, tag_name: str) -> bool:

        tag_name = tag_name.strip().lower()
        name_hash = self._hash(tag_name)

        media_count = (
            self.session.query(Media)
            .join(Media.tags)
            .filter(Tag.name_hash == name_hash)
            .count()
        )

        return media_count > 0

    # -------------------------
    # DELETE TAG GLOBALLY
    # -------------------------
    def delete_tag(self, tag_name: str) -> bool:

        tag_name = tag_name.strip().lower()
        name_hash = self._hash(tag_name)

        tag = (
            self.session.query(Tag)
            .filter_by(name_hash=name_hash)
            .first()
        )

        if not tag:
            return False

        if tag.is_system:
            return False

        self.session.delete(tag)
        self.session.commit()

        return True

    # -------------------------
    # GET ALL TAGS
    # -------------------------
    def get_all_tags(self):

        tags = (
            self.session.query(Tag)
            .all()
        )

        for tag in tags:
            self._attach_display_name(tag)

        # system tags first, then alphabetical
        tags.sort(
            key=lambda t: (not t.is_system, t.display_name)
        )

        return tags

    # -------------------------
    # FILTER BY TAG
    # -------------------------
    def get_media_by_tag(self, tag_name: str):

        tag_name = tag_name.strip().lower()
        name_hash = self._hash(tag_name)

        return (
            self.session.query(Media)
            .join(Media.tags)
            .filter(Tag.name_hash == name_hash)
            .all()
        )

    # -------------------------
    # GET TAGS FOR MEDIA
    # -------------------------
    def get_tags_for_media(self, media_id: int):

        media = (
            self.session.query(Media)
            .filter_by(id=media_id)
            .first()
        )

        if not media:
            return []

        tags = list(media.tags)

        for tag in tags:
            self._attach_display_name(tag)

        # system tags first, then alphabetical
        tags.sort(
            key=lambda t: (not t.is_system, t.display_name)
        )

        return tags
    
    # -------------------------
    # FILTER BY MULTIPLE TAGS (AND)
    # -------------------------
    def get_media_by_tags(self, tag_names: list):
        """
        Returns media items that have ALL of the given tags
        (AND semantics). Returns an empty list if tag_names is
        empty.
        """

        if not tag_names:
            return []

        name_hashes = [
            self._hash(name.strip().lower())
            for name in tag_names
        ]

        query = self.session.query(Media)

        for name_hash in name_hashes:

            query = query.filter(
                Media.tags.any(
                    Tag.name_hash == name_hash
                )
            )

        return query.all()