with open('apps/api/app/services/ai_assistant.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace block 1
target1 = """        if "india" in q_lower and not filters.get("location_name"):
            filters["location_name"] = "India\""""
replace1 = """        if re.search(r'\\bindia\\b', q_lower) and not filters.get("location_name"):
            filters["location_name"] = "India\""""
content = content.replace(target1, replace1)

# Replace block 2
target2 = """        if not events:
            if query_text and len(query_text) > 2:
                events, _ = self.event_repo.search_events("""
replace2 = """        if not events or (domain and not any(e.domain and e.domain.lower() == domain.lower() for e in events)):
            if query_text and len(query_text) > 2:
                events, _ = self.event_repo.search_events("""
content = content.replace(target2, replace2)

with open('apps/api/app/services/ai_assistant.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Files patched successfully.")
