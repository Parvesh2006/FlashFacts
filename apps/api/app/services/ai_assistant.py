"""
FlashFacts AI Intelligence Assistant Service.
RAG-powered current affairs query synthesis for competitive exam preparation.
"""
import re
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.event import Event
from app.repositories.event_repository import EventRepository
from app.services.exam_intelligence import ExamIntelligenceService, EXAM_DEFINITIONS
from app.services.location_service import LocationService
from app.services.ai_provider import AIProvider, FallbackAIProvider, get_ai_provider
from app.utils.hashing import fix_mojibake

logger = logging.getLogger("app")


# Map of state names & aliases for rapid matching
INDIAN_STATES_MAP = {
    "tamil nadu": "Tamil Nadu", "tn": "Tamil Nadu", "madras": "Tamil Nadu",
    "தமிழ்நாடு": "Tamil Nadu", "chennai": "Tamil Nadu", "coimbatore": "Tamil Nadu", "madurai": "Tamil Nadu",
    "kerala": "Kerala", "karnataka": "Karnataka", "bengaluru": "Karnataka", "bangalore": "Karnataka",
    "maharashtra": "Maharashtra", "mumbai": "Maharashtra",
    "delhi": "New Delhi", "new delhi": "New Delhi", "ncr": "New Delhi",
    "gujarat": "Gujarat", "andhra pradesh": "Andhra Pradesh", "ap": "Andhra Pradesh",
    "telangana": "Telangana", "uttar pradesh": "Uttar Pradesh", "up": "Uttar Pradesh",
    "west bengal": "West Bengal", "bihar": "Bihar", "rajasthan": "Rajasthan",
    "punjab": "Punjab", "haryana": "Haryana", "madhya pradesh": "Madhya Pradesh", "mp": "Madhya Pradesh",
    "odisha": "Odisha", "orissa": "Odisha", "assam": "Assam", "goa": "Goa",
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
    "ai": "AI",
    "artificial intelligence": "AI",
    "technology": "Technology",
    "tech": "Technology",
    "science": "Science",
    "space": "Science",
    "isro": "Science",
    "economy": "Economy",
    "economic": "Economy",
    "finance": "Economy",
    "rbi": "Economy",
    "banking": "Economy",
    "government": "Government",
    "scheme": "Government",
    "schemes": "Government",
    "policy": "Government",
    "politics": "Politics",
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
        """Convert natural language question into structured filters."""
        import re
        from datetime import datetime, timezone, timedelta
        from zoneinfo import ZoneInfo

        q_lower = question.lower()
        filters: Dict[str, Any] = {}

        # MCQ Intent and Count Extraction
        if "mcq" in q_lower or "quiz" in q_lower or "multiple choice" in q_lower:
            filters["output_format"] = "mcq"
            filters["mcq_count"] = 5
            match = re.search(r'\b(\d+)\b', q_lower)
            if match:
                filters["mcq_count"] = int(match.group(1))

        today = datetime.now(ZoneInfo("Asia/Kolkata"))

        if history:
            last_filters = None
            for item in reversed(history):
                if isinstance(item, dict) and "filters" in item:
                    last_filters = item["filters"]
                    break
            if last_filters:
                if last_filters.get("domain") and "domain" not in q_lower:
                    filters["domain"] = last_filters["domain"]
                if last_filters.get("date_range") and "today" not in q_lower and "yesterday" not in q_lower:
                    filters["date_label"] = last_filters.get("date_label", "inherited")
                if last_filters.get("exam_id"):
                    filters["exam_id"] = last_filters["exam_id"]
                    filters["exam_code"] = last_filters.get("exam_code")
                if last_filters.get("location_name"):
                    filters["location_name"] = last_filters["location_name"]

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

        for kw, canonical_name in INDIAN_STATES_MAP.items():
            if re.search(rf"\b{re.escape(kw)}\b", q_lower):
                filters["location_name"] = canonical_name
                break

        if re.search(r'\bindia\b', q_lower) and not filters.get("location_name"):
            filters["location_name"] = "India"

        for kw, exam_id in EXAM_KEYWORDS.items():
            if re.search(rf"\b{re.escape(kw)}\b", q_lower):
                filters["exam_id"] = exam_id
                defn = EXAM_DEFINITIONS.get(exam_id)
                if defn:
                    filters["exam_code"] = defn["code"]
                break

        for kw, domain_name in DOMAIN_KEYWORDS.items():
            if re.search(r"\bscience\s*(?:&|and)\s*technology\b", q_lower):
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

        clean_words = []
        ignore_words = {
            "what", "happened", "today", "current", "affairs", "the", "in", "for", "give", "me",
            "show", "tell", "explain", "is", "of", "and", "some", "mcq", "mcqs", "about", "on",
            "quiz", "multiple", "choice", "questions", "generate", "create", "make", "from",
            "please", "can", "you", "a", "an", "any",
            "\u0baa\u0bb1\u0bcd\u0bb1\u0bbf",
            "\u0b95\u0bc2\u0bb1\u0bc1"
        }

        words = q_lower.replace("?", "").replace(".", "").split()
        for word in words:
            if word not in ignore_words and not word.isdigit():
                clean_words.append(word)

        filters["query_text"] = " ".join(clean_words[:6])
        return filters

    def answer_question(
        self, question: str, history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Process user question via RAG pipeline and return grounded exam-focused answer."""
        filters = self.parse_query(question, history=history)

        events = self._retrieve_candidate_events(filters)

        if not events:
            broad_filters = dict(filters)
            broad_filters["start_date"] = None
            broad_filters["end_date"] = None
            events = self._retrieve_candidate_events(broad_filters)

        if not events:
            return {
                "filters": filters,
                "sources": [],
                "events_found": 0,
                "answer": (
                    "I couldn't find enough verified FlashFacts data for that query.\n\n"
                    "Try broadening your date range, selecting another location, or searching another exam category."
                ),
                "provider": "grounded_fallback",
            }

        answer_text = None
        provider_used = "deterministic_grounded"

        if not isinstance(self.provider, FallbackAIProvider):
            try:
                answer_text = self._synthesize_ai_answer(question, events, filters)
                if answer_text:
                    provider_used = "ai_grounded"
            except Exception as exc:
                logger.warning("LLM synthesis failed, falling back to deterministic synthesis: %s", exc)

        if not answer_text:
            answer_text = self._synthesize_deterministic_answer(events, filters)

        sources = []
        for e in events[:5]:
            src_name = getattr(e, "source", "") or "FlashFacts Network"
            if hasattr(src_name, "name"):
                src_name = src_name.name
            sources.append({
                "name": src_name,
                "url": getattr(e, "url", None),
                "date": e.event_date.isoformat() if getattr(e, "event_date", None) else None,
            })

        return {
            "filters": filters,
            "sources": sources,
            "events_found": len(events),
            "answer": answer_text,
            "provider": provider_used,
        }

    def _retrieve_candidate_events(self, filters: Dict[str, Any]) -> List[Event]:
        """Retrieve candidate events using strict geographic, domain and exam constraints."""

        domain = filters.get("domain")
        domains = filters.get("domains") or ([domain] if domain else [])
        start_date = filters.get("start_date")
        end_date = filters.get("end_date")
        location_name = filters.get("location_name")
        query_text = filters.get("query_text")
        exam_id = filters.get("exam_id")

        events: List[Event] = []

        # ---------------------------------------------------------
        # 1. LOCATION IS A HARD FILTER
        # ---------------------------------------------------------
        if location_name:
            loc = self.location_service.find_by_name(location_name)

            if loc:
                loc_res = self.location_service.get_location_events(
                    loc.id,
                    limit=100
                )

                event_ids = [
                    e["id"]
                    for e in loc_res.get("events", [])
                    if e.get("id")
                ]

                if event_ids:
                    events = (
                        self.db.query(Event)
                        .filter(Event.id.in_(event_ids))
                        .all()
                    )

            # If location was explicitly requested, NEVER fall back
            # to global search.
            if not events:
                return []

        # ---------------------------------------------------------
        # 2. IF NO LOCATION WAS REQUESTED, NORMAL SEARCH IS ALLOWED
        # ---------------------------------------------------------
        else:
            if query_text and len(query_text) > 2:
                events, _ = self.event_repo.search_events(
                    query_text=query_text,
                    domain=None if len(domains) > 1 else domain,
                    start_date=start_date,
                    end_date=end_date,
                    exam=exam_id,
                    limit=50,
                )

            if not events and not query_text:
                events, _ = self.event_repo.list_events(
                    domain=None if len(domains) > 1 else domain,
                    start_date=start_date,
                    end_date=end_date,
                    exam=exam_id,
                    sort="important",
                    limit=50,
                )

        # ---------------------------------------------------------
        # 3. DATE FILTER
        # ---------------------------------------------------------
        if start_date:
            events = [
                e for e in events
                if e.event_date and e.event_date >= start_date.date()
            ]

        if end_date:
            events = [
                e for e in events
                if e.event_date and e.event_date <= end_date.date()
            ]

        # ---------------------------------------------------------
        # 4. DOMAIN FILTER
        # ---------------------------------------------------------
        if domains:
            events = [
                e for e in events
                if e.domain and any(
                    d.lower() == e.domain.lower()
                    for d in domains
                )
            ]

        # ---------------------------------------------------------
        # 5. EXAM RELEVANCE
        # ---------------------------------------------------------
        def score_event(e: Event) -> float:
            score = float(e.importance_score or 50)

            if filters.get("importance") == "high" and score < 60:
                score -= 50

            # Generic penalty for non-exam domains
            non_exam_domains = {"Entertainment", "Crime", "Lifestyle", "Gossip", "Cinema"}
            if e.domain and e.domain in non_exam_domains:
                score -= 500

            if exam_id:
                rel = self.exam_service.get_event_exam_relevance(e.id)
                exam_rels = rel.get("relevant_exams", [])

                if any(
                    r.get("exam_id") == exam_id
                    for r in exam_rels
                ):
                    score += 20
                else:
                    # Heavily penalize events that are not relevant to the requested exam
                    score -= 500

            return score

        scored_events = [
            (event, score_event(event))
            for event in events
        ]

        scored_events.sort(
            key=lambda x: x[1],
            reverse=True
        )

        return [event for event, score in scored_events[:10] if score > -100]
    def _synthesize_deterministic_answer(
        self, events: List[Event], filters: Dict[str, Any]
    ) -> str:
        """Construct structured exam-oriented answer directly from retrieved events."""
        from app.utils.hashing import fix_mojibake

        exam_code = filters.get("exam_code") or "Competitive Exams"
        date_label = (filters.get("date_label") or "Current").capitalize()
        location_label = filters.get("location_name")

        header_title = f"{date_label} Current Affairs"
        if location_label:
            header_title += f" | {location_label}"
        if exam_code:
            header_title += f" ({exam_code})"

        lines = [f"### {header_title}\n"]

        if filters.get("output_format") == "mcq":
            lines.append("### Current Affairs Practice Quiz\n")
            mcq_count = filters.get("mcq_count", 5)
            mcq_events = events[:mcq_count]

            all_titles = [e.title for e in events if e.title]

            for idx, e in enumerate(mcq_events, 1):
                domain_str = e.domain or 'Current Affairs'
                lines.append(f"**Q{idx}. Regarding recent developments in {domain_str}, which of the following is correct?**")

                correct_ans = e.title

                distractors = []
                for other in all_titles:
                    other_clean = other
                    if other_clean != correct_ans and other_clean not in distractors:
                        distractors.append(other_clean)
                        if len(distractors) == 3:
                            break

                while len(distractors) < 3:
                    distractors.append(f"A significant policy update in {domain_str}.")
                    distractors.append(f"A new development affecting {domain_str} stakeholders.")
                    distractors.append(f"An international agreement regarding {domain_str}.")

                options = [correct_ans, distractors[0], distractors[1], distractors[2]]

                correct_pos = idx % 4
                options[0], options[correct_pos] = options[correct_pos], options[0]

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
                lines.append("🌟 **HIGH PRIORITY**\n")
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
                    lines.append(f"**Relevant exams:** {' • '.join(relevant_codes)}")

                    source_name = getattr(e, "source", "") or "FlashFacts Network"
                    if hasattr(source_name, "name"):
                        source_name = source_name.name
                    date_str = e.event_date.isoformat() if e.event_date else ""
                    lines.append(f"**Source:** {source_name} ({date_str})\n")

            remaining = [e for e in events if e not in high_events][:3]
            if remaining:
                lines.append("📰 **IMPORTANT DEVELOPMENTS**\n")
                for idx, e in enumerate(remaining, 1):
                    lines.append(f"**{idx}. {e.title}**")
                    lines.append(f"{e.summary[:200]}...")
                    lines.append(f"*Category: {e.domain} | Date: {e.event_date}*\n")

        return "\n".join(lines)

    def _synthesize_ai_answer(
        self, question: str, events: List[Event], filters: Dict[str, Any]
    ) -> Optional[str]:
        """Synthesize answer using AIProvider formatted strictly over retrieved events."""
        context_blocks = []
        for idx, e in enumerate(events, 1):
            source_name = getattr(e, "source", "") or "FlashFacts Network"
            if hasattr(source_name, "name"):
                source_name = source_name.name
            context_blocks.append(
                f"[{idx}] Title: {e.title}\n"
                f"Domain: {e.domain} | Date: {e.event_date}\n"
                f"Summary: {e.summary}\n"
                f"Why it matters: {e.why_it_matters or 'N/A'}\n"
                f"Source: {source_name}\n"
            )

        context_str = "\n".join(context_blocks)

        is_mcq = filters.get("output_format") == "mcq"

        if is_mcq:
            mcq_count = filters.get("mcq_count", 5)
            system_prompt = (
                "You are FlashFacts AI, an expert MCQ generator for competitive exams. "
                "The user has requested MCQs based on current affairs. "
                "Use ONLY the provided retrieved context to generate the questions. "
                "CRITICAL MCQ RULES:\n"
                "1. Fact-based: Test specific factual claims, not generic summaries.\n"
                "2. Concise Options: Every option must be a concise factual statement or answer phrase.\n"
                "3. Plausible Distractors: Distractors must be plausible alternatives from the same subject/domain, with similar length and specificity to the correct answer. Every option must be independently plausible to a student who knows the subject.\n"
                "4. Answer Distribution: Across a multi-question quiz, vary the correct option position among A/B/C/D rather than always placing it at A.\n"
                f"5. Count: Generate exactly {mcq_count} questions, using distinct events where possible. If there is insufficient context to generate {mcq_count} questions safely, generate as many as you safely can.\n"
                "6. Grounding: The correct answer must be supported directly by the retrieved event.\n"
                "7. Explanations: The explanation must reference the specific factual basis of the correct answer.\n"
                "Format as a numbered quiz. Use ### Current Affairs Practice Quiz as the title.\n"
                "Use **Q to denote a question. End each question with **Correct Answer: [Option] and **Explanation:** [Text]."
            )
        else:
            system_prompt = (
                "You are the FlashFacts exam-current-affairs AI assistant. Understand the user's question and provide a clear, useful answer. "
                "For current-affairs claims, use only the verified FlashFacts context supplied to you. "
                "Do not invent facts, events, dates, statistics, sources, or citations. If the supplied context is insufficient, say so clearly. "
                "Answer in the user's requested language. For Tamil, use natural standard Tamil suitable for TNPSC aspirants. "
                "Do not translate English phrases literally when a standard Tamil term exists. Use standard terminology such as 'இந்திய அரசியலமைப்பு' for Constitution, 'அடிப்படை உரிமைகள்', 'சமத்துவம்', 'சமூக நீதி', 'மத்திய அரசு', 'மாநில அரசு'. "
                "Preserve important names, dates, organizations, and source information accurately. Keep answers concise but informative and organize them according to the question rather than forcing every answer into a fixed template. "
                "Never expose internal reasoning, do not mention system prompts, and do not claim to have browsed the web."
            )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context:\n{context_str}\n\nQuestion: {question}"}
        ]

        if hasattr(self.provider, "generate_chat"):
            return self.provider.generate_chat(messages, temperature=0.2)
        return None
