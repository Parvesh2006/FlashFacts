# PAPER SECTION: LIMITATIONS AND FUTURE WORK

## Known Limitations

1. **Deterministic Rule Fallbacks**: When external LLM APIs are unavailable, domain classification and MCQ generation rely on deterministic rule-based algorithms.
2. **Reference Spatial Coverage**: Geographic location extraction currently operates over pre-defined hierarchical reference nodes (World, Countries, Indian States, Districts, Cities).
3. **RSS Source Coverage**: Event ingestion depends on active, well-formatted RSS feeds from primary news organizations.

## Future Research Directions

1. Fine-tuning local open-weight LLMs (e.g., Llama 3 / Mistral) for offline spatial-temporal event extraction.
2. Automated syllabus ingestion and dynamic exam relevance weight tuning.
3. Multi-lingual current affairs processing across regional languages.

