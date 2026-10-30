import pytest
from datetime import date, datetime, timezone
from app.services.content_cleaner import ContentCleaningService
from app.services.news_relevance_service import NewsRelevanceService
from app.services.exam_intelligence import ExamIntelligenceService
from app.models.event import Event
from app.models.source import Source


# ── 1. Content Cleaning Tests ────────────────────────────────────────────────

def test_html_cleaning_english():
    """Verify HTML tags, image tags, anchors, and entities are stripped cleanly."""
    raw = '<p>The <b>Reserve Bank of India</b> issued new guidelines on <a href="https://example.com">banking</a>. <img src="chart.png" alt="chart"/> Details follow &amp; apply.</p>'
    cleaned = ContentCleaningService.clean_html(raw)
    assert "<" not in cleaned
    assert ">" not in cleaned
    assert "chart.png" not in cleaned
    assert "https://example.com" not in cleaned
    assert "Details follow & apply." in cleaned
    assert "Reserve Bank of India" in cleaned


def test_html_cleaning_tamil_and_unicode_preservation():
    """Verify Tamil Unicode is preserved while stripping embedded figure/video tags."""
    raw_tamil = 'தவெக ஆட்சி மீது நம்பிக்கை வந்துள்ளது! - நடிகர் ஜெய் | TVK. <figure>\n<div id="gumlet_video_player" style="padding: 100% 0 0 0;">\n\n</div></figure>'
    summary = ContentCleaningService.build_clean_summary("தவெக ஆட்சி மீது நம்பிக்கை வந்துள்ளது!", raw_tamil)
    assert "<" not in summary
    assert ">" not in summary
    assert "gumlet_video_player" not in summary
    # Tamil Unicode text is preserved without mojibake or loss
    assert "நடிகர் ஜெய்" in summary
    assert "TVK" in summary


def test_script_and_style_removal():
    """Verify <script> and <style> tags AND their inner contents are completely discarded."""
    raw = '<html><head><style>.ad{color:red;}</style><script>alert("malicious");</script></head><body><p>Public distribution system expanded in Tamil Nadu.</p></body></html>'
    cleaned = ContentCleaningService.clean_html(raw)
    assert "alert" not in cleaned
    assert "malicious" not in cleaned
    assert "color:red" not in cleaned
    assert "<script" not in cleaned
    assert cleaned == "Public distribution system expanded in Tamil Nadu."


def test_duplicate_headline_and_description_handling():
    """Verify that when description starts with identical title, the title repetition is removed."""
    title = "ISRO prepares for Gaganyaan test vehicle mission"
    content = "ISRO prepares for Gaganyaan test vehicle mission. Scientists at Sriharikota completed fueling checks for the crew escape system."
    summary = ContentCleaningService.build_clean_summary(title, content)
    # The summary should not repeat "ISRO prepares for Gaganyaan test vehicle mission"
    assert summary.count("ISRO prepares for Gaganyaan test vehicle mission") == 0
    assert "Scientists at Sriharikota completed fueling checks" in summary


# ── 2. Exam Relevance & Negative Exclusion Tests ─────────────────────────────

def test_entertainment_sk_black_pandi_excluded():
    """SK / Black Pandi entertainment stories must be excluded as non-exam content."""
    title = "நடிகர் சிவகார்த்திகேயன் மற்றும் பிளாக் பாண்டி புதிய நகைச்சுவை படம் அப்டேட்"
    content = "இயக்குநர் இயக்கத்தில் நடிகர் சிவகார்த்திகேயன், பிளாக் பாண்டி நடிக்கும் புதிய படத்தின் படப்பிடிப்பு தொடங்கியது."
    res = NewsRelevanceService.evaluate(title, content, domain="Entertainment")
    assert res.is_eligible is False
    assert res.relevance_score <= 15
    assert res.rejection_reason == "Entertainment / celebrity content"


def test_routine_crime_prison_escape_excluded():
    """Routine prison escape and local arrest reports must be excluded from exam feeds."""
    title = "மத்திய சிறையிலிருந்து தப்பியோடிய கைதி வடவள்ளியில் கைது: போலீசார் நடவடிக்கை"
    content = "கோவை மத்திய சிறையிலிருந்து தப்பியோடிய கைதியை போலீசார் தீவிர விசாரணை நடத்தி கைது செய்தனர்."
    res = NewsRelevanceService.evaluate(title, content, domain="Crime")
    assert res.is_eligible is False
    assert res.relevance_score <= 15
    assert res.rejection_reason == "Routine crime report"


def test_corporate_exit_package_excluded():
    """Microsoft voluntary employee exit packages must be excluded unless policy/economic substance."""
    title = "Microsoft offers voluntary exit packages to employees in global cost-cutting move"
    content = "Microsoft is offering voluntary separation and severance exit packages to employees as part of operational restructuring."
    res = NewsRelevanceService.evaluate(title, content, domain="Technology")
    assert res.is_eligible is False
    assert res.relevance_score <= 15
    assert "corporate announcement" in res.rejection_reason.lower()


def test_viral_animal_shark_rescue_excluded():
    """Ordinary shark-rescue viral stories must be excluded unless conservation/ecological angle."""
    title = "Beachgoers rescue stranded baby shark washed ashore in viral video"
    content = "Tourists on the beach dragged a small stranded shark back into deep water as spectators filmed the dramatic animal rescue scene."
    res = NewsRelevanceService.evaluate(title, content, domain="Environment")
    assert res.is_eligible is False
    assert res.relevance_score <= 15
    assert "viral" in res.rejection_reason.lower() or "insufficient" in res.rejection_reason.lower()


# ── 3. Positive Exam Relevance & Exception Tests ─────────────────────────────

def test_un_veto_developments_retained():
    """UN veto developments involving India must be retained under International Relations."""
    title = "India calls for United Nations Security Council reform and scrutiny of veto power"
    content = "At the United Nations General Assembly, India's permanent representative stressed the urgent need to reform the UNSC and restrict the use of veto power."
    res = NewsRelevanceService.evaluate(title, content, domain="International")
    assert res.is_eligible is True
    assert res.relevance_score >= 60
    assert "International Relations" in res.syllabus_topic
    assert "International Relations" in res.inclusion_reason


def test_major_scientific_discovery_retained():
    """ISRO space missions and scientific breakthroughs must be retained under Science & Tech."""
    title = "ISRO successfully conducts qualification test of cryogenic engine for Gaganyaan mission"
    content = "The Indian Space Research Organisation (ISRO) completed the high-thrust test of the CE20 cryogenic engine at Mahendragiri."
    res = NewsRelevanceService.evaluate(title, content, domain="Science")
    assert res.is_eligible is True
    assert res.relevance_score >= 70
    assert "Science" in res.syllabus_topic


def test_tn_government_scheme_retained():
    """Tamil Nadu government schemes (e.g. Breakfast Scheme, Pudhumai Penn) must be retained."""
    title = "Tamil Nadu Cabinet approves expansion of Chief Minister's Breakfast Scheme"
    content = "The state government approved Rs 500 crore allocation to extend the morning breakfast scheme across all government primary schools."
    res = NewsRelevanceService.evaluate(title, content, domain="Government")
    assert res.is_eligible is True
    assert res.relevance_score >= 70
    assert "Government Schemes" in res.syllabus_topic


def test_court_judgment_bns_retained():
    """Significant court judgments and Bharatiya Nyaya Sanhita reforms must be retained."""
    title = "Supreme Court Constitution Bench delivers landmark judgment on Bharatiya Nyaya Sanhita"
    content = "The Supreme Court Constitution Bench upheld key provisions of the Bharatiya Nyaya Sanhita (BNS) while issuing guidelines on fundamental rights."
    res = NewsRelevanceService.evaluate(title, content, domain="Government")
    assert res.is_eligible is True
    assert res.relevance_score >= 80
    assert "Indian Polity" in res.syllabus_topic


def test_confidence_does_not_equal_relevance():
    """A 100% classification confidence must not make an entertainment or corporate story exam-eligible."""
    title = "Instagram's latest feature lets you add tagged posts to your profile"
    content = "Instagram's newest feature lets users take posts from the Tagged tab and move it to their main profile grid."
    res = NewsRelevanceService.evaluate(title, content, domain="Technology")
    # Even if domain classifier is 100% confident it is 'Technology', it is NOT exam-eligible
    assert res.is_eligible is False
    assert res.relevance_score <= 15


# ── 4. Pipeline Integration & API Filtering Tests ───────────────────────────

def test_pipeline_filters_ineligible_articles(db_session, client):
    """Verify ineligible articles do not appear in default feeds or exam feeds."""
    src = Source(
        name="Test Ingestion Feed",
        url="https://example.com/feed",
        feed_url="https://example.com/feed/rss",
        source_type="rss",
        domain="Technology",
        reliability_score=1.0,
        enabled=True,
    )
    db_session.add(src)
    db_session.commit()

    ineligible_event = Event(
        title="நடிகர் பிளாக் பாண்டி புதிய நகைச்சுவை வீடியோ வைரல்",
        summary="நடிகர் பிளாக் பாண்டி நகைச்சுவை காட்சி சமூக வலைதளங்களில் வைரலாகி வருகிறது.",
        domain="Entertainment",
        source_id=src.id,
        source_url="https://example.com/pandi-video-1",
        event_date=date(2026, 10, 25),
        published_at=datetime.now(timezone.utc),
        dedup_hash="test_ineligible_pandi_hash",
        is_exam_eligible=False,
        rejection_reason="Entertainment / celebrity content",
        importance_score=10,
    )
    db_session.add(ineligible_event)

    eligible_event = Event(
        title="ISRO Chandrayaan mission receives international space award",
        summary="ISRO was conferred the prestigious aviation and space exploration award for Chandrayaan lunar landing.",
        domain="Science",
        source_id=src.id,
        source_url="https://example.com/isro-award-1",
        event_date=date(2026, 10, 25),
        published_at=datetime.now(timezone.utc),
        dedup_hash="test_eligible_isro_hash",
        is_exam_eligible=True,
        inclusion_reason="Relevant to Science & Technology",
        syllabus_topic="Science, Technology & Innovation",
        importance_score=85,
    )
    db_session.add(eligible_event)
    db_session.commit()

    # Default feed
    resp = client.get("/api/v1/events")
    assert resp.status_code == 200
    ids = [e["id"] for e in resp.json()["events"]]
    assert ineligible_event.id not in ids, "Ineligible entertainment must be excluded from default feed"
    assert eligible_event.id in ids, "Eligible science event must be included"

    # Search filter
    search_resp = client.get("/api/v1/events?domain=Entertainment")
    assert search_resp.status_code == 200
    search_ids = [e["id"] for e in search_resp.json()["events"]]
    assert ineligible_event.id not in search_ids


def test_mcq_generation_rejects_ineligible_articles(db_session):
    """Verify MCQ generation rejects ineligible events with clear error."""
    src = Source(name="Test News", url="https://example.com", feed_url="https://example.com/rss", domain="Entertainment")
    db_session.add(src)
    db_session.commit()

    event = Event(
        title="Celebrity wedding photos trend on social media",
        summary="Actors celebrated wedding reception in Chennai.",
        domain="Entertainment",
        source_id=src.id,
        source_url="https://example.com/wedding",
        event_date=date(2026, 10, 25),
        published_at=datetime.now(timezone.utc),
        dedup_hash="test_wedding_hash",
        is_exam_eligible=False,
        rejection_reason="Entertainment / celebrity content",
        importance_score=10,
    )
    db_session.add(event)
    db_session.commit()

    intel_service = ExamIntelligenceService(db_session)
    mcq_result = intel_service.generate_mcqs(event.id)
    assert mcq_result.get("error") is not None
    assert "excluded from exam relevance" in mcq_result["error"].lower()
    assert len(mcq_result.get("mcqs", [])) == 0


# ── 5. Production Relevance Repair & Unicode Validation Tests ────────────────

def test_tamil_nadu_government_scheme_news_eligible():
    """Tamil Nadu government welfare scheme news must be classified as exam-eligible."""
    title = "முதலமைச்சரின் காலை உணவுத் திட்டம் விரிவாக்கம் மற்றும் நிதி ஒதுக்கீடு"
    content = "தமிழ்நாடு அரசு தொடக்கப் பள்ளி மாணவர்களுக்கான காலை உணவுத் திட்டத்தை விரிவுபடுத்தி புதிய அரசாணை வெளியிட்டுள்ளது."
    res = NewsRelevanceService.evaluate(title, content, domain="Government")
    assert res.is_eligible is True
    assert "Government Schemes" in res.syllabus_topic
    assert res.relevance_score >= 60


def test_tamil_constitutional_or_sc_judgment_eligible():
    """Tamil constitutional or Supreme Court judgment news must be eligible under Indian Polity."""
    title = "உச்ச நீதிமன்றம் அரசியலமைப்பு அமர்வு வரலாற்று சிறப்புமிக்க தீர்ப்பு"
    content = "அடிப்படை உரிமை மற்றும் சட்டத்திருத்தம் தொடர்பாக 5 நீதிபதிகள் கொண்ட அரசியலமைப்பு சாசனம் அமர்வு முக்கிய தீர்ப்பை வழங்கியுள்ளது."
    res = NewsRelevanceService.evaluate(title, content, domain="Government")
    assert res.is_eligible is True
    assert "Indian Polity" in res.syllabus_topic
    assert res.relevance_score >= 80


def test_tamil_isro_science_tech_news_eligible():
    """ISRO space missions and technological breakthroughs in Tamil must be exam-eligible."""
    title = "இஸ்ரோ புதிய செயற்கைக்கோள் மற்றும் ஏவுகணை வரலாற்று சாதனை"
    content = "ஸ்ரீஹரிகோட்டாவிலிருந்து இஸ்ரோ விஞ்ஞானிகள் புதிய விண்கலத்தை வெற்றிகரமாக விண்ணில் செலுத்தினர்."
    res = NewsRelevanceService.evaluate(title, content, domain="Science")
    assert res.is_eligible is True
    assert "Science" in res.syllabus_topic
    assert res.relevance_score >= 60


def test_routine_theft_crime_news_ineligible():
    """Routine local theft and crime reports in Tamil must be classified as ineligible."""
    title = "செல்போன் கடை ஊழியரை ஏமாற்றி ரூ.50,000 திருட்டு: போலீசார் விசாரணை"
    content = "பூட்டிய வீட்டில் நகை கொள்ளை மற்றும் மர்ம நபர் திருட்டு தொடர்பாக போலீசார் வழக்குப்பதிவு செய்து விசாரணை நடத்தி வருகின்றனர்."
    res = NewsRelevanceService.evaluate(title, content, domain="Crime")
    assert res.is_eligible is False
    assert res.syllabus_topic == "Routine Crime"
    assert res.rejection_reason == "Routine crime report"


def test_cinema_celebrity_gossip_ineligible():
    """Cinema, movie updates, and celebrity gossip in Tamil must be classified as ineligible."""
    title = "நடிகர் சிவகார்த்திகேயன் புதிய திரைப்படம் பாடல் வெளியீடு மற்றும் படப்பிடிப்பு"
    content = "திரையரங்கம் மற்றும் ஓடிடி தளங்களில் வெளியாகும் புதிய திரைப்படத்தின் முன்னோட்டம் வெளியாகி ரசிகர்கள் மத்தியில் வரவேற்பு பெற்றுள்ளது."
    res = NewsRelevanceService.evaluate(title, content, domain="Entertainment")
    assert res.is_eligible is False
    assert res.syllabus_topic == "Entertainment"
    assert res.rejection_reason == "Entertainment / celebrity content"


def test_political_policy_announcement_eligible_not_rejected_as_feud():
    """Government policy announcements by political leaders must not be falsely rejected as political feuds."""
    title = "முதல்வர் மகளிர் இலவச பேருந்து பயண திட்டம் மற்றும் புதிய அரசாணை அறிவிப்பு"
    content = "அமைச்சரவை ஒப்புதல் பெற்று மகளிர் உரிமைத் தொகை மற்றும் நலத்திட்டங்களுக்கான நிதி ஒதுக்கீடு குறித்து முதல்வர் முக்கிய அறிக்கை வெளியிட்டுள்ளார்."
    res = NewsRelevanceService.evaluate(title, content, domain="Government")
    assert res.is_eligible is True
    assert res.syllabus_topic != "Political Feud"
    assert "Government Schemes" in res.syllabus_topic or "Indian Polity" in res.syllabus_topic


def test_partisan_political_argument_without_policy_substance_ineligible():
    """Partisan political dispute and verbal clashes without policy substance must be rejected as Political Feud."""
    title = "எதிர்க்கட்சி தலைவர் கடும் சாடல் மற்றும் காரசார விவாதம்"
    content = "அரசியல் சர்ச்சை மற்றும் தேர்தல் வதந்திகள் தொடர்பாக கட்சிகளிடையே சரமாரி குற்றச்சாட்டுகள் மற்றும் வார்த்தை மோதல் வெடித்தது."
    res = NewsRelevanceService.evaluate(title, content, domain="Politics")
    assert res.is_eligible is False
    assert res.syllabus_topic == "Political Feud"
    assert "Partisan political dispute" in res.rejection_reason


def test_content_cleaner_tamil_unicode_and_mulu_vivaram_preservation():
    """Content cleaner must preserve readable Tamil Unicode and not aggressively truncate on 'முழு விவரம் இதோ:'."""
    title = "தமிழ்நாடு அரசு புதிய கல்வி உதவித்தொகை திட்டம்"
    content = (
        "சென்னை: பள்ளி மாணவ, மாணவிகளுக்கான திட்டத்தின் முழு விவரம் இதோ: அரசு பள்ளியில் படிக்கும் "
        "மாணவர்களுக்கு ஆண்டுக்கு ரூ.12,000 உதவித்தொகை வழங்கப்படும். இத்திட்டம் கிராமப்புற மாணவர்களின் "
        "கல்வியை உறுதி செய்யும்.\n\n"
        "மேலும் செய்திகளுக்கு இங்கே கிளிக் செய்யவும்."
    )
    cleaned = ContentCleaningService.clean_article_text(title, content)
    # Essential article body and phrase must NOT be truncated
    assert "முழு விவரம் இதோ:" in cleaned
    assert "ஆண்டுக்கு ரூ.12,000 உதவித்தொகை வழங்கப்படும்" in cleaned
    assert "கல்வியை உறுதி செய்யும்" in cleaned
    # Trailing clickthrough boilerplate must be stripped
    assert "மேலும் செய்திகளுக்கு இங்கே கிளிக் செய்யவும்" not in cleaned
    # Summary builds cleanly
    summary = ContentCleaningService.build_clean_summary(title, content)
    assert "உதவித்தொகை" in summary
    assert "<" not in summary
    assert ">" not in summary
