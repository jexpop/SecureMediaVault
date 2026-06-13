from sqlalchemy import Column, Integer, String
from src.database.db_manager import Base


class Tag(Base):

    __tablename__ = "tags"

    id = Column(
        Integer,
        primary_key=True
    )

    name = Column(
        String,
        unique=True,
        nullable=False,
        index=True
    )

    def __repr__(self):
        return f"<Tag {self.name}>"