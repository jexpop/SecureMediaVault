from src.database.db_manager import SessionLocal

from src.database.models.tag_models import Tag
from src.database.models.media_model import Media


class TagService:

    def __init__(self):

        self.session = SessionLocal()

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

        tag = (
            self.session.query(Tag)
            .filter_by(
                name=tag_name
            )
            .first()
        )

        if not tag:

            tag = Tag(
                name=tag_name
            )

            self.session.add(
                tag
            )

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
                name=tag_name
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
        """
        Check if a tag is associated with any media.
        
        Args:
            tag_name: The name of the tag to check
            
        Returns:
            True if the tag has associated media, False otherwise
        """
        tag_name = (
            tag_name
            .strip()
            .lower()
        )

        media_count = (
            self.session
            .query(Media)
            .join(Media.tags)
            .filter(
                Tag.name == tag_name
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

        tag = (
            self.session.query(Tag)
            .filter_by(
                name=tag_name
            )
            .first()
        )

        if not tag:
            return False

        self.session.delete(
            tag
        )

        self.session.commit()

        return True

    # -------------------------
    # GET ALL TAGS
    # -------------------------
    def get_all_tags(self):

        return (
            self.session
            .query(Tag)
            .order_by(
                Tag.name.asc()
            )
            .all()
        )

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

        return (
            self.session
            .query(Media)
            .join(Media.tags)
            .filter(
                Tag.name == tag_name
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

        return media.tags
