import requests, sys
sys.stdout.reconfigure(encoding='utf-8')
queries = [
    "What are the major politics events from the last week?",
    "What are the major science events from the last week?",
    "What are the major AI events from the last week?",
    "What are the important Tamil Nadu current affairs?",
    "Give me TNPSC Group 4 exam current affairs.",
    "Give me SSC CGL current affairs.",
    "Create 5 MCQs from recent Indian science and technology current affairs.",
    "What are the latest Antarctic research updates for 2050?"
]
for i, q in enumerate(queries, 1):
    print(f'\n--- Query {i} ---')
    print(f'Question: {q}')
    resp = requests.post('http://127.0.0.1:8000/api/v1/ask', json={'question': q})
    print(f'HTTP Status: {resp.status_code}')
    if resp.status_code == 200:
        data = resp.json()
        print(f"events_found: {data.get('events_found')}")
        print(f"filters: {data.get('filters')}")
        print(f"provider: {data.get('provider')}")
        ans = data.get('answer', '')
        print(f"answer length: len {len(ans)}")
        print(f"answer starts with: {ans[:150]}...")
        if data.get('events_found') == 0:
            print(f"answer full text: {ans}")
        for s in data.get('sources', []):
            print(f"  - name: {s.get('name')}, date: {s.get('date')}")
    else:
        print(resp.text)
