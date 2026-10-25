"""
Exam Classification Service for FlashFacts.

Classifies events for Exam Relevance, Exam Importance, Geography Level,
Exam Facts, and Question Angles.
"""
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.exam_intelligence import (
    EventExamMetadata,
    EventExamRelevance,
    EXAM_TYPES,
    RELEVANCE_LEVELS,
    IMPORTANCE_LEVELS,
    GEOGRAPHIC_LEVELS,
)
from app.utils.hashing import fix_mojibake

logger = logging.getLogger("app")

# ─── Geography keyword lists ───────────────────────────────────────────────────

TN_KEYWORDS = [
    "tamil nadu", "tn", "chennai", "coimbatore", "madurai", "tiruchirappalli",
    "salem", "tirunelveli", "thanjavur", "vellore", "thoothukudi", "dindigul",
    "kovai", "madras", "stalin", "mk stalin", "tnpsc",
]

# keyword → canonical 2-letter state code
STATE_CODE_MAP = {
    "tamil nadu": "TN",
    "kerala": "KL",
    "karnataka": "KA",
    "andhra pradesh": "AP",
    "telangana": "TS",
    "maharashtra": "MH",
    "delhi": "DL",
    "new delhi": "DL",
    "uttar pradesh": "UP",
    "west bengal": "WB",
    "gujarat": "GJ",
    "rajasthan": "RJ",
    "madhya pradesh": "MP",
    "bihar": "BR",
    "odisha": "OD",
    "orissa": "OD",
    "punjab": "PB",
    "haryana": "HR",
    "assam": "AS",
}

# canonical code → display name
STATE_DISPLAY_MAP = {
    "TN": "Tamil Nadu",
    "KL": "Kerala",
    "KA": "Karnataka",
    "AP": "Andhra Pradesh",
    "TS": "Telangana",
    "MH": "Maharashtra",
    "DL": "Delhi",
    "UP": "Uttar Pradesh",
    "WB": "West Bengal",
    "GJ": "Gujarat",
    "RJ": "Rajasthan",
    "MP": "Madhya Pradesh",
    "BR": "Bihar",
    "OD": "Odisha",
    "PB": "Punjab",
    "HR": "Haryana",
    "AS": "Assam",
    "UT": "Union Territory",
}

UT_KEYWORDS = [
    "puducherry", "chandigarh", "ladakh", "jammu", "kashmir", "andaman",
]

INTERNATIONAL_KEYWORDS = [
    "usa", "united states", "uk", "china", "japan", "russia",
    "un", "g20", "brics", "global", "world",
]


# ─── Service ───────────────────────────────────────────────────────────────────

class ExamClassificationService:
    """Service to generate structured Exam Intelligence metadata for Events."""

    def __init__(self, db: Session):
        self.db = db

    # ── Public entry point ────────────────────────────────────────────────────

    def classify_event(
        self, event: Event
    ) -> Tuple[EventExamMetadata, List[EventExamRelevance]]:
        """
        Classify an event into structured Exam Intelligence parameters
        and persist EventExamMetadata & EventExamRelevance records.
        """
        title = event.title or ""
        summary = event.summary or ""
        domain = event.domain or "Technology"
        event_type = event.event_type or "event"
        imp_score = event.importance_score or 50

        combined_text = f"{title} {summary}".lower()

        # 1. Geographic Classification
        geo_level, primary_state = self._determine_geography(combined_text)

        # 2. Exam Importance Classification
        exam_importance = self._determine_exam_importance(imp_score, combined_text, event_type, domain=domain)

        # 3. Why It Matters
        why_it_matters = event.why_it_matters or self._generate_why_it_matters(
            title, domain, primary_state, event_type
        )

        # 4. Exam Facts & Question Angles
        exam_facts = self._extract_exam_facts(event, title, summary, domain, primary_state)
        question_angles = self._extract_question_angles(event, title, summary, domain, event_type)

        # 5. Relevance Factors
        relevance_factors = {
            "syllabus_relevance": min(100, imp_score + 15),
            "factual_question_potential": 85 if len(exam_facts) >= 3 else 60,
            "government_significance": (
                90 if domain in ("Government", "Politics", "Economy") else 50
            ),
            "national_importance": 90 if geo_level == "NATIONAL" else 60,
            "state_importance": (
                95 if primary_state == "TN" else (80 if primary_state else 40)
            ),
            "recentness": 100,
        }

        # Save or update EventExamMetadata
        meta = (
            self.db.query(EventExamMetadata)
            .filter(EventExamMetadata.event_id == event.id)
            .first()
        )
        if not meta:
            meta = EventExamMetadata(event_id=event.id)

        meta.exam_importance = exam_importance
        meta.geographic_level = geo_level
        meta.primary_state = primary_state
        meta.why_it_matters = why_it_matters
        meta.exam_facts = exam_facts
        meta.question_angles = question_angles
        meta.relevance_factors = relevance_factors

        self.db.add(meta)

        # 6. Exam Relevance for all exam types
        relevances: List[EventExamRelevance] = []
        for exam_type in EXAM_TYPES:
            rel_score, rel_level, explanation = self._evaluate_exam_relevance(
                exam_type, domain, event_type, geo_level, primary_state, combined_text, imp_score
            )
            rel_obj = (
                self.db.query(EventExamRelevance)
                .filter(
                    EventExamRelevance.event_id == event.id,
                    EventExamRelevance.exam_type == exam_type,
                )
                .first()
            )
            if not rel_obj:
                rel_obj = EventExamRelevance(event_id=event.id, exam_type=exam_type)

            rel_obj.relevance_level = rel_level
            rel_obj.relevance_score = rel_score
            rel_obj.explanation = explanation
            self.db.add(rel_obj)
            relevances.append(rel_obj)

        self.db.commit()
        self.db.refresh(meta)
        return meta, relevances

    # ── Geography ─────────────────────────────────────────────────────────────

    def _determine_geography(self, text_lower: str) -> Tuple[str, Optional[str]]:
        """
        Return (geographic_level, primary_state_code).

        Priority: TN_STATE > STATE > UT > INTERNATIONAL > NATIONAL
        """
        # 1. Tamil Nadu detection
        for kw in TN_KEYWORDS:
            if re.search(rf"\b{re.escape(kw)}\b", text_lower):
                return "TN_STATE", "TN"

        # 2. Other Indian state detection
        for kw, state_code in STATE_CODE_MAP.items():
            if re.search(rf"\b{re.escape(kw)}\b", text_lower):
                return "STATE", state_code

        # 3. Union Territory detection
        for kw in UT_KEYWORDS:
            if re.search(rf"\b{re.escape(kw)}\b", text_lower):
                return "STATE", "UT"

        # 4. International detection
        for kw in INTERNATIONAL_KEYWORDS:
            if re.search(rf"\b{re.escape(kw)}\b", text_lower):
                return "INTERNATIONAL", None

        # 5. Default — national
        return "NATIONAL", None

    # ── Importance ────────────────────────────────────────────────────────────

    def _determine_exam_importance(
        self, imp_score: int, text_lower: str, event_type: str, domain: str = ""
    ) -> str:
        if domain == "Crime":
            landmark_legal_words = [
                "supreme court", "high court", "constitution bench", "constitutional bench",
                "landmark judgment", "law commission", "criminal law reform",
                "bharatiya nyaya sanhita", "bns", "ipc amendment",
                "உச்ச நீதிமன்றம்", "உயர் நீதிமன்றம்", "அரசியலமைப்பு", "நீதிபதிகள் அமர்வு",
                "வரலாற்று சிறப்புமிக்க தீர்ப்பு", "சட்டத்திருத்தம்", "சட்ட திருத்தம்"
            ]
            if not any(w in text_lower for w in landmark_legal_words):
                return "BACKGROUND"
        """Map score + signals → MUST_KNOW | IMPORTANT | USEFUL | BACKGROUND."""
        high_signal_words = [
            "rbi", "budget", "isro", "constitution", "supreme court", "launch",
        ]
        if imp_score >= 75 or any(w in text_lower for w in high_signal_words):
            return "MUST_KNOW"
        elif imp_score >= 55 or event_type in ("policy", "appointment", "agreement"):
            return "IMPORTANT"
        elif imp_score >= 35:
            return "USEFUL"
        else:
            return "BACKGROUND"

    # ── Why It Matters ────────────────────────────────────────────────────────

    def _generate_why_it_matters(
        self, title: str, domain: str, state: Optional[str], event_type: str
    ) -> str:
        if state == "TN":
            return (
                f"High-priority state current affair for TNPSC examinations "
                f"under the {domain} syllabus."
            )
        elif domain == "Economy":
            return (
                "Crucial economic update relevant for Banking, UPSC, and SSC "
                "General Awareness questions."
            )
        elif domain == "Science":
            return (
                "Key scientific/technological advancement frequently tested in "
                "UPSC CSE and SSC Science sections."
            )
        elif domain == "Government":
            return (
                "Important government policy/scheme update essential for polity "
                "and governance exam papers."
            )
        else:
            return (
                f"Relevant {domain.lower()} event for general awareness across "
                "competitive examinations."
            )

    # ── Exam Facts ────────────────────────────────────────────────────────────

    def _extract_exam_facts(
        self,
        event: Event,
        title: str,
        summary: str,
        domain: str,
        state: Optional[str],
    ) -> List[Dict[str, str]]:
        """Extract structured facts from an event for exam revision."""
        facts: List[Dict[str, str]] = []

        if domain:
            facts.append({"label": "Domain / Category", "value": domain})

        if state:
            state_display = STATE_DISPLAY_MAP.get(state, state)
            facts.append({"label": "State / Region", "value": state_display})
        else:
            facts.append({"label": "Country / Scope", "value": "India / Global"})

        if event.event_type:
            facts.append({"label": "Event Type", "value": event.event_type.capitalize()})

        if hasattr(event, "event_entities") and event.event_entities:
            orgs = [
                ee.entity.name
                for ee in event.event_entities
                if ee.entity and ee.entity.entity_type == "ORGANIZATION"
            ]
            if orgs:
                facts.append({"label": "Key Organization", "value": ", ".join(orgs[:3])})

        facts.append({
            "label": "Event Date",
            "value": event.event_date.isoformat() if event.event_date else "",
        })
        return facts

    # ── Question Angles ───────────────────────────────────────────────────────

    def _extract_question_angles(
        self,
        event: Event,
        title: str,
        summary: str,
        domain: str,
        event_type: str,
    ) -> List[str]:
        """Return question-worthy factual angles for exam aspirants."""
        angles: List[str] = ["Location and spatial context of event"]

        if domain in ("Government", "Politics"):
            angles.append("Policy objective and implementation ministry")
            angles.append("Constitutional or statutory basis")
        elif domain == "Economy":
            angles.append("Regulatory body (e.g. RBI/SEBI) policy impact")
            angles.append("Financial allocation or economic index impact")
        elif domain == "Science":
            angles.append("Scientific agency / organisation involved")
            angles.append("Technology or mission objective")

        if event_type == "appointment":
            angles.append("Name of appointed person and tenure/office")
        elif event_type == "launch":
            angles.append("Vehicle / platform and launching entity")

        return angles

    # ── Exam Relevance ────────────────────────────────────────────────────────

    def _evaluate_exam_relevance(
        self,
        exam_type: str,
        domain: str,
        event_type: str,
        geo_level: str,
        state: Optional[str],
        text_lower: str,
        imp_score: int,
    ) -> Tuple[int, str, str]:
        """Return (score 0-100, level string, explanation string)."""
        if domain == "Crime":
            landmark_legal_words = [
                "supreme court", "high court", "constitution bench", "constitutional bench",
                "landmark judgment", "law commission", "criminal law reform",
                "bharatiya nyaya sanhita", "bns", "ipc amendment",
                "உச்ச நீதிமன்றம்", "உயர் நீதிமன்றம்", "அரசியலமைப்பு", "நீதிபதிகள் அமர்வு",
                "வரலாற்று சிறப்புமிக்க தீர்ப்பு", "சட்டத்திருத்தம்", "சட்ட திருத்தம்"
            ]
            has_landmark_legal = any(w in text_lower for w in landmark_legal_words)
            if not has_landmark_legal:
                return 10, "NOT_RELEVANT", f"Routine local incident/crime without broader {exam_type} competitive exam or syllabus applicability."

        score = 40  # baseline

        if exam_type == "TNPSC":
            if geo_level == "TN_STATE" or state == "TN":
                score += 45
            elif domain in ("Government", "Politics", "Economy", "Environment"):
                score += 25

        elif exam_type == "UPSC":
            if domain in ("Environment", "International", "Economy", "Government", "Science"):
                score += 35
            if imp_score >= 70:
                score += 15

        elif exam_type == "SSC":
            if domain in ("Government", "Sports", "Science", "Economy"):
                score += 30
            if event_type in ("appointment", "award", "launch"):
                score += 20

        elif exam_type == "BANKING":
            if domain == "Economy" or any(
                w in text_lower for w in ["bank", "rbi", "finance", "gdp", "interest"]
            ):
                score += 50
            else:
                score -= 20

        elif exam_type == "RAILWAY":
            if any(
                w in text_lower
                for w in ["railway", "rrb", "transport", "train", "infrastructure"]
            ):
                score += 45
            elif domain in ("Government", "Sports", "Science"):
                score += 20

        elif exam_type == "GENERAL_GOVT":
            if domain in ("Government", "Economy", "Science", "Education"):
                score += 30

        score = max(10, min(100, score))

        if score >= 80:
            level = "VERY_HIGH"
            explanation = f"Extremely high yield for {exam_type} core syllabus."
        elif score >= 60:
            level = "HIGH"
            explanation = f"High relevance for {exam_type} General Studies / Current Affairs."
        elif score >= 40:
            level = "MEDIUM"
            explanation = f"Moderate relevance for {exam_type} general awareness."
        elif score >= 25:
            level = "LOW"
            explanation = f"Secondary background relevance for {exam_type}."
        else:
            level = "NOT_RELEVANT"
            explanation = f"Limited applicability for {exam_type} examinations."

        return score, level, explanation
