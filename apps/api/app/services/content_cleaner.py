import html
import re
import unicodedata
from html.parser import HTMLParser
from typing import Optional
from app.utils.hashing import fix_mojibake


class _HTMLTextExtractor(HTMLParser):
    """
    Strips HTML markup and extracts clean text while dropping unwanted blocks
    (scripts, styles, figure, video, audio, iframe, noscript, etc.) and their inner content.
    """
    DISCARD_TAGS = {
        "script", "style", "figure", "video", "audio", "iframe",
        "noscript", "svg", "canvas", "template", "head", "object", "embed"
    }

    BLOCK_TAGS = {
        "p", "div", "br", "h1", "h2", "h3", "h4", "h5", "h6",
        "li", "blockquote", "section", "article", "header", "footer", "tr"
    }

    def __init__(self):
        super().__init__()
        self._discard_depth = 0
        self._pieces = []

    def handle_starttag(self, tag, attrs):
        t = tag.lower()
        if t in self.DISCARD_TAGS:
            self._discard_depth += 1
        elif t in self.BLOCK_TAGS and self._discard_depth == 0:
            self._pieces.append("\n")

    def handle_endtag(self, tag):
        t = tag.lower()
        if t in self.DISCARD_TAGS:
            if self._discard_depth > 0:
                self._discard_depth -= 1
        elif t in self.BLOCK_TAGS and self._discard_depth == 0:
            self._pieces.append("\n")

    def handle_data(self, data):
        if self._discard_depth == 0:
            self._pieces.append(data)

    def get_text(self) -> str:
        return "".join(self._pieces)


class ContentCleaningService:
    """
    Shared, robust content cleaner used across ingestion, extraction,
    enrichment, search, RAG, and API serialization.
    """

    # Boilerplate patterns to remove from news feeds
    BOILERPLATE_PATTERNS = [
        re.compile(r"(?i)\b(also\s+read|read\s+also|click\s+here\s+to\s+read|read\s+more|subscribe\s+to|follow\s+us\s+on\s+twitter|follow\s+us\s+on\s+whatsapp|follow\s+us\s+on\s+telegram)\b.*$", re.DOTALL),
        re.compile(r"(?i)\b(image\s+credit|photo\s+credit|source\s*:|reuters|ani|pti)\s*:?.*$", re.MULTILINE),
        re.compile(r"(?i)https?://\S+"),  # raw URLs in text
        re.compile(r"(?:\n|^)\s*(?:தொடர்ந்து\s+படிக்க|மேலும்\s+செய்திகளுக்கு)[\s\S]*$", re.MULTILINE),
        re.compile(r"(?:\n|^)\s*(?:முழு\s+விவரம்\s*(?:காண|அறிய|படிக்க|தெரிந்து\s*கொள்ள|இங்கே\s*கிளிக்)|முழு\s+விவரத்திற்கு\s*கிளிக்|முழு\s+விவரங்களை\s+படிக்க)[\s\S]*$", re.MULTILINE),
    ]

    @classmethod
    def clean_html(cls, raw_html: Optional[str]) -> str:
        """
        Safely strips all HTML tags, scripts, styles, video/figure blocks,
        and unescapes entities recursively. Preserves Tamil/Indic Unicode.
        """
        if not raw_html:
            return ""

        text = fix_mojibake(str(raw_html))
        text = unicodedata.normalize("NFC", text)
        text = re.sub(r"[\u200b-\u200d\ufeff]", "", text)

        # Recursively unescape entities up to 3 times to handle double-encoding (e.g. &amp;lt;p&amp;gt;)
        for _ in range(3):
            prev = text
            text = html.unescape(text)
            if text == prev:
                break

        # If tags are present, parse with HTMLTextExtractor
        if "<" in text and ">" in text:
            try:
                parser = _HTMLTextExtractor()
                parser.feed(text)
                parser.close()
                text = parser.get_text()
            except Exception:
                # Fallback: regex tag strip
                text = re.sub(r"(?is)<(script|style|figure|video|iframe)[^>]*>.*?</\1>", "", text)
                text = re.sub(r"<[^>]+>", " ", text)

        # Final regex sweep to ensure zero tag remnants (e.g. lone <img> or <br/>)
        text = re.sub(r"<[^>]+>", " ", text)

        # Remove image and media URL residues
        text = re.sub(r"\bhttps?://\S+\.(?:jpg|jpeg|png|gif|webp|svg|mp4|webm)\b", "", text, flags=re.IGNORECASE)

        # Normalize whitespace while preserving basic paragraph structure
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
        text = "\n".join(line for line in lines if line)
        text = re.sub(r"\n{3,}", "\n\n", text).strip()

        return unicodedata.normalize("NFC", text)

    @classmethod
    def clean_article_text(cls, title: str, content: str) -> str:
        """
        Cleans content, removes boilerplate, and eliminates leading duplicated title.
        """
        clean_t = cls.clean_html(title)
        clean_c = cls.clean_html(content)

        if not clean_c:
            return clean_t

        # Remove common boilerplate lines
        for pattern in cls.BOILERPLATE_PATTERNS:
            clean_c = pattern.sub("", clean_c).strip()

        # Step 1: Direct prefix check (ignoring trailing punctuation and ellipsis on title)
        clean_t_stripped = clean_t.strip().rstrip(".!?:-–—|… '\'\"‘’“”")
        if clean_t_stripped and len(clean_t_stripped) > 8:
            if clean_c.lower().startswith(clean_t_stripped.lower()):
                remainder = clean_c[len(clean_t_stripped):].lstrip(". :-–—|!?;'\"‘’“” ")
                if remainder and len(remainder) >= 8:
                    clean_c = remainder

        # Step 2: Check normalized text without punctuation
        clean_t_norm = re.sub(r"[^\w\s]", "", clean_t.lower()).strip()
        clean_c_norm = re.sub(r"[^\w\s]", "", clean_c.lower()).strip()

        if clean_c_norm.startswith(clean_t_norm) and len(clean_t_norm) > 8:
            # Strip the redundant leading title from content
            words_t = clean_t.split()
            words_c = clean_c.split()
            if len(words_c) > len(words_t):
                match_prefix = True
                compare_len = min(len(words_t), len(words_c), 5)
                for i in range(compare_len):
                    w_t = re.sub(r"[^\w\s]", "", words_t[i].lower())
                    w_c = re.sub(r"[^\w\s]", "", words_c[i].lower())
                    if w_t and w_c and w_t != w_c:
                        match_prefix = False
                        break
                if match_prefix:
                    remainder = " ".join(words_c[len(words_t):]).lstrip(". :-–—|!?;'\"‘’“” ")
                    if remainder and len(remainder) >= 8:
                        clean_c = remainder

        # If content became empty after removing duplicated title or boilerplate
        if not clean_c or len(clean_c.strip()) < 15:
            return clean_t

        return clean_c.strip()

    @classmethod
    def build_clean_summary(cls, title: str, content: str, max_words: int = 75) -> str:
        """
        Generates a concise, readable, plain-text Intelligence Summary.
        Guarantees zero HTML, zero script/image URLs, and no title repetition.
        """
        clean_t = cls.clean_html(title)
        body = cls.clean_article_text(title, content)

        # If body is just the title, return the title directly without duplicating
        if not body or body.strip().lower() == clean_t.strip().lower():
            return clean_t

        # If body doesn't start with title, check whether to include title
        # For readability, an Intelligence Summary should be a continuous narrative
        # If body starts with distinct factual information:
        words = body.split()
        if len(words) > max_words:
            truncated = " ".join(words[:max_words])
            # Don't cut off in the middle of a sentence if a period is close
            last_period = truncated.rfind(".")
            if last_period > len(truncated) * 0.7:
                truncated = truncated[:last_period + 1]
            else:
                truncated += "..."
            summary = truncated
        else:
            summary = body

        # Final verification: zero '<' or '>'
        summary = re.sub(r"<[^>]+>", "", summary)
        summary = html.unescape(summary).strip()

        if not summary:
            return clean_t or "Verified event information available at the original source."

        return summary
