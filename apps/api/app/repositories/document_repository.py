from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.document import Document
from app.schemas.document import DocumentCreate


class DocumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, document_id: int) -> Optional[Document]:
        return self.db.query(Document).filter(Document.id == document_id).first()

    def get_by_content_hash(self, content_hash: str) -> Optional[Document]:
        return self.db.query(Document).filter(Document.content_hash == content_hash).first()

    def get_by_url(self, url: str) -> Optional[Document]:
        return self.db.query(Document).filter(Document.url == url).first()

    def get_by_source_url(self, source_id: int, url: str) -> Optional[Document]:
        return (
            self.db.query(Document)
            .filter(Document.source_id == source_id, Document.url == url)
            .first()
        )

    def create(self, doc_in: DocumentCreate) -> Document:
        doc = Document(**doc_in.model_dump())
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def mark_processed(self, document_id: int) -> Optional[Document]:
        doc = self.get_by_id(document_id)
        if doc:
            doc.processed = True
            self.db.commit()
            self.db.refresh(doc)
        return doc

    def get_unprocessed(self, limit: int = 100) -> List[Document]:
        return self.db.query(Document).filter(Document.processed == False).limit(limit).all()
