import re

with open('apps/api/app/services/ai_assistant.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = """        sources = []
        for e in events[:5]:
            src_name = getattr(e, "source", "") or "FlashFacts Network"
            if hasattr(src_name, "name"):
                src_name = src_name.name
            sources.append({
                "title": e.title,
                "domain": e.domain,
                "date": e.event_date.isoformat() if e.event_date else None,
                "source": src_name,
            })"""

replacement = """        sources = []
        for e in events[:5]:
            src_name = getattr(e, "source", "") or "FlashFacts Network"
            if hasattr(src_name, "name"):
                src_name = src_name.name
            sources.append({
                "name": src_name,
                "url": getattr(e, "url", None),
                "date": e.event_date.isoformat() if getattr(e, "event_date", None) else None,
            })"""

content = content.replace(target, replacement)
with open('apps/api/app/services/ai_assistant.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed SourceItem schema!")
