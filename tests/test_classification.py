from app.services.classification import KeywordDomainClassifier
from app.schemas.source import SourceCreate, SourceUpdate
from app.schemas.event import EventCreate
from pydantic import ValidationError
import pytest


def test_domain_classifier_ai():
    classifier = KeywordDomainClassifier()
    title = "OpenAI releases new GPT LLM neural network model"
    content = "The artificial intelligence breakthrough demonstrates deep learning capabilities."
    domain = classifier.classify(title, content)
    assert domain == "AI"


def test_domain_classifier_sports():
    classifier = KeywordDomainClassifier()
    title = "National team wins football championship match"
    content = "The tournament ended with a thrilling score in the stadium."
    domain = classifier.classify(title, content)
    assert domain == "Sports"


def test_domain_classifier_fallback():
    classifier = KeywordDomainClassifier()
    title = "Unrelated random text"
    content = "No specific domain keywords present here."
    domain = classifier.classify(title, content, default_domain="Economy")
    assert domain == "Economy"


def test_unknown_articles_fall_back_to_a_supported_domain():
    classifier = KeywordDomainClassifier()
    domain, confidence = classifier.classify_with_confidence(
        "Unrelated random text",
        "No specific domain keywords present here.",
        default_domain="General News",
    )

    assert domain == "Technology"
    assert confidence == 0.50
    assert "General" not in classifier.DOMAIN_KEYWORDS


def test_domains_api_does_not_return_general_news_or_general(client):
    response = client.get("/api/v1/domains")

    assert response.status_code == 200
    domains = {item["domain"] for item in response.json()}
    assert "General News" not in domains
    assert "General" not in domains


def test_source_and_event_schemas_reject_general_news():
    source_data = {
        "name": "Example Source",
        "url": "https://example.com",
        "feed_url": "https://example.com/feed.xml",
        "domain": "General News",
    }

    with pytest.raises(ValidationError):
        SourceCreate(**source_data)
    with pytest.raises(ValidationError):
        SourceUpdate(domain="General News")
    with pytest.raises(ValidationError):
        EventCreate(
            title="Example event",
            summary="Example summary",
            domain="General News",
            event_date="2026-10-21",
            published_at="2026-10-21T00:00:00Z",
            source_id=1,
            source_url="https://example.com/story",
            dedup_hash="a" * 64,
        )
