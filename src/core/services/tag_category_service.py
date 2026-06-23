import hmac
import hashlib

from src.core.config.vault_session import VaultSession
from src.core.crypto.string_crypto_service import StringCryptoService
from src.database.models.tag_category_model import TagCategory
from src.database.models.tag_models import Tag
from src.database.repositories.tag_category_repository import (
    TagCategoryRepository
)
from src.database.db_manager import SessionLocal


class TagCategoryService:
    """
    CRUD for tag categories with the same encryption model as
    TagService: names are stored AES-256-GCM encrypted, and a
    deterministic HMAC-SHA256 hash is stored alongside for
    uniqueness checks / lookups without decrypting.

    Categories are purely organisational — they don't affect
    how tags are stored on media items.
    """

    def __init__(self):

        self.repository = TagCategoryRepository()
        self.string_crypto = StringCryptoService()
        self.session = SessionLocal()

    # -------------------------
    # HMAC HASH (for lookups)
    # -------------------------
    def _hash(self, name: str) -> str:

        metadata_key = VaultSession.get_metadata_key()

        return hmac.new(
            metadata_key,
            name.strip().lower().encode(),
            hashlib.sha256
        ).hexdigest()

    # -------------------------
    # DECRYPT DISPLAY NAME
    # -------------------------
    def _attach_display_name(self, category: TagCategory):

        metadata_key = VaultSession.get_metadata_key()

        try:
            category.display_name = (
                self.string_crypto.decrypt(
                    category.name_encrypted,
                    metadata_key
                )
            )
        except Exception:
            category.display_name = "[unreadable]"

        return category

    # -------------------------
    # GET ALL
    # -------------------------
    def get_all_categories(self):

        categories = self.repository.get_all()

        for cat in categories:
            self._attach_display_name(cat)

        categories.sort(key=lambda c: c.display_name.lower())

        return categories

    # -------------------------
    # CREATE
    # -------------------------
    def create_category(self, name: str):
        """
        Creates a new category. Returns the saved TagCategory, or
        None if a category with the same name already exists.
        """

        name_clean = name.strip()

        if not name_clean:
            return None

        name_hash = self._hash(name_clean)

        if self.repository.get_by_hash(name_hash) is not None:
            return None

        metadata_key = VaultSession.get_metadata_key()

        name_encrypted = self.string_crypto.encrypt(
            name_clean,
            metadata_key
        )

        category = TagCategory(
            name_hash=name_hash,
            name_encrypted=name_encrypted
        )

        saved = self.repository.save(category)

        self._attach_display_name(saved)

        return saved

    # -------------------------
    # RENAME
    # -------------------------
    def rename_category(
        self,
        category: TagCategory,
        new_name: str
    ) -> bool:
        """
        Renames a category. Returns False if the new name already
        exists (collision) or is empty.
        """

        new_name_clean = new_name.strip()

        if not new_name_clean:
            return False

        new_hash = self._hash(new_name_clean)

        # Check collision (ignore self)
        existing = self.repository.get_by_hash(new_hash)

        if existing is not None and existing.id != category.id:
            return False

        metadata_key = VaultSession.get_metadata_key()

        category.name_hash = new_hash

        category.name_encrypted = self.string_crypto.encrypt(
            new_name_clean,
            metadata_key
        )

        self.repository.update()

        self._attach_display_name(category)

        return True

    # -------------------------
    # DELETE
    # -------------------------
    def delete_category(self, category: TagCategory):
        """
        Deletes a category. All tags that belonged to it become
        uncategorised (category_id set to None before deletion).
        """

        tags = (
            self.session
            .query(Tag)
            .filter_by(category_id=category.id)
            .all()
        )

        for tag in tags:
            tag.category_id = None

        self.session.commit()

        self.repository.delete(category)

    # -------------------------
    # ASSIGN TAG TO CATEGORY
    # -------------------------
    def assign_tag(
        self,
        tag: Tag,
        category: TagCategory
    ):
        """
        Assigns a tag to a category (replacing any previous
        category assignment).
        """

        tag.category_id = category.id

        self.session.commit()

    # -------------------------
    # REMOVE TAG FROM CATEGORY
    # -------------------------
    def unassign_tag(self, tag: Tag):
        """
        Removes a tag from its category (makes it uncategorised).
        """

        tag.category_id = None

        self.session.commit()

    # -------------------------
    # GET TAGS FOR CATEGORY
    # -------------------------
    def get_tags_for_category(self, category: TagCategory):

        from src.core.crypto.string_crypto_service import (
            StringCryptoService
        )

        metadata_key = VaultSession.get_metadata_key()

        tags = (
            self.session
            .query(Tag)
            .filter_by(category_id=category.id)
            .all()
        )

        for tag in tags:
            try:
                tag.display_name = self.string_crypto.decrypt(
                    tag.name_encrypted,
                    metadata_key
                )
            except Exception:
                tag.display_name = "[unreadable]"

        tags.sort(key=lambda t: t.display_name.lower())

        return tags

    # -------------------------
    # GET UNCATEGORISED TAGS
    # -------------------------
    def get_uncategorised_tags(self):

        metadata_key = VaultSession.get_metadata_key()

        tags = (
            self.session
            .query(Tag)
            .filter(Tag.category_id.is_(None))
            .filter_by(is_system=False)
            .all()
        )

        for tag in tags:
            try:
                tag.display_name = self.string_crypto.decrypt(
                    tag.name_encrypted,
                    metadata_key
                )
            except Exception:
                tag.display_name = "[unreadable]"

        tags.sort(key=lambda t: t.display_name.lower())

        return tags
