"""
Tests for security, input validation, and boundary conditions.
"""
import pytest


def test_invalid_exam_id_404(client):
    """Verify requesting an invalid exam ID returns 404 rather than 500."""
    response = client.get("/api/v1/exams/invalid-exam-xyz")
    assert response.status_code == 404
    assert "detail" in response.json()


def test_invalid_event_id_404(client):
    """Verify requesting a non-existent event ID returns 404 cleanly."""
    response = client.get("/api/v1/events/99999999")
    assert response.status_code == 404
    assert "detail" in response.json()


def test_pagination_limits_validation(client):
    """Verify input validation rejects invalid/negative pagination parameters."""
    response = client.get("/api/v1/events?limit=-5")
    assert response.status_code == 422

    response = client.get("/api/v1/events?limit=500")
    assert response.status_code == 422

    response = client.get("/api/v1/events?offset=-1")
    assert response.status_code == 422


def test_mcq_count_bounds_validation(client):
    """Verify MCQ count param enforces minimum and maximum bounds."""
    response = client.get("/api/v1/events/1/mcq?count=0")
    assert response.status_code == 422

    response = client.get("/api/v1/events/1/mcq?count=10")
    assert response.status_code == 422

