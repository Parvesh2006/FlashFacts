import pytest
from fastapi.testclient import TestClient

def test_create_and_submit_mock_test(client: TestClient, db_session):
    # Insert a PYQ first so we have at least 1 question
    pyq_payload = {
        "exam_name": "TNPSC Group 4",
        "year": 2022,
        "question_text": "Who is the founder of the Chola Empire?",
        "options": ["Rajaraja Chola", "Vijayalaya Chola", "Rajendra Chola", "Aditya Chola"],
        "correct_answer": "Vijayalaya Chola"
    }
    client.post("/api/v1/pyqs/", json=pyq_payload)

    # Create Mock Test
    payload = {
        "exam_name": "TNPSC Group 4",
        "total_questions": 2,
        "include_pyqs": True,
        "include_events": True
    }
    response = client.post("/api/v1/mock-tests/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["exam_name"] == "TNPSC Group 4"
    assert "id" in data
    assert data["status"] == "ready"
    assert len(data["questions"]) > 0

    test_id = data["id"]
    q1 = data["questions"][0]

    # Submit Mock Test Attempt
    answers = {
        str(q1["id"]): "A"  # We don't know correct answer offhand, just checking submit logic
    }

    submit_payload = {
        "answers": answers
    }

    submit_response = client.post(f"/api/v1/mock-tests/{test_id}/attempts", json=submit_payload)
    assert submit_response.status_code == 201
    submit_data = submit_response.json()
    assert submit_data["test_id"] == test_id
    assert submit_data["total_answered"] == 1
    assert "score" in submit_data

    # Get test again
    get_res = client.get(f"/api/v1/mock-tests/{test_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == test_id
