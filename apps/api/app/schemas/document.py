from datetime import datetime
from pydantic import BaseModel, ConfigDict


class DocumentBase(BaseModel):
    source_id: int
    title: str
    content: str
    url: str
    published_at: datetime | None = None


class DocumentCreate(DocumentBase):
    content_hash: str
    source_guid: str | None = None


class DocumentResponse(DocumentBase):
    id: int
    content_hash: str
    crawled_at: datetime
    processed: bool

    model_config = ConfigDict(from_attributes=True)
