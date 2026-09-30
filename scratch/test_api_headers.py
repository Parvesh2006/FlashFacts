import httpx
resp = httpx.post('http://127.0.0.1:8000/api/v1/ask', json={'question': 'Give me important TNPSC Group 4 current affairs'})
print('Headers:', resp.headers)
print('Content sample:', repr(resp.text[:200]))
