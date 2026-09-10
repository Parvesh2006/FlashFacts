import json

import pytest

from app.services.evaluation import (
    calculate_entity_metrics,
    calculate_latency_metrics,
    evaluate_benchmark,
    load_benchmark_dataset,
)


@pytest.fixture
def sample_benchmark():
    return [
        {
            "id": "benchmark-001",
            "title": "OpenAI launches new AI model for healthcare analytics",
            "content": "OpenAI announced a new AI model for healthcare analytics to improve patient summaries.",
            "expected_domain": "technology",
            "expected_event_type": "announcement",
            "expected_importance_score": 82,
            "expected_entities": [
                {"name": "OpenAI", "entity_type": "ORGANIZATION"},
                {"name": "AI", "entity_type": "TECHNOLOGY"},
                {"name": "healthcare", "entity_type": "CONCEPT"},
            ],
        },
        {
            "id": "benchmark-002",
            "title": "India launches satellite program to expand climate monitoring",
            "content": "The Indian Space Research Organisation announced a satellite launch for climate monitoring.",
            "expected_domain": "science",
            "expected_event_type": "launch",
            "expected_importance_score": 74,
            "expected_entities": [
                {"name": "India", "entity_type": "COUNTRY"},
                {"name": "ISRO", "entity_type": "ORGANIZATION"},
                {"name": "climate monitoring", "entity_type": "CONCEPT"},
            ],
        },
    ]


@pytest.fixture
def sample_predictions():
    return [
        {
            "id": "benchmark-001",
            "domain": "technology",
            "event_type": "announcement",
            "importance_score": 80,
            "entities": [
                {"name": "openai", "entity_type": "ORGANIZATION"},
                {"name": "AI", "entity_type": "TECHNOLOGY"},
                {"name": "healthcare", "entity_type": "CONCEPT"},
                {"name": "OpenAI", "entity_type": "ORGANIZATION"},
            ],
        },
        {
            "id": "benchmark-002",
            "domain": "science",
            "event_type": "launch",
            "importance_score": 70,
            "entities": [
                {"name": "india", "entity_type": "COUNTRY"},
                {"name": "ISRO", "entity_type": "ORGANIZATION"},
                {"name": "climate monitoring", "entity_type": "CONCEPT"},
            ],
        },
    ]


def test_classification_accuracy(sample_benchmark, sample_predictions):
    result = evaluate_benchmark(sample_benchmark, predictions=sample_predictions)
    assert result["classification"]["accuracy"] == pytest.approx(1.0)


def test_event_type_accuracy(sample_benchmark, sample_predictions):
    result = evaluate_benchmark(sample_benchmark, predictions=sample_predictions)
    assert result["event_type"]["accuracy"] == pytest.approx(1.0)


def test_strict_evaluation_does_not_fill_missing_predictions(sample_benchmark):
    result = evaluate_benchmark(
        sample_benchmark,
        predictions=[{"id": "benchmark-001", "entities": []}],
    )

    assert result["classification"]["accuracy"] == pytest.approx(0.0)
    assert result["event_type"]["accuracy"] == pytest.approx(0.0)
    assert result["importance"]["mae"] == pytest.approx(78.0)
    assert result["importance"]["rmse"] == pytest.approx(78.102497)
    assert result["entities"]["recall"] == pytest.approx(0.0)


def test_strict_evaluation_treats_missing_importance_as_zero_and_penalizes_missing_prediction():
    result = evaluate_benchmark(
        [{
            "id": "b-1",
            "title": "AI launches healthcare policy tool",
            "content": "OpenAI announces an AI tool for healthcare policy reporting.",
            "expected_domain": "technology",
            "expected_event_type": "announcement",
            "expected_importance_score": 82,
            "expected_entities": [{"name": "OpenAI", "entity_type": "ORGANIZATION"}],
        }],
        predictions=[{"id": "b-1", "domain": "technology", "event_type": "announcement", "entities": []}],
    )

    assert result["importance"]["mae"] == pytest.approx(82.0)
    assert result["importance"]["rmse"] == pytest.approx(82.0)


def test_entity_precision_recall_f1(sample_benchmark, sample_predictions):
    result = evaluate_benchmark(sample_benchmark, predictions=sample_predictions)
    assert result["entities"]["precision"] == pytest.approx(1.0)
    assert result["entities"]["recall"] == pytest.approx(1.0)
    assert result["entities"]["f1"] == pytest.approx(1.0)


def test_duplicate_entity_normalization(sample_benchmark):
    prediction = {
        "id": "benchmark-001",
        "domain": "technology",
        "event_type": "announcement",
        "importance_score": 80,
        "entities": [
            {"name": "OpenAI", "entity_type": "ORGANIZATION"},
            {"name": "openai", "entity_type": "ORGANIZATION"},
            {"name": "AI", "entity_type": "TECHNOLOGY"},
            {"name": "HealthCare", "entity_type": "CONCEPT"},
        ],
    }
    metrics = calculate_entity_metrics(sample_benchmark[0], prediction)
    assert metrics["precision"] == pytest.approx(1.0)
    assert metrics["recall"] == pytest.approx(1.0)
    assert metrics["f1"] == pytest.approx(1.0)


def test_importance_mae_and_rmse(sample_benchmark, sample_predictions):
    result = evaluate_benchmark(sample_benchmark, predictions=sample_predictions)
    assert result["importance"]["mae"] == pytest.approx(3.0)
    assert result["importance"]["rmse"] == pytest.approx(3.16227766)


def test_empty_dataset_handling():
    result = evaluate_benchmark([])
    assert result["dataset"]["size"] == 0
    assert result["classification"]["accuracy"] == 0.0
    assert result["event_type"]["accuracy"] == 0.0
    assert result["entities"]["precision"] == 0.0
    assert result["entities"]["recall"] == 0.0
    assert result["entities"]["f1"] == 0.0
    assert result["importance"]["mae"] == 0.0
    assert result["importance"]["rmse"] == 0.0


def test_malformed_benchmark_handling():
    malformed = [{"id": "broken", "title": "missing fields"}]
    result = evaluate_benchmark(malformed)
    assert result["dataset"]["size"] == 0
    assert result["classification"]["accuracy"] == 0.0


def test_enrichment_metrics():
    metrics = {
        "total": 10,
        "successful": 7,
        "failed": 2,
        "fallback": 1,
        "skipped": 0,
    }
    result = evaluate_benchmark([], enrichment_metrics=metrics)
    assert result["enrichment"]["success_rate"] == pytest.approx(0.7)
    assert result["enrichment"]["fallback_rate"] == pytest.approx(0.1)
    assert result["enrichment"]["failure_rate"] == pytest.approx(0.2)


def test_latency_calculation():
    durations = [120.0, 200.0, 160.0]
    result = calculate_latency_metrics(durations)
    assert result["average_ms"] == pytest.approx(160.0)
    assert result["median_ms"] == pytest.approx(160.0)
    assert result["min_ms"] == pytest.approx(120.0)
    assert result["max_ms"] == pytest.approx(200.0)


def test_api_response_shape(client):
    response = client.get("/api/v1/evaluation/summary")
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == {"dataset", "classification", "event_type", "entities", "importance", "enrichment", "latency"}
    assert data["dataset"]["name"]
    assert data["dataset"]["size"] >= 0
    assert "accuracy" in data["classification"]
    assert "precision" in data["entities"]
    assert "mae" in data["importance"]


def test_deterministic_repeated_evaluation(sample_benchmark, sample_predictions):
    first = evaluate_benchmark(sample_benchmark, predictions=sample_predictions)
    second = evaluate_benchmark(sample_benchmark, predictions=sample_predictions)
    assert first == second


def test_load_benchmark_dataset(tmp_path):
    path = tmp_path / "benchmark.json"
    payload = {
        "name": "Test Bench",
        "version": "v1",
        "items": [
            {
                "id": "b-1",
                "title": "AI launch in healthcare",
                "content": "OpenAI announced a healthcare AI deployment.",
                "expected_domain": "technology",
                "expected_event_type": "announcement",
                "expected_importance_score": 80,
                "expected_entities": [{"name": "OpenAI", "entity_type": "ORGANIZATION"}],
            }
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    data = load_benchmark_dataset(path)
    assert data["dataset"]["name"] == "Test Bench"
    assert data["dataset"]["size"] == 1


def test_summary_endpoint_returns_404_for_missing_or_invalid_results(tmp_path, monkeypatch, client):
    invalid_path = tmp_path / "missing-results.json"
    monkeypatch.setattr("app.api.v1.evaluation.DEFAULT_RESULTS_PATH", invalid_path)
    response = client.get("/api/v1/evaluation/summary")
    assert response.status_code == 404

    invalid_path.write_text("{not valid json}", encoding="utf-8")
    response = client.get("/api/v1/evaluation/summary")
    assert response.status_code == 404
