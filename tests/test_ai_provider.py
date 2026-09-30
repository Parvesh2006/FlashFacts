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


def test_fallback_infers_domain_and_event_type_from_neutral_hint():
    provider = FallbackAIProvider()
    enrichment = provider.enrich_event(
        title="Championship league final draws record attendance",
        content="The final boosted regional tourism and broadcast revenue.",
        domain="unknown",
    )

    assert enrichment["classification"] == "sports"
    assert enrichment["event_type"] == "event"
    assert enrichment["used_fallback"] is True


def test_fallback_domain_and_event_type_handle_announcement_semantics():
    provider = FallbackAIProvider()
    enrichment = provider.enrich_event(
        title="OpenAI launches new AI model for healthcare analytics",
        content="OpenAI announces the model to help clinicians summarize patient records reliably.",
        domain="unknown",
    )

    assert enrichment["classification"] == "technology"
    assert enrichment["event_type"] == "announcement"


def test_fallback_extracts_benchmark_entities_from_source_text():
    provider = FallbackAIProvider()
    title = "India expands climate monitoring satellite program"
    content = "Trade ministers sign a customs agreement while the championship final boosts tourism."
    enrichment = provider.enrich_event(title=title, content=content, domain="unknown")
    names = {entity["name"] for entity in enrichment["entities"]}

    assert "India" in names
    assert "climate monitoring" in names
    assert "trade ministers" in names
    assert "customs" in names
    assert "championship" in names
    assert "tourism" in names


def test_fallback_importance_score_is_bounded_and_deterministic():
    provider = FallbackAIProvider()
    first = provider.enrich_event(
        title="AI partnership accelerates healthcare research and policy rollout",
        content="OpenAI and public health agencies announce a broad digital health initiative.",
        domain="unknown",
    )
    second = provider.enrich_event(
        title="AI partnership accelerates healthcare research and policy rollout",
        content="OpenAI and public health agencies announce a broad digital health initiative.",
        domain="unknown",
    )

    assert first["importance_score"] == second["importance_score"]
    assert 0 <= first["importance_score"] <= 100
    assert isinstance(first["importance_score"], int)


def test_fallback_provider_does_not_fake_semantic_embeddings():
    provider = FallbackAIProvider()

    with pytest.raises(NotImplementedError):
        provider.generate_embedding("semantic similarity text")
