import pytest
from app.models.event import Event
from datetime import datetime

def test_ask_endpoint_tamil_utf8_encoding(client, db_session):
    # Insert a fake event with Tamil text to ensure the RAG returns it without mojibake
    tamil_title = "தமிழ்நாடு மற்றும் இந்தியாவில் புதிய திட்டங்கள்"
    tamil_summary = "தமிழ்நாடு அரசு புதிய கல்வி திட்டத்தை அறிமுகப்படுத்தியுள்ளது."

    test_event = Event(
        title=tamil_title,
        summary=tamil_summary,
        domain="Government",
        event_date=datetime.utcnow(),
        published_at=datetime.utcnow(),
        source_id=1,
        source_url="http://example.com/tamil",
        processing_status="completed",
        dedup_hash="fakehash123"
    )
    db_session.add(test_event)
    db_session.commit()
    db_session.refresh(test_event)

    # Make request to ask endpoint
    response = client.post("/api/v1/ask", json={
        "question": "தமிழ்நாடு திட்டங்கள் பற்றி கூறு"
    })

    assert response.status_code == 200
    assert "application/json" in response.headers.get("content-type", "")

    data = response.json()
    answer = data.get("answer", "")

    # Verify the actual Unicode characters exist in the parsed response
    assert "தமிழ்நாடு" in answer or "இந்தியாவில்" in answer or tamil_title in answer, "Tamil Unicode characters not found in answer. Found: " + repr(answer)
