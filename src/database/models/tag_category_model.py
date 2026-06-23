from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from src.database.db_manager import Base


class TagCategory(Base):

    __tablename__ = "tag_categories"

    id = Column(
        Integer,
        primary_key=True
    )

    # Deterministic HMAC-SHA256 hash of the (stripped, lowercased)
    # category name, derived from the vault metadata key.
    # Used for uniqueness checks without revealing the plaintext.
    name_hash = Column(
        String,
        unique=True,
        nullable=False,
        index=True
    )

    # Encrypted category name (AES-256-GCM, vault metadata key).
    name_encrypted = Column(
        String,
        nullable=False
    )

    # Tags belonging to this category (back-populated from Tag)
    tags = relationship(
        "Tag",
        back_populates="category",
        lazy="select"
    )

    def __repr__(self):
        return (
            f"<TagCategory hash={self.name_hash[:8]}...>"
        )
