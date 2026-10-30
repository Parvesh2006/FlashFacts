import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
import re
import httpx

from app.models.event import Event
from app.models.source import Source
from app.services.ai_assistant import FlashFactsAIAssistant
from app.services.ai_provider import OllamaProvider
from app.api.v1.ask import ask_ai_assistant, AskRequest


def test_parse_query_stop_words_and_country_handling(db_session):
    assistant = FlashFactsAIAssistant(db_session)

    # 1. India space mission: "India" should NOT be assigned as state location_name
    filters_space = assistant.parse_query("What is the latest important space mission in India?")
    assert filters_space.get("location_name") is None, "India should not be a state location filter"
    assert filters_space.get("country") == "India"
    assert "space" in filters_space.get("query_text", "").lower()
    assert filters_space.get("domain") == "Science" or "Science" in filters_space.get("domains", [])

    # 2. Fundamental duties: noise words removed, conceptual query captured
    filters_polity = assistant.parse_query("Explain the fundamental duties of the Indian Constitution.")
    assert "fundamental" in filters_polity.get("query_text", "").lower()
    assert "duties" in filters_polity.get("query_text", "").lower()
    assert "explain" not in filters_polity.get("query_text", "").lower()

    # 3. Tamil Nadu query: state identified, noise stripped
    filters_tn = assistant.parse_query("What are the major recent developments in Tamil Nadu?")
    assert filters_tn.get("location_name") == "Tamil Nadu"
    assert "major" not in filters_tn.get("query_text", "").lower()
    assert "recent" not in filters_tn.get("query_text", "").lower()


def test_ollama_thinking_model_prefill():
    provider = OllamaProvider(base_url="http://localhost:11434", model="qwen3:8b")
    assert provider.is_thinking_model() is True

    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of Tamil Nadu?"}
    ]

    with patch.object(httpx.Client, "post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {"content": "The capital of Tamil Nadu is Chennai."}
        }
        mock_post.return_value = mock_response

        reply = provider.generate_chat(messages)
        assert "Chennai" in reply

        # Verify assistant prefill was added for thinking models
        call_kwargs = mock_post.call_args[1]
        sent_messages = call_kwargs["json"]["messages"]
        assert sent_messages[-1]["role"] == "assistant"
        assert "<think>" in sent_messages[-1]["content"]


def test_ollama_timeout_error_propagation():
    provider = OllamaProvider(base_url="http://localhost:11434", model="qwen3:8b", timeout=1.0)
    messages = [{"role": "user", "content": "Hello"}]

    with patch.object(httpx.Client, "post", side_effect=httpx.TimeoutException("Read timed out")):
        with pytest.raises(TimeoutError) as exc_info:
            provider.generate_chat(messages)
        assert "timed out" in str(exc_info.value).lower()


# --- Requirement 1: Fundamental Duties — exactly 5 numbered points, relevant sources only ---
def test_fundamental_duties_exact_5_numbered_points(db_session):
    assistant = FlashFactsAIAssistant(db_session)
    mock_provider = MagicMock()
    # Simulate LLM returning 5 duties
    mock_provider.generate_chat.return_value = (
        "1. Abide by the Constitution and respect its ideals, the National Flag and the National Anthem.\n"
        "2. Cherish and follow the noble ideals which inspired our national struggle for freedom.\n"
        "3. Uphold and protect the sovereignty, unity, and integrity of India.\n"
        "4. Defend the country and render national service when called upon to do so.\n"
        "5. Promote harmony and the spirit of common brotherhood among all the people of India."
    )
    assistant.provider = mock_provider

    res = assistant.answer_question("Explain the fundamental duties of the Indian Constitution in 5 lines")

    assert res["filters"].get("format_constraint") == "points"
    assert res["filters"].get("point_count") == 5

    points = [line for line in res["answer"].splitlines() if re.match(r'^\d+\.', line.strip())]
    assert len(points) == 5, f"Expected exactly 5 numbered points, got {len(points)}:\n{res['answer']}"
    assert points[0].startswith("1. ")
    assert points[4].startswith("5. ")

    # Must NOT attach unrelated sources
    assert res["sources"] == []
    assert res["events_found"] == 0
    assert res["provider"] == "ai_syllabus"


# --- Requirement 2: Fundamental Duties — exactly 3 points ---
def test_fundamental_duties_exact_3_points(db_session):
    assistant = FlashFactsAIAssistant(db_session)
    mock_provider = MagicMock()
    mock_provider.generate_chat.return_value = (
        "1. Uphold and protect the sovereignty, unity, and integrity of India under Article 51A(c).\n"
        "2. Defend the nation and render national service when summoned under Article 51A(d).\n"
        "3. Safeguard public property and renounce violence under Article 51A(i)."
    )
    assistant.provider = mock_provider

    res = assistant.answer_question("Explain the fundamental duties in 3 points")

    assert res["filters"].get("format_constraint") == "points"
    assert res["filters"].get("point_count") == 3

    points = [line for line in res["answer"].splitlines() if re.match(r'^\d+\.', line.strip())]
    assert len(points) == 3, f"Expected exactly 3 numbered points, got {len(points)}:\n{res['answer']}"
    assert points[0].startswith("1. ")
    assert points[2].startswith("3. ")
    assert res["sources"] == []
    assert res["provider"] == "ai_syllabus"


# --- Requirement 3: A one-sentence answer request ---
def test_one_sentence_answer_request(db_session):
    assistant = FlashFactsAIAssistant(db_session)
    mock_provider = MagicMock()
    # LLM returned conversational intro plus sentence
    mock_provider.generate_chat.return_value = (
        "Here is the summary: Chandrayaan-3 is India's third lunar exploration mission developed by ISRO that successfully achieved a soft landing near the lunar south pole in August 2023."
    )
    assistant.provider = mock_provider

    res = assistant.answer_question("Explain what is Chandrayaan-3 in one sentence")

    assert res["filters"].get("format_constraint") == "sentence"
    assert res["filters"].get("sentence_count") == 1

    answer = res["answer"].strip()
    assert "\n" not in answer, "One-sentence answer should not contain newlines"
    # Ensure it ends with period and does not contain secondary sentences
    assert answer.endswith(".")
    assert "Here is the summary" not in answer
    assert "Chandrayaan-3 is India's third lunar exploration mission" in answer


# --- Requirement 4: A detailed explanation request without an artificial short limit ---
def test_detailed_explanation_request_without_short_limit(db_session):
    assistant = FlashFactsAIAssistant(db_session)
    detailed_text = (
        "The Fundamental Duties of Indian citizens are enshrined in Part IVA, Article 51A of the Constitution of India. "
        "Originally, the Constitution adopted in 1950 did not contain fundamental duties. They were incorporated upon the recommendation "
        "of the Swaran Singh Committee via the 42nd Constitutional Amendment Act of 1976 during the Emergency. "
        "Initially, 10 Fundamental Duties were added, drawing inspiration from the Constitution of the erstwhile USSR. "
        "Later, the 86th Constitutional Amendment Act of 2002 added an 11th duty under Article 51A(k), obligating parents or guardians "
        "to provide educational opportunities to their children between 6 and 14 years. "
        "Unlike Fundamental Rights, Fundamental Duties are non-justiciable in nature, meaning they cannot be directly enforced by courts "
        "through writs. However, they serve as crucial moral obligations and guiding principles for judicial interpretation of statutes."
    )
    mock_provider = MagicMock()
    mock_provider.generate_chat.return_value = detailed_text
    assistant.provider = mock_provider

    res = assistant.answer_question("Provide a detailed explanation of the fundamental duties of the Indian Constitution")

    assert res["filters"].get("format_constraint") == "detailed"
    assert res["filters"].get("is_detailed") is True
    # Verify the detailed answer is preserved fully and not truncated artificially
    assert len(res["answer"].split()) >= 100
    assert "Swaran Singh Committee" in res["answer"]
    assert "86th Constitutional Amendment" in res["answer"]
    assert res["sources"] == []
    assert res["provider"] == "ai_syllabus"


# --- Requirement 5: A Tamil-language question with a specified point count ---
def test_tamil_language_specified_point_count(db_session):
    assistant = FlashFactsAIAssistant(db_session)
    mock_provider = MagicMock()
    mock_provider.generate_chat.return_value = (
        "1. இந்திய அரசியலமைப்பு, தேசியக் கொடி மற்றும் தேசிய கீதத்தை மதித்து நடத்தல்.\n"
        "2. விடுதலைப் போராட்டத்திற்கு உத்வேகம் அளித்த உன்னத நோக்கங்களைப் போற்றிப் பின்பற்றுதல்.\n"
        "3. இந்தியாவின் இறையாண்மை, ஒற்றுமை மற்றும் ஒருமைப்பாட்டைப் பேணிப் பாதுகாத்தல்."
    )
    assistant.provider = mock_provider

    tamil_query = "இந்திய அரசியலமைப்பின் அடிப்படைக் கடமைகள் பற்றி 3 குறிப்புகளில் விளக்குக"
    res = assistant.answer_question(tamil_query)

    assert res["filters"].get("format_constraint") == "points"
    assert res["filters"].get("point_count") == 3

    points = [line for line in res["answer"].splitlines() if re.match(r'^\d+\.', line.strip())]
    assert len(points) == 3, f"Expected exactly 3 points in Tamil, got {len(points)}:\n{res['answer']}"
    assert "இறையாண்மை" in res["answer"]
    assert res["sources"] == []
    assert res["provider"] == "ai_syllabus"


# --- Requirement 6: A current-affairs question whose retrieved articles are relevant ---
def test_current_affairs_question_retrieved_articles_relevant(db_session):
    source = Source(
        name="The Hindu National",
        url="https://thehindu.com",
        feed_url="https://thehindu.com/rss",
        reliability_score=0.9
    )
    db_session.add(source)
    db_session.flush()

    event = Event(
        title="ISRO Launches Next Generation Space Mission for Lunar Survey",
        summary="ISRO has scheduled preparations for the next phase of lunar exploration from Sriharikota.",
        why_it_matters="Advancement in space science and lunar rover telemetry.",
        event_date=datetime(2026, 10, 20),
        published_at=datetime(2026, 10, 20, 10, 0, 0),
        source_id=source.id,
        source_url="https://thehindu.com/sci-tech/space/isro-lunar-survey",
        dedup_hash="isrospace999",
        domain="Science",
        importance_score=90,
    )
    db_session.add(event)
    db_session.commit()

    assistant = FlashFactsAIAssistant(db_session)
    mock_provider = MagicMock()
    mock_provider.generate_chat.return_value = (
        "ISRO has scheduled preparations for the next generation lunar survey space mission from Sriharikota. "
        "The mission advances India's scientific capabilities in lunar exploration."
    )
    assistant.provider = mock_provider

    res = assistant.answer_question("What is the latest space mission in India?")

    assert res["events_found"] == 1
    assert len(res["sources"]) == 1
    assert res["sources"][0]["name"] == "The Hindu National"
    assert res["sources"][0]["url"] == "https://thehindu.com/sci-tech/space/isro-lunar-survey"
    assert res["provider"] == "ai_grounded"
    assert "ISRO" in res["answer"]


# --- Requirement 7: A question for which no relevant source exists ---
def test_question_no_relevant_source_exists(db_session):
    assistant = FlashFactsAIAssistant(db_session)
    mock_provider = MagicMock()
    mock_provider.generate_chat.return_value = (
        "The Basic Structure Doctrine was established by the Supreme Court in the landmark Kesavananda Bharati case (1973)."
    )
    assistant.provider = mock_provider

    res = assistant.answer_question("Explain the basic structure doctrine of the Indian Constitution")

    assert res["events_found"] == 0
    assert res["sources"] == []
    assert res["provider"] == "ai_syllabus"
    assert "Kesavananda Bharati" in res["answer"]


# --- Requirement 8: Unrelated NASA or tech articles appear among candidates but are strictly excluded ---
def test_unrelated_nasa_or_tech_articles_excluded(db_session):
    nasa_source = Source(
        name="NASA News Releases",
        url="https://nasa.gov",
        feed_url="https://nasa.gov/rss",
        reliability_score=0.95
    )
    mit_source = Source(
        name="MIT Technology Review",
        url="https://technologyreview.com",
        feed_url="https://technologyreview.com/rss",
        reliability_score=0.95
    )
    db_session.add_all([nasa_source, mit_source])
    db_session.flush()

    e1 = Event(
        title="NASA Announces Bold Science Initiatives for Deep Space Exploration",
        summary="NASA reveals plans for long duration planetary probe telemetry.",
        why_it_matters="Space research and astrophysics developments.",
        event_date=datetime(2026, 10, 22),
        published_at=datetime(2026, 10, 22, 8, 0, 0),
        source_id=nasa_source.id,
        source_url="https://nasa.gov/deep-space",
        dedup_hash="nasa123",
        domain="Science",
        importance_score=85,
    )
    e2 = Event(
        title="MIT Technology Review Evaluates Quantum AI Breakthroughs",
        summary="Recent neural network quantum computing architectures demonstrate superior training efficiency.",
        why_it_matters="AI and machine learning benchmarks.",
        event_date=datetime(2026, 10, 24),
        published_at=datetime(2026, 10, 24, 8, 0, 0),
        source_id=mit_source.id,
        source_url="https://technologyreview.com/quantum-ai",
        dedup_hash="mit456",
        domain="Technology",
        importance_score=80,
    )
    db_session.add_all([e1, e2])
    db_session.commit()

    assistant = FlashFactsAIAssistant(db_session)
    mock_provider = MagicMock()
    mock_provider.generate_chat.return_value = (
        "1. Abide by the Constitution and respect the National Flag and National Anthem.\n"
        "2. Uphold and protect the sovereignty, unity, and integrity of India.\n"
        "3. Defend the nation and render national service when called upon.\n"
        "4. Value and preserve the rich heritage of our composite culture.\n"
        "5. Protect and improve the natural environment."
    )
    assistant.provider = mock_provider

    # Pass previous conversation history containing Science domain to test domain leakage prevention
    history = [
        {"role": "user", "content": "Recent Science developments", "filters": {"domain": "Science"}},
        {"role": "assistant", "content": "NASA announced new initiatives."}
    ]

    res = assistant.answer_question("Explain the fundamental duties of the Indian Constitution in 5 lines", history=history)

    # 1. Unrelated NASA/MIT articles MUST NOT appear in displayed sources
    assert len(res["sources"]) == 0, f"Unrelated sources leaked into response: {res['sources']}"
    for src in res["sources"]:
        assert "NASA" not in src["name"]
        assert "Technology Review" not in src["name"]

    # 2. Must not be labeled ai_grounded on unrelated documents
    assert res["provider"] == "ai_syllabus"
    assert res["events_found"] == 0

    # 3. Format constraint of 5 lines strictly enforced
    points = [line for line in res["answer"].splitlines() if re.match(r'^\d+\.', line.strip())]
    assert len(points) == 5, f"Expected exactly 5 points, got {len(points)}:\n{res['answer']}"


def test_ask_ai_handles_timeout_honestly(db_session):
    assistant = FlashFactsAIAssistant(db_session)
    mock_provider = MagicMock()
    mock_provider.generate_chat.side_effect = TimeoutError("Ollama 150s timeout")
    assistant.provider = mock_provider

    res = assistant.answer_question("Explain the fundamental duties of the Indian Constitution.")

    assert res["provider"] == "ollama_timeout"
    assert "⚠️" in res["answer"]
    assert "Timeout" in res["answer"]


def test_ask_ai_conversation_history_retention(db_session):
    assistant = FlashFactsAIAssistant(db_session)
    mock_provider = MagicMock()
    mock_provider.generate_chat.return_value = "It landed near the south pole of the Moon."
    assistant.provider = mock_provider

    history = [
        {"role": "user", "content": "What is Chandrayaan-3?"},
        {"role": "assistant", "content": "Chandrayaan-3 is India's third lunar exploration mission."},
    ]

    res = assistant.answer_question("Where did it land?", history=history)

    assert mock_provider.generate_chat.called
    call_args = mock_provider.generate_chat.call_args[0][0]
    user_contents = [m["content"] for m in call_args if m.get("role") == "user"]
    assert any("Chandrayaan-3" in c for c in user_contents)


def test_ask_api_endpoint(db_session):
    with patch("app.api.v1.ask.FlashFactsAIAssistant") as mock_cls:
        instance = mock_cls.return_value
        instance.answer_question.return_value = {
            "answer": "Test answer regarding Indian Polity.",
            "filters": {"domain": "Polity"},
            "sources": [{"name": "PIB", "url": "https://pib.gov.in", "date": "2026-10-25"}],
            "events_found": 1,
            "provider": "ai_grounded"
        }

        req = AskRequest(question="What is the Preamble?")
        res = ask_ai_assistant(req, db=db_session)
        assert res["answer"] == "Test answer regarding Indian Polity."
        assert len(res["sources"]) == 1
        assert res["events_found"] == 1
        assert res["provider"] == "ai_grounded"


# ==============================================================================
# AUDIT REGRESSION SUITE: 8 Deterministic Tests for Factual Accuracy & Grounding
# ==============================================================================

# Test 1: Older Indian space mission not called latest when newer verified exists
def test_regression_1_older_mission_not_called_latest_when_newer_verified_exists(db_session):
    src = Source(
        name="ISRO Media",
        url="https://isro.gov.in",
        feed_url="https://isro.gov.in/rss",
        reliability_score=0.98
    )
    db_session.add(src)
    db_session.flush()

    # Older mission (2023)
    e_old = Event(
        title="ISRO Chandrayaan-3 Lunar Mission Landing",
        summary="Chandrayaan-3 achieved soft landing on the lunar south pole.",
        why_it_matters="Lunar exploration history.",
        event_date=datetime(2023, 8, 23),
        published_at=datetime(2023, 8, 23, 18, 0, 0),
        source_id=src.id,
        source_url="https://isro.gov.in/chandrayaan3",
        dedup_hash="ch3_2023",
        domain="Science",
        importance_score=95,
    )
    # Newer mission (October 2026)
    e_new = Event(
        title="ISRO to launch indigenous navigation satellite NVS-03",
        summary="ISRO prepares launch of NVS-03 navigation satellite from Sriharikota.",
        why_it_matters="Strengthening NavIC indigenous navigation constellation.",
        event_date=datetime(2026, 10, 22),
        published_at=datetime(2026, 10, 22, 10, 0, 0),
        source_id=src.id,
        source_url="https://isro.gov.in/nvs-03",
        dedup_hash="nvs03_2026",
        domain="Government",
        importance_score=90,
    )
    db_session.add_all([e_old, e_new])
    db_session.commit()

    assistant = FlashFactsAIAssistant(db_session)
    mock_provider = MagicMock()
    mock_provider.generate_chat.return_value = (
        "ISRO is scheduled to launch its indigenous navigation satellite NVS-03 from Sriharikota."
    )
    assistant.provider = mock_provider

    res = assistant.answer_question("What is the latest space mission in India in one sentence?")

    assert res["provider"] == "ai_grounded"
    assert res["events_found"] >= 1
    # The newest event must be ranked first and cited
    assert res["sources"][0]["name"] == "ISRO Media"
    assert res["sources"][0]["url"] == "https://isro.gov.in/nvs-03"
    assert res["sources"][0]["date"] == "2026-10-22"
    assert "NVS-03" in res["answer"]
    assert "Chandrayaan-3" not in res["answer"]


# Test 2: Unrelated NASA article rejected and cannot support Indian mission claim
def test_regression_2_unrelated_nasa_article_cannot_support_indian_mission(db_session):
    nasa_src = Source(
        name="NASA Science News",
        url="https://nasa.gov",
        feed_url="https://nasa.gov/rss",
        reliability_score=0.95
    )
    db_session.add(nasa_src)
    db_session.flush()

    e_nasa = Event(
        title="NASA Artemis III Crew Selection and Space Mission Architecture",
        summary="NASA announces contractor updates for lunar orbital resupply space mission.",
        why_it_matters="US deep space human exploration program.",
        event_date=datetime(2026, 10, 24),
        published_at=datetime(2026, 10, 24, 15, 0, 0),
        source_id=nasa_src.id,
        source_url="https://nasa.gov/artemis3",
        dedup_hash="nasa_artemis_2026",
        domain="Science",
        importance_score=92,
    )
    db_session.add(e_nasa)
    db_session.commit()

    assistant = FlashFactsAIAssistant(db_session)
    mock_provider = MagicMock()
    assistant.provider = mock_provider

    res = assistant.answer_question("What is the latest space mission in India in one sentence?")

    # NASA article must be strictly excluded
    assert res["events_found"] == 0
    assert res["sources"] == []
    assert res["provider"] == "ai_unverified_limitation"
    assert "NASA" not in res["answer"]
    assert not mock_provider.generate_chat.called, "Should not hallucinate when evidence is insufficient"


# Test 3: Genuinely relevant source with verified event date supports answer
def test_regression_3_relevant_source_with_verified_event_date_supports_answer(db_session):
    src = Source(
        name="The Hindu Science",
        url="https://thehindu.com",
        feed_url="https://thehindu.com/sci/rss",
        reliability_score=0.9
    )
    db_session.add(src)
    db_session.flush()

    e = Event(
        title="Gaganyaan: ISRO completes key test ahead of first uncrewed mission",
        summary="ISRO successfully completed the crucial qualification test for Gaganyaan propulsion.",
        why_it_matters="Major milestone for India's human spaceflight program.",
        event_date=datetime(2026, 10, 18),
        published_at=datetime(2026, 10, 18, 12, 0, 0),
        source_id=src.id,
        source_url="https://thehindu.com/gaganyaan-test",
        dedup_hash="gaganyaan_2026",
        domain="Science",
        importance_score=94,
    )
    db_session.add(e)
    db_session.commit()

    assistant = FlashFactsAIAssistant(db_session)
    mock_provider = MagicMock()
    mock_provider.generate_chat.return_value = (
        "ISRO has completed a key qualification test for the Gaganyaan mission ahead of its first uncrewed flight."
    )
    assistant.provider = mock_provider

    res = assistant.answer_question("What is the latest space mission in India in one sentence?")

    assert res["provider"] == "ai_grounded"
    assert res["events_found"] == 1
    assert len(res["sources"]) == 1
    assert res["sources"][0]["name"] == "The Hindu Science"
    assert res["sources"][0]["date"] == "2026-10-18"
    assert "Gaganyaan" in res["answer"]


# Test 4: Article publication dates and event dates handled separately
def test_regression_4_event_date_vs_publication_date_separation(db_session):
    src = Source(
        name="Space Chronology",
        url="https://spacechronology.com",
        feed_url="https://spacechronology.com/rss",
        reliability_score=0.88
    )
    db_session.add(src)
    db_session.flush()

    # Article published late (Oct 26) about an OLD event (Aug 2023)
    e_retrospective = Event(
        title="ISRO Chandrayaan-3 Mission Retrospective Analysis",
        summary="Detailed review of Chandrayaan-3 lunar touchdown data.",
        why_it_matters="Historical scientific data analysis.",
        event_date=datetime(2023, 8, 23),
        published_at=datetime(2026, 10, 26, 8, 0, 0),
        source_id=src.id,
        source_url="https://spacechronology.com/ch3-review",
        dedup_hash="ch3_review_2026",
        domain="Science",
        importance_score=80,
    )
    # Article published earlier (Oct 19) about a RECENT event (Oct 18)
    e_recent = Event(
        title="ISRO conducts Gaganyaan Service Module test",
        summary="ISRO tested the propulsion system at Mahendragiri facility.",
        why_it_matters="Direct step towards human spaceflight readiness.",
        event_date=datetime(2026, 10, 18),
        published_at=datetime(2026, 10, 19, 9, 0, 0),
        source_id=src.id,
        source_url="https://spacechronology.com/gaganyaan-sm",
        dedup_hash="gaganyaan_sm_2026",
        domain="Science",
        importance_score=85,
    )
    db_session.add_all([e_retrospective, e_recent])
    db_session.commit()

    assistant = FlashFactsAIAssistant(db_session)
    mock_provider = MagicMock()
    mock_provider.generate_chat.return_value = (
        "ISRO conducted the Gaganyaan service module propulsion test at Mahendragiri."
    )
    assistant.provider = mock_provider

    res = assistant.answer_question("What is the latest space mission in India?")

    # e_recent has newer event_date (2026-10-18 vs 2023-08-23), must be ranked higher despite retrospective's later publication
    assert res["sources"][0]["date"] == "2026-10-18"
    assert res["sources"][0]["url"] == "https://spacechronology.com/gaganyaan-sm"


# Test 5: Missing or stale evidence produces an honest limitation
def test_regression_5_stale_or_missing_evidence_produces_honest_limitation(db_session):
    src = Source(
        name="Historical Archives",
        url="https://archives.org",
        feed_url="https://archives.org/rss",
        reliability_score=0.8
    )
    db_session.add(src)
    db_session.flush()

    # Only a 3-year-old mission exists in database
    e_stale = Event(
        title="ISRO launches PSLV-C56 mission",
        summary="ISRO successfully launched seven Singaporean satellites into orbit.",
        why_it_matters="Commercial launch milestone.",
        event_date=datetime(2023, 7, 30),
        published_at=datetime(2023, 7, 30, 10, 0, 0),
        source_id=src.id,
        source_url="https://archives.org/pslv-c56",
        dedup_hash="pslv_2023",
        domain="Science",
        importance_score=85,
    )
    db_session.add(e_stale)
    db_session.commit()

    assistant = FlashFactsAIAssistant(db_session)
    mock_provider = MagicMock()
    assistant.provider = mock_provider

    res = assistant.answer_question("What is the latest space mission in India?")

    # Must NOT call the 2023 mission latest, must return honest limitation
    assert res["provider"] == "ai_unverified_limitation"
    assert res["events_found"] == 0
    assert res["sources"] == []
    assert "contemporary records" in res["answer"].lower() or "not currently contain" in res["answer"].lower()


# Test 6: Stable syllabus questions continue returning exact requested point counts
def test_regression_6_stable_syllabus_exact_point_formatting(db_session):
    assistant = FlashFactsAIAssistant(db_session)
    mock_provider = MagicMock()
    mock_provider.generate_chat.return_value = (
        "1. Abide by Constitution and respect Flag and Anthem.\n"
        "2. Cherish noble ideals of freedom struggle.\n"
        "3. Protect sovereignty, unity and integrity of India.\n"
        "4. Defend country and render national service.\n"
        "5. Promote spirit of common brotherhood."
    )
    assistant.provider = mock_provider

    res_5 = assistant.answer_question("Explain the fundamental duties of the Indian Constitution in 5 lines")
    pts_5 = [l for l in res_5["answer"].splitlines() if re.match(r'^\d+\.', l.strip())]
    assert len(pts_5) == 5
    assert res_5["provider"] == "ai_syllabus"
    assert res_5["sources"] == []

    mock_provider.generate_chat.return_value = (
        "1. Respect National Flag.\n"
        "2. Protect sovereignty.\n"
        "3. Safeguard public property."
    )
    res_3 = assistant.answer_question("Explain the fundamental duties in 3 points")
    pts_3 = [l for l in res_3["answer"].splitlines() if re.match(r'^\d+\.', l.strip())]
    assert len(pts_3) == 3
    assert res_3["provider"] == "ai_syllabus"
    assert res_3["sources"] == []


# Test 7: One-sentence request remains one sentence even when evidence is insufficient
def test_regression_7_one_sentence_remains_one_sentence_on_insufficient_evidence(db_session):
    assistant = FlashFactsAIAssistant(db_session)
    mock_provider = MagicMock()
    assistant.provider = mock_provider

    res = assistant.answer_question("What is the latest space mission in India in one sentence?")

    assert res["provider"] == "ai_unverified_limitation"
    assert res["events_found"] == 0
    assert res["sources"] == []
    ans = res["answer"].strip()
    assert "\n" not in ans, "Answer must not contain multiple lines"
    assert ans.endswith("."), "One sentence must end with a period"
    # Ensure no multiple sentences
    sentences = [s for s in re.split(r'(?<=[.!?])\s+', ans) if s.strip()]
    assert len(sentences) == 1, f"Expected exactly 1 sentence, got: {sentences}"


# Test 8: Tamil freshness-sensitive questions follow the same evidence rules
def test_regression_8_tamil_freshness_question_follows_evidence_rules(db_session):
    assistant = FlashFactsAIAssistant(db_session)
    mock_provider = MagicMock()
    assistant.provider = mock_provider

    res = assistant.answer_question("இந்தியாவின் சமீபத்திய விண்வெளித் திட்டம் எது?")

    assert res["provider"] == "ai_unverified_limitation"
    assert res["events_found"] == 0
    assert res["sources"] == []
    # Contains Tamil explanation of limitation
    assert any("\u0b80" <= c <= "\u0bff" for c in res["answer"])
    assert "பதிவுகள்" in res["answer"] or "சமீபத்திய" in res["answer"]


# Test 9: Broad live-update pages are strictly excluded from source cards
def test_regression_9_broad_live_update_pages_excluded(db_session):
    src = Source(
        name="Indian Express National",
        url="https://indianexpress.com",
        feed_url="https://indianexpress.com/rss",
        reliability_score=0.9
    )
    db_session.add(src)
    db_session.flush()

    # Broad live-update rollup page mentioning ISRO in title
    e_live = Event(
        title="India News Live Updates, 25 October 2026: ISRO plans four functional launch pads by 2029, says Chairman Narayanan",
        summary="Live updates on politics, crime, weather, and launch pads by 2029.",
        why_it_matters="Rolling news coverage.",
        event_date=datetime(2026, 10, 25),
        published_at=datetime(2026, 10, 25, 10, 0, 0),
        source_id=src.id,
        source_url="https://indianexpress.com/article/india/india-news-live-updates-25-october-2026-delhi-mumbai-weather-breaking-latest/",
        dedup_hash="live_blog_123",
        domain="Government",
        importance_score=75,
    )
    # Dedicated satellite launch article
    e_dedicated = Event(
        title="ISRO to launch navigation satellite NVS-03 on Friday",
        summary="ISRO prepares launch of NVS-03 navigation satellite from Sriharikota.",
        why_it_matters="NavIC navigation satellite constellation update.",
        event_date=datetime(2026, 10, 28),
        published_at=datetime(2026, 10, 28, 19, 0, 0),
        source_id=src.id,
        source_url="https://indianexpress.com/article/india/isro-to-launch-navigation-satellite-nvs-03-on-friday-10941152/",
        dedup_hash="nvs03_dedicated_123",
        domain="Government",
        importance_score=92,
    )
    db_session.add_all([e_live, e_dedicated])
    db_session.commit()

    assistant = FlashFactsAIAssistant(db_session)
    mock_provider = MagicMock()
    mock_provider.generate_chat.return_value = (
        "ISRO is scheduled to launch navigation satellite NVS-03 from Sriharikota on Friday."
    )
    assistant.provider = mock_provider

    res = assistant.answer_question("What is the latest space mission in India in one sentence?")

    assert res["provider"] == "ai_grounded"
    # Live updates page must NOT be in sources
    urls = [s["url"] for s in res["sources"]]
    assert not any("live-updates" in (u or "") for u in urls), f"Live updates page leaked into sources: {urls}"
    assert "https://indianexpress.com/article/india/isro-to-launch-navigation-satellite-nvs-03-on-friday-10941152/" in urls


# Test 10: Topic switch from Science to Polity prevents filter leakage
def test_regression_10_topic_switch_science_to_polity_no_filter_leak(db_session):
    sci_src = Source(
        name="Science Journal",
        url="https://science.org",
        feed_url="https://science.org/rss",
        reliability_score=0.9
    )
    db_session.add(sci_src)
    db_session.flush()

    e_sci = Event(
        title="Deep Space Telescope Survey Observes Distant Exoplanet Atmosphere",
        summary="Astronomers discover methane signatures in distant exoplanet atmosphere.",
        why_it_matters="Astrophysics breakthrough.",
        event_date=datetime(2026, 10, 26),
        published_at=datetime(2026, 10, 26, 14, 0, 0),
        source_id=sci_src.id,
        source_url="https://science.org/exoplanet",
        dedup_hash="sci_exo_999",
        domain="Science",
        importance_score=85,
    )
    db_session.add(e_sci)
    db_session.commit()

    assistant = FlashFactsAIAssistant(db_session)
    mock_provider = MagicMock()
    mock_provider.generate_chat.return_value = (
        "1. Abide by Constitution and respect Flag and Anthem.\n"
        "2. Cherish noble ideals of freedom struggle.\n"
        "3. Protect sovereignty, unity and integrity of India.\n"
        "4. Defend country and render national service.\n"
        "5. Promote spirit of common brotherhood."
    )
    assistant.provider = mock_provider

    # Previous conversational turns focused heavily on Science and Space
    history = [
        {"role": "user", "content": "Tell me about space missions", "filters": {"domain": "Science", "query_text": "space"}},
        {"role": "assistant", "content": "NASA and ISRO have conducted space exploration."},
        {"role": "user", "content": "What about telescope observations?", "filters": {"domain": "Science"}},
        {"role": "assistant", "content": "Telescopes observe exoplanets."}
    ]

    # Now user switches completely to a Polity / Constitution question
    res = assistant.answer_question("Explain the fundamental duties of the Indian Constitution in 5 lines", history=history)

    # 1. Filters must NOT have domain="Science"
    assert res["filters"].get("domain") == "Polity" or "Polity" in res["filters"].get("domains", [])
    # 2. Science event must NOT be attached to Constitution answer
    assert res["sources"] == []
    assert res["events_found"] == 0
    assert res["provider"] == "ai_syllabus"
    # 3. 5 points maintained
    pts = [l for l in res["answer"].splitlines() if re.match(r'^\d+\.', l.strip())]
    assert len(pts) == 5
