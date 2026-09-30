# PAPER SECTION: ARCHITECTURE & SYSTEM DESIGN

## Abstract Architectural Description

FlashFacts implements an event-centric spatio-temporal current-affairs intelligence architecture. Unlike traditional document-centric news aggregators, the system extracts canonical event instances from heterogeneous RSS feeds, normalizes their spatial and temporal attributes, maps them onto competitive examination syllabi, and generates grounded evaluation artifacts.

## System Pipeline Stages

1. **Document Ingestion & Fingerprinting**: Fetching RSS feeds with retry mechanisms and computing SHA-256 document hashes for level-1 deduplication.
2. **Event Extraction & Consolidation**: Clustering documents into distinct event entities using level-2 title/date matching.
3. **Spatial Hierarchy Resolution**: Mapping event text to normalized reference geographic nodes (World, Country, State, District, City).
4. **Temporal Lineage Extraction**: Linking events into chronological sequences (Preceding, Current, Subsequent).
5. **Exam Relevance & MCQ Generation**: Deterministically scoring events for competitive exams and producing grounded 4-option MCQs with explanations.

