import hashlib
import re


def normalize_text(text: str) -> str:
    """Lowercase text and strip punctuation/extra whitespace."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def compute_content_hash(url: str, title: str, content: str) -> str:
    """Generate deterministic SHA-256 hash for document content."""
    normalized_url = (url or "").strip().lower()
    normalized_title = normalize_text(title)
    normalized_content = normalize_text(content)
    raw_payload = f"{normalized_url}|{normalized_title}|{normalized_content}"
    return hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()


def compute_event_dedup_hash(title: str, event_date_str: str) -> str:
    """Generate SHA-256 hash for event deduplication based on normalized title and event date."""
    normalized_title = normalize_text(title)
    raw_payload = f"{normalized_title}|{event_date_str}"
    return hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()
