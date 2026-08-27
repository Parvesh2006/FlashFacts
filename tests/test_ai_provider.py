import pytest
from app.services.ai_provider import FallbackAIProvider, OpenAIProvider, get_ai_provider


def test_fallback_ai_provider_enrichment():
    provider = FallbackAIProvider()
    title = "NASA Launches Artemis Rocket for Lunar Exploration"
    content = "NASA has successfully launched its new rocket from Kennedy Space Center in the United States to explore lunar orbit."
    domain = "Science"
    reliability = 0.99

    enrichment = provider.enrich_event(title, content, domain, reliability)

    assert "summary" in enrichment
    assert len(enrichment["summary"].split()) <= 100
    assert "why_it_matters" in enrichment
    assert isinstance(enrichment["importance_score"], int)
    assert 0 <= enrichment["importance_score"] <= 100
    assert enrichment["classification"] == domain
    assert 0.0 <= enrichment["classification_confidence"] <= 1.0
    
    entities = enrichment["entities"]
    assert isinstance(entities, list)
    entity_names = [e["name"] for e in entities]
    assert "NASA" in entity_names or "Artemis" in entity_names or "United States" in entity_names


def test_openai_provider_fallback_when_no_key():
    provider = OpenAIProvider(api_key="")
    enrichment = provider.enrich_event(
        title="Microsoft Announces New AI Research Center",
        content="Microsoft revealed plans for a new quantum AI laboratory in Europe.",
        domain="AI",
        reliability_score=0.95
    )

    assert enrichment["summary"] is not None
    assert enrichment["importance_score"] > 0
    assert len(enrichment["entities"]) > 0


def test_get_ai_provider_factory():
    provider = get_ai_provider()
    assert provider is not None
