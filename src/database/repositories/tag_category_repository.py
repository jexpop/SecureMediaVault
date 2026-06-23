from src.database.db_manager import SessionLocal
from src.database.models.tag_category_model import TagCategory


class TagCategoryRepository:

    def __init__(self):

        self.session = SessionLocal()

    def get_all(self):

        return (
            self.session
            .query(TagCategory)
            .all()
        )

    def get_by_id(self, category_id: int):

        return (
            self.session
            .query(TagCategory)
            .filter_by(id=category_id)
            .first()
        )

    def get_by_hash(self, name_hash: str):

        return (
            self.session
            .query(TagCategory)
            .filter_by(name_hash=name_hash)
            .first()
        )

    def save(self, category: TagCategory):

        self.session.add(category)
        self.session.commit()
        self.session.refresh(category)

        return category

    def delete(self, category: TagCategory):

        self.session.delete(category)
        self.session.commit()

    def update(self):

        self.session.commit()
