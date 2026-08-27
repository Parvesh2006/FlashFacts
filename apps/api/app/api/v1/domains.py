from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.event import DomainStatResponse
from app.repositories.event_repository import EventRepository
from app.services.classification import KeywordDomainClassifier

router = APIRouter(prefix="/domains", tags=["Domains"])


@router.get("", response_model=List[DomainStatResponse])
def list_domains(db: Session = Depends(get_db)):
    repo = EventRepository(db)
    counts_map = {d.domain: d.count for d in repo.get_domain_counts()}
    
    # Return all 13 core domain categories with their counts (0 if no events)
    all_domains = list(KeywordDomainClassifier.DOMAIN_KEYWORDS.keys())
    response = []
    for domain in all_domains:
        response.append(
            DomainStatResponse(
                domain=domain,
                count=counts_map.get(domain, 0)
            )
        )
    return response
