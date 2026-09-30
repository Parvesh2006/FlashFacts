import re

with open('apps/api/app/repositories/event_repository.py', 'r', encoding='utf-8') as f:
    content = f.read()

replacement = '''if domain:
            domains = [d.strip() for d in domain.split(",") if d.strip()]
            query = query.filter(or_(*[Event.domain.ilike(d) for d in domains]))'''

content = re.sub(r'if domain:\s*query = query\.filter\(Event\.domain\.ilike\(domain\)\)', replacement, content)

with open('apps/api/app/repositories/event_repository.py', 'w', encoding='utf-8') as f:
    f.write(content)
