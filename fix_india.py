import re

with open('apps/api/app/services/ai_assistant.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = '''        if "india" in q_lower and not filters["location_name"]:
            filters["location_name"] = "India"'''

replacement = '''        if re.search(r'\\bindia\\b', q_lower) and not filters["location_name"]:
            filters["location_name"] = "India"'''

content = content.replace(target, replacement)

with open('apps/api/app/services/ai_assistant.py', 'w', encoding='utf-8') as f:
    f.write(content)
