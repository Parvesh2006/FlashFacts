#!/usr/bin/env python3
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
API_ROOT = REPO_ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.services.evaluation import DEFAULT_BENCHMARK_PATH, DEFAULT_RESULTS_PATH, evaluate_dataset_file, load_benchmark_dataset


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


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate FlashFacts benchmark events.")
    parser.add_argument("--dataset", default=str(DEFAULT_BENCHMARK_PATH), help="Path to benchmark JSON dataset.")
    parser.add_argument("--output", default=str(DEFAULT_RESULTS_PATH), help="Where to save the evaluation result JSON.")
    args = parser.parse_args()

    try:
        dataset = load_benchmark_dataset(args.dataset)
        items = dataset["items"]
        summary = evaluate_dataset_file(args.dataset)
        print_metrics(summary)

        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        runtime = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "dataset": summary["dataset"],
            "metrics": summary,
            "software": {"name": "FlashFacts", "version": "1.0.0"},
        }
        output_path.write_text(json.dumps(runtime, indent=2), encoding="utf-8")
        print(f"Results saved to: {output_path}")
        return 0
    except Exception as exc:
        print(f"Evaluation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
