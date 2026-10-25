with open('apps/api/app/repositories/event_repository.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = "        if domain:\n            query = query.filter(Event.domain.ilike(domain))\n        if event_date:"
replacement = "        if domain:\n            query = query.filter(Event.domain.ilike(domain))\n        else:\n            # Exclude non-exam domains from default competitive-exam current-affairs feed\n            non_exam_domains = [\"Entertainment\", \"Crime\", \"Lifestyle\", \"Gossip\", \"Cinema\"]\n            query = query.filter(~Event.domain.in_(non_exam_domains))\n        if event_date:"

# Also handle CRLF if present
if target not in text and target.replace('\n', '\r\n') in text:
    target = target.replace('\n', '\r\n')
    replacement = replacement.replace('\n', '\r\n')

assert target in text, "Target not found in event_repository.py"
text = text.replace(target, replacement, 1)

with open('apps/api/app/repositories/event_repository.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Updated event_repository.py successfully")
