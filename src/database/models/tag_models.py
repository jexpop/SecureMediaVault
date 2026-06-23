from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from src.database.db_manager import Base


class Tag(Base):

    __tablename__ = "tags"

    id = Column(
        Integer,
        primary_key=True
    )

    # Deterministic HMAC-SHA256 hash of the (stripped, lowercased)
    # tag name, derived from the vault metadata key.
    name_hash = Column(
        String,
        unique=True,
        nullable=False,
        index=True
    )

    # Encrypted tag name (AES-256-GCM, vault metadata key).
    name_encrypted = Column(
        String,
        nullable=False
    )

    # System tags ("images", "videos") are assigned automatically
    # on import and cannot be edited, removed from media, or
    # deleted by the user.
    is_system = Column(
        Boolean,
        nullable=False,
        default=False
    )

    # Optional category this tag belongs to (nullable).
    # Each tag belongs to at most one category.
    category_id = Column(
        Integer,
        ForeignKey("tag_categories.id"),
        nullable=True,
        default=None
    )

    category = relationship(
        "TagCategory",
        back_populates="tags"
    )

    def __repr__(self):
        return (
            f"<Tag hash={self.name_hash[:8]}... "
            f"system={self.is_system}>"
        )
