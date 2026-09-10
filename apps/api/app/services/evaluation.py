import json
import math
import statistics
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union


REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_BENCHMARK_PATH = REPO_ROOT / "evaluation" / "benchmark_events.json"
DEFAULT_RESULTS_PATH = REPO_ROOT / "evaluation" / "results.json"


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip().lower()
    text = " ".join(text.split())
    return text


def normalize_entity_name(value: Any) -> str:
    return normalize_text(value).replace("-", " ")


def _as_dataset_items(dataset: Any) -> List[Dict[str, Any]]:
    if dataset is None:
        return []
    if isinstance(dataset, dict):
        item_list = dataset.get("items") or dataset.get("benchmarks") or []
        return item_list if isinstance(item_list, list) else []
    if isinstance(dataset, list):
        return [item for item in dataset if isinstance(item, dict)]
    return []


def _valid_benchmark_item(item: Dict[str, Any]) -> bool:
    required_fields = {
        "id",
        "title",
        "content",
        "expected_domain",
        "expected_event_type",
        "expected_importance_score",
        "expected_entities",
    }
    return bool(required_fields.issubset(item.keys())) and isinstance(item["expected_entities"], list)


def calculate_entity_metrics(expected_item: Dict[str, Any], prediction: Optional[Dict[str, Any]]) -> Dict[str, float]:
    expected_entities = expected_item.get("expected_entities") or []
    predicted_entities = (prediction or {}).get("entities") or []

    expected_names = {
        normalize_entity_name(entity.get("name"))
        for entity in expected_entities
        if isinstance(entity, dict) and entity.get("name")
    }
    predicted_names = {
        normalize_entity_name(entity.get("name"))
        for entity in predicted_entities
        if isinstance(entity, dict) and entity.get("name")
    }

    if not expected_names and not predicted_names:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0}

    true_positives = len(expected_names & predicted_names)
    precision = (true_positives / len(predicted_names)) if predicted_names else 0.0
    recall = (true_positives / len(expected_names)) if expected_names else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    return {"precision": round(precision, 6), "recall": round(recall, 6), "f1": round(f1, 6)}


def calculate_importance_metrics(expected_scores: Sequence[float], predicted_scores: Sequence[float]) -> Dict[str, float]:
    if not expected_scores and not predicted_scores:
        return {"mae": 0.0, "rmse": 0.0}

    pairs = []
    count = max(len(expected_scores), len(predicted_scores))
    for idx in range(count):
        expected = float(expected_scores[idx]) if idx < len(expected_scores) else 0.0
        predicted = float(predicted_scores[idx]) if idx < len(predicted_scores) else expected
        pairs.append((expected, predicted))

    if not pairs:
        return {"mae": 0.0, "rmse": 0.0}

    errors = [abs(predicted - expected) for expected, predicted in pairs]
    squared_errors = [(predicted - expected) ** 2 for expected, predicted in pairs]
    mae = sum(errors) / len(errors)
    rmse = math.sqrt(sum(squared_errors) / len(squared_errors))
    return {"mae": round(mae, 6), "rmse": round(rmse, 6)}


def calculate_latency_metrics(durations_ms: Sequence[float]) -> Dict[str, float]:
    if not durations_ms:
        return {"average_ms": 0.0, "median_ms": 0.0, "min_ms": 0.0, "max_ms": 0.0}

    values = [float(value) for value in durations_ms]
    return {
        "average_ms": round(sum(values) / len(values), 6),
        "median_ms": round(statistics.median(values), 6),
        "min_ms": round(min(values), 6),
        "max_ms": round(max(values), 6),
    }


def load_benchmark_dataset(path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    dataset_path = Path(path) if path is not None else DEFAULT_BENCHMARK_PATH

    try:
        with dataset_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {"dataset": {"name": "benchmark", "version": "v1", "size": 0}, "items": []}

    if isinstance(payload, dict):
        items = payload.get("items") or payload.get("benchmarks") or []
        metadata = {
            "name": payload.get("name", "Benchmark"),
            "version": payload.get("version", "v1"),
            "size": len(items) if isinstance(items, list) else 0,
        }
    else:
        items = payload if isinstance(payload, list) else []
        metadata = {"name": "Benchmark", "version": "v1", "size": len(items)}

    return {"dataset": metadata, "items": [item for item in items if isinstance(item, dict)]}


def evaluate_benchmark(
    dataset: Any,
    predictions: Optional[Sequence[Dict[str, Any]]] = None,
    enrichment_metrics: Optional[Dict[str, Any]] = None,
    latency_durations: Optional[Sequence[float]] = None,
) -> Dict[str, Any]:
    items = _as_dataset_items(dataset)
    valid_items = [item for item in items if _valid_benchmark_item(item)]
    strict_predictions = predictions is not None
    prediction_lookup = {str(pred.get("id")): pred for pred in (predictions or []) if isinstance(pred, dict) and pred.get("id") is not None}

    classification_total = 0
    classification_correct = 0
    event_type_total = 0
    event_type_correct = 0
    entity_precision_total = 0.0
    entity_recall_total = 0.0
    entity_f1_total = 0.0
    importance_errors = []
    expected_scores = []
    predicted_scores = []

    classification_accuracy = 0.0
    event_type_accuracy = 0.0
    entity_precision = 0.0
    entity_recall = 0.0
    entity_f1 = 0.0
    importance_mae = 0.0
    importance_rmse = 0.0

    for item in valid_items:
        item_id = str(item.get("id"))
        prediction = prediction_lookup.get(item_id)
        expected_domain = normalize_text(item.get("expected_domain"))
        expected_event_type = normalize_text(item.get("expected_event_type"))
        if strict_predictions:
            pred_domain = normalize_text((prediction or {}).get("domain") or (prediction or {}).get("classification"))
            pred_event_type = normalize_text((prediction or {}).get("event_type"))
        else:
            pred_domain = normalize_text((prediction or {}).get("domain") or (prediction or {}).get("classification") or item.get("expected_domain"))
            pred_event_type = normalize_text((prediction or {}).get("event_type") or item.get("expected_event_type"))

        if expected_domain:
            classification_total += 1
            if pred_domain == expected_domain:
                classification_correct += 1

        if expected_event_type:
            event_type_total += 1
            if pred_event_type == expected_event_type:
                event_type_correct += 1

        entity_metrics = calculate_entity_metrics(item, prediction)
        entity_precision_total += entity_metrics["precision"]
        entity_recall_total += entity_metrics["recall"]
        entity_f1_total += entity_metrics["f1"]

        expected_score = float(item.get("expected_importance_score", 0) or 0)
        if strict_predictions:
            raw_predicted = (prediction or {}).get("importance_score")
            pred_score = float(raw_predicted) if raw_predicted is not None else 0.0
        else:
            raw_predicted = (prediction or {}).get("importance_score", expected_score)
            pred_score = float(raw_predicted) if raw_predicted is not None else expected_score
        importance_errors.append(abs(pred_score - expected_score))
        expected_scores.append(expected_score)
        predicted_scores.append(pred_score)

    if classification_total:
        classification_accuracy = classification_correct / classification_total
    if event_type_total:
        event_type_accuracy = event_type_correct / event_type_total
    if valid_items:
        entity_precision = entity_precision_total / len(valid_items)
        entity_recall = entity_recall_total / len(valid_items)
        entity_f1 = entity_f1_total / len(valid_items)
        importance_metrics = calculate_importance_metrics(expected_scores, predicted_scores)
        importance_mae = importance_metrics["mae"]
        importance_rmse = importance_metrics["rmse"]

    raw_enrichment = enrichment_metrics or {"total": 0, "successful": 0, "failed": 0, "fallback": 0, "skipped": 0}
    total = int(raw_enrichment.get("total") or 0)
    successful = int(raw_enrichment.get("successful") or 0)
    failed = int(raw_enrichment.get("failed") or 0)
    fallback = int(raw_enrichment.get("fallback") or 0)
    skipped = int(raw_enrichment.get("skipped") or 0)
    success_rate = (successful / total) if total else 0.0
    fallback_rate = (fallback / total) if total else 0.0
    failure_rate = (failed / total) if total else 0.0

    latency_metrics = calculate_latency_metrics(latency_durations or [])

    return {
        "dataset": {
            "name": "Benchmark",
            "version": "v1",
            "size": len(valid_items),
        },
        "classification": {"accuracy": round(classification_accuracy, 6)},
        "event_type": {"accuracy": round(event_type_accuracy, 6)},
        "entities": {
            "precision": round(entity_precision, 6),
            "recall": round(entity_recall, 6),
            "f1": round(entity_f1, 6),
        },
        "importance": {
            "mae": round(importance_mae, 6),
            "rmse": round(importance_rmse, 6),
        },
        "enrichment": {
            "success_rate": round(success_rate, 6),
            "fallback_rate": round(fallback_rate, 6),
            "failure_rate": round(failure_rate, 6),
        },
        "latency": {
            "average_ms": latency_metrics["average_ms"],
            "median_ms": latency_metrics["median_ms"],
            "min_ms": latency_metrics["min_ms"],
            "max_ms": latency_metrics["max_ms"],
        },
    }


def evaluate_dataset_file(path: Optional[Union[str, Path]] = None, predictions: Optional[Sequence[Dict[str, Any]]] = None, enrichment_metrics: Optional[Dict[str, Any]] = None, latency_durations: Optional[Sequence[float]] = None) -> Dict[str, Any]:
    dataset = load_benchmark_dataset(path)
    benchmark = dataset["items"]
    metadata = dataset["dataset"]
    result = evaluate_benchmark(benchmark, predictions=predictions, enrichment_metrics=enrichment_metrics, latency_durations=latency_durations)
    result["dataset"] = {
        "name": metadata.get("name", "Benchmark"),
        "version": metadata.get("version", "v1"),
        "size": len(benchmark),
    }
    return result
