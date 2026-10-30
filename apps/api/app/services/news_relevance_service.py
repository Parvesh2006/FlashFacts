"""
FlashFacts Syllabus-Based Exam Relevance and News Quality Service.

Evaluates every news article/event against competitive examination syllabi
(TNPSC Group 4, TNPSC Group 2, UPSC CSE, SSC CGL, RRB, Banking)
to ensure feeds contain strictly exam-relevant current affairs, while excluding
entertainment gossip, routine local crimes, partisan political disputes,
ordinary corporate announcements, and viral stories.
"""

import re
import unicodedata
from typing import Dict, Any, List, Optional
from app.utils.hashing import normalize_text
from app.services.content_cleaner import ContentCleaningService


class ExamRelevanceResult:
    def __init__(
        self,
        is_eligible: bool,
        relevance_score: int,
        syllabus_topic: str,
        inclusion_reason: str,
        rejection_reason: Optional[str] = None,
        signals: Optional[List[str]] = None,
    ):
        self.is_eligible = is_eligible
        self.relevance_score = max(0, min(100, relevance_score))
        self.syllabus_topic = syllabus_topic
        self.inclusion_reason = inclusion_reason
        self.rejection_reason = rejection_reason
        self.signals = signals or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_eligible": self.is_eligible,
            "relevance_score": self.relevance_score,
            "syllabus_topic": self.syllabus_topic,
            "inclusion_reason": self.inclusion_reason,
            "rejection_reason": self.rejection_reason,
            "signals": self.signals,
        }


def _normalize_indic_text(s: str) -> str:
    """Normalizes Indic/Tamil text into canonical NFC form and removes zero-width characters."""
    if not s:
        return ""
    s = unicodedata.normalize("NFC", s)
    s = re.sub(r"[\u200b-\u200d\ufeff]", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip().lower()


def _matches_keyword(kw: str, text: str, text_indic: Optional[str] = None) -> bool:
    """Matches a keyword using word boundaries for ASCII/Latin and exact phrase for Indic."""
    if not kw or not text:
        return False
    kw_clean = kw.strip()
    # If purely ASCII, require word boundaries
    if all(ord(c) < 128 for c in kw_clean):
        pattern = r"\b" + re.escape(kw_clean.lower()) + r"\b"
        return bool(re.search(pattern, text))
    else:
        # Indic / Unicode: check normalized phrase
        kw_norm = _normalize_indic_text(kw_clean)
        target = text_indic if text_indic is not None else _normalize_indic_text(text)
        return kw_norm in target


class NewsRelevanceService:
    """
    Evaluates articles for competitive exam relevance using configured
    syllabus domains, explicit negative patterns, and substantive educational signals.
    """

    # ── 1. High-Priority Landmark / Constitutional Exceptions ─────────────────
    LANDMARK_EXCEPTIONS = [
        "supreme court", "high court", "constitution bench", "constitutional bench",
        "landmark judgment", "landmark judgement", "law commission", "criminal law reform",
        "bharatiya nyaya sanhita", "bns", "bharatiya nagarik suraksha sanhita", "bnss",
        "bharatiya sakshya adhiniyam", "bsa", "ipc amendment", "legal reform",
        "collegium", "basic structure", "fundamental rights", "habeas corpus",
        "judicial review", "election commission of india", "cag report",
        "உச்ச நீதிமன்றம்", "உயர் நீதிமன்றம்", "அரசியலமைப்பு", "நீதிபதிகள் அமர்வு",
        "வரலாற்று சிறப்புமிக்க தீர்ப்பு", "வரலாற்று தீர்ப்பு", "சட்டத்திருத்தம்",
        "சட்ட திருத்தம்", "குற்றவியல் சட்டம்", "அரசியலமைப்பு சாசனம்",
        "அடிப்படை உரிமை", "தேர்தல் ஆணையம்"
    ]

    # ── 2. Explicit Rejection Categories ──────────────────────────────────────

    # A. Entertainment / Cinema / Celebrity Gossip
    ENTERTAINMENT_KEYWORDS = [
        "cinema", "movie", "film", "box office", "actor", "actress", "celebrity",
        "comedian", "trailer", "teaser", "audio launch", "ott release", "heroine",
        "kollywood", "bollywood", "tollywood", "gossip", "director", "song release",
        "sivakarthikeyan", "sk", "black pandi", "thalapathy", "vijaykanth",
        "vadivelu", "nayanthara", "rajinikanth", "kamal haasan", "anirudh",
        "nicolas cage", "hollywood", "pop star", "grammy", "oscar",
        "திரைப்படம்", "நடிகர்", "நடிகை", "நகைச்சுவை நடிகர்", "இயக்குநர்",
        "பிளாக் பாண்டி", "சிவகார்த்திகேயன்", "பாடல் வெளியீடு", "படப்பிடிப்பு",
        "திரையரங்கம்", "ஓடிடி", "சினிமா", "வடிவேலு", "கதாநாயகி", "பாக்ஸ் ஆபீஸ்"
    ]

    # B. Routine Crime / Local Theft / Arrests / Prison Escapes
    ROUTINE_CRIME_KEYWORDS = [
        "escaped from prison", "prison escape", "inmate escaped", "escaped prisoner",
        "jailbreak", "stealing mobile", "stolen phone", "theft", "stolen", "stealing",
        "robbery", "robbed", "burglary", "burglar", "thief", "extortion", "snatching",
        "chain snatching", "shoplifting", "pickpocket", "cheated mobile", "tricking",
        "swindled", "conman", "cctv footage", "cctv", "arrested for stealing",
        "local police arrested", "police chase", "fir registered for theft",
        "sinkhole", "accident", "fatal crash",
        "தப்பியோடிய கைதி", "சிறையிலிருந்து தப்பியோட்டம்", "செல்போன் திருட்டு",
        "திருட்டு", "திருடி", "கொள்ளை", "கொள்ளையடித்த", "மோசடி", "ஏமாற்றி",
        "செயின் பறிப்பு", "பிக்பாக்கெட்", "மர்ம நபர்", "போலீசார் வழக்குப்பதிவு",
        "போலீசார் வழக்கு பதிவு", "போலீசார் விசாரணை", "கைதானார்", "கைது செய்யப்பட்டார்"
    ]

    # C. Routine Corporate Announcements & Layoffs (without macroeconomic/policy substance)
    ROUTINE_CORP_KEYWORDS = [
        "voluntary exit package", "voluntary separation", "severance package",
        "layoffs", "laying off", "employee exit", "tagged posts", "passkeys",
        "workplace collaboration tools", "series a", "series b", "series c",
        "doubles valuation", "funding round", "seed funding", "q1 results",
        "q2 results", "q3 results", "q4 results", "quarterly profit", "shares jumped",
        "shares tanked", "stock dips", "product launch", "smartphone launch",
        "marketing campaign", "gadget review"
    ]

    # D. Partisan Political Feuds & Party Gossip (without governance/policy substance)
    POLITICAL_FEUD_KEYWORDS = [
        "slams", "hits out at", "war of words", "feud", "political spat",
        "election rumor", "verbal attack", "exchanges barbs", "alleges",
        "கடும் சாடல்", "சரமாரி தாக்கு", "மோதல்", "காரசார விவாதம்",
        "கட்சிக் கூட்டம்", "அரசியல் சர்ச்சை"
    ]

    # E. Viral Animal / Ordinary Wildlife Rescue (without biodiversity/conservation substance)
    VIRAL_ANIMAL_KEYWORDS = [
        "shark rescue", "shark rescued", "beached whale", "dog rescued",
        "cat rescued", "puppy saved", "viral animal", "funny cat", "cute puppy",
        "விலங்கு மீட்பு", "நாய்க்குட்டி", "சுறா மீட்பு"
    ]

    # F. Live Update Feeds & Clickbait
    INVALID_CONTENT_PATTERNS = [
        r"(?i)^live\s*:", r"(?i)^live\s+updates", r"(?i)\blive\s+blog\b",
        r"(?i)\bhighlights\s*:\b", r"(?i)\badvertisement\b", r"(?i)\bsponsored\b"
    ]

    # ── 3. Substantive Syllabus Topics ────────────────────────────────────────

    SYLLABUS_DOMAINS = {
        "Indian Polity": {
            "keywords": [
                "constitution", "preamble", "fundamental rights", "fundamental duties",
                "dpsp", "directive principles", "parliament", "lok sabha", "rajya sabha",
                "president of india", "prime minister", "governor", "chief minister",
                "judiciary", "supreme court", "high court", "tribunal", "attorney general",
                "comptroller and auditor general", "cag report", "election commission", "upsc",
                "tnpsc", "finance commission", "panchayat raj", "municipality", "local body",
                "delimitation", "citizenship amendment", "inter-state council", "anti-defection",
                "ordinance", "bill passed", "act enacted", "statutory", "niti aayog",
                "அரசியலமைப்பு", "அரசியல் சாசனம்", "அடிப்படை உரிமைகள்", "நாடாளுமன்றம்",
                "மக்களவை", "மாநிலங்களவை", "குடியரசுத் தலைவர்", "ஆளுநர்", "முதல்வர்",
                "நீதிமன்றம்", "உயர் நீதிமன்றம்", "உச்ச நீதிமன்றம்", "தேர்தல் ஆணையம்",
                "பஞ்சாயத்து ராஜ்", "உள்ளாட்சி", "சட்டப்பேரவை", "சட்டமன்றம்", "அரசாணை",
                "நிதி ஆணையம்", "மத்திய அரசு", "மாநில அரசு"
            ],
            "topic_label": "Indian Polity & Constitutional Governance",
            "inclusion_reason": "Relevant to Indian Polity — Constitutional framework, governance, or judicial rulings",
        },
        "Government Schemes": {
            "keywords": [
                "government scheme", "welfare scheme", "public policy", "cabinet approved",
                "cabinet approves", "cabinet approval", "scheme", "welfare", "subsidy", "social justice",
                "pudhumai penn", "magalir urimai", "kalaignar", "breakfast scheme",
                "chief minister's breakfast scheme", "cm breakfast scheme", "approved allocation",
                "illam thedi kalvi", "makkalai thedi maruthuvam", "naan mudhalvan", "pm kisan",
                "ayushman bharat", "pm awas", "jal jeevan", "mgnrega", "midday meal", "ration card",
                "public distribution system", "free bus travel", "pension scheme", "self help group",
                "திட்டம்", "அரசு திட்டம்", "மகளிர் உரிமைத் தொகை", "புதுமைப் பெண்",
                "முதலமைச்சரின் காலை உணவுத் திட்டம்", "இல்லம் தேடி கல்வி", "மக்களைத் தேடி மருத்துவம்",
                "நான் முதல்வன்", "குடும்ப அட்டை", "ரேஷன்", "மகளிர் சுய உதவிக் குழு",
                "சமூக நலத் திட்டம்", "அமைச்சரவை ஒப்புதல்", "நிதி ஒதுக்கீடு"
            ],
            "topic_label": "Government Schemes & Social Welfare",
            "inclusion_reason": "Relevant to Government Schemes — Public policy and state/central welfare initiatives",
        },
        "Economy": {
            "keywords": [
                "reserve bank of india", "rbi", "monetary policy", "repo rate",
                "reverse repo", "inflation", "cpi", "wpi", "gdp", "economic growth",
                "fiscal deficit", "union budget", "state budget", "goods and services tax",
                "gst", "direct tax", "income tax", "foreign direct investment", "fdi",
                "forex reserves", "banking reform", "nationalised bank", "npa",
                "insolvency", "sebi", "stock exchange", "agriculture census",
                "minimum support price", "msp", "food security", "disinvestment",
                "ரிசர்வ் வங்கி", "வட்டி விகிதம்", "பணவீக்கம்", "பொருளாதாரம்", "ஜிடிபி",
                "பட்ஜெட்", "நிதிநிலை அறிக்கை", "சரக்கு மற்றும் சேவை வரி", "ஜிஎஸ்டி",
                "வரி விதிப்பு", "நேரடி வரி", "குறைந்தபட்ச ஆதரவு விலை", "விவசாயம்", "உணவுப் பாதுகாப்பு"
            ],
            "topic_label": "Indian Economy & Financial System",
            "inclusion_reason": "Relevant to Indian Economy — Monetary policy, fiscal indicators, or economic planning",
        },
        "Science & Technology": {
            "keywords": [
                "isro", "nasa", "space mission", "chandrayaan", "gaganyaan", "aditya-l1",
                "mangalyaan", "satellite", "pslv", "gslv", "sslv", "space telescope",
                "drdo", "missile test", "defence research", "supercomputer", "quantum mission",
                "semiconductor mission", "artificial intelligence policy", "biotechnology",
                "crispr", "genetics", "nuclear power", "renewable energy", "green hydrogen",
                "patent", "scientific discovery", "indigenous",
                "இஸ்ரோ", "விண்கலம்", "செயற்கைக்கோள்", "ராக்கெட்", "சந்திரயான்",
                "ககன்யான்", "டிஆர்டிஓ", "ஏவுகணை", "அறிவியல் கண்டுபிடிப்பு",
                "சூரிய ஆற்றல்", "பசுமை ஹைட்ரஜன்", "அணுசக்தி"
            ],
            "topic_label": "Science, Technology & Innovation",
            "inclusion_reason": "Relevant to Science & Technology — Space missions, scientific research, and innovation",
        },
        "Environment & Ecology": {
            "keywords": [
                "climate change", "global warming", "cop28", "cop29", "unfccc",
                "paris agreement", "biodiversity", "wildlife protection act", "national park",
                "wildlife sanctuary", "biosphere reserve", "tiger reserve", "elephant reserve",
                "ramsar site", "wetland", "western ghats", "mangrove", "forest survey",
                "air quality index", "aqi", "pollution control", "cyclone", "monsoon",
                "disaster management", "ndrf", "tndrf", "soil conservation",
                "பருவநிலை மாற்றம்", "சுற்றுச்சூழல்", "பல்லுயிர்", "தேசிய பூங்கா",
                "வனவிலங்கு சரணாலயம்", "புலிகள் காப்பகம்", "ராம்சார் தளம்",
                "மேற்கு தொடர்ச்சி மலை", "சதுப்பு நிலம்", "புயல்", "பருவமழை", "வெள்ளம்"
            ],
            "topic_label": "Environment, Biodiversity & Disaster Management",
            "inclusion_reason": "Relevant to Environment & Biodiversity — Ecology, climate treaties, and conservation",
        },
        "History & Culture": {
            "keywords": [
                "archaeology", "excavation", "keeladi", "porunai", "sivagalai", "kodumanal",
                "sangam age", "indus valley", "chola", "pandya", "pallava", "cheran",
                "thirukkural", "unesco heritage site", "monument", "temple architecture",
                "freedom struggle", "inscriptions", "epigraphy", "renaissance",
                "கீழடி", "பொருநை", "தொல்லியல்", "அகழ்வாராய்ச்சி", "சங்க காலம்",
                "சோழர்", "பாண்டியர்", "பல்லவர்", "திருக்குறள்", "பாரம்பரிய தளம்", "கல்வெட்டு"
            ],
            "topic_label": "History, Culture & Heritage",
            "inclusion_reason": "Relevant to History & Culture — Archaeological heritage, literature, and historical milestones",
        },
        "International Relations": {
            "keywords": [
                "united nations", "un security council", "unsc", "un general assembly",
                "veto", "veto power", "treaty", "bilateral summit", "g20", "brics", "asean",
                "sco", "quad", "international court of justice", "icj", "wto", "world health organization",
                "imf", "world bank", "ambassador", "foreign policy", "diplomacy", "extradition",
                "ஐக்கிய நாடுகள் சபை", "பாதுகாப்பு கவுன்சில்", "வீட்டோ", "ஜி20", "பிரிக்ஸ்",
                "சர்வதேச ஒப்பந்தம்", "இருதரப்பு பேச்சுவார்த்தை", "வெளியுறவு கொள்கை"
            ],
            "topic_label": "International Relations & Multilateral Forums",
            "inclusion_reason": "Relevant to International Relations — Global diplomacy, treaties, and international bodies",
        },
        "Awards, Sports & Personalities": {
            "keywords": [
                "nobel prize", "bharat ratna", "padma vibhushan", "padma bhushan", "padma shri",
                "sahitya akademi", "jnanpith", "booker prize", "dadasaheb phalke",
                "olympics", "paralympics", "asian games", "commonwealth games",
                "world championship", "national games", "grand slam", "chess olympiad",
                "national science day", "constitution day", "voter day", "world environment day",
                "நோபல் பரிசு", "பாரத ரத்னா", "பத்ம விருது", "சாகித்திய அகாடமி",
                "ஒலிம்பிக்", "ஆசிய விளையாட்டு", "செஸ் ஒலிம்பியாட்", "தேசிய தினம்"
            ],
            "topic_label": "Awards, Honours, Sports & Observances",
            "inclusion_reason": "Relevant to National Current Affairs — Major honors, international sports, or observance days",
        },
    }

    @classmethod
    def evaluate(cls, title: str, content: str, domain: Optional[str] = None) -> ExamRelevanceResult:
        """
        Evaluates an article for competitive exam relevance using word boundaries
        and substantive syllabus matching.
        """
        clean_title = ContentCleaningService.clean_html(title or "")
        clean_content = ContentCleaningService.clean_html(content or "")
        combined = f"{clean_title} {clean_content}".strip()
        combined_lower = combined.lower()
        title_lower = clean_title.lower()
        combined_indic = _normalize_indic_text(combined)
        title_indic = _normalize_indic_text(clean_title)

        # ── Check 0: Content Length / Validity ──
        if len(clean_title) < 8 or len(combined) < 20:
            return ExamRelevanceResult(
                is_eligible=False,
                relevance_score=0,
                syllabus_topic="Unusable Content",
                inclusion_reason="",
                rejection_reason="Invalid or unusable content — text too short or empty",
                signals=["insufficient_length"],
            )

        # Check for live tickers / clickbait
        for pat in cls.INVALID_CONTENT_PATTERNS:
            if re.search(pat, title_lower):
                return ExamRelevanceResult(
                    is_eligible=False,
                    relevance_score=5,
                    syllabus_topic="Live Feed",
                    inclusion_reason="",
                    rejection_reason="Invalid or unusable content — live-feed ticker or advertisement",
                    signals=["live_feed_or_ad"],
                )

        # ── Check 1: Landmark Constitutional / Legal Exceptions ──
        has_landmark = any(_matches_keyword(term, combined_lower, combined_indic) for term in cls.LANDMARK_EXCEPTIONS)
        if has_landmark:
            return ExamRelevanceResult(
                is_eligible=True,
                relevance_score=95,
                syllabus_topic="Indian Polity & Constitutional Governance",
                inclusion_reason="Relevant to Indian Polity — Landmark judicial ruling or statutory reform",
                rejection_reason=None,
                signals=["landmark_legal_exception"],
            )

        # ── Check 2: Explicit Rejections ──

        # A. Entertainment / Cinema Gossip
        entertainment_hits = [w for w in cls.ENTERTAINMENT_KEYWORDS if _matches_keyword(w, combined_lower, combined_indic)]
        if entertainment_hits:
            title_hit = any(_matches_keyword(w, title_lower, title_indic) for w in cls.ENTERTAINMENT_KEYWORDS)
            if title_hit or len(entertainment_hits) >= 2 or domain in ("Entertainment", "Cinema", "Gossip"):
                return ExamRelevanceResult(
                    is_eligible=False,
                    relevance_score=10,
                    syllabus_topic="Entertainment",
                    inclusion_reason="",
                    rejection_reason="Entertainment / celebrity content",
                    signals=[f"entertainment_keywords: {', '.join(entertainment_hits[:3])}"],
                )

        # B. Routine Crime / Prison Escape / Local Theft
        crime_hits = [w for w in cls.ROUTINE_CRIME_KEYWORDS if _matches_keyword(w, combined_lower, combined_indic)]
        if crime_hits:
            title_hit = any(_matches_keyword(w, title_lower, title_indic) for w in cls.ROUTINE_CRIME_KEYWORDS)
            if title_hit or len(crime_hits) >= 2 or domain == "Crime":
                return ExamRelevanceResult(
                    is_eligible=False,
                    relevance_score=10,
                    syllabus_topic="Routine Crime",
                    inclusion_reason="",
                    rejection_reason="Routine crime report",
                    signals=[f"crime_keywords: {', '.join(crime_hits[:3])}"],
                )

        # C. Routine Corporate Announcements / Layoffs
        corp_hits = [w for w in cls.ROUTINE_CORP_KEYWORDS if _matches_keyword(w, combined_lower, combined_indic)]
        if corp_hits:
            macro_words = ["antitrust", "competition commission", "national policy", "rbi", "gdp", "taxation", "union budget"]
            has_macro = any(_matches_keyword(w, combined_lower, combined_indic) for w in macro_words)
            if not has_macro:
                return ExamRelevanceResult(
                    is_eligible=False,
                    relevance_score=15,
                    syllabus_topic="Corporate Announcement",
                    inclusion_reason="",
                    rejection_reason="Routine corporate announcement without substantive policy relevance",
                    signals=[f"corporate_keywords: {', '.join(corp_hits[:3])}"],
                )

        # D. Viral Animal Stories
        viral_animal_hits = [w for w in cls.VIRAL_ANIMAL_KEYWORDS if _matches_keyword(w, combined_lower, combined_indic)]
        if viral_animal_hits:
            conserv_words = ["wildlife protection act", "iucn", "red list", "endangered", "biosphere", "national park", "forest department survey", "biodiversity"]
            has_conserv = any(_matches_keyword(w, combined_lower, combined_indic) for w in conserv_words)
            if not has_conserv:
                return ExamRelevanceResult(
                    is_eligible=False,
                    relevance_score=10,
                    syllabus_topic="Viral Story",
                    inclusion_reason="",
                    rejection_reason="Insufficient educational relevance / viral animal story",
                    signals=[f"viral_animal: {', '.join(viral_animal_hits[:2])}"],
                )

        # E. Partisan Political Feuds
        political_feud_hits = [w for w in cls.POLITICAL_FEUD_KEYWORDS if _matches_keyword(w, combined_lower, combined_indic)]
        if political_feud_hits:
            policy_words = [
                "scheme", "policy", "cabinet", "bill", "act", "ordinance", "fund", "welfare", "statutory",
                "அரசாணை", "திட்டம்", "நிதி", "ஒதுக்கீடு", "அமைச்சரவை", "ஒப்புதல்"
            ]
            has_policy = any(_matches_keyword(w, combined_lower, combined_indic) for w in policy_words)
            if not has_policy and any(_matches_keyword(w, title_lower, title_indic) for w in cls.POLITICAL_FEUD_KEYWORDS):
                return ExamRelevanceResult(
                    is_eligible=False,
                    relevance_score=20,
                    syllabus_topic="Political Feud",
                    inclusion_reason="",
                    rejection_reason="Partisan political dispute without governance substance",
                    signals=[f"political_feud: {', '.join(political_feud_hits[:2])}"],
                )

        # ── Check 3: Match Against Syllabus Topics ──
        best_topic = None
        best_score = 0
        best_reason = None
        best_signals = []

        for category, info in cls.SYLLABUS_DOMAINS.items():
            cat_keywords = info["keywords"]
            matches = []
            score = 0

            for kw in cat_keywords:
                if _matches_keyword(kw, combined_lower, combined_indic):
                    matches.append(kw)
                    if _matches_keyword(kw, title_lower, title_indic):
                        score += 30
                    else:
                        score += 15

            if matches:
                if domain and domain.lower() in category.lower():
                    score += 20

                if score > best_score:
                    best_score = score
                    best_topic = info["topic_label"]
                    best_reason = info["inclusion_reason"]
                    best_signals = [f"{category} terms: {', '.join(matches[:4])}"]

        if best_score >= 30 and best_topic:
            return ExamRelevanceResult(
                is_eligible=True,
                relevance_score=min(95, best_score),
                syllabus_topic=best_topic,
                inclusion_reason=best_reason or f"Relevant to {best_topic}",
                rejection_reason=None,
                signals=best_signals,
            )

        return ExamRelevanceResult(
            is_eligible=False,
            relevance_score=max(10, best_score),
            syllabus_topic="General News",
            inclusion_reason="",
            rejection_reason="Insufficient educational relevance to competitive examination syllabi",
            signals=["no_substantive_syllabus_match"],
        )
