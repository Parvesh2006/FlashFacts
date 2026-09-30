import re

with open('apps/api/app/services/ai_assistant.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = '''        # Keyword or general retrieval
        if not events:
            if query_text and len(query_text) > 2:
                events, _ = self.event_repo.search_events(
                    query_text=query_text,
                    domain=domain,
                    start_date=start_date,
                    end_date=end_date,
                    limit=50,
                )

        if not events:
            events, _ = self.event_repo.list_events(
                domain=domain,
                start_date=start_date,
                end_date=end_date,
                sort="important",
                limit=50,
            )

        # Additional domain filtering if specified
        if domain:
            domains = [d.strip().lower() for d in domain.split(",")]
            events = [e for e in events if e.domain and e.domain.lower() in domains]'''

replacement = '''        # Apply domain filtering to location events first
        if domain and events:
            domains = [d.strip().lower() for d in domain.split(",")]
            events = [e for e in events if e.domain and e.domain.lower() in domains]

        # Keyword or general retrieval
        if not events:
            if query_text and len(query_text) > 2:
                events, _ = self.event_repo.search_events(
                    query_text=query_text,
                    domain=domain,
                    start_date=start_date,
                    end_date=end_date,
                    limit=50,
                )

        if not events:
            events, _ = self.event_repo.list_events(
                domain=domain,
                start_date=start_date,
                end_date=end_date,
                sort="important",
                limit=50,
            )'''

content = content.replace(target, replacement, 1)

with open('apps/api/app/services/ai_assistant.py', 'w', encoding='utf-8') as f:
    f.write(content)
