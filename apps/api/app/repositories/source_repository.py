from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.source import Source
from app.schemas.source import SourceCreate, SourceUpdate


class SourceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, source_id: int) -> Optional[Source]:
        return self.db.query(Source).filter(Source.id == source_id).first()

    def get_by_feed_url(self, feed_url: str) -> Optional[Source]:
        return self.db.query(Source).filter(Source.feed_url == feed_url).first()

    def list_sources(self, enabled_only: bool = False) -> List[Source]:
        query = self.db.query(Source)
        if enabled_only:
            query = query.filter(Source.enabled == True)
        return query.all()

    def create(self, source_in: SourceCreate) -> Source:
        source = Source(**source_in.model_dump())
        self.db.add(source)
        self.db.commit()
        self.db.refresh(source)
        return source

    def update(self, source_id: int, source_in: SourceUpdate) -> Optional[Source]:
        source = self.get_by_id(source_id)
        if not source:
            return None
        update_data = source_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(source, field, value)
        self.db.commit()
        self.db.refresh(source)
        return source

    def delete(self, source_id: int) -> bool:
        source = self.get_by_id(source_id)
        if not source:
            return False
        self.db.delete(source)
        self.db.commit()
        return True
