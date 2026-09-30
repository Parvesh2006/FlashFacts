import httpx
resp = httpx.post('http://127.0.0.1:8000/api/v1/ask', json={'question': 'Give me important TNPSC Group 4 current affairs'})
with open('test_api_full.txt', 'w', encoding='utf-8') as f:
    f.write(resp.json()['answer'])
