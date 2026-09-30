# PRIOR-ART LANDSCAPE: EVENT-CENTRIC SPATIO-TEMPORAL INTELLIGENCE SYSTEMS

## Executive Overview

This document provides a technical prior-art review covering event extraction, spatio-temporal news knowledge graphs, location-aware news recommendation, and educational current-affairs systems.

## Domain Matrix & Research Categories

| Domain Category | Key Prior Art Technologies | Primary Research Focus |
|---|---|---|
| **Event-Centric Knowledge Graphs** | Wikidata Events, GDELT, EventRegistry | Extracting structured event nodes from news streams |
| **Spatio-Temporal Aggregation** | Spatial-Temporal Knowledge Graphs (ST-KG), Geo-Parser | Hierarchical location resolution and temporal indexing |
| **Educational Current-Affairs** | Test-prep news portals (GK Today, AffairsCloud) | Domain-oriented curation for competitive exams |
| **Source-Grounded Question Generation** | QG models, T5/GPT-based MCQ generation | Constructing validated MCQs from source facts |

## Prior Art Overlap Analysis

Existing commercial news aggregators (Google News, Apple News) group articles primarily by story clusters using textual similarity. Event-centric knowledge graphs (GDELT, EventRegistry) emphasize global scale event extraction without specific exam-oriented educational utility or localized hierarchical district mapping. Competitive exam applications provide current-affairs quizzes but rely heavily on manual content curation without automated multi-level spatial extraction or source provenance metadata.

## Structural Position of FlashFacts

FlashFacts unifies:
1. **Event Extraction & Deduplication**: Event-level clustering over document-level aggregation.
2. **Hierarchical Geographic Resolution**: Multi-level spatial taxonomy (World → Country → State → District → City).
3. **Temporal & Chronological Lineage**: Relational context and event history tracking.
4. **Exam Relevance & Source-Grounded MCQs**: Automated explainable relevance scoring across competitive exams with deterministic option generation.

