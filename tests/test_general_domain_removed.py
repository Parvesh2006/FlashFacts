import pytest
from app.services.classification import KeywordDomainClassifier
from app.models.event import Event
from app.models.source import Source
from app.schemas.source import SourceCreate
from pydantic import ValidationError


def test_domain_keywords_excludes_general():
    classifier = KeywordDomainClassifier()
    assert "General" not in classifier.DOMAIN_KEYWORDS
    assert "General News" not in classifier.DOMAIN_KEYWORDS
    assert "Crime" in classifier.DOMAIN_KEYWORDS
    assert len(classifier.DOMAIN_KEYWORDS) == 14


def test_classifier_never_returns_general():
    classifier = KeywordDomainClassifier()
    assert classifier.classify("", "") != "General"
    assert classifier.classify("Random gibberish xyz123", "Nothing relevant") != "General"
    assert classifier.classify("முத்தரப்பு கிரிக்கெட் தொடர்", "அணி அறிவிப்பு") == "Sports"
    assert classifier.classify("தங்கம் விலை உயர்வு", "பொருளாதாரம்") == "Economy"


def test_domains_api_excludes_general(client):
    response = client.get("/api/v1/domains")
    assert response.status_code == 200
    data = response.json()
    domain_names = [d["domain"] for d in data]
    assert "General" not in domain_names
    assert "General News" not in domain_names
    assert len(domain_names) == 13


def test_database_has_no_general_records(db_session):
    event_count = db_session.query(Event).filter(Event.domain.in_(["General", "General News"])).count()
    assert event_count == 0

    source_count = db_session.query(Source).filter(Source.domain.in_(["General", "General News"])).count()
    assert source_count == 0


def test_source_create_rejects_general_domain():
    with pytest.raises(ValidationError):
        SourceCreate(
            name="Invalid Source",
            url="https://example.com",
            feed_url="https://example.com/rss",
            domain="General News",
        )

    with pytest.raises(ValidationError):
        SourceCreate(
            name="Invalid Source 2",
            url="https://example.com",
            feed_url="https://example.com/rss2",
            domain="General",
        )
