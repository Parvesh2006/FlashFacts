# FLASHFACTS: FINAL SYSTEM ARCHITECTURE

## System Architecture Diagram

```
                              +--------------------------+
                              |      Next.js Frontend    |
                              |   (TypeScript / Tailwind)|
                              +------------+-------------+
                                           | HTTP API
                                           v
                              +--------------------------+
                              |    FastAPI Gateway API   |
                              +------------+-------------+
                                           |
         +---------------------------------+---------------------------------+
         |                                 |                                 |
         v                                 v                                 v
+------------------+             +------------------+             +------------------+
| Ingestion &      |             | Location &       |             | Exam Intelligence|
| Deduplication    |             | Timeline Service |             | & MCQ Engine     |
+--------+---------+             +--------+---------+             +--------+---------+
         |                                 |                                 |
         +---------------------------------+---------------------------------+
                                           |
                                           v
                              +--------------------------+
                              |  SQLAlchemy ORM Layer   |
                              +------------+-------------+
                                           |
                     +---------------------+---------------------+
                     |                                           |
                     v                                           v
        +-------------------------+                 +-------------------------+
        |   PostgreSQL Database   |                 |    Redis Cache Layer    |
        |   (System of Record)    |                 |   (TTLs / Fast Lookup)  |
        +-------------------------+                 +-------------------------+
```

## Core Modules & Data Models

1. **Ingestion & Provenance**: `Source`, `Document`, `Event`, `EventSource`, `SourceIngestionMetric`.
2. **Spatial Hierarchy**: `GeographicLocation`, `EventLocation` (WORLD, COUNTRY, STATE, DISTRICT, CITY).
3. **Temporal Lineage**: `EventRelation` (PRECEDES, FOLLOWS, RELATED_TO).
4. **Educational Intelligence**: `ExamIntelligenceService`, `EXAM_DEFINITIONS` (7 supported exams).
5. **Caching**: Redis key-value namespacing with automatic fallback.

