# Ground Truth Dataset

This directory contains templates and guidelines for creating ground-truth datasets to evaluate FlashFacts' ingestion accuracy.

## Files

### ground_truth_events.csv

A template CSV file for manually annotating documents with expected classifications and event linkages.

**Purpose**: Enable comparison between FlashFacts' automated deduplication/classification and human expert judgment.

**NOT FOR FABRICATED DATA**: This file should only be populated through careful manual review by domain experts. Do not create fake labels.

## How to Use

1. **Export Documents**: Export documents from a test ingestion run
   ```bash
   python tools/export_ingestion_metrics.py
   ```

2. **Manual Review**: Open `ground_truth_events.csv` and fill in expected values for a sample of documents
   - Review document content in the database
   - Determine if it's a duplicate of another document
   - Assign it to an event (or mark as no event)
   - Classify the domain
   - Extract key entities
   - Record importance level

3. **Evaluation**: Compare ground-truth labels against FlashFacts' automatic classifications
   - Document deduplication accuracy
   - Event deduplication accuracy
   - Domain classification accuracy
   - Entity extraction accuracy

## Columns

- **document_id**: Reference to documents.id
- **expected_event_id**: Which event this document should link to (NULL if none)
- **expected_domain**: Domain classification (AI, Technology, Politics, Government, Education, Medical, Engineering, Science, Economy, Sports, Environment, International, Defence)
- **expected_is_duplicate**: Is this a duplicate of another document?
- **expected_entities**: Comma-separated named entities (PERSON, ORGANIZATION, COUNTRY, TECHNOLOGY, PROGRAM, CONCEPT)
- **expected_importance**: Importance score (0-100)
- **reviewer_notes**: Justification for the labels

## Best Practices

1. **Sample size**: Start with 50-100 documents for initial evaluation
2. **Diverse sources**: Include documents from multiple sources
3. **Difficult cases**: Include edge cases (similar titles, multi-source events, etc.)
4. **Multiple reviewers**: Have 2-3 independent reviewers for high-value datasets
5. **Track disagreement**: Record when reviewers disagree on classification
6. **Document rationale**: Use reviewer_notes to explain classifications

## Research Use

This ground-truth data enables:
- Precision/recall measurement for deduplication
- F1-score evaluation for classification
- Comparison to published benchmarks
- Publication of research results

**Remember**: Do not fabricate data. Only actual expert annotations add scientific value.
