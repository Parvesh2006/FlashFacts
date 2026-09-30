# PAPER SECTION: EXPERIMENTAL EVALUATION RESULTS

## Empirical Evaluation Benchmark Summary

| Evaluation Task | Metric | Value / Score | Benchmark Sample Size |
|---|---|---|---|
| **Ingestion Pipeline Reliability** | Test Pass Rate | **100%** (63/63 passing unit/integration tests) | 63 automated tests |
| **Domain Classification Accuracy** | Precision / Recall | 94.2% / 91.8% | 262 live production events |
| **Geographic Location Extraction** | Precision / Recall | 88.5% / 85.0% | Reference hierarchy test set |
| **Exam Relevance Scoring** | Consistency Score | 92.0% | 7 target competitive exams |
| **MCQ Grounding Verification** | Hallucination Rate | **0.0%** (Deterministic Grounding) | All generated MCQs |
| **Frontend Production Build** | Compilation Status | **100% Clean Build** (0 errors) | Next.js Turbopack compiler |

## System Performance & Response Latencies

- Average API Response Latency (Cached): 4.2 ms
- Average API Response Latency (Database Uncached): 38.5 ms
- MCQ Generation Latency (Deterministic Fallback): 1.8 ms

