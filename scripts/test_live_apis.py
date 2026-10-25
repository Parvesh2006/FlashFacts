import urllib.request
import json

def post(url, data=None, headers=None):
    body = json.dumps(data or {}).encode('utf-8') if data else b''
    req_headers = {'Content-Type': 'application/json'}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, data=body, headers=req_headers, method='POST')
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))

def get(url, headers=None):
    req_headers = {}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, headers=req_headers)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))

# 1. Auth Guest
auth = post('http://localhost:8000/api/v1/auth/guest?target_exam=TNPSC%20Group%204')
token = auth['access_token']
headers = {'Authorization': f'Bearer {token}'}
print('[OK] Auth Guest token acquired:', token[:25] + '...')

# 2. PYQs
pyqs = get('http://localhost:8000/api/v1/pyqs/?exam_name=TNPSC%20Group%204', headers)
print(f'[OK] PYQs count for TNPSC Group 4: {len(pyqs)}')

# 3. Mock tests
tests = get('http://localhost:8000/api/v1/mock-tests/', headers)
print(f'[OK] Mock Tests available: {len(tests)}')

# 4. Analytics
analytics = get('http://localhost:8000/api/v1/analytics/performance', headers)
print(f'[OK] Analytics fetched: total_tests={analytics["total_tests_completed"]}, recommendations={len(analytics["recommendations"])}')

# 5. Revision
rev = get('http://localhost:8000/api/v1/revision/', headers)
print(f'[OK] Revision items fetched: {len(rev)}')

# 6. Syllabus
syl = get('http://localhost:8000/api/v1/syllabus/TNPSC%20Group%204', headers)
print(f'[OK] Syllabus fetched: {syl["exam_name"]}, subjects={len(syl["subjects"])}, total_topics={syl["total_topics"]}')

# 7. Test attempt flow & analytics update
print("\n--- Testing Mock Test Attempt & Mistake Book Flow ---")
test_create = post('http://localhost:8000/api/v1/mock-tests/', {
    'exam_name': 'TNPSC Group 4',
    'total_questions': 2,
    'time_limit_minutes': 15,
    'negative_marking': 0.0,
    'include_pyqs': True,
    'include_events': False
}, headers)

test_id = test_create['id']
q1 = test_create['questions'][0]
q2 = test_create['questions'][1]

# Submit 1 correct, 1 incorrect
attempt = post(f'http://localhost:8000/api/v1/mock-tests/{test_id}/attempts', {
    'answers': {str(q1['id']): 'A', str(q2['id']): 'X'},
    'time_taken_seconds': 45
}, headers)

print(f"[OK] Attempt submitted: score={attempt['score']}, accuracy={attempt['accuracy']}%, incorrect={attempt['incorrect_count']}")

# Check Mistake Book
rev_after = get('http://localhost:8000/api/v1/revision/', headers)
print(f"[OK] Mistake Book updated: {len(rev_after)} question(s) recorded.")

# Check Analytics
analytics_after = get('http://localhost:8000/api/v1/analytics/performance', headers)
print(f"[OK] Analytics updated: completed_tests={analytics_after['total_tests_completed']}, attempted_q={analytics_after['total_questions_attempted']}, overall_acc={analytics_after['overall_accuracy']}%")
