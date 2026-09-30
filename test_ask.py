from fastapi.testclient import TestClient
from apps.api.app.main import app

client = TestClient(app)

tests = [
    "Give me 5 MCQs from Indian science and technology current affairs",
    "Give me some MCQs about climate tech companies",
    "Give me 5 TNPSC Group 4 current affairs MCQs"
]

for t in tests:
    print(f"\n--- TEST: {t} ---")
    response = client.post("/api/v1/ask", json={"question": t})
    if response.status_code == 200:
        data = response.json()
        print(f"Events found: {data.get('events_found')}")
        print(f"Provider: {data.get('provider')}")
        ans = data.get('answer', '')
        # print safe snippet
        safe_ans = ans[:500].encode('ascii', 'ignore').decode('ascii')
        print(f"Answer snippet: {safe_ans}")
        
        # Check for duplicates or bad formats
        if 'cancelled' in ans.lower() or 'none of the above' in ans.lower():
            print("WARNING: Bad distractor found!")
        
        q_count = ans.count('**Q')
        print(f"Detected questions: {q_count}")
    else:
        print(f"Error {response.status_code}: {response.text}")

