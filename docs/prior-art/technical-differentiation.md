# TECHNICAL DIFFERENTIATION MATRIX

## Feature & Architecture Classification

| System Feature / Dimension | Classification | Prior-Art Context | FlashFacts Implementation |
|---|---|---|---|
| **RSS Ingestion & Deduplication** | COMMON | Standard news aggregator pattern | Content hashing + two-level event dedup |
| **Topic Domain Classification** | COMMON | standard text classification | Deterministic domain categorization |
| **Hierarchical Location Resolution** | PARTIALLY OVERLAPPING | Spatial KGs and Geo-parsers | World → Country → State → District → City hierarchy |
| **Event Chronology & Lineage** | PARTIALLY OVERLAPPING | Temporal Knowledge Graphs | Preceding / Current / Subsequent timeline graphs |
| **Exam Relevance Scoring** | POTENTIALLY DIFFERENTIATING | Manual EdTech curation | Explainable scoring across 7 competitive exams |
| **Source-Grounded MCQ Generation** | POTENTIALLY DIFFERENTIATING | Automated Question Generation | Grounded MCQs with deterministic fallback |

## Summary Hypothesis

The primary engineering contribution of FlashFacts is a unified event-centric framework linking spatial, temporal, domain, and provenance metadata to automated educational assessment.

