# FlashFacts Current Limitations

Last updated: 2026-09-19

- Geographic reference data is intentionally small and does not represent complete global or India coverage.
- Geographic extraction is deterministic alias matching, not full geoparsing.
- Event deduplication is title/date hash based, not semantic deduplication.
- Event timelines currently include same-domain chronological context unless explicit relations are created; this is not proof of causal or story lineage.
- The fallback AI provider is deterministic and does not provide semantic embeddings.
- MCQ fallback is source-grounded deterministic generation, not LLM generation.
- Redis cache invalidation is incomplete and currently relies mostly on TTL behavior.
- Docker/PostgreSQL/Redis live startup could not be verified in this pass because Docker access was denied.
- Prior-art and patent documentation require source-backed review before being used for novelty or legal strategy.
- Performance/load-test results have not been measured in this pass.

