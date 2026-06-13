from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Table,
    ForeignKey
)

from sqlalchemy.orm import relationship

from datetime import datetime

from src.database.db_manager import Base


# -------------------------
# TABLA INTERMEDIA
# -------------------------
media_tags = Table(
    "media_tags",
    Base.metadata,
    Column("media_id", Integer, ForeignKey("media.id")),
    Column("tag_id", Integer, ForeignKey("tags.id"))
)


# -------------------------
# MEDIA MODEL
# -------------------------
class Media(Base):

    __tablename__ = "media"

    id = Column(
        Integer,
        primary_key=True
    )

    uuid = Column(
        String,
        unique=True,
        nullable=False
    )

    encrypted_path = Column(
        String,
        nullable=False
    )

    original_filename = Column(
        String,
        nullable=False
    )

    media_type = Column(
        String,
        nullable=False
    )

    imported_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    # -------------------------
    # TAGS RELATIONSHIP
    # -------------------------
    tags = relationship(
        "Tag",
        secondary=media_tags,
        backref="media"
    )