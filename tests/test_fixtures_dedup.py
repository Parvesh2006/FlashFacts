"""
Synthetic test data fixtures for deduplication testing.

These fixtures represent different deduplication scenarios to test:
1. Exact document duplicates
2. Same event, different sources
3. Similar titles, different events
4. Multi-source events
5. Unrelated articles with similar wording
"""

# Case 1: Exact Duplicate
# Same article published twice
CASE_1_EXACT_DUPLICATE = {
    "documents": [
        {
            "title": "Government Announces New AI Regulations",
            "content": "The government today announced comprehensive new regulations for artificial intelligence development.",
            "url": "https://example-gov.com/ai-regulations",
            "published_at": "2026-09-01T10:00:00Z",
            "source_id": 1,
        },
        {
            "title": "Government Announces New AI Regulations",
            "content": "The government today announced comprehensive new regulations for artificial intelligence development.",
            "url": "https://example-gov.com/ai-regulations",
            "published_at": "2026-09-01T10:00:00Z",
            "source_id": 2,
        }
    ],
    "expected_outcome": {
        "documents_stored": 1,
        "events_created": 1,
        "events_deduplicated": 0,
        "reasoning": "Same article from two sources - document dedup by content hash prevents duplicate storage"
    }
}

# Case 2: Same Event, Different Sources (Multi-Source)
# Different sources reporting the same real-world event with different wording
CASE_2_MULTI_SOURCE_EVENT = {
    "documents": [
        {
            "title": "New AI Policy Unveiled by Government",
            "content": "Government officials announced a new policy framework for AI regulation.",
            "url": "https://techcrunch.com/ai-policy",
            "published_at": "2026-09-01T08:00:00Z",
            "source_id": 1,
        },
        {
            "title": "Government Unveils AI Framework",
            "content": "New artificial intelligence framework released by government.",
            "url": "https://bbc.com/news/ai-framework",
            "published_at": "2026-09-01T09:00:00Z",
            "source_id": 2,
        },
        {
            "title": "New AI Regulation Announced",
            "content": "Government announces new regulations for artificial intelligence.",
            "url": "https://reuters.com/ai-regulation",
            "published_at": "2026-09-01T10:30:00Z",
            "source_id": 3,
        }
    ],
    "expected_outcome": {
        "documents_stored": 3,
        "events_created": 1,
        "events_deduplicated": 2,
        "event_sources": 3,
        "reasoning": "Three different documents from different sources describing the same event - should deduplicate to 1 event with 3 source links"
    }
}

# Case 3: Different Events with Similar Titles
# Articles with similar wording but different actual events
CASE_3_DIFFERENT_EVENTS_SIMILAR_TITLES = {
    "documents": [
        {
            "title": "Tech Company Announces Cloud Service",
            "content": "Microsoft announced a new cloud computing service for enterprise customers.",
            "url": "https://microsoft.com/cloud-announcement",
            "published_at": "2026-09-01T08:00:00Z",
            "source_id": 1,
        },
        {
            "title": "Tech Company Announces Cloud Service",
            "content": "Amazon AWS introduced a new cloud platform for data analysis.",
            "url": "https://aws.amazon.com/announcement",
            "published_at": "2026-09-01T08:15:00Z",
            "source_id": 2,
        }
    ],
    "expected_outcome": {
        "documents_stored": 2,
        "events_created": 2,
        "events_deduplicated": 0,
        "reasoning": "Similar titles but different companies and different products - should NOT deduplicate despite title similarity"
    }
}

# Case 4: Same Event, Different Publication Times
# One event reported over multiple days
CASE_4_SAME_EVENT_DIFFERENT_DATES = {
    "documents": [
        {
            "title": "Breaking: Space Launch Successful",
            "content": "SpaceX successfully launches new satellite constellation.",
            "url": "https://techcrunch.com/spacex-launch",
            "published_at": "2026-09-01T15:00:00Z",
            "source_id": 1,
        },
        {
            "title": "Space Launch Update: Mission Status",
            "content": "The SpaceX satellite launch completed all primary objectives.",
            "url": "https://space.com/spacex-update",
            "published_at": "2026-09-02T08:00:00Z",  # Next day
            "source_id": 2,
        }
    ],
    "expected_outcome": {
        "documents_stored": 2,
        "events_created": 2,  # Different event dates = different events (this is correct behavior)
        "events_deduplicated": 0,
        "reasoning": "Same real-world event but reported on different dates - may create separate events (depends on date sensitivity)"
    }
}

# Case 5: Unrelated Articles with Similar Keywords
# Articles using similar keywords but unrelated events
CASE_5_UNRELATED_SIMILAR_KEYWORDS = {
    "documents": [
        {
            "title": "AI Researchers Publish Breakthrough Paper",
            "content": "MIT researchers published a landmark paper on artificial intelligence applications in medicine.",
            "url": "https://mit.edu/ai-research",
            "published_at": "2026-09-01T10:00:00Z",
            "source_id": 1,
        },
        {
            "title": "Google AI Meets 'Breakthrough' Performance Targets",
            "content": "Google announced their new AI system achieved breakthrough performance on standard benchmarks.",
            "url": "https://google.com/ai-performance",
            "published_at": "2026-09-01T10:30:00Z",
            "source_id": 2,
        }
    ],
    "expected_outcome": {
        "documents_stored": 2,
        "events_created": 2,
        "events_deduplicated": 0,
        "reasoning": "Both mention 'AI' and 'breakthrough' but are different institutions with different announcements"
    }
}

# Case 6: Whitespace Variations
# Same article with different whitespace/formatting
CASE_6_WHITESPACE_VARIATIONS = {
    "documents": [
        {
            "title": "Government    Announces   New   Policy",
            "content": "The government announced a new policy today.  Multiple spaces.",
            "url": "https://gov.com/policy",
            "published_at": "2026-09-01T10:00:00Z",
            "source_id": 1,
        },
        {
            "title": "Government Announces New Policy",
            "content": "The government announced a new policy today. Single spaces.",
            "url": "https://gov.com/policy",
            "published_at": "2026-09-01T10:00:00Z",
            "source_id": 2,
        }
    ],
    "expected_outcome": {
        "documents_stored": 1,
        "events_created": 1,
        "events_deduplicated": 0,
        "reasoning": "Whitespace normalization should treat these as the same document"
    }
}

# Test Suite Definition
DEDUP_TEST_CASES = [
    ("Case 1: Exact Duplicate", CASE_1_EXACT_DUPLICATE),
    ("Case 2: Multi-Source Event", CASE_2_MULTI_SOURCE_EVENT),
    ("Case 3: Different Events Similar Titles", CASE_3_DIFFERENT_EVENTS_SIMILAR_TITLES),
    ("Case 4: Same Event Different Dates", CASE_4_SAME_EVENT_DIFFERENT_DATES),
    ("Case 5: Unrelated Similar Keywords", CASE_5_UNRELATED_SIMILAR_KEYWORDS),
    ("Case 6: Whitespace Variations", CASE_6_WHITESPACE_VARIATIONS),
]
