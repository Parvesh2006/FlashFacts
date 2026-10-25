from abc import ABC, abstractmethod
from typing import Dict, List, Tuple
import re
from app.utils.hashing import normalize_text


class BaseClassifier(ABC):
    @abstractmethod
    def classify(self, title: str, content: str, default_domain: str = "Government") -> str:
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
            "intel", "amd", "app", "startup", "gadget", "smartphone", "browser",
            "தொழில்நுட்பம்"
        ],
        "Politics": [
            "election", "vote", "parliament", "senate", "congress", "democrat",
            "republican", "campaign", "poll", "voter", "party", "candidate",
            "தேர்தல்", "வாக்காளர்", "பாஜக", "காங்கிரஸ்", "திமுக", "அதிமுக", "கட்சி",
            "பிரேமலதா", "விஜயகாந்த்", "ராகுல் காந்தி", "சீமான்", "எடப்பாடி", "ஸ்டாலின்", "பிரதமர் மோடி"
        ],
        "Government": [
            "regulation", "bill", "law", "court", "executive order", "federal",
            "agency", "sanction", "policy", "supreme court", "legislation", "ministry", "patta", "upholds", "inmates", "prison", "jail", "tribunal", "judgment", "judgement", "high court",
            "அரசு", "அரசாணை", "திட்டம்", "நீதிமன்றம்", "உயர் நீதிமன்றம்", "உச்ச நீதிமன்றம்",
            "காவல்துறை", "சிறை", "தீர்ப்பு", "பேருந்து", "கட்டணம்", "அமைச்சரவை", "ஆணையம்", "விசாரணை"
        ],
        "Education": [
            "university", "school", "curriculum", "students", "degree",
            "academic", "stem", "college", "professor", "education", "tuition",
            "பள்ளி", "கல்லூரி", "பல்கலைக்கழகம்", "மாணவர்", "மாணவர்கள்", "தேர்வு", "கல்வி", "குடிமைப் பணித் தேர்வு"
        ],
        "Medical": [
            "health", "fda", "clinical", "pharma", "vaccine", "disease",
            "hospital", "therapy", "cancer", "medical", "doctor", "medicine", "virus",
            "மருத்துவம்", "மருத்துவமனை", "தடுப்பூசி", "சிகிச்சை", "நோய்"
        ],
        "Engineering": [
            "bridge", "infrastructure", "civil engineering", "mechanical",
            "aerospace", "circuit", "manufacturing", "semiconductor fab", "construction",
            "கட்டுமானம்", "பொறியியல்", "பாலம்"
        ],
        "Science": [
            "nasa", "physics", "astronomy", "genetics", "biology", "chemist",
            "telescope", "discovery", "laboratory", "mars", "space", "exoplanet",
            "விண்கலம்", "இஸ்ரோ", "நாசா", "செயற்கைக்கோள்", "ராக்கெட்", "அறிவியல்"
        ],
        "Economy": [
            "inflation", "fed", "federal reserve", "stock", "gdp", "revenue",
            "market", "trade", "tariff", "interest rate", "banking", "finance", "wall street",
            "தங்கம் விலை", "பொருளாதாரம்", "பங்குச்சந்தை", "வங்கி", "விலை உயர்வு", "ரூபாய்", "வரி", "ஜிடிபி", "பட்ஜெட்", "பணவீக்கம்"
        ],
        "Sports": [
            "olympics", "nfl", "nba", "fifa", "championship", "tournament",
            "match", "score", "football", "basketball", "soccer", "tennis", "athlete",
            "கிரிக்கெட்", "விளையாட்டு", "வெள்ளி வென்று", "தங்கம் வென்று", "மல்யுத்தம்", "போட்டி", "அணி அறிவிப்பு", "கோப்பை", "ரன்கள்", "விக்கெட்", "சாம்பியன்"
        ],
        "Environment": [
            "climate", "emissions", "renewable", "carbon", "solar", "wind energy",
            "wildfire", "disaster", "global warming", "biodiversity", "ocean", "rain", "rainfall", "monsoon", "flood", "flooding", "weather", "cyclone", "cyclonic", "storm", "drought", "imd", "meteorological",
            "மழை", "வெள்ளம்", "புயல்", "பருவமழை", "வானிலை", "சுற்றுச்சூழல்", "காடு"
        ],
        "International": [
            "treaty", "diplomacy", "un", "united nations", "summit", "foreign",
            "bilateral", "global", "ambassador", "geopolitics"
        ],
        "Defence": [
            "military", "army", "navy", "air force", "defense", "defence",
            "missile", "pentagon", "nato", "warfare", "soldier", "weapon",
            "ராணுவம்", "படை", "ஏவுகணை"
        ],
        "Crime": [
            "theft", "stolen", "stealing", "robbery", "robbed", "burglary", "burglar",
            "thief", "extortion", "snatching", "chain snatching", "shoplifting", "pickpocket",
            "murder", "murdered", "homicide", "cheated", "tricking", "swindled", "fraud",
            "conman", "arrested for stealing", "fir registered", "police arrested",
            "local police", "tricking a mobile-shop employee",
            "திருட்டு", "திருடி", "கொள்ளை", "கொள்ளையடித்த", "கொலை", "மோசடி",
            "ஏமாற்றி", "பறிப்பு", "செயின் பறிப்பு", "பிக்பாக்கெட்", "மர்ம நபர்",
            "கைது", "கைதானார்", "கைது செய்யப்பட்டார்", "போலீசார் வழக்குப்பதிவு",
            "போலீசார் வழக்கு பதிவு", "போலீசார் விசாரணை"
        ],
    }

    def classify_with_confidence(self, title: str, content: str, default_domain: str = "Government") -> Tuple[str, float]:
        combined_text = normalize_text(f"{title} {content}")
        title_lower = normalize_text(title)

        # High-priority headline rules prevent unrelated keyword matches
        # in long article bodies from dominating the classification.
        title_rules = [
            ("Government", (
                "supreme court", "high court", "constitution bench", "constitutional bench",
                "landmark judgment", "law commission", "criminal law reform",
                "bharatiya nyaya sanhita", "bns", "ipc amendment", "legal reform",
                "உச்ச நீதிமன்றம்", "உயர் நீதிமன்றம்", "அரசியலமைப்பு", "நீதிபதிகள் அமர்வு",
                "வரலாற்று சிறப்புமிக்க தீர்ப்பு", "வரலாற்று தீர்ப்பு", "சட்டத்திருத்தம்", "சட்ட திருத்தம்", "குற்றவியல் சட்டம்",
                "appointed to ias", "civil service officers",
                "state civil service", "weaving wages",
                "seeks krishna water", "krishna water",
                "books by inmates", "inmates released",
                "central prison"
            )),
            ("Crime", (
                "stealing", "stolen", "theft", "robbery", "burglary", "chain snatching",
                "tricking", "cheated", "swindled", "snatching",
                "திருட்டு", "கொள்ளை", "ஏமாற்றி", "செயின் பறிப்பு", "பிக்பாக்கெட்",
                "4 போன்கள்", "செல்போன் கடை ஊழியரை ஏமாற்றி"
            )),
            ("Environment", (
                "monsoon", "heavy rain", "rainfall", "cyclone", "cyclonic",
                "flooding", "flood", "drought", "storm"
            )),
        ]
        for rule_domain, phrases in title_rules:
            if any(phrase in title_lower for phrase in phrases):
                return rule_domain, 0.88

        scores: Dict[str, int] = {}
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            score = 0
            for kw in keywords:
                if any(ord(c) > 127 for c in kw):
                    norm_kw = normalize_text(kw)
                    if norm_kw and norm_kw in combined_text:
                        matches = combined_text.count(norm_kw)
                        if norm_kw in normalize_text(title):
                            score += matches * 3
                        else:
                            score += matches
                else:
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
            domain_map = {
                "Tamil Nadu": "Government",
                "National": "Government",
                "Science & Technology": "Technology",
                "Geography": "Environment",
                "General News": "Technology",
                "General": "Technology",
            }
            mapped_default = domain_map.get(default_domain, default_domain)
            final_domain = mapped_default if mapped_default in self.DOMAIN_KEYWORDS else "Government"
            return final_domain, 0.50

        best_domain = max(scores, key=scores.get)
        top_score = scores[best_domain]
        total_score = sum(scores.values())

        # Confidence ratio calculation
        confidence = min(0.95, round(0.55 + (top_score / (total_score + 1)) * 0.40, 2))
        return best_domain, confidence

    def classify(self, title: str, content: str, default_domain: str = "Government") -> str:
        domain, _ = self.classify_with_confidence(title, content, default_domain)
        return domain
