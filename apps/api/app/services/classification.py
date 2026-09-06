from abc import ABC, abstractmethod
from typing import Dict, List, Tuple
import re
from app.utils.hashing import normalize_text


class BaseClassifier(ABC):
    @abstractmethod
    def classify(self, title: str, content: str, default_domain: str = "Technology") -> str:
        pass


class KeywordDomainClassifier(BaseClassifier):
    """
    Rule/Keyword-based classifier with confidence score calculation.
    Supports 13 domains: AI, Technology, Politics, Government, Education,
    Medical, Engineering, Science, Economy, Sports, Environment, International, Defence.
    """

    DOMAIN_KEYWORDS: Dict[str, List[str]] = {
        "AI": [
            "ai", "artificial intelligence", "llm", "neural network", "gpt",
            "machine learning", "deep learning", "openai", "anthropic", "transformer",
            "claude", "gemini", "robotics", "generative ai", "large language model"
        ],
        "Technology": [
            "software", "hardware", "chip", "semiconductor", "cybersecurity",
            "cloud", "quantum computing", "apple", "google", "microsoft", "nvidia",
            "intel", "amd", "app", "startup", "gadget", "smartphone", "browser"
        ],
        "Politics": [
            "election", "vote", "parliament", "senate", "congress", "democrat",
            "republican", "campaign", "poll", "voter", "party", "candidate"
        ],
        "Government": [
            "regulation", "bill", "law", "court", "executive order", "federal",
            "agency", "sanction", "policy", "supreme court", "legislation", "ministry"
        ],
        "Education": [
            "university", "school", "curriculum", "students", "degree",
            "academic", "stem", "college", "professor", "education", "tuition"
        ],
        "Medical": [
            "health", "fda", "clinical", "pharma", "vaccine", "disease",
            "hospital", "therapy", "cancer", "medical", "doctor", "medicine", "virus"
        ],
        "Engineering": [
            "bridge", "infrastructure", "civil engineering", "mechanical",
            "aerospace", "circuit", "manufacturing", "semiconductor fab", "construction"
        ],
        "Science": [
            "nasa", "physics", "astronomy", "genetics", "biology", "chemist",
            "telescope", "discovery", "laboratory", "mars", "space", "exoplanet"
        ],
        "Economy": [
            "inflation", "fed", "federal reserve", "stock", "gdp", "revenue",
            "market", "trade", "tariff", "interest rate", "banking", "finance", "wall street"
        ],
        "Sports": [
            "olympics", "nfl", "nba", "fifa", "championship", "tournament",
            "match", "score", "football", "basketball", "soccer", "tennis", "athlete"
        ],
        "Environment": [
            "climate", "emissions", "renewable", "carbon", "solar", "wind energy",
            "wildfire", "disaster", "global warming", "biodiversity", "ocean"
        ],
        "International": [
            "treaty", "diplomacy", "un", "united nations", "summit", "foreign",
            "bilateral", "global", "ambassador", "geopolitics"
        ],
        "Defence": [
            "military", "army", "navy", "air force", "defense", "defence",
            "missile", "pentagon", "nato", "warfare", "soldier", "weapon"
        ]
    }

    def classify_with_confidence(self, title: str, content: str, default_domain: str = "Technology") -> Tuple[str, float]:
        combined_text = normalize_text(f"{title} {content}")

        scores: Dict[str, int] = {}
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            score = 0
            for kw in keywords:
                pattern = r"\b" + re.escape(kw) + r"\b"
                matches = len(re.findall(pattern, combined_text))
                if matches:
                    if kw in normalize_text(title):
                        score += matches * 3
                    else:
                        score += matches
            if score > 0:
                scores[domain] = score

        if not scores:
            final_domain = default_domain if default_domain in self.DOMAIN_KEYWORDS else "Technology"
            return final_domain, 0.50

        best_domain = max(scores, key=scores.get)
        top_score = scores[best_domain]
        total_score = sum(scores.values())

        # Confidence ratio calculation
        confidence = min(0.95, round(0.55 + (top_score / (total_score + 1)) * 0.40, 2))
        return best_domain, confidence

    def classify(self, title: str, content: str, default_domain: str = "Technology") -> str:
        domain, _ = self.classify_with_confidence(title, content, default_domain)
        return domain
