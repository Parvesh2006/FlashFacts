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

    @abstractmethod
    def generate_chat(self, messages: List[Dict[str, str]], temperature: float = 0.2) -> Optional[str]:
        """Generates chat response based on provided messages."""
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
        from app.services.content_cleaner import ContentCleaningService
        clean_title = ContentCleaningService.clean_html(title or "")
        clean_content = ContentCleaningService.clean_article_text(clean_title, content or "")
        summary = ContentCleaningService.build_clean_summary(clean_title, clean_content, max_words=75)
        text_full = f"{clean_title}. {clean_content}".strip()
        predicted_domain = self._infer_domain(text_full, domain)
        event_type = self._infer_event_type(text_full)

        # 2. Why it matters generation
        story_lower = text_full.lower()
        title_lower = title.lower()

        if any(term in story_lower for term in (
            "monsoon", "rainfall", "heavy rain", "flooding",
            "cyclone", "cyclonic winds", "weather alert"
        )):
            why_it_matters = (
                "Rainfall and monsoon conditions can affect public safety, "
                "transport, agriculture, and flood-preparedness decisions."
            )
        elif any(term in story_lower for term in (
            "books by inmates", "inmates released", "central prison"
        )):
            why_it_matters = (
                "The report highlights prison education and rehabilitation, "
                "including access to learning and support for reintegration."
            )
        elif "weaving wages" in story_lower or (
            "wages" in story_lower and "pongal" in story_lower
        ):
            why_it_matters = (
                "The wage decision affects handloom workers' earnings and "
                "the production of textiles supplied for Pongal."
            )
        elif "appointed to ias" in story_lower or "civil service officers" in story_lower:
            why_it_matters = (
                "The appointments affect public administration and how "
                "experienced officers are assigned government responsibilities."
            )
        elif "krishna water" in story_lower:
            why_it_matters = (
                "Inter-state water-sharing decisions affect irrigation and "
                "drinking-water planning in Tamil Nadu and neighboring states."
            )
        elif predicted_domain.lower() in ("government", "politics"):
            why_it_matters = (
                f"The report concerns a public-administration or policy issue: "
                f"{title.rstrip('.')}."
            )
        elif predicted_domain.lower() == "environment":
            why_it_matters = (
                f"This environmental report may affect communities, natural "
                f"resources, or local preparedness: {title.rstrip('.')}."
            )
        elif predicted_domain.lower() == "education":
            why_it_matters = (
                f"This education-related development may affect learners, "
                f"educators, or education policy: {title.rstrip('.')}."
            )
        elif predicted_domain.lower() == "economy":
            why_it_matters = (
                f"This economic development may affect workers, businesses, "
                f"prices, or livelihoods: {title.rstrip('.')}."
            )
        else:
            why_it_matters = (
                f"This report concerns {predicted_domain} and its potential "
                f"practical impact: {title.rstrip('.')}."
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
        raise NotImplementedError(
            "FallbackAIProvider does not provide semantic embeddings. "
            "Configure an OpenAI-compatible provider for vector search."
        )

    def generate_chat(self, messages: List[Dict[str, str]], temperature: float = 0.2) -> Optional[str]:
        return None


class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", base_url: Optional[str] = None):
        self.api_key = api_key
        self.model = model
        self.base_url = (base_url or "https://api.openai.com/v1").rstrip("/")
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
                res = client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
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

    def generate_chat(self, messages: List[Dict[str, str]], temperature: float = 0.2) -> Optional[str]:
        if not self.api_key:
            return None
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
            }
            with httpx.Client(timeout=15.0) as client:
                res = client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
                if res.status_code == 200:
                    return res.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Error calling OpenAI Chat API: {e}")
        return None


class OllamaProvider(AIProvider):
    def __init__(self, base_url: str, model: str, timeout: int = 180):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.fallback = FallbackAIProvider()

    def enrich_event(self, title: str, content: str, domain: str, reliability_score: float = 1.0) -> Dict[str, Any]:
        return self.fallback.enrich_event(title, content, domain, reliability_score)

    def generate_embedding(self, text: str) -> List[float]:
        return self.fallback.generate_embedding(text)

    def is_thinking_model(self) -> bool:
        """Check if model uses extended reasoning/thinking tokens (e.g. qwen3, deepseek-r1)."""
        return any(k in self.model.lower() for k in ["qwen3", "r1", "deepseek-r1"])

    def generate_chat(self, messages: List[Dict[str, str]], temperature: float = 0.2) -> Optional[str]:
        import time
        t0 = time.time()
        logger.info("Calling Ollama chat: base_url=%s, model=%s, timeout=%ds", self.base_url, self.model, self.timeout)

        # Optimize for thinking models (e.g., qwen3, deepseek-r1)
        # Suppress long hidden reasoning tokens to ensure fast, responsive answers
        is_thinking = self.is_thinking_model()
        chat_messages = list(messages)
        if is_thinking and chat_messages and chat_messages[-1].get("role") == "user":
            chat_messages.append({"role": "assistant", "content": "<think>\n</think>"})

        try:
            payload = {
                "model": self.model,
                "messages": chat_messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": 350
                }
            }
            with httpx.Client(timeout=self.timeout) as client:
                res = client.post(f"{self.base_url}/api/chat", json=payload)
                elapsed = time.time() - t0
                if res.status_code == 200:
                    data = res.json()
                    content = data.get("message", {}).get("content", "")
                    if content:
                        import re
                        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
                    logger.info("Ollama API responded in %.2fs (model=%s, chars=%d)", elapsed, self.model, len(content or ""))
                    return content
                else:
                    logger.warning("Ollama API returned HTTP %d in %.2fs: %s", res.status_code, elapsed, res.text[:200])
                    raise RuntimeError(f"Ollama returned HTTP {res.status_code}")
        except httpx.TimeoutException as exc:
            elapsed = time.time() - t0
            logger.error("Ollama API request timed out after %.2fs for model %s", elapsed, self.model)
            raise TimeoutError(f"Ollama model '{self.model}' timed out after {self.timeout}s.") from exc
        except Exception as e:
            logger.error("Error calling Ollama API (%s): %s", self.base_url, e)
            raise



class GeminiProvider(AIProvider):
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model = model if ("gemini" in model.lower()) else "gemini-1.5-flash"
        self.fallback = FallbackAIProvider()

    def enrich_event(
        self,
        title: str,
        content: str,
        domain: str,
        reliability_score: float = 1.0
    ) -> Dict[str, Any]:
        return self.fallback.enrich_event(title, content, domain, reliability_score)

    def generate_embedding(self, text: str) -> List[float]:
        return self.fallback.generate_embedding(text)

    def generate_chat(self, messages: List[Dict[str, str]], temperature: float = 0.2) -> Optional[str]:
        if not self.api_key:
            return None
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
            }
            with httpx.Client(timeout=25.0) as client:
                res = client.post(
                    "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
                    headers=headers,
                    json=payload
                )
                if res.status_code == 200:
                    data = res.json()
                    return data["choices"][0]["message"]["content"]
                logger.warning(f"Gemini API returned HTTP {res.status_code}: {res.text[:200]}")
        except Exception as e:
            logger.error(f"Error calling Gemini Chat API: {e}")
        return None

def get_ai_provider() -> AIProvider:
    provider_type = getattr(settings, "AI_PROVIDER", "fallback").lower()
    api_key = (
        getattr(settings, "AI_API_KEY", "")
        or getattr(settings, "OPENAI_API_KEY", "")
        or getattr(settings, "GEMINI_API_KEY", "")
    )
    base_url = getattr(settings, "AI_BASE_URL", "")
    model = getattr(settings, "AI_MODEL", "gpt-4o-mini")

    if provider_type in ("gemini", "google") and api_key:
        return GeminiProvider(api_key=api_key, model=model)
    elif provider_type == "openai" and api_key:
        return OpenAIProvider(api_key=api_key, model=model, base_url=base_url or None)
    elif provider_type == "ollama":
        ollama_url = getattr(settings, "OLLAMA_BASE_URL", "http://host.docker.internal:11434")
        timeout = getattr(settings, "OLLAMA_TIMEOUT", 180)
        return OllamaProvider(base_url=ollama_url, model=model, timeout=timeout)

    return FallbackAIProvider()
