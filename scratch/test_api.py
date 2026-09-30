import json, requests, sys

base_url = 'http://127.0.0.1:8000/api/v1/ask'
queries = [
    "What are the latest Indian current affairs?",
    "What are the important Tamil Nadu current affairs?",
    "Give me TNPSC Group 4 exam current affairs.",
    "What are the major politics events from the last week?",
    "Create 5 MCQs from recent Indian science and technology current affairs.",
    "What are the latest Antarctic research updates for 2050?",
]

for i, q in enumerate(queries, 1):
    try:
        resp = requests.post(base_url, json={"question": q})
        print(f"--- Query {i} ---")
        print(f"Question: {q}")
        print(f"HTTP Status: {resp.status_code}")
        try:
            data = resp.json()
        except Exception as e:
            print("Failed to parse JSON:", e)
            print("Response text:", resp.text)
            continue
        print("events_found:", data.get('events_found'))
        print("filters:", data.get('filters'))
        print("provider:", data.get('provider'))
        answer = data.get('answer','')
        print("answer length:", len(answer))
        sources = data.get('sources') or []
        for src in sources:
            print(f"  - name: {src.get('name')}, date: {src.get('date')}")
    except Exception as exc:
        print(f"Error for query {i}: {exc}")
