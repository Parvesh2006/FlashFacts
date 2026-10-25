UNSUPPORTED_DOMAIN_LABELS = {"general", "general news"}


def validate_exam_domain(domain: str) -> str:
    normalized = domain.strip().casefold()
    if normalized in UNSUPPORTED_DOMAIN_LABELS:
        raise ValueError("General News is not a supported domain")
    return domain
