from datetime import datetime, timezone, date
import html
import re
from typing import Dict, Any
from app.models.document import Document
from app.models.source import Source
from app.services.classification import BaseClassifier, KeywordDomainClassifier


class EventExtractorService:
    def __init__(self, classifier: BaseClassifier = None):
        self.classifier = classifier or KeywordDomainClassifier()

    def clean_text(self, text: str) -> str:
        if not text:
            return ""
        # Unescape HTML entities
        text = html.unescape(text)
        # Strip HTML tags
        text = re.sub(r"<[^>]+>", "", text)
        # Clean up whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def extract_event_candidate(self, document: Document, source: Source) -> Dict[str, Any]:
        clean_title = self.clean_text(document.title)
        clean_content = self.clean_text(document.content)

        # Summary truncation if too long
        summary = clean_content
        if len(summary) > 500:
            summary = summary[:497] + "..."
        if not summary:
            summary = clean_title

        # Domain classification
        domain = self.classifier.classify(clean_title, clean_content, default_domain=source.domain)

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
            "confidence_score": 1.0
        }
