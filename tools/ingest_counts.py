import os,sys
from pathlib import Path
os.environ['DATABASE_URL']=f"sqlite:///{Path.cwd()/ 'flashfacts_test.db'}"
os.environ['APP_ENV']='testing'

sys.path.insert(0,str(Path.cwd()/'apps'/'api'))
from app.core.database import SessionLocal
from app.models.entity import Entity
from app.models.event import Event, EventSource
from app.models.document import Document
from sqlalchemy import func
s=SessionLocal()
try:
    entity_count=s.query(func.count(Entity.id)).scalar()
    event_count=s.query(func.count(Event.id)).scalar()
    doc_count=s.query(func.count(Document.id)).scalar()
    evsrc_count=s.query(func.count(EventSource.id)).scalar()
    print('entities',entity_count,'events',event_count,'documents',doc_count,'event_sources',evsrc_count)
finally:
    s.close()
