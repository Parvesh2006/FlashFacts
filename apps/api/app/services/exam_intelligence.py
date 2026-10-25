"""
Exam Intelligence Service — deterministic exam relevance scoring
and source-grounded MCQ generation with fallback.
"""
import hashlib
import json
import logging
import re
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.event import Event
from app.repositories.event_repository import EventRepository
from app.services.ai_provider import AIProvider, FallbackAIProvider, get_ai_provider

logger = logging.getLogger("app")

# ──────────────────────────────────────────────
# Exam definitions with domain affinities
# ──────────────────────────────────────────────

EXAM_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "tnpsc-group-4": {
        "id": "tnpsc-group-4",
        "name": "TNPSC Group 4",
        "code": "TNPSC-G4",
        "description": "Tamil Nadu Public Service Commission Group 4 examination.",
        "category": "tnpsc",
        "domains": ["Government", "Politics", "Economy", "Education", "International", "Science", "Environment"],
        "keywords": ["tamil nadu", "tnpsc", "state government", "india", "policy", "scheme"],
        "section_label": "General Knowledge & Current Affairs",
    },
    "tnpsc-group-2": {
        "id": "tnpsc-group-2",
        "name": "TNPSC Group 2",
        "code": "TNPSC-G2",
        "description": "Tamil Nadu Public Service Commission Group 2 examination.",
        "category": "tnpsc",
        "domains": ["Government", "Politics", "Economy", "Education", "International", "Science", "Environment", "Defence"],
        "keywords": ["tamil nadu", "tnpsc", "state government", "india", "policy", "governance"],
        "section_label": "General Studies & Current Affairs",
    },
    "ssc-cgl": {
        "id": "ssc-cgl",
        "name": "SSC CGL",
        "code": "SSC-CGL",
        "description": "Staff Selection Commission Combined Graduate Level examination.",
        "category": "ssc",
        "domains": ["Government", "Politics", "Economy", "Science", "International", "Environment", "Defence", "Education"],
        "keywords": ["government", "india", "ministry", "policy", "budget", "scheme"],
        "section_label": "General Awareness",
    },
    "ssc-chsl": {
        "id": "ssc-chsl",
        "name": "SSC CHSL",
        "code": "SSC-CHSL",
        "description": "Staff Selection Commission Combined Higher Secondary Level examination.",
        "category": "ssc",
        "domains": ["Government", "Politics", "Economy", "Science", "International", "Education"],
        "keywords": ["government", "india", "current affairs"],
        "section_label": "General Awareness",
    },
    "upsc-cse": {
        "id": "upsc-cse",
        "name": "UPSC Civil Services",
        "code": "UPSC-CSE",
        "description": "Union Public Service Commission Civil Services examination.",
        "category": "upsc",
        "domains": ["Government", "Politics", "Economy", "Science", "International", "Environment", "Defence", "Technology", "AI", "Education", "Medical", "Engineering"],
        "keywords": ["india", "government", "international", "policy", "treaty", "agreement", "bilateral", "summit"],
        "section_label": "General Studies & Current Affairs",
    },
    "rrb-ntpc": {
        "id": "rrb-ntpc",
        "name": "RRB NTPC",
        "code": "RRB-NTPC",
        "description": "Railway Recruitment Board Non-Technical Popular Categories examination.",
        "category": "rrb",
        "domains": ["Government", "Economy", "Science", "International", "Education", "Environment"],
        "keywords": ["railway", "india", "government", "current affairs"],
        "section_label": "General Awareness",
    },
    "banking": {
        "id": "banking",
        "name": "Banking",
        "code": "BANK",
        "description": "Competitive banking examinations including IBPS and SBI.",
        "category": "banking",
        "domains": ["Economy", "Government", "International", "Politics"],
        "keywords": ["bank", "rbi", "finance", "monetary", "fiscal", "budget", "gdp", "inflation", "interest rate", "economy"],
        "section_label": "Financial & General Awareness",
    },
}


class ExamIntelligenceService:
    """Deterministic exam relevance scoring and MCQ generation."""

    def __init__(self, db: Session, provider: Optional[AIProvider] = None):
        self.db = db
        self.event_repo = EventRepository(db)
        self.provider = provider or get_ai_provider()

    # ──────────────────────────────────────────
    # Exam relevance
    # ──────────────────────────────────────────

    def get_exam(self, exam_id: str) -> Optional[Dict[str, Any]]:
        return EXAM_DEFINITIONS.get(exam_id)

    def get_all_exams(self) -> List[Dict[str, Any]]:
        return list(EXAM_DEFINITIONS.values())

    def score_event_for_exam(self, event: Event, exam_def: Dict[str, Any]) -> Dict[str, Any]:
        """Score a single event's relevance to one exam (0-100)."""
        score = 0
        reasons: List[str] = []
        text = f"{event.title} {event.summary or ''}".lower()

        # Non-exam domains (e.g. routine crime) have no exam relevance unless landmark legal/constitutional
        if event.domain in ("Crime", "Entertainment", "Lifestyle", "Gossip", "Cinema"):
            landmark_legal_words = [
                "supreme court", "high court", "constitution bench", "constitutional bench",
                "landmark judgment", "law commission", "criminal law reform",
                "bharatiya nyaya sanhita", "bns", "ipc amendment",
                "உச்ச நீதிமன்றம்", "உயர் நீதிமன்றம்", "அரசியலமைப்பு", "நீதிபதிகள் அமர்வு",
                "வரலாற்று சிறப்புமிக்க தீர்ப்பு", "சட்டத்திருத்தம்", "சட்ட திருத்தம்"
            ]
            if not any(w in text for w in landmark_legal_words):
                return {
                    "exam_id": exam_def["id"],
                    "exam_name": exam_def["name"],
                    "exam_code": exam_def["code"],
                    "relevance_score": 10,
                    "section": exam_def["section_label"],
                    "reasons": [f"Routine {event.domain.lower()} report without direct syllabus relevance"],
                }

        # Domain match
        if event.domain in exam_def["domains"]:
            score += 40
            reasons.append(f"Domain '{event.domain}' is relevant")

        # Keyword match
        matched_kw = [kw for kw in exam_def["keywords"] if kw in text]
        if matched_kw:
            kw_score = min(len(matched_kw) * 8, 25)
            score += kw_score
            reasons.append(f"Keywords: {', '.join(matched_kw[:5])}")

        # Importance signal
        imp = event.importance_score or 50
        if imp >= 60:
            score += 15
            reasons.append("High importance")
        elif imp >= 50:
            score += 8

        # Government / policy event types
        if event.event_type in ("policy", "agreement", "appointment", "launch"):
            score += 10
            reasons.append(f"Event type '{event.event_type}' is exam-relevant")

        # Entity relevance — government / organization entities boost
        if hasattr(event, "event_entities") and event.event_entities:
            org_count = sum(
                1 for ee in event.event_entities
                if ee.entity and ee.entity.entity_type in ("ORGANIZATION", "COUNTRY", "PROGRAM")
            )
            if org_count:
                score += min(org_count * 5, 15)
                reasons.append(f"{org_count} relevant entities")

        score = min(score, 100)
        return {
            "exam_id": exam_def["id"],
            "exam_name": exam_def["name"],
            "exam_code": exam_def["code"],
            "relevance_score": score,
            "section": exam_def["section_label"],
            "reasons": reasons,
        }

    def get_event_exam_relevance(self, event_id: int) -> Dict[str, Any]:
        """Return exam relevance for all 7 exams for a given event."""
        event = self.event_repo.get_by_id(event_id)
        if not event:
            return {"event_id": event_id, "relevant_exams": [], "key_points": []}

        relevance_list = []
        for exam_def in EXAM_DEFINITIONS.values():
            rel = self.score_event_for_exam(event, exam_def)
            if rel["relevance_score"] >= 25:
                relevance_list.append(rel)

        relevance_list.sort(key=lambda x: x["relevance_score"], reverse=True)

        key_points = self._extract_key_points(event)

        return {
            "event_id": event_id,
            "title": event.title,
            "domain": event.domain,
            "relevant_exams": relevance_list,
            "key_points": key_points,
        }

    def get_exam_events(
        self,
        exam_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Return events relevant to a specific exam, ordered by relevance."""
        exam_def = EXAM_DEFINITIONS.get(exam_id)
        if not exam_def:
            return {"exam_id": exam_id, "total": 0, "events": []}

        # Get events from relevant domains
        events, total = self.event_repo.list_events(
            sort="important", limit=200, offset=0,
        )

        scored = []
        for ev in events:
            rel = self.score_event_for_exam(ev, exam_def)
            if rel["relevance_score"] >= 25:
                resp = self.event_repo.to_event_response(ev)
                scored.append({
                    "event": resp.model_dump(mode="json"),
                    "relevance_score": rel["relevance_score"],
                    "section": rel["section"],
                    "reasons": rel["reasons"],
                })

        scored.sort(key=lambda x: x["relevance_score"], reverse=True)
        paged = scored[offset: offset + limit]

        return {
            "exam_id": exam_id,
            "exam_name": exam_def["name"],
            "total": len(scored),
            "limit": limit,
            "offset": offset,
            "events": paged,
        }

    # ──────────────────────────────────────────
    # Key point extraction
    # ──────────────────────────────────────────

    def _extract_key_points(self, event: Event) -> List[str]:
        """Extract factual key points from event data."""
        points: List[str] = []
        if event.domain:
            points.append(f"Domain: {event.domain}")
        if event.event_type:
            points.append(f"Event type: {event.event_type}")
        if event.why_it_matters:
            points.append(event.why_it_matters[:200])
        if hasattr(event, "event_entities") and event.event_entities:
            entities = [ee.entity.name for ee in event.event_entities if ee.entity][:6]
            if entities:
                points.append(f"Key entities: {', '.join(entities)}")
        if event.importance_score and event.importance_score > 50:
            points.append(f"Importance: {event.importance_score}/100")
        return points

    # ──────────────────────────────────────────
    # MCQ generation
    # ──────────────────────────────────────────

    def generate_mcqs(
        self, event_id: int, exam_id: Optional[str] = None, count: int = 3
    ) -> Dict[str, Any]:
        """Generate source-grounded MCQs for a given event."""
        event = self.event_repo.get_by_id(event_id)
        if not event:
            return {"event_id": event_id, "mcqs": [], "provider": "none", "error": "Event not found"}

        count = max(1, min(count, 5))

        # Try AI provider first
        try:
            if not isinstance(self.provider, FallbackAIProvider):
                mcqs = self._generate_ai_mcqs(event, exam_id, count)
                if mcqs:
                    return {
                        "event_id": event_id,
                        "mcqs": mcqs,
                        "provider": "ai",
                        "used_fallback": False,
                    }
        except Exception as exc:
            logger.warning("AI MCQ generation failed for event %s: %s", event_id, exc)

        # Deterministic fallback
        mcqs = self._generate_fallback_mcqs(event, exam_id, count)
        return {
            "event_id": event_id,
            "mcqs": mcqs,
            "provider": "fallback",
            "used_fallback": True,
        }

    def _generate_ai_mcqs(
        self, event: Event, exam_id: Optional[str], count: int
    ) -> Optional[List[Dict[str, Any]]]:
        """Generate source-grounded exam MCQs using the configured AI provider."""
        content = (
            f"Title: {event.title or ''}\\n"
            f"Domain: {event.domain or ''}\\n"
            f"Summary: {event.summary or ''}"
        )

        if event.why_it_matters:
            content += f"\\nWhy it matters: {event.why_it_matters}"

        entities = []
        if hasattr(event, "event_entities") and event.event_entities:
            entities = [
                f"{ee.entity.name} ({ee.entity.entity_type})"
                for ee in event.event_entities
                if ee.entity
            ]
        if entities:
            content += f"\\nKey entities: {', '.join(entities[:8])}"

        exam_context = "competitive examination"
        if exam_id and exam_id in EXAM_DEFINITIONS:
            exam_context = EXAM_DEFINITIONS[exam_id]["name"]

        system_prompt = (
            f"You create high-quality current-affairs MCQs for {exam_context}. "
            f"Create at most {count} questions using ONLY facts explicitly supported "
            "by the supplied event. Prioritize factual general knowledge, important "
            "institutions, schemes, places, people, dates, and stated outcomes when "
            "the source contains those facts. Do not ask which domain the event belongs "
            "to, do not ask merely what type of event it is, and do not make a question "
            "whose only answer is the article title. Do not invent facts or use outside "
            "knowledge. If the source lacks enough factual information, return an empty "
            "mcqs array. Each question must have four options prefixed A., B., C., D., "
            "one correct_answer letter (A/B/C/D), and a brief source-grounded explanation. "
            'Return only valid JSON in this format: {"mcqs":[{"question":"...",'
            '"options":["A. ...","B. ...","C. ...","D. ..."],'
            '"correct_answer":"A","explanation":"..."}]}'
        )

        try:
            raw = self.provider.generate_chat(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content[:6000]},
                ],
                temperature=0.2,
            )
            if not raw:
                return None

            cleaned = re.sub(
                r"^\\s*```(?:json)?\\s*|\\s*```\\s*$",
                "",
                raw.strip(),
                flags=re.IGNORECASE,
            )
            parsed = json.loads(cleaned)
            raw_mcqs = parsed.get("mcqs", []) if isinstance(parsed, dict) else []

            validated = [
                self._validate_mcq(q, event)
                for q in raw_mcqs
                if isinstance(q, dict)
            ]
            return [q for q in validated if q is not None][:count]

        except Exception as exc:
            logger.warning(
                "Configured AI provider MCQ generation failed for event %s: %s",
                event.id,
                exc,
            )
            return None

    def _validate_mcq(self, q: Dict[str, Any], event: Event) -> Optional[Dict[str, Any]]:
        """Validate MCQ structure and return cleaned version or None."""
        question = q.get("question", "").strip()
        options = q.get("options", [])
        correct = q.get("correct_answer", "").strip().upper()
        explanation = q.get("explanation", "").strip()

        if not question or len(options) != 4:
            return None
        if correct not in ("A", "B", "C", "D"):
            return None

        return {
            "question": question[:500],
            "options": [str(o)[:200] for o in options],
            "correct_answer": correct,
            "explanation": explanation[:500],
            "event_id": event.id,
        }

    def _generate_fallback_mcqs(
        self, event: Event, exam_id: Optional[str], count: int
    ) -> List[Dict[str, Any]]:
        """Deterministic fallback MCQ generation from stored event facts."""
        mcqs: List[Dict[str, Any]] = []

        title = event.title or ""
        domain = event.domain or "Technology"
        event_type = event.event_type or "event"
        summary = event.summary or ""

        # Stable seed for deterministic option ordering
        seed = int(hashlib.md5(f"{event.id}".encode()).hexdigest()[:8], 16)

        # Q1: Domain classification question
        all_domains = ["AI", "Technology", "Government", "Politics", "Education",
                       "Medical", "Science", "Economy", "Sports", "Environment",
                       "International", "Defence", "Engineering"]
        wrong_domains = [d for d in all_domains if d != domain]
        # Pick 3 deterministic wrong answers
        rng_offset = seed % max(1, len(wrong_domains))
        distractors = []
        for i in range(3):
            idx = (rng_offset + i * 3) % len(wrong_domains)
            distractors.append(wrong_domains[idx])

        options_raw = [domain] + distractors
        # Deterministic shuffle
        order = [(seed + i * 7) % 4 for i in range(4)]
        # Simple sort by hash to get stable order
        indexed = list(enumerate(options_raw))
        indexed.sort(key=lambda x: (seed + x[0] * 13) % 97)
        options_sorted = [item[1] for item in indexed]
        correct_idx = options_sorted.index(domain)
        correct_letter = chr(65 + correct_idx)

        mcqs.append({
            "question": f"Which domain does the following current affair belong to? \"{title[:120]}\"",
            "options": [f"{chr(65+i)}. {opt}" for i, opt in enumerate(options_sorted)],
            "correct_answer": correct_letter,
            "explanation": f"This event is classified under the '{domain}' domain based on its content and subject matter.",
            "event_id": event.id,
        })

        if len(mcqs) >= count:
            return mcqs[:count]

        # Q2: Event type question (if event_type is available)
        if event_type and event_type != "other":
            event_types = ["announcement", "agreement", "launch", "policy",
                           "discovery", "appointment", "acquisition", "event"]
            wrong_types = [t for t in event_types if t != event_type]
            type_distractors = []
            for i in range(3):
                idx = (seed + i * 5 + 1) % len(wrong_types)
                type_distractors.append(wrong_types[idx])

            type_options_raw = [event_type] + type_distractors
            type_indexed = list(enumerate(type_options_raw))
            type_indexed.sort(key=lambda x: (seed + x[0] * 17 + 3) % 89)
            type_sorted = [item[1] for item in type_indexed]
            type_correct_idx = type_sorted.index(event_type)
            type_correct_letter = chr(65 + type_correct_idx)

            mcqs.append({
                "question": f"What type of event is described: \"{title[:120]}\"?",
                "options": [f"{chr(65+i)}. {opt.capitalize()}" for i, opt in enumerate(type_sorted)],
                "correct_answer": type_correct_letter,
                "explanation": f"This event is categorized as a '{event_type}' based on its content describing a {event_type}.",
                "event_id": event.id,
            })

        if len(mcqs) >= count:
            return mcqs[:count]

        # Q3: Entity-based question (if entities exist)
        if hasattr(event, "event_entities") and event.event_entities:
            real_entities = [ee.entity for ee in event.event_entities if ee.entity]
            if real_entities:
                target_entity = real_entities[0]
                entity_name = target_entity.name
                entity_type = target_entity.entity_type

                decoy_names = ["World Economic Forum", "International Space Station",
                               "Central Bureau of Investigation", "National Green Tribunal",
                               "BRICS Development Bank", "ASEAN Secretariat"]
                decoy_names = [d for d in decoy_names if d.lower() != entity_name.lower()]
                ent_distractors = []
                for i in range(3):
                    idx = (seed + i * 11 + 2) % len(decoy_names)
                    ent_distractors.append(decoy_names[idx])

                ent_options_raw = [entity_name] + ent_distractors
                ent_indexed = list(enumerate(ent_options_raw))
                ent_indexed.sort(key=lambda x: (seed + x[0] * 19 + 7) % 83)
                ent_sorted = [item[1] for item in ent_indexed]
                ent_correct_idx = ent_sorted.index(entity_name)
                ent_correct_letter = chr(65 + ent_correct_idx)

                mcqs.append({
                    "question": f"Which of the following is mentioned in this current affair: \"{title[:100]}\"?",
                    "options": [f"{chr(65+i)}. {opt}" for i, opt in enumerate(ent_sorted)],
                    "correct_answer": ent_correct_letter,
                    "explanation": f"'{entity_name}' ({entity_type}) is directly mentioned in this event.",
                    "event_id": event.id,
                })

        return mcqs[:count]
