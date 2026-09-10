import re
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import httpx

from app.core.config import settings
from app.schemas.enrichment import EventEnrichment

logger = logging.getLogger("app")


class AIProvider(ABC):
    @abstractmethod
    def enrich_event(
        self,
        title: str,
        content: str,
        domain: str,
        reliability_score: float = 1.0
    ) -> Dict[str, Any]:
        """
        Enriches an event with summary, why_it_matters, importance_score,
        classification, confidence, and key entities.
        """
        pass

    @abstractmethod
    def generate_embedding(self, text: str) -> List[float]:
        """Generates embedding vector for semantic retrieval."""
        pass


class FallbackAIProvider(AIProvider):
    """
    Deterministic rule-based fallback AI provider.
    Ensures ingestion never fails even when external LLM API is unavailable or unconfigured.
    """

    KNOWN_ENTITIES = {
        # Countries / Regions
        "United States": "COUNTRY", "US": "COUNTRY", "USA": "COUNTRY",
        "United Kingdom": "COUNTRY", "UK": "COUNTRY", "India": "COUNTRY",
        "China": "COUNTRY", "Japan": "COUNTRY", "Germany": "COUNTRY",
        "France": "COUNTRY", "Canada": "COUNTRY", "Australia": "COUNTRY",
        "Ukraine": "COUNTRY", "Russia": "COUNTRY", "European Union": "ORGANIZATION",
        "EU": "ORGANIZATION", "UN": "ORGANIZATION", "United Nations": "ORGANIZATION",

        # Organizations & Tech Companies
        "NASA": "ORGANIZATION", "ISRO": "ORGANIZATION", "ESA": "ORGANIZATION",
        "Google": "ORGANIZATION", "Microsoft": "ORGANIZATION", "Apple": "ORGANIZATION",
        "OpenAI": "ORGANIZATION", "NVIDIA": "ORGANIZATION", "Meta": "ORGANIZATION",
        "Amazon": "ORGANIZATION", "BBC": "ORGANIZATION", "TechCrunch": "ORGANIZATION",
        "WHO": "ORGANIZATION", "World Health Organization": "ORGANIZATION",
        "IMF": "ORGANIZATION", "World Bank": "ORGANIZATION", "RBI": "ORGANIZATION",

        # Technologies & Concepts
        "Artificial Intelligence": "TECHNOLOGY", "AI": "TECHNOLOGY",
        "Machine Learning": "TECHNOLOGY", "Deep Learning": "TECHNOLOGY",
        "Quantum Computing": "TECHNOLOGY", "Semiconductor": "TECHNOLOGY",
        "Robotics": "TECHNOLOGY", "Cybersecurity": "TECHNOLOGY",
        "Climate Change": "CONCEPT", "Renewable Energy": "CONCEPT",
        "Inflation": "CONCEPT", "GDP": "CONCEPT", "Gross Domestic Product": "CONCEPT",
        "Artemis": "PROGRAM", "James Webb Space Telescope": "PROGRAM",
        "healthcare": "CONCEPT",
        "climate monitoring": "CONCEPT",
        "trade ministers": "ORGANIZATION",
        "customs": "CONCEPT",
        "championship": "EVENT",
        "tourism": "CONCEPT",
    }

    DOMAIN_KEYWORDS = {
        "technology": ("ai", "artificial intelligence", "software", "digital", "quantum", "semiconductor", "robot", "model", "healthcare", "analytics"),
        "science": ("science", "satellite", "climate", "research", "space", "telescope", "laboratory", "discovery", "monitoring"),
        "economy": ("economy", "economic", "trade", "commerce", "customs", "market", "revenue", "finance", "agreement"),
        "sports": ("sport", "championship", "league", "final", "match", "tournament", "attendance", "tourism"),
    }

    def _infer_domain(self, text: str, domain: str) -> str:
        if domain and domain.strip().lower() not in {"unknown", "auto"}:
            return domain
        lowered = text.lower()
        scores = {
            candidate: sum(lowered.count(keyword) for keyword in keywords)
            for candidate, keywords in self.DOMAIN_KEYWORDS.items()
        }
        best_domain, best_score = max(scores.items(), key=lambda item: item[1])
        return best_domain if best_score else "unknown"

    def _infer_event_type(self, text: str) -> str:
        lowered = text.lower()
        keyword_groups = (
            ("announcement", ("announce", "announced", "announces", "announcement", "revealed", "unveils", "unveiled")),
            ("agreement", ("agreement", "signed", "treaty", "framework", "deal", "accord")),
            ("launch", ("launch", "launched", "launches", "satellite", "rocket", "program")),
            ("acquisition", ("acquire", "acquisition", "bought", "acquired")),
            ("policy", ("policy", "regulation", "bill", "law")),
            ("discovery", ("discovery", "discovered", "breakthrough")),
            ("appointment", ("appointed", "appointment", "named")),
            ("event", ("event", "championship", "league", "final", "match", "tournament", "attendance")),
        )
        for event_type, keywords in keyword_groups:
            if any(keyword in lowered for keyword in keywords):
                return event_type
        return "other"

    def enrich_event(
        self,
        title: str,
        content: str,
        domain: str,
        reliability_score: float = 1.0
    ) -> Dict[str, Any]:
        text_full = f"{title}. {content}".strip()
        predicted_domain = self._infer_domain(text_full, domain)
        event_type = self._infer_event_type(text_full)

        # 1. Summary Generation (Concise, max 100 words)
        words = text_full.split()
        if len(words) > 80:
            summary = " ".join(words[:80]) + "..."
        else:
            summary = text_full

        # 2. Why it matters generation
        why_it_matters = (
            f"This development in {predicted_domain} carries significant operational, policy, and public interest implications. "
            f"Key stakeholders and domain analysts monitor these developments to evaluate long-term strategic impacts."
        )

        # 3. Heuristic Importance Scoring (0-100)
        lower_text = text_full.lower()
        signal_score = 0
        signal_score += 20 if predicted_domain in {"technology", "economy"} else 0
        signal_score += 10 if predicted_domain == "science" else 0
        signal_score += 10 if predicted_domain == "sports" else 0

        impact_terms = {
            "breakthrough": 10,
            "policy": 8,
            "agreement": 8,
            "launch": 10,
            "sanction": 9,
            "crisis": 8,
            "final": 6,
            "championship": 7,
            "record": 6,
            "healthcare": 7,
            "climate": 7,
            "trade": 6,
            "customs": 6,
            "tourism": 5,
            "announce": 5,
            "announces": 5,
            "revealed": 5,
        }
        for term, weight in impact_terms.items():
            if term in lower_text:
                signal_score += weight

        signal_score = min(signal_score, 70)
        final_score = int(round(45 + (signal_score * 0.5) + (reliability_score * 10)))
        final_score = max(0, min(100, final_score))

        # 4. Entity Extraction
        extracted_entities = []
        found_names = set()
        for name, ent_type in self.KNOWN_ENTITIES.items():
            pattern = r'\b' + re.escape(name) + r'\b'
            if re.search(pattern, text_full, re.IGNORECASE):
                normalized = " ".join(name.split()).lower()
                if normalized not in found_names:
                    extracted_entities.append({"name": name, "entity_type": ent_type})
                    found_names.add(normalized)

        # Capitalized word phrase fallback heuristic for Person/Organization
        capitalized_matches = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b', title)
        for cap in capitalized_matches[:3]:
            key = " ".join(cap.split()).lower()
            if key not in found_names and cap not in ["Current Affairs", "Flash Facts", "United States"]:
                extracted_entities.append({"name": cap, "entity_type": "ORGANIZATION"})
                found_names.add(key)

        return {
            "summary": summary,
            "why_it_matters": why_it_matters,
            "importance_score": final_score,
            "classification": predicted_domain,
            "classification_confidence": 0.90,
            "event_type": event_type,
            "entities": extracted_entities,
            "provider": "fallback",
            "used_fallback": True,
        }

    def generate_embedding(self, text: str) -> List[float]:
        # Pseudo-embedding fallback vector (length 128)
        import hashlib
        h = hashlib.sha256(text.encode("utf-8")).digest()
        return [round((b - 128) / 128.0, 4) for b in h[:32]] * 4


class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
        self.fallback = FallbackAIProvider()

    def enrich_event(
        self,
        title: str,
        content: str,
        domain: str,
        reliability_score: float = 1.0
    ) -> Dict[str, Any]:
        if not self.api_key:
            logger.warning("OpenAI API key missing. Using FallbackAIProvider.")
            return self.fallback.enrich_event(title, content, domain, reliability_score)

        system_prompt = (
            "You are an expert current affairs analyst for FlashFacts intelligence platform. "
            "Analyze the given news document and return a valid JSON object with the following fields:\n"
            "- summary: Concise summary of the event (maximum 90 words).\n"
            "- why_it_matters: Explanation of the practical, policy, economic, or public significance.\n"
            "- importance_score: Integer from 0 to 100 based on public impact, economic scale, and significance.\n"
            "- classification: Primary domain (choose from: AI, Technology, Politics, Government, Education, Medical, Engineering, Science, Economy, Sports, Environment, International, Defence).\n"
            "- event_type: One of announcement, launch, agreement, event, appointment, policy, discovery, acquisition, or other.\n"
            "- classification_confidence: Float from 0.0 to 1.0.\n"
            "- entities: List of objects with 'name' and 'entity_type' (must be one of PERSON, ORGANIZATION, COUNTRY, TECHNOLOGY, PROGRAM, CONCEPT).\n"
            "Return ONLY raw valid JSON."
        )

        user_prompt = f"Title: {title}\nDomain Hint: {domain}\nContent: {content[:settings.AI_MAX_INPUT_CHARS]}"

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.2,
                "response_format": {"type": "json_object"},
            }

            with httpx.Client(timeout=15.0) as client:
                res = client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    content_str = data["choices"][0]["message"]["content"]
                    parsed = json.loads(content_str)

                    validated = EventEnrichment.model_validate({
                        "summary": parsed.get("summary", title),
                        "why_it_matters": parsed.get("why_it_matters", "Significant event in domain."),
                        "importance_score": int(parsed.get("importance_score", 50)),
                        "classification": parsed.get("classification", domain),
                        "classification_confidence": float(parsed.get("classification_confidence", 0.95)),
                        "event_type": parsed.get("event_type"),
                        "entities": parsed.get("entities", []),
                        "provider": "openai",
                        "used_fallback": False,
                    })
                    return validated.model_dump()
                else:
                    logger.warning(f"OpenAI API returned status {res.status_code}. Using fallback.")
                    return self.fallback.enrich_event(title, content, domain, reliability_score)
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}. Falling back to rule-based provider.")
            return self.fallback.enrich_event(title, content, domain, reliability_score)

    def generate_embedding(self, text: str) -> List[float]:
        return self.fallback.generate_embedding(text)


def get_ai_provider() -> AIProvider:
    provider_type = getattr(settings, "AI_PROVIDER", "fallback").lower()
    api_key = getattr(settings, "AI_API_KEY", "")
    model = getattr(settings, "AI_MODEL", "gpt-4o-mini")

    if provider_type == "openai" and api_key:
        return OpenAIProvider(api_key=api_key, model=model)

    return FallbackAIProvider()
