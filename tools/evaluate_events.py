#!/usr/bin/env python3
import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
API_ROOT = REPO_ROOT / "apps" / "api"

if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.schemas.enrichment import EventEnrichment
from app.services.ai_provider import FallbackAIProvider, get_ai_provider
from app.services.evaluation import (
    DEFAULT_BENCHMARK_PATH,
    DEFAULT_RESULTS_PATH,
    evaluate_benchmark,
    load_benchmark_dataset,
)
from app.utils.hashing import normalize_text


def print_metrics(summary: dict) -> None:
    dataset = summary["dataset"]

    print("=" * 50)
    print("FLASHFACTS EVALUATION")
    print("=" * 50)
    print()

    print("Dataset:")
    print(f"{dataset['name']} {dataset['version']}")
    print()

    print("Events evaluated:")
    print(dataset["size"])
    print()

    print("Classification Accuracy:")
    print(f"{summary['classification']['accuracy'] * 100:.2f}%")
    print()

    print("Event Type Accuracy:")
    print(f"{summary['event_type']['accuracy'] * 100:.2f}%")
    print()

    print("Entity Precision:")
    print(f"{summary['entities']['precision'] * 100:.2f}%")
    print()

    print("Entity Recall:")
    print(f"{summary['entities']['recall'] * 100:.2f}%")
    print()

    print("Entity F1:")
    print(f"{summary['entities']['f1'] * 100:.2f}%")
    print()

    print("Importance MAE:")
    print(f"{summary['importance']['mae']:.2f}")
    print()

    print("Importance RMSE:")
    print(f"{summary['importance']['rmse']:.2f}")
    print()

    print("Enrichment Success:")
    print(f"{summary['enrichment']['success_rate'] * 100:.2f}%")
    print()

    print("Fallback Rate:")
    print(f"{summary['enrichment']['fallback_rate'] * 100:.2f}%")
    print()

    print("Average Latency:")
    print(f"{summary['latency']['average_ms']:.2f} ms")
    print()

    print("Median Latency:")
    print(f"{summary['latency']['median_ms']:.2f} ms")
    print()

    print("=" * 50)


def build_prediction(provider, item: dict) -> tuple[dict, float, bool]:
    """
    Generate an actual FlashFacts enrichment prediction for one benchmark item.

    This intentionally does not create or persist a database Event because the
    benchmark is synthetic evaluation data.
    """
    title = item["title"]
    content = item.get("content", "")
    domain = "unknown"

    started = time.perf_counter()

    used_fallback = False

    try:
        raw = provider.enrich_event(
            title=title,
            content=content,
            domain=domain,
            reliability_score=1.0,
        )

        enrichment = EventEnrichment.model_validate(raw)

    except Exception:
        used_fallback = True

        fallback = FallbackAIProvider().enrich_event(
            title,
            content,
            domain,
            1.0,
        )

        enrichment = EventEnrichment.model_validate({
            **fallback,
            "provider": "fallback",
            "used_fallback": True,
        })

    latency_ms = (time.perf_counter() - started) * 1000

    # Apply the same entity grounding principle used by
    # EventEnrichmentService._ground_and_normalize().
    source_text = normalize_text(f"{title} {content}")

    grounded_entities = [
        entity
        for entity in enrichment.entities
        if normalize_text(entity.name) in source_text
    ]

    prediction = {
        "id": item["id"],
        "domain": enrichment.classification or "unknown",
        "classification": enrichment.classification or "unknown",
        "event_type": enrichment.event_type,
        "importance_score": enrichment.importance_score,
        "provider": enrichment.provider,
        "used_fallback": enrichment.used_fallback,
        "entities": [
            {
                "name": entity.name,
                "entity_type": entity.entity_type,
            }
            for entity in grounded_entities
        ],
    }

    return prediction, latency_ms, (
        used_fallback or enrichment.used_fallback
    )


def generate_predictions(dataset: dict) -> tuple[list[dict], dict]:
    """
    Run actual enrichment against every benchmark item.
    """
    provider = get_ai_provider()

    predictions = []
    latency_durations = []

    succeeded = 0
    fallback = 0
    failed = 0

    print("Generating actual predictions...")
    print()

    for item in dataset["items"]:
        print(f"Evaluating: {item['id']}")

        try:
            prediction, latency_ms, used_fallback = build_prediction(
                provider,
                item,
            )

            predictions.append(prediction)
            latency_durations.append(latency_ms)

            succeeded += 1
            if used_fallback:
                fallback += 1
                print(f"  Provider: fallback")
            else:
                print(f"  Provider: AI")

            print(f"  Domain: {prediction['domain']}")
            print(f"  Event Type: {prediction['event_type']}")
            print(f"  Importance: {prediction['importance_score']}")
            print(f"  Entities: {len(prediction['entities'])}")
            print(f"  Latency: {latency_ms:.2f} ms")
            print()

        except Exception as exc:
            failed += 1
            print(f"  FAILED: {exc}")
            print()

    enrichment_metrics = {
        "total": len(dataset["items"]),
        "successful": succeeded,
        "failed": failed,
        "fallback": fallback,
        "skipped": 0,
    }

    return predictions, {
        "enrichment": enrichment_metrics,
        "latency": latency_durations,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate FlashFacts benchmark events."
    )

    parser.add_argument(
        "--dataset",
        default=str(DEFAULT_BENCHMARK_PATH),
        help="Path to benchmark JSON dataset.",
    )

    parser.add_argument(
        "--output",
        default=str(DEFAULT_RESULTS_PATH),
        help="Where to save the evaluation result JSON.",
    )

    args = parser.parse_args()

    try:
        dataset = load_benchmark_dataset(args.dataset)

        predictions, runtime_metrics = generate_predictions(dataset)

        summary = evaluate_benchmark(
            dataset,
            predictions=predictions,
            enrichment_metrics=runtime_metrics["enrichment"],
            latency_durations=runtime_metrics["latency"],
        )

        print_metrics(summary)

        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        runtime = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "dataset": summary["dataset"],
            "metrics": summary,
            "predictions": predictions,
            "software": {
                "name": "FlashFacts",
                "version": "1.0.0",
            },
        }

        output_path.write_text(
            json.dumps(runtime, indent=2),
            encoding="utf-8",
        )

        print(f"Results saved to: {output_path}")

        return 0

    except Exception as exc:
        print(f"Evaluation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())