from datetime import datetime, timezone, date
from typing import Dict, Any, Optional
from app.models.document import Document
from app.models.source import Source
from app.services.classification import BaseClassifier, KeywordDomainClassifier
from app.services.content_cleaner import ContentCleaningService
from app.services.news_relevance_service import NewsRelevanceService


class EventExtractorService:
    def __init__(self, classifier: Optional[BaseClassifier] = None):
        self.classifier = classifier or KeywordDomainClassifier()

    def clean_text(self, text: str) -> str:
        """Clean HTML, scripts, styles, and unescape entities safely."""
        return ContentCleaningService.clean_html(text)

    def extract_event_candidate(self, document: Document, source: Source) -> Dict[str, Any]:
        clean_title = ContentCleaningService.clean_html(document.title or "")
        clean_content = ContentCleaningService.clean_article_text(clean_title, document.content or "")

        # Generate readable, plain-text Intelligence Summary
        summary = ContentCleaningService.build_clean_summary(clean_title, clean_content, max_words=75)

        # Domain classification
        domain = self.classifier.classify(clean_title, clean_content, default_domain=source.domain)

        # Exam relevance evaluation
        relevance_res = NewsRelevanceService.evaluate(clean_title, clean_content, domain=domain)

        # Date extraction
        pub_dt = document.published_at or datetime.now(timezone.utc)
        event_date = pub_dt.date()

        return {
            "title": clean_title,
            "summary": summary,
            "domain": domain,
            "event_date": event_date,
            "published_at": pub_dt,
            "source_id": source.id,
            "source_url": document.url,
            "confidence_score": 1.0,
            "is_exam_eligible": relevance_res.is_eligible,
            "importance_score": relevance_res.relevance_score if relevance_res.is_eligible else 15,
            "inclusion_reason": relevance_res.inclusion_reason if relevance_res.is_eligible else None,
            "rejection_reason": relevance_res.rejection_reason if not relevance_res.is_eligible else None,
            "syllabus_topic": relevance_res.syllabus_topic if relevance_res.is_eligible else None,
        }
