import httpx
import json

queries = [
    "What are the latest science and technology events from the last week?",
    "Give me important TNPSC Group 4 current affairs",
    "Give me 5 MCQs from Indian science and technology current affairs",
    "Give me verified FlashFacts updates about Antarctic research in 2050"
]

with open('C:/FlashFacts/scratch/qa_results.txt', 'w', encoding='utf-8') as f:
    for q in queries:
        f.write('='*50 + '\n')
        f.write(f'QUERY: {q}\n')
        resp = httpx.post('http://127.0.0.1:8000/api/v1/ask', json={'question': q}, timeout=10.0)
        data = resp.json()
        f.write(f"events_found: {data.get('events_found')}\n")
        f.write(f"provider: {data.get('provider')}\n")
        f.write(f"filters: {data.get('filters')}\n")
        f.write(f"Answer snippet:\n{data.get('answer')[:800]}\n")
        f.write('='*50 + '\n')
