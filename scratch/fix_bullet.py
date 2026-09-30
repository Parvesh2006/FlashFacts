import sys
content = open('apps/api/app/services/ai_assistant.py', 'r', encoding='utf-8').read()
content = content.replace(" ' \u2022 '.join", " ' | '.join")
content = content.replace(" ' \xe2\x80\xa2 '.join", " ' | '.join")
content = content.replace(" \u00b7 ", " | ")
content = content.replace(" \xc2\xb7 ", " | ")
with open('apps/api/app/services/ai_assistant.py', 'w', encoding='utf-8') as f:
    f.write(content)
