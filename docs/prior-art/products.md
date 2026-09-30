# PRIOR-ART ANALYSIS: COMMERCIAL PRODUCTS & PLATFORMS

## Product Comparison

| Product / Platform | Primary Mechanism | Temporal Features | Geographic Granularity | Educational/Exam Utility | Source Provenance |
|---|---|---|---|---|---|
| **Google News** | Textual clustering & ranking | Article timestamp | Country/City | None (General News) | URL Redirect |
| **GDELT Project** | Global news event extraction | Event timestamp | Country/Coordinates | Academic / Research | Source URL |
| **GKToday / AffairsCloud** | Manual editorial current affairs | Daily/Monthly PDF | Country/State | High (Manual MCQs) | Weak / Omitted |
| **FlashFacts Platform** | Automated Event Extraction + Spatio-Temporal Graph | Event date + Chronological timeline | World → State → District → City | Automated Exam Relevance + Grounded MCQs | Full Source Metadata + Fingerprint |

## Key Product Differences & Technical Gaps

1. **Automation vs Manual Curation**: Existing exam prep portals rely on manual human authoring of current affairs summaries and quizzes. FlashFacts automates the entire ingestion-to-MCQ pipeline.
2. **Event-Centricity vs Document-Centricity**: Mass aggregators focus on article lists. FlashFacts extracts unified event entities that consolidate multiple source documents while retaining provenance.
3. **Hierarchical Spatial Resolution**: Standard news APIs offer keyword search for locations; FlashFacts implements parent-child spatial graph traversal (e.g., Coimbatore -> Tamil Nadu -> India).

