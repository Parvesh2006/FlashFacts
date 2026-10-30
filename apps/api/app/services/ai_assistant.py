import re
import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.event import Event
from app.repositories.event_repository import EventRepository
from app.services.location_service import LocationService
from app.services.exam_intelligence import ExamIntelligenceService, EXAM_DEFINITIONS
from app.services.ai_provider import get_ai_provider, AIProvider, FallbackAIProvider
from app.core.config import settings

logger = logging.getLogger("app")

INDIAN_STATES_MAP = {
    "tamil nadu": "Tamil Nadu",
    "tamilnadu": "Tamil Nadu",
    "kerala": "Kerala",
    "karnataka": "Karnataka",
    "andhra pradesh": "Andhra Pradesh",
    "andhra": "Andhra Pradesh",
    "telangana": "Telangana",
    "maharashtra": "Maharashtra",
    "delhi": "Delhi",
    "uttar pradesh": "Uttar Pradesh",
    "west bengal": "West Bengal",
    "gujarat": "Gujarat",
    "rajasthan": "Rajasthan",
    "punjab": "Punjab",
    "odisha": "Odisha",
    "bihar": "Bihar",
    "madhya pradesh": "Madhya Pradesh",
    "haryana": "Haryana",
    "assam": "Assam",
    "jammu and kashmir": "Jammu and Kashmir",
    "jammu & kashmir": "Jammu and Kashmir",
}

EXAM_KEYWORDS = {
    "tnpsc": "tnpsc-group-4",
    "tnpsc group 4": "tnpsc-group-4",
    "tnpsc group 2": "tnpsc-group-2",
    "tnpsc group 1": "tnpsc-group-2",
    "upsc": "upsc-cse",
    "upsc cse": "upsc-cse",
    "civil services": "upsc-cse",
    "ssc": "ssc-cgl",
    "ssc cgl": "ssc-cgl",
    "ssc chsl": "ssc-chsl",
    "rrb": "rrb-ntpc",
    "rrb ntpc": "rrb-ntpc",
    "railway": "rrb-ntpc",
    "bank": "banking",
    "banking": "banking",
    "ibps": "banking",
    "sbi": "banking",
}

DOMAIN_KEYWORDS = {
    # Polity, Constitution & Governance
    "constitution": "Polity",
    "constitutional": "Polity",
    "fundamental duties": "Polity",
    "fundamental rights": "Polity",
    "fundamental duty": "Polity",
    "fundamental right": "Polity",
    "preamble": "Polity",
    "directive principles": "Polity",
    "dpsp": "Polity",
    "polity": "Polity",
    "parliament": "Polity",
    "judiciary": "Polity",
    "supreme court": "Polity",
    "high court": "Polity",
    "amendment": "Polity",
    "governance": "Government",
    "basic structure": "Polity",

    # Science & Technology
    "ai": "AI",
    "artificial intelligence": "AI",
    "technology": "Technology",
    "tech": "Technology",
    "science": "Science",
    "space": "Science",
    "isro": "Science",
    "nasa": "Science",

    # Economy & Banking
    "economy": "Economy",
    "economic": "Economy",
    "finance": "Economy",
    "rbi": "Economy",
    "banking": "Economy",

    # Government & Schemes
    "government": "Government",
    "scheme": "Government",
    "schemes": "Government",
    "policy": "Government",
    "politics": "Politics",

    # Social & General
    "education": "Education",
    "medical": "Medical",
    "health": "Medical",
    "sports": "Sports",
    "environment": "Environment",
}


class FlashFactsAIAssistant:
    """RAG-powered conversational assistant for competitive exam current affairs."""

    def __init__(self, db: Session, provider: Optional[AIProvider] = None):
        self.db = db
        self.event_repo = EventRepository(db)
        self.location_service = LocationService(db)
        self.exam_service = ExamIntelligenceService(db)
        self.provider = provider or get_ai_provider()

    def parse_query(self, question: str, history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Convert natural language question into structured filters with length/format constraint extraction."""
        from zoneinfo import ZoneInfo

        q_lower = question.lower()
        filters: Dict[str, Any] = {}

        # 1. Freshness / time-sensitivity detection
        freshness_patterns = [
            r'\blatest\b', r'\brecent\b', r'\brecently\b', r'\bnewest\b', r'\bcurrent\b',
            r'\bcurrently\b', r'\btoday\b', r'\byesterday\b', r'\bthis week\b', r'\bthis month\b',
            r'\bpast week\b', r'\bupcoming\b', r'\blast (?:mission|launch|event|development|scheme|update)\b',
            r'சமீபத்திய', r'தற்போதைய', r'இன்றைய', r'புதிய', r'கடைசி'
        ]
        if any(re.search(pat, q_lower) for pat in freshness_patterns):
            filters["freshness_sensitive"] = True

        # Tamil freshness terms expressed with Unicode escapes to avoid shell encoding corruption.
        tamil_freshness_terms = tuple(
            bytes(term, "ascii").decode("unicode_escape")
            for term in (
                r"\u0b9a\u0bae\u0bc0\u0baa\u0ba4\u0bcd\u0ba4\u0bbf\u0baf",
                r"\u0ba4\u0bb1\u0bcd\u0baa\u0bcb\u0ba4\u0bc8\u0baf",
                r"\u0b87\u0ba9\u0bcd\u0bb1\u0bc8\u0baf",
                r"\u0baa\u0bc1\u0ba4\u0bbf\u0baf",
                r"\u0b95\u0b9f\u0bc8\u0b9a\u0bbf",
                r"\u0b9a\u0bae\u0bc0\u0baa\u0ba4\u0bcd\u0ba4\u0bbf\u0bb2\u0bcd",
                r"\u0ba8\u0b9f\u0baa\u0bcd\u0baa\u0bc1"
            )
        )
        if any(term in q_lower for term in tamil_freshness_terms):
            filters["freshness_sensitive"] = True

        # 2. Indian Space query detection
        indian_space_patterns = [
            r'\bisro\b',
            r'\bindian space\b',
            r'\bspace\s+(?:mission|program|launch|project|craft|research)\s+(?:in|of|by)\s+india\b',
            r'\bindia(?:\'s)?\s+space\b',
            r'இந்திய\s+விண்வெளி',
            r'இஸ்ரோ'
        ]
        if any(re.search(pat, q_lower) for pat in indian_space_patterns) or ("space" in q_lower and "india" in q_lower):
            filters["is_indian_space"] = True
            filters["country"] = "India"

        # 3. MCQ Intent and Count Extraction
        if "mcq" in q_lower or "quiz" in q_lower or "multiple choice" in q_lower:
            filters["output_format"] = "mcq"
            filters["mcq_count"] = 5
            match = re.search(r'\b(\d+)\b', q_lower)
            if match:
                filters["mcq_count"] = int(match.group(1))

        # 4. Length & format constraint extraction (lines, points, one sentence, word limits)
        num_word_map = {
            "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
            "ஒரு": 1, "ஒரே": 1, "ஒன்று": 1, "இரண்டு": 2, "மூன்று": 3, "நான்கு": 4, "ஐந்து": 5,
            "ஆறு": 6, "ஏழு": 7, "எட்டு": 8, "ஒன்பது": 9, "பத்து": 10
        }

        # Check for one-sentence request
        if re.search(r'\b(?:in\s+)?(?:one|1|a\s+single)\s+sentence\b', q_lower) or re.search(r'\b(?:ஒரே|ஒரு)\s+வாக்கியத்தில்\b', q_lower):
            filters["format_constraint"] = "sentence"
            filters["sentence_count"] = 1
        else:
            # Check for points / lines (e.g. "in 5 lines", "in 3 points", "5 bullet points", "3 points", "5 வரிகளில்", "3 குறிப்புகளில்")
            pt_match = re.search(r'\b(?:in\s+|within\s+|give\s+|write\s+)?(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s*(?:points|lines|bullet\s*points|bullet\s*lines|key\s*points)\b', q_lower)
            if not pt_match:
                pt_match = re.search(r'(\d+|ஒன்று|இரண்டு|மூன்று|நான்கு|ஐந்து|ஆறு|ஏழு|எட்டு|ஒன்பது|பத்து)\s*(?:வரிகளில்|புள்ளிகளில்|குறிப்புகளில்|வரிகள்|குறிப்புகள்)', q_lower)

            if not pt_match:
                tamil_point_pattern = r"(\d+)\s*(?:வரிகளில்|புள்ளிகளில்|குறிப்புகளில்|வரிகள்|குறிப்புகள்)"
                pt_match = re.search(tamil_point_pattern, q_lower)

            if pt_match:
                raw_n = pt_match.group(1).lower()
                n = int(raw_n) if raw_n.isdigit() else num_word_map.get(raw_n, 5)
                filters["format_constraint"] = "points"
                filters["point_count"] = max(1, min(n, 20))
            else:
                # Check for word count ("in 100 words", "under 50 words", "50 words", "100 வார்த்தைகளில்")
                word_match = re.search(r'\b(?:in\s+|within\s+|under\s+|max\s+|around\s+|about\s+)?(\d+)\s*words\b', q_lower)
                if not word_match:
                    word_match = re.search(r'(\d+)\s*வார்த்தைகளில்', q_lower)
                if word_match:
                    filters["format_constraint"] = "words"
                    filters["word_limit"] = int(word_match.group(1))
                elif any(kw in q_lower for kw in ["detailed", "in detail", "comprehensive", "in-depth", "elaborate", "விரிவாக", "முழு விளக்கம்"]):
                    filters["format_constraint"] = "detailed"
                    filters["is_detailed"] = True

        today = datetime.now(ZoneInfo("Asia/Kolkata"))

        # 3. Contextual history inheritance (prevent history domain leakage on fresh topics)
        is_followup = any(kw in q_lower for kw in [
            "this", "that", "it", "these", "those", "above", "mentioned", "more about",
            "who was involved", "when did it", "why did this", "related to this", "இதனை", "இதை", "இதில்"
        ])
        has_own_topic = any(kw in q_lower for kw in DOMAIN_KEYWORDS.keys()) or any(s in q_lower for s in INDIAN_STATES_MAP.keys())

        if history and (is_followup or not has_own_topic):
            last_filters = None
            for item in reversed(history):
                if isinstance(item, dict) and "filters" in item:
                    last_filters = item["filters"]
                    break
            if last_filters:
                if last_filters.get("domain") and "domain" not in q_lower and not has_own_topic:
                    filters["domain"] = last_filters["domain"]
                if last_filters.get("date_range") and "today" not in q_lower and "yesterday" not in q_lower:
                    filters["date_label"] = last_filters.get("date_label", "inherited")
                if last_filters.get("exam_id"):
                    filters["exam_id"] = last_filters["exam_id"]
                    filters["exam_code"] = last_filters.get("exam_code")
                if last_filters.get("location_name") and not any(s in q_lower for s in INDIAN_STATES_MAP.keys()):
                    filters["location_name"] = last_filters["location_name"]

        # 4. Temporal constraints
        if "today" in q_lower:
            filters["start_date"] = today
            filters["end_date"] = today
            filters["date_label"] = "today"
        elif "yesterday" in q_lower:
            yesterday = today - timedelta(days=1)
            filters["start_date"] = yesterday
            filters["end_date"] = yesterday
            filters["date_label"] = "yesterday"
        elif any(w in q_lower for w in ["this week", "past 7 days", "last 7 days"]):
            filters["start_date"] = today - timedelta(days=7)
            filters["end_date"] = today
            filters["date_label"] = "this week"
        elif any(w in q_lower for w in ["last week", "past fortnight"]):
            filters["start_date"] = today - timedelta(days=14)
            filters["end_date"] = today - timedelta(days=7)
            filters["date_label"] = "last week"
        elif any(w in q_lower for w in ["this month", "past 30 days"]):
            filters["start_date"] = today - timedelta(days=30)
            filters["end_date"] = today
            filters["date_label"] = "this month"

        # 5. Geographic constraints (India is treated as national context, not local state filter)
        for kw, canonical_name in INDIAN_STATES_MAP.items():
            if re.search(rf"\b{re.escape(kw)}\b", q_lower):
                filters["location_name"] = canonical_name
                break

        if re.search(r'\bindia\b', q_lower):
            filters["country"] = "India"

        # 6. Exam target
        for kw, exam_id in EXAM_KEYWORDS.items():
            if re.search(rf"\b{re.escape(kw)}\b", q_lower):
                filters["exam_id"] = exam_id
                defn = EXAM_DEFINITIONS.get(exam_id)
                if defn:
                    filters["exam_code"] = defn["code"]
                break

        # 7. Domain detection
        if filters.get("is_indian_space"):
            # Space missions in India are covered under Science, Technology, and Government/National
            filters["domains"] = ["Science", "Technology", "Government"]
            filters["domain"] = None
        elif re.search(r"\bscience\s*(?:&|and)\s*technology\b", q_lower):
            filters["domains"] = ["Science", "Technology"]
            filters["domain"] = "Science & Technology"
        else:
            for kw, domain_name in DOMAIN_KEYWORDS.items():
                if re.search(rf"\b{re.escape(kw)}\b", q_lower):
                    filters["domains"] = [domain_name]
                    filters["domain"] = domain_name
                    break

        if any(w in q_lower for w in ["important", "high priority", "major", "top"]):
            filters["importance"] = "high"

        # 8. Clean query text extraction: strip noise, conversational, and formatting words
        ignore_words = {
            "what", "which", "where", "when", "why", "who", "how", "happened", "today",
            "current", "affairs", "the", "in", "for", "give", "me", "show", "tell",
            "explain", "is", "are", "was", "were", "of", "and", "some", "mcq", "mcqs",
            "about", "on", "quiz", "multiple", "choice", "questions", "generate",
            "create", "make", "from", "please", "can", "you", "a", "an", "any",
            "latest", "recent", "important", "major", "top", "development",
            "developments", "topics", "relevant", "details", "brief", "discuss",
            "india", "indian", "lines", "line", "points", "point", "bullet", "bullets",
            "sentence", "sentences", "words", "word", "detailed", "detail", "short",
            "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
            "பற்றி", "கூறு", "விளக்குக", "செய்திகள்", "வரிகளில்", "புள்ளிகளில்", "குறிப்புகளில்",
            "வாக்கியத்தில்", "வார்த்தைகளில்", "விரிவாக"
        }

        clean_words = []
        words = q_lower.replace("?", " ").replace(".", " ").replace(",", " ").replace(":", " ").split()
        for word in words:
            if word not in ignore_words and not word.isdigit() and len(word) > 2:
                clean_words.append(word)

        if filters.get("is_indian_space") and "isro" not in clean_words:
            clean_words.insert(0, "isro")

        filters["query_text"] = " ".join(clean_words[:6])
        return filters

    def _filter_relevant_events(
        self,
        events: List[Event],
        query_text: str,
        question: str,
        target_domain: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Event]:
        """Filter candidate events to ensure every displayed source genuinely supports the query."""
        if not events:
            return []

        q_lower = question.lower()
        is_indian_space = (filters and filters.get("is_indian_space")) or bool(
            re.search(r'\b(?:isro|space.*india|indian.*space|india.*space)\b', q_lower)
        )
        is_indian_query = (filters and filters.get("country") == "India") or is_indian_space or bool(
            re.search(r'\b(?:india|indian|bharat)\b', q_lower)
        )

        # Extract core content keywords from query_text and question
        stop_words = {
            "a", "an", "the", "is", "are", "was", "were", "in", "on", "at", "of", "for", "to",
            "from", "and", "or", "with", "about", "what", "which", "who", "how", "me", "tell",
            "show", "find", "give", "latest", "news", "current", "affairs", "today", "event",
            "events", "lines", "points", "sentence", "words", "explain", "important", "major",
            "recent"
        }
        if not is_indian_query:
            stop_words.update({"india", "indian"})

        tokens = [
            t.lower() for t in re.findall(r'[^\W_]+', f"{query_text} {question}", flags=re.UNICODE)
            if len(t) > 2 and t.lower() not in stop_words and not t.isdigit()
        ]
        unique_tokens = list(dict.fromkeys(tokens))

        relevant: List[Tuple[Event, int]] = []
        for e in events:
            ev_domain = (e.domain or "").lower()
            ev_title = (e.title or "").lower()
            ev_summary = (e.summary or "").lower()
            ev_matters = (e.why_it_matters or "").lower()
            ev_text = f"{ev_title} {ev_summary} {ev_matters}"

            # Determine source name
            src_val = getattr(e, "source", None)
            src_name = (getattr(src_val, "name", None) or str(src_val or "")).lower()

            # Exclude broad live-update rollup tickers / aggregators unless live updates specifically asked
            is_live_update_page = any(k in (e.source_url or "").lower() for k in ["live-updates", "live-news-updates", "/liveblog/", "live-blog"]) or any(k in (e.title or "").lower() for k in ["live updates:", "live updates,", "live news updates", "live updates -"])
            if is_live_update_page and not any(k in q_lower for k in ["live update", "live updates", "live news"]):
                continue

            # 1. Indian space entity check: must have genuine Indian space context
            if is_indian_space:
                indian_space_refs = [
                    "isro", "sriharikota", "gaganyaan", "chandrayaan", "aditya", "mangalyaan",
                    "nvs", "pslv", "gslv", "sslv", "in-space", "trishna", "nisar", "bharat",
                    "indian space", "space commission", "antrix", "newspace india", "nsil",
                    "விண்வெளி", "இஸ்ரோ"
                ]
                has_indian_ref = any(ref in ev_text for ref in indian_space_refs) or (
                    ("india" in ev_text or "indian" in ev_text) and any(w in ev_text for w in ["space", "satellite", "rocket", "orbit", "launch", "payload"])
                )
                if not has_indian_ref:
                    continue

                # When user asks about a space mission/satellite/launch, must have actual spaceflight/mission focus
                # Exclude broad administrative commentary or ground infrastructure debates
                if any(k in q_lower for k in ["mission", "satellite", "launch", "craft"]):
                    has_mission_focus = any(k in ev_text for k in [
                        "satellite", "launch", "mission", "lander", "rover", "spacecraft",
                        "propulsion", "uncrewed", "crew", "payload", "orbit", "navic",
                        "nvs", "gaganyaan", "aditya", "chandrayaan", "trishna", "nisar",
                        "pslv", "gslv", "sslv"
                    ])
                    if not has_mission_focus:
                        continue

                # Strictly reject foreign space missions with zero Indian involvement
                foreign_agencies = ["nasa", "spacex", "esa", "roscosmos", "jaxa", "boeing"]
                if any(f in ev_text or f in src_name for f in foreign_agencies) and not any(k in ev_text for k in ("isro", "india", "indian", "sriharikota", "bharat")):
                    continue

            # 2. General Indian context check: if asking about India, reject foreign sources with no Indian context
            elif is_indian_query:
                foreign_indicators = ("nasa", "white house", "mit technology", "esa", "spacex", "pentagon", "boeing")
                if any(f in src_name for f in foreign_indicators) or any(f in ev_title for f in foreign_indicators):
                    has_indian_inst = any(k in ev_text for k in ("isro", "sriharikota", "bharat", "tnpsc", "upsc", "parliament", "rbi", "drdo")) or (
                        "government of india" in ev_text or "indian government" in ev_text or "india and" in ev_text or "india's" in ev_text
                    )
                    if not has_indian_inst:
                        continue
                else:
                    has_indian_ref = any(k in ev_text for k in ("india", "indian", "bharat", "delhi", "tnpsc", "upsc", "parliament", "rbi", "isro"))
                    if not has_indian_ref and any(f in src_name for f in ("international", "foreign", "reuters")):
                        continue

            # 3. If question is explicitly Polity / Constitution, strictly exclude unrelated Science/Tech/AI articles
            if target_domain and target_domain.lower() in ("polity", "constitution", "law"):
                if ev_domain in ("science", "ai", "technology") and not any(k in ev_text for k in ("constitution", "polity", "amendment", "court", "act", "law", "duty", "duties")):
                    continue

            # Count token matches and distinct tokens in event content
            score = 0
            matched_tokens = set()
            for t in unique_tokens:
                if t in ev_title:
                    score += 3
                    matched_tokens.add(t)
                elif t in ev_summary:
                    score += 2
                    matched_tokens.add(t)
                elif t in ev_matters:
                    score += 1
                    matched_tokens.add(t)
                elif t in ev_domain:
                    score += 1
                    matched_tokens.add(t)

            # Only accept events that have genuine textual overlap with the query terms
            is_relevant = False
            if len(unique_tokens) >= 3:
                if len(matched_tokens) >= 2 and score >= 4:
                    is_relevant = True
            elif score >= 2:
                is_relevant = True

            if is_indian_space and "isro" in ev_text:
                is_relevant = True

            if is_relevant:
                relevant.append((e, score))

        if not relevant:
            return []

        # Freshness ranking: distinguish event occurrence date from publication date
        if filters and filters.get("freshness_sensitive"):
            def event_freshness_key(item: Tuple[Event, int]):
                ev = item[0]
                e_date = ev.event_date
                if not e_date and ev.published_at:
                    e_date = ev.published_at.date()
                if not e_date:
                    e_date = datetime.min.date()
                p_date = ev.published_at or datetime.min

                # Prefer official ISRO release sources when available
                src_val = getattr(ev, "source", None)
                src_name = (getattr(src_val, "name", None) or str(src_val or "")).lower()
                is_official = 1 if "isro" in src_name or "isro.gov.in" in (ev.source_url or "").lower() else 0

                return (e_date, is_official, p_date, item[1])

            relevant.sort(key=event_freshness_key, reverse=True)
        else:
            relevant.sort(key=lambda x: x[1], reverse=True)

        return [e for e, _ in relevant[:4]]

    def _select_grounding_sources(self, events: List[Event], filters: Dict[str, Any]) -> List[Event]:
        """Ensure displayed source cards strictly correspond to evidence supporting the primary claim."""
        if not events:
            return []
        if not filters.get("freshness_sensitive"):
            return events[:4]

        # For freshness-sensitive queries, the primary claim is anchored on events[0]
        primary_ev = events[0]
        primary_text = f"{primary_ev.title or ''} {primary_ev.summary or ''}".lower()

        # Stop words to extract key named entities / mission topic words
        stop = {
            "isro", "india", "indian", "the", "a", "an", "on", "in", "to", "for", "of", "and",
            "but", "has", "say", "says", "with", "from", "report", "news", "friday", "today"
        }
        primary_tokens = [
            t for t in re.findall(r'[^\W_]+', primary_text)
            if len(t) > 2 and t not in stop and not t.isdigit()
        ]

        grounding_events = [primary_ev]
        for e in events[1:]:
            ev_text = f"{e.title or ''} {e.summary or ''}".lower()
            matches = sum(1 for t in primary_tokens if t in ev_text)
            # Must share at least one distinctive entity token (e.g. nvs, gaganyaan, aditya, trishna) or same occurrence date
            has_distinct_match = any(t in ev_text for t in primary_tokens if t not in ("space", "satellite", "launch", "mission", "oct"))
            if has_distinct_match or matches >= 2 or (primary_ev.event_date and e.event_date == primary_ev.event_date):
                grounding_events.append(e)

        return grounding_events[:4]

    def answer_question(
        self, question: str, history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Process user question via RAG pipeline and return grounded exam-focused answer."""
        t_start = time.time()

        filters = self.parse_query(question, history=history)
        raw_events = self._retrieve_candidate_events(filters)

        # If strict date filters found nothing, broaden date range
        if not raw_events and (filters.get("start_date") or filters.get("end_date")):
            broad_filters = dict(filters)
            broad_filters["start_date"] = None
            broad_filters["end_date"] = None
            raw_events = self._retrieve_candidate_events(broad_filters)

        # Filter strictly for genuine source relevance
        events = self._filter_relevant_events(
            raw_events,
            filters.get("query_text", ""),
            question,
            filters.get("domain"),
            filters=filters
        )

        # Freshness staleness check: if query is freshness-sensitive and candidate events are stale (> 365 days old)
        if events and filters.get("freshness_sensitive"):
            newest_ev = events[0]
            newest_date = newest_ev.event_date or (newest_ev.published_at.date() if newest_ev.published_at else None)
            ref_date = filters.get("end_date")
            if ref_date:
                ref_date = ref_date.date() if isinstance(ref_date, datetime) else ref_date
            else:
                ref_date = datetime.now().date()
            if newest_date and (ref_date - newest_date).days > 365:
                logger.info("Rejecting stale events for freshness query: newest_date=%s vs ref_date=%s", newest_date, ref_date)
                events = []

        # Select strictly corroborating sources for displayed cards
        grounded_events = self._select_grounding_sources(events, filters)

        provider_name = getattr(self.provider, "model", getattr(settings, "AI_PROVIDER", "ai"))
        logger.info(
            "FlashFacts Ask AI: provider=%s, events_found=%d (raw=%d), location=%s, domain=%s, query=%s",
            provider_name, len(grounded_events), len(raw_events), filters.get("location_name"), filters.get("domain"), filters.get("query_text")
        )

        sources = []
        if grounded_events:
            for e in grounded_events:
                src_name = getattr(e, "source", "") or "FlashFacts Network"
                if hasattr(src_name, "name"):
                    src_name = src_name.name

                # Prioritize direct source_url to open the cited document
                article_url = getattr(e, "source_url", None)
                if not article_url and hasattr(e, "source") and e.source:
                    article_url = getattr(e.source, "url", None)

                sources.append({
                    "name": src_name,
                    "url": article_url,
                    "date": e.event_date.isoformat() if getattr(e, "event_date", None) else None,
                })

        answer_text = None
        provider_used = "ai_grounded"

        # Case 1: Genuinely matching events found in database
        if grounded_events:
            if not isinstance(self.provider, FallbackAIProvider):
                try:
                    answer_text = self._synthesize_ai_answer(question, grounded_events, filters, history=history)
                    if answer_text:
                        provider_used = "ai_grounded"
                except TimeoutError as exc:
                    logger.warning("Ollama timeout during answer synthesis: %s", exc)
                    fallback_answer = self._synthesize_deterministic_answer(grounded_events, filters)
                    fallback_answer = self._enforce_format_constraints(fallback_answer, filters)
                    return {
                        "filters": filters,
                        "sources": sources,
                        "events_found": len(grounded_events),
                        "answer": (
                            "⚠️ **Model Timeout:** The local AI model took longer than expected to synthesize the answer. "
                            "Here is the verified current-affairs summary from FlashFacts records:\n\n"
                            + fallback_answer
                        ),
                        "provider": "ollama_timeout",
                    }
                except Exception as exc:
                    logger.error("LLM synthesis error: %s", exc)
                    fallback_answer = self._synthesize_deterministic_answer(grounded_events, filters)
                    fallback_answer = self._enforce_format_constraints(fallback_answer, filters)
                    return {
                        "filters": filters,
                        "sources": sources,
                        "events_found": len(grounded_events),
                        "answer": (
                            "⚠️ **AI Service Error:** Unable to reach the local AI engine. "
                            "Here is the verified current-affairs summary from FlashFacts records:\n\n"
                            + fallback_answer
                        ),
                        "provider": "ollama_error",
                    }

            if not answer_text:
                answer_text = self._synthesize_deterministic_answer(grounded_events, filters)
                provider_used = "deterministic_archive"

        # Case 2: No matching news events found
        else:
            if filters.get("freshness_sensitive"):
                provider_used = "ai_unverified_limitation"
                answer_text = self._synthesize_limitation_answer(question, filters)
            else:
                # General syllabus / conceptual question
                if not isinstance(self.provider, FallbackAIProvider):
                    try:
                        answer_text = self._synthesize_general_ai_answer(question, filters, history=history)
                        if answer_text:
                            provider_used = "ai_syllabus"
                    except TimeoutError as exc:
                        logger.warning("Ollama timeout during syllabus query: %s", exc)
                        return {
                            "filters": filters,
                            "sources": [],
                            "events_found": 0,
                            "answer": "⚠️ **Model Timeout:** The local AI model took longer than expected to respond. Please check your Ollama server and try again.",
                            "provider": "ollama_timeout",
                        }
                    except Exception as exc:
                        logger.error("LLM syllabus synthesis error: %s", exc)
                        return {
                            "filters": filters,
                            "sources": [],
                            "events_found": 0,
                            "answer": "⚠️ **AI Service Error:** The local AI service could not be reached. Please verify Ollama is active on your system.",
                            "provider": "ollama_error",
                        }

                if not answer_text:
                    answer_text = (
                        "No matching current-affairs events were found in the FlashFacts archive for this query. "
                        "To explore syllabus topics, please ensure local Ollama is running, or search within the PYQs and Syllabus sections."
                    )
                    provider_used = "fallback_no_records"

        # Enforce exact formatting and length constraints on generated answer
        answer_text = self._enforce_format_constraints(answer_text, filters)

        elapsed = time.time() - t_start
        logger.info("FlashFacts Ask AI completed in %.2fs (provider=%s)", elapsed, provider_used)

        return {
            "filters": filters,
            "sources": sources if events else [],
            "events_found": len(events),
            "answer": answer_text,
            "provider": provider_used,
        }

    def _retrieve_candidate_events(self, filters: Dict[str, Any]) -> List[Event]:
        """Retrieve candidate events using geographic, domain and exam constraints."""
        domain = filters.get("domain")
        domains = filters.get("domains") or ([domain] if domain else [])
        start_date = filters.get("start_date")
        end_date = filters.get("end_date")
        location_name = filters.get("location_name")
        query_text = filters.get("query_text")
        exam_id = filters.get("exam_id")

        events: List[Event] = []

        # 1. State / Regional location filter (exclude generic 'India')
        if location_name and location_name.lower() not in ("india", "bharat"):
            loc = self.location_service.find_by_name(location_name)
            if loc:
                loc_res = self.location_service.get_location_events(loc.id, limit=50)
                event_ids = [e["id"] for e in loc_res.get("events", []) if e.get("id")]
                if event_ids:
                    events = self.db.query(Event).filter(Event.id.in_(event_ids)).all()
            if not events:
                events, _ = self.event_repo.search_events(
                    query_text=f"{location_name} {query_text or ''}".strip(),
                    limit=20
                )
                if not events:
                    return []

        # 2. General search if no specific state location
        if not events:
            if query_text and len(query_text) > 2:
                events, _ = self.event_repo.search_events(
                    query_text=query_text,
                    domain=None if len(domains) > 1 else domain,
                    start_date=start_date,
                    end_date=end_date,
                    exam=exam_id,
                    limit=30,
                )

                # Fallback: if multi-word query returned 0, search with first 2 main words
                if not events and " " in query_text:
                    shorter_query = " ".join(query_text.split()[:2])
                    events, _ = self.event_repo.search_events(
                        query_text=shorter_query,
                        domain=None if len(domains) > 1 else domain,
                        limit=20,
                    )

            # NOTE: We ONLY invoke list_events if user asked an open query without specific subject keywords
            if not events and (not query_text or len(query_text) <= 2):
                if domain or domains or exam_id:
                    events, _ = self.event_repo.list_events(
                        domain=None if len(domains) > 1 else domain,
                        start_date=start_date,
                        end_date=end_date,
                        exam=exam_id,
                        sort="important",
                        limit=20,
                    )

        # 3. If query is about Indian space, supplement with 'isro' and 'india space' searches
        if filters.get("is_indian_space"):
            extra_1, _ = self.event_repo.search_events(query_text="isro", limit=20)
            extra_2, _ = self.event_repo.search_events(query_text="india space", limit=20)
            existing_ids = {e.id for e in events if getattr(e, "id", None) is not None}
            for e in (extra_1 + extra_2):
                e_id = getattr(e, "id", None)
                if e_id is not None and e_id not in existing_ids:
                    events.append(e)
                    existing_ids.add(e_id)
                elif e_id is None:
                    events.append(e)

        # 4. Date filtering
        if start_date:
            events = [e for e in events if e.event_date and e.event_date >= start_date.date()]
        if end_date:
            events = [e for e in events if e.event_date and e.event_date <= end_date.date()]

        # 4. Domain filtering
        if domains:
            events = [e for e in events if e.domain and any(d.lower() == e.domain.lower() for d in domains)]

        # 5. Score events for relevance
        def score_event(e: Event) -> float:
            score = float(e.importance_score or 50)
            if filters.get("importance") == "high" and score < 60:
                score -= 30
            non_exam_domains = {"Entertainment", "Crime", "Lifestyle", "Gossip", "Cinema"}
            if e.domain and e.domain in non_exam_domains:
                score -= 200
            if exam_id:
                rel = self.exam_service.get_event_exam_relevance(e.id)
                exam_rels = rel.get("relevant_exams", [])
                if any(r.get("exam_id") == exam_id for r in exam_rels):
                    score += 25
            return score

        scored_events = [(event, score_event(event)) for event in events]
        scored_events.sort(key=lambda x: x[1], reverse=True)

        return [event for event, score in scored_events[:4] if score > -100]

    def _format_length_instruction(self, filters: Dict[str, Any]) -> str:
        """Construct unambiguous system prompt instruction for the requested length/format."""
        format_constraint = filters.get("format_constraint")
        point_count = filters.get("point_count")
        word_limit = filters.get("word_limit")

        if format_constraint == "points" and point_count:
            return (
                f"STRICT FORMATTING RULE: The user explicitly requested exactly {point_count} points. "
                f"You MUST format your answer as EXACTLY {point_count} numbered points (numbered 1. through {point_count}.). "
                f"Each point must begin on a new line with its number (e.g. '1. ...', '2. ...'). "
                f"Do NOT provide more or fewer than {point_count} points. "
                "Do NOT include conversational filler, preamble, or concluding chatter."
            )
        elif format_constraint == "sentence":
            return (
                "STRICT FORMATTING RULE: The user explicitly requested a one-sentence answer. "
                "You MUST answer in EXACTLY ONE complete, well-formed sentence ending with a period. "
                "Do NOT write multiple sentences, paragraphs, or bullet points."
            )
        elif format_constraint == "words" and word_limit:
            return (
                f"STRICT FORMATTING RULE: Keep your answer concise and within {word_limit} words."
            )
        elif format_constraint == "detailed":
            return (
                "Provide a detailed, comprehensive, and well-structured examination explanation "
                "covering background, core constitutional/historical provisions, legal significance, and exam relevance."
            )
        return (
            "Provide a direct, accurate, and concise examination answer (100-200 words) "
            "with clear factual substance."
        )

    def _enforce_format_constraints(self, answer: str, filters: Dict[str, Any]) -> str:
        """Validate and strictly enforce requested answer length and formatting."""
        if not answer:
            return answer

        format_constraint = filters.get("format_constraint")
        if not format_constraint:
            return answer

        # 1. Numbered Points / Lines constraint: exactly N numbered points
        if format_constraint == "points":
            target_n = filters.get("point_count", 5)

            lines = answer.strip().splitlines()
            extracted_points = []

            for line in lines:
                l_strip = line.strip()
                if not l_strip:
                    continue
                # Match numbered or bulleted items
                m = re.match(r'^(?:(?:\d+[\.\)]|[\*\-\â€¢])\s*)(.+)', l_strip)
                if m:
                    extracted_points.append(m.group(1).strip())

            # If model produced numbered/bulleted points >= target_n, take first target_n
            if len(extracted_points) >= target_n:
                return "\n".join(f"{i}. {pt}" for i, pt in enumerate(extracted_points[:target_n], 1))

            # If fewer points found, split prose into sentences
            cleaned_text = re.sub(
                r'^(?:here (?:is|are)[^\n:]*[:\n]|sure[^\n:]*[:\n]|certainly[^\n:]*[:\n])',
                '',
                answer,
                flags=re.IGNORECASE
            ).strip()
            sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', cleaned_text) if len(s.strip()) > 10]

            combined = extracted_points + [s for s in sentences if not any(p in s for p in extracted_points)]
            if len(combined) >= target_n:
                return "\n".join(f"{i}. {pt.rstrip('.') + '.'}" for i, pt in enumerate(combined[:target_n], 1))

            # If still fewer, call zero-shot reformat if provider is available
            if hasattr(self.provider, "generate_chat") and not isinstance(self.provider, FallbackAIProvider):
                reformat_prompt = [
                    {
                        "role": "system",
                        "content": f"Extract and format EXACTLY {target_n} numbered points (1. to {target_n}.) from the text. Return ONLY the {target_n} numbered points with no conversational text."
                    },
                    {"role": "user", "content": answer}
                ]
                try:
                    reformatted = self.provider.generate_chat(reformat_prompt, temperature=0.0)
                    if reformatted:
                        re_pts = []
                        for r_line in reformatted.strip().splitlines():
                            rm = re.match(r'^(?:(?:\d+[\.\)]|[\*\-\â€¢])\s*)(.+)', r_line.strip())
                            if rm:
                                re_pts.append(rm.group(1).strip())
                        if len(re_pts) >= target_n:
                            return "\n".join(f"{i}. {pt}" for i, pt in enumerate(re_pts[:target_n], 1))
                except Exception as e:
                    logger.warning("Reformat attempt failed: %s", e)

            # Fallback point fulfillment
            if combined:
                while len(combined) < target_n:
                    combined.append(f"Key examination provision relevant to {filters.get('query_text', 'this topic')}.")
                return "\n".join(f"{i}. {pt.rstrip('.') + '.'}" for i, pt in enumerate(combined[:target_n], 1))

        # 2. One sentence constraint: exactly 1 sentence
        elif format_constraint == "sentence":
            cleaned = re.sub(r'^[#*\-\s]+', '', answer).strip()
            cleaned = re.sub(r'^(?:here is|certainly|sure|in summary|to summarize)[,\s:]+', '', cleaned, flags=re.IGNORECASE).strip()
            s_match = re.search(r'([^.!?]+[.!?])', cleaned)
            if s_match:
                return s_match.group(1).strip()
            return cleaned.rstrip('.') + '.'

        # 3. Word limit constraint
        elif format_constraint == "words":
            max_w = filters.get("word_limit", 100)
            words = answer.strip().split()
            if len(words) > int(max_w * 1.3):
                current_count = 0
                selected_sentences = []
                for s in re.split(r'(?<=[.!?])\s+', answer):
                    s_words = len(s.split())
                    if current_count + s_words <= max_w * 1.2 or not selected_sentences:
                        selected_sentences.append(s)
                        current_count += s_words
                    else:
                        break
                return " ".join(selected_sentences)

        return answer

    def _synthesize_deterministic_answer(
        self, events: List[Event], filters: Dict[str, Any]
    ) -> str:
        """Construct structured exam-oriented answer directly from retrieved events."""
        exam_code = filters.get("exam_code") or "Competitive Exams"
        date_label = (filters.get("date_label") or "Current").capitalize()
        location_label = filters.get("location_name")

        header_title = f"{date_label} Current Affairs"
        if location_label:
            header_title += f" | {location_label}"
        if exam_code:
            header_title += f" ({exam_code})"

        lines = [f"### ðŸ“‹ {header_title}\n"]

        is_mcq = filters.get("output_format") == "mcq"
        if is_mcq:
            mcq_count = filters.get("mcq_count", 5)
            lines.append("### ðŸŽ¯ Current Affairs Practice Quiz\n")
            for idx, e in enumerate(events[:mcq_count], 1):
                lines.append(f"**Question {idx}:** {e.title}")
                correct_ans = e.summary.split('.')[0] if '.' in e.summary else e.summary[:80]
                distractors = [
                    f"Related development in {e.domain} policy",
                    f"Initiative announced by international committee",
                    f"Proposal scheduled for legislative review next year"
                ]
                options = [correct_ans] + distractors
                import random
                rng = random.Random(e.id or idx)
                rng.shuffle(options)
                correct_pos = options.index(correct_ans)

                labels = ['A', 'B', 'C', 'D']
                for i, opt in enumerate(options):
                    lines.append(f"{labels[i]}) {opt}")

                lines.append(f"**Correct Answer: {labels[correct_pos]}**")
                lines.append(f"**Explanation:** {e.summary}\n")
        else:
            high_events = [e for e in events if (e.importance_score or 50) >= 60][:3]
            if not high_events and events:
                high_events = events[:2]

            if high_events:
                lines.append("ðŸŒŸ **HIGH PRIORITY**\n")
                for idx, e in enumerate(high_events, 1):
                    lines.append(f"**{idx}. {e.title}**")
                    lines.append(f"**What happened:** {e.summary}")
                    if e.why_it_matters:
                        lines.append(f"**Why it matters:** {e.why_it_matters}")

                    fact = f"Domain: {e.domain} | Category: {e.event_type or 'Current Affairs'}"
                    lines.append(f"**Exam Fact:** {fact}")

                    rel = self.exam_service.get_event_exam_relevance(e.id)
                    relevant_codes = [r["exam_code"] for r in rel.get("relevant_exams", [])[:3]]
                    if not relevant_codes:
                        relevant_codes = [exam_code, "UPSC"]
                    lines.append(f"**Relevant exams:** {' â€¢ '.join(relevant_codes)}")

                    source_name = getattr(e, "source", "") or "FlashFacts Network"
                    if hasattr(source_name, "name"):
                        source_name = source_name.name
                    date_str = e.event_date.isoformat() if e.event_date else ""
                    lines.append(f"**Source:** {source_name} ({date_str})\n")

            remaining = [e for e in events if e not in high_events][:2]
            if remaining:
                lines.append("ðŸ“° **IMPORTANT DEVELOPMENTS**\n")
                for idx, e in enumerate(remaining, 1):
                    lines.append(f"**{idx}. {e.title}**")
                    lines.append(f"{e.summary[:200]}...")
                    lines.append(f"*Category: {e.domain} | Date: {e.event_date}*\n")

        return "\n".join(lines)

    def _synthesize_limitation_answer(self, question: str, filters: Dict[str, Any]) -> str:
        """Synthesize an honest, transparent limitation when verified contemporary evidence is absent."""
        is_tamil = any("\u0b80" <= c <= "\u0bff" for c in question)
        format_constraint = filters.get("format_constraint")
        query_topic = filters.get("query_text") or "this topic"

        if is_tamil:
            if format_constraint == "sentence":
                return "\u0baa\u0bbf\u0bb3\u0bbe\u0bb7\u0b83\u0baa\u0bc6\u0b95\u0bcd\u0b9f\u0b8d\u0bb8\u0bcd \u0b9a\u0bb0\u0bbf\u0baa\u0bbe\u0bb0\u0bcd\u0b95\u0bcd\u0b95\u0baa\u0bcd\u0baa\u0b9f\u0bcd\u0b9f \u0b86\u0bb5\u0ba3\u0b99\u0bcd\u0b95\u0bb3\u0bbf\u0bb2\u0bcd \u0b9a\u0bae\u0bc0\u0baa\u0ba4\u0bcd\u0ba4\u0bbf\u0baf \u0ba4\u0b95\u0bb5\u0bb2\u0bcd\u0b95\u0bb3\u0bc8 \u0b89\u0bb1\u0bc1\u0ba4\u0bbf\u0baa\u0bcd\u0baa\u0b9f\u0bc1\u0ba4\u0bcd\u0ba4\u0bc1\u0bb5\u0ba4\u0bb1\u0bcd\u0b95\u0bbe\u0ba9 \u0baa\u0ba4\u0bbf\u0bb5\u0bc1\u0b95\u0bb3\u0bcd \u0ba4\u0bb1\u0bcd\u0baa\u0bcb\u0ba4\u0bc1 \u0b87\u0bb2\u0bcd\u0bb2\u0bc8."
            elif format_constraint == "points":
                n = filters.get("point_count", 3)
                pts = [
                    "\u0baa\u0bbf\u0bb3\u0bbe\u0bb7\u0b83\u0baa\u0bc6\u0b95\u0bcd\u0b9f\u0b8d\u0bb8\u0bcd \u0b86\u0bb5\u0ba3\u0b99\u0bcd\u0b95\u0bb3\u0bbf\u0bb2\u0bcd \u0b87\u0ba4\u0bb1\u0bcd\u0b95\u0bbe\u0ba9 \u0b9a\u0bae\u0bc0\u0baa\u0ba4\u0bcd\u0ba4\u0bbf\u0baf \u0ba4\u0b95\u0bb5\u0bb2\u0bcd\u0b95\u0bb3\u0bcd \u0b87\u0b9f\u0bae\u0bcd\u0baa\u0bc6\u0bb1\u0bb5\u0bbf\u0bb2\u0bcd\u0bb2\u0bc8.",
                    "\u0baa\u0bcb\u0b9f\u0bcd\u0b9f\u0bbf\u0ba4\u0bcd \u0ba4\u0bc7\u0bb0\u0bcd\u0bb5\u0bc1\u0b95\u0bcd\u0b95\u0bbe\u0ba9 \u0ba4\u0bb1\u0bcd\u0baa\u0bcb\u0ba4\u0bc8\u0baf \u0ba8\u0bbf\u0b95\u0bb4\u0bcd\u0bb5\u0bc1\u0b95\u0bb3\u0bc8 \u0b85\u0ba4\u0bbf\u0b95\u0bbe\u0bb0\u0baa\u0bcd\u0baa\u0bc2\u0bb0\u0bcd\u0bb5 \u0b85\u0bb1\u0bbf\u0bb5\u0bbf\u0baa\u0bcd\u0baa\u0bc1\u0b95\u0bb3\u0bcd \u0bae\u0bc2\u0bb2\u0bae\u0bcd \u0b89\u0bb1\u0bc1\u0ba4\u0bbf\u0baa\u0bcd\u0baa\u0b9f\u0bc1\u0ba4\u0bcd\u0ba4\u0bb5\u0bc1\u0bae\u0bcd.",
                    "\u0bae\u0bc7\u0bb2\u0bc1\u0bae\u0bcd \u0bb5\u0bbf\u0bb5\u0bb0\u0b99\u0bcd\u0b95\u0bb3\u0bc1\u0b95\u0bcd\u0b95\u0bc1 \u0b85\u0ba4\u0bbf\u0b95\u0bbe\u0bb0\u0baa\u0bcd\u0baa\u0bc2\u0bb0\u0bcd\u0bb5 \u0ba4\u0bb3\u0b99\u0bcd\u0b95\u0bb3\u0bc8 \u0baa\u0bbe\u0bb0\u0bcd\u0b95\u0bcd\u0b95\u0bb5\u0bc1\u0bae\u0bcd."
                ]
                while len(pts) < n:
                    pts.append("\u0b85\u0ba4\u0bbf\u0b95\u0bbe\u0bb0\u0baa\u0bcd\u0baa\u0bc2\u0bb0\u0bcd\u0bb5 \u0ba4\u0b95\u0bb5\u0bb2\u0bcd\u0b95\u0bb3\u0bc8\u0ba4\u0bcd \u0ba4\u0bca\u0b9f\u0bb0\u0bcd\u0ba8\u0bcd\u0ba4\u0bc1 \u0b9a\u0bb0\u0bbf\u0baa\u0bbe\u0bb0\u0bcd\u0b95\u0bcd\u0b95\u0bb5\u0bc1\u0bae\u0bcd.")
                return "\n".join(f"{i}. {pt}" for i, pt in enumerate(pts[:n], 1))
            return "\u0baa\u0bbf\u0bb3\u0bbe\u0bb7\u0b83\u0baa\u0bc6\u0b95\u0bcd\u0b9f\u0b8d\u0bb8\u0bcd \u0b9a\u0bb0\u0bbf\u0baa\u0bbe\u0bb0\u0bcd\u0b95\u0bcd\u0b95\u0baa\u0bcd\u0baa\u0b9f\u0bcd\u0b9f \u0ba4\u0bc7\u0bb0\u0bcd\u0bb5\u0bc1 \u0b86\u0bb5\u0ba3\u0b99\u0bcd\u0b95\u0bb3\u0bbf\u0bb2\u0bcd \u0b87\u0ba4\u0bc1 \u0b95\u0bc1\u0bb1\u0bbf\u0ba4\u0bcd\u0ba4 \u0b9a\u0bae\u0bc0\u0baa\u0ba4\u0bcd\u0ba4\u0bbf\u0baf \u0ba8\u0b9f\u0baa\u0bcd\u0baa\u0bc1 \u0ba8\u0bbf\u0b95\u0bb4\u0bcd\u0bb5\u0bc1\u0baa\u0bcd \u0baa\u0ba4\u0bbf\u0bb5\u0bc1\u0b95\u0bb3\u0bcd \u0ba4\u0bb1\u0bcd\u0baa\u0bcb\u0ba4\u0bc1 \u0b95\u0bbf\u0b9f\u0bc8\u0b95\u0bcd\u0b95\u0baa\u0bcd\u0baa\u0bc6\u0bb1\u0bb5\u0bbf\u0bb2\u0bcd\u0bb2\u0bc8. \u0ba4\u0bc1\u0bb2\u0bcd\u0bb2\u0bbf\u0baf\u0bae\u0bbe\u0ba9 \u0ba4\u0b95\u0bb5\u0bb2\u0bcd\u0b95\u0bb3\u0bc1\u0b95\u0bcd\u0b95\u0bc1 \u0b85\u0ba4\u0bbf\u0b95\u0bbe\u0bb0\u0baa\u0bcd\u0baa\u0bc2\u0bb0\u0bcd\u0bb5 \u0ba4\u0bb3\u0b99\u0bcd\u0b95\u0bb3\u0bc8 \u0b85\u0ba3\u0bc1\u0b95\u0bb5\u0bc1\u0bae\u0bcd."
        else:
            if format_constraint == "sentence":
                return "FlashFacts verified archives currently do not contain contemporary records verifying the latest development for this query as of this date."
            elif format_constraint == "points":
                n = filters.get("point_count", 3)
                pts = [
                    "FlashFacts verified examination archives currently lack contemporary records to verify the latest event for this topic.",
                    "Available records cannot confirm the most recent status without risk of presenting outdated information.",
                    "Aspirants are advised to refer to official agency releases for the latest real-time updates."
                ]
                while len(pts) < n:
                    pts.append(f"Official verification is recommended for recent {query_topic} developments.")
                return "\n".join(f"{i}. {pt}" for i, pt in enumerate(pts[:n], 1))
            return (
                "FlashFacts verified examination archives currently do not contain contemporary records verifying the latest development for this query. "
                "To maintain strict factual integrity for competitive examinations, an unverified or outdated event is not asserted as current."
            )

    def _synthesize_ai_answer(
        self,
        question: str,
        events: List[Event],
        filters: Dict[str, Any],
        history: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[str]:
        """Synthesize answer using AIProvider formatted strictly over retrieved events."""
        context_blocks = []
        for idx, e in enumerate(events[:4], 1):
            source_name = getattr(e, "source", "") or "FlashFacts Network"
            if hasattr(source_name, "name"):
                source_name = source_name.name
            date_str = e.event_date.isoformat() if getattr(e, "event_date", None) else ""
            context_blocks.append(
                f"[{idx}] Title: {e.title}\n"
                f"Domain: {e.domain} | Date: {date_str} | Source: {source_name}\n"
                f"Summary: {e.summary}\n"
                f"Significance: {e.why_it_matters or 'Relevant for general awareness'}\n"
            )

        context_str = "\n".join(context_blocks)
        is_mcq = filters.get("output_format") == "mcq"
        exam_code = filters.get("exam_code") or "Competitive Exams"
        length_instruction = self._format_length_instruction(filters)

        if is_mcq:
            mcq_count = filters.get("mcq_count", 5)
            system_prompt = (
                f"You are FlashFacts AI, an expert exam MCQ creator for {exam_code}. "
                "The user has requested practice MCQs based on verified current affairs records. "
                "Use ONLY the provided context to generate questions. "
                f"Generate up to {mcq_count} questions. For each question, provide 4 options (A, B, C, D), "
                "mark the correct option, and provide a clear explanation. Format as ### Current Affairs Practice Quiz."
            )
        else:
            freshness_rule = ""
            if filters.get("freshness_sensitive") and events:
                latest_e = events[0]
                e_d = latest_e.event_date.isoformat() if getattr(latest_e, "event_date", None) else ""
                freshness_rule = (
                    f"The user has specifically asked for the latest or current development. "
                    f"You MUST ground your answer on the most recent verified event provided in the context (Event [1], dated {e_d}). "
                    f"Accurately distinguish the status of the mission: whether it is a planned/upcoming launch, "
                    f"a launch that has already occurred, a satellite deployment, or a mission test. "
                    f"Do NOT assert an upcoming or planned launch has already occurred, and do NOT assert an older historical event "
                    f"(such as Chandrayaan-3 from 2023) as the latest development when newer verified developments are present in the context. "
                )
            system_prompt = (
                f"You are FlashFacts AI, an exam intelligence assistant for {exam_code}. "
                f"{length_instruction} "
                f"{freshness_rule}"
                "Ground all current-affairs claims strictly on the provided verified FlashFacts context. "
                "Cite the source names and dates naturally in your response when relevant. "
                "Do not invent facts, events, dates, statistics, sources, or citations. "
                "If the context is insufficient to fully answer, state what is known and clarify what is missing. "
                "If the question is in Tamil, answer in natural standard Tamil appropriate for TNPSC candidates. "
                "Do not output internal thinking or reasoning tags; begin immediately with your direct answer."
            )

        messages = [{"role": "system", "content": system_prompt}]

        if history:
            for h in history[-4:]:
                role = "assistant" if h.get("sender") == "assistant" or h.get("role") == "assistant" else "user"
                content = h.get("text") or h.get("content") or ""
                if content:
                    messages.append({"role": role, "content": content})

        messages.append({
            "role": "user",
            "content": f"Verified FlashFacts Context:\n{context_str}\n\nQuestion: {question}"
        })

        if hasattr(self.provider, "generate_chat"):
            return self.provider.generate_chat(messages, temperature=0.2)
        return None

    def _synthesize_general_ai_answer(
        self,
        question: str,
        filters: Dict[str, Any],
        history: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[str]:
        """Generate conceptual syllabus / educational answer when no specific news events match."""
        is_mcq = filters.get("output_format") == "mcq"
        exam_code = filters.get("exam_code") or "Competitive Exams"
        length_instruction = self._format_length_instruction(filters)

        if is_mcq:
            mcq_count = filters.get("mcq_count", 5)
            system_prompt = (
                f"You are FlashFacts AI, an expert exam question creator for {exam_code}. "
                f"Generate exactly {mcq_count} high-quality practice MCQs on the requested topic. "
                "For each question, provide 4 distinct options (A, B, C, D), mark the correct answer, "
                "and provide a factual explanation. Format clearly as ### Practice Quiz."
            )
        else:
            system_prompt = (
                f"You are FlashFacts AI, a knowledgeable exam intelligence assistant for competitive exams (UPSC, TNPSC, SSC, Banking). "
                f"{length_instruction} "
                "Organize your answer clearly with key facts, articles, amendments, or historical/scientific background. "
                "Do not fabricate breaking current-affairs news events or claim this is from recent FlashFacts news records. "
                "If the question is in Tamil, answer in natural standard Tamil appropriate for TNPSC exams. "
                "Do not output internal thinking or reasoning tags; begin immediately with the answer."
            )

        messages = [{"role": "system", "content": system_prompt}]

        if history:
            for h in history[-4:]:
                role = "assistant" if h.get("sender") == "assistant" or h.get("role") == "assistant" else "user"
                content = h.get("text") or h.get("content") or ""
                if content:
                    messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": question})

        if hasattr(self.provider, "generate_chat"):
            return self.provider.generate_chat(messages, temperature=0.2)
        return None
