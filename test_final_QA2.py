import httpx
import json

queries = {
    "A": "Give me 5 MCQs from Indian science and technology current affairs",
    "B": "Give me important TNPSC Group 4 current affairs",
    "C": "What are the major science and technology events from the last week?",
    "D": "What happened in Tamil Nadu this week?"
}

with open('qa_results2.txt', 'w', encoding='utf-8') as f:
    for label, q in queries.items():
        f.write('='*50 + '\n')
        f.write(f'TEST {label} QUERY: {q}\n')
        resp = httpx.post('http://127.0.0.1:8000/api/v1/ask', json={'question': q}, timeout=10.0)
        data = resp.json()
        f.write(f"events_found: {data.get('events_found')}\n")
        f.write(f"provider: {data.get('provider')}\n")
        f.write(f"filters: {data.get('filters')}\n")
        f.write(f"Answer snippet:\n{data.get('answer')[:800]}\n")
        f.write('='*50 + '\n')
