from datetime import datetime, timezone
from app.models.document import Document
from app.models.source import Source
from app.services.extraction import EventExtractorService


def test_event_extraction():
    extractor = EventExtractorService()
    source = Source(id=1, name="Test Source", domain="Medical")
    doc = Document(
        id=10,
        source_id=1,
        title="<b>New Cancer Vaccine Trial</b> Shows Promise",
        content="<p>Clinical trials for the breakthrough mRNA vaccine yielded positive health outcomes.</p>",
        url="https://example.com/med-news",
        published_at=datetime(2026, 8, 18, 12, 0, 0, tzinfo=timezone.utc),
        content_hash="test_hash"
    )

    candidate = extractor.extract_event_candidate(doc, source)

    assert candidate["title"] == "New Cancer Vaccine Trial Shows Promise"
    assert candidate["domain"] == "Medical"
    assert candidate["source_id"] == 1
    assert candidate["source_url"] == "https://example.com/med-news"
    assert str(candidate["event_date"]) == "2026-08-18"
