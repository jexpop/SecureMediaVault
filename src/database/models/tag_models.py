from sqlalchemy import Column, Integer, String
from src.database.db_manager import Base


class Tag(Base):

    __tablename__ = "tags"

    id = Column(
        Integer,
        primary_key=True
    )

    # Deterministic HMAC-SHA256 hash of the (stripped, lowercased)
    # tag name, derived from the vault metadata key.
    # Used for uniqueness and lookups, since the real name
    # is never stored in clear.
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

    def __repr__(self):
        return f"<Tag hash={self.name_hash[:8]}...>"