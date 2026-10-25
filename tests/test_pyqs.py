import pytest
from fastapi.testclient import TestClient

def test_create_and_get_pyq(client: TestClient, db_session):
    # Create PYQ
    payload = {
        "exam_name": "TNPSC Group 4",
        "year": 2022,
        "paper_name": "General Studies",
        "subject": "History",
        "question_text": "Who is the founder of the Chola Empire?",
        "options": ["Rajaraja Chola", "Vijayalaya Chola", "Rajendra Chola", "Aditya Chola"],
        "correct_answer": "Vijayalaya Chola",
        "explanation": "Vijayalaya Chola revived the Chola dynasty in 850 CE."
    }
    response = client.post("/api/v1/pyqs/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["exam_name"] == "TNPSC Group 4"
    assert data["id"] is not None
    pyq_id = data["id"]

    # Get PYQ by ID
    response = client.get(f"/api/v1/pyqs/{pyq_id}")
    assert response.status_code == 200
    assert response.json()["correct_answer"] == "Vijayalaya Chola"

    # List PYQs by Exam
    response = client.get("/api/v1/pyqs/?exam_name=TNPSC Group 4")
    assert response.status_code == 200
    data_list = response.json()
    assert len(data_list) >= 1
    assert any(pyq["id"] == pyq_id for pyq in data_list)

    # List PYQs by Language
    response_lang = client.get("/api/v1/pyqs/?language=en")
    assert response_lang.status_code == 200
    assert any(pyq["id"] == pyq_id for pyq in response_lang.json())
