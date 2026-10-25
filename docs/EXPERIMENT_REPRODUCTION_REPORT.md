# FlashFacts — Experiment Reproduction & Empirical Benchmark Report

**Execution Date**: October 2026
**Benchmarking Environment**:
- **Host OS**: Windows 11 Enterprise (x86_64)
- **Container Engine**: Docker Desktop 24.0.7 / Linux Alpine Engine
- **Backend Runtime**: Python 3.11.17, FastAPI 0.110.0, SQLAlchemy 2.0.27
- **Database**: PostgreSQL 15 (Alpine) with 5,070 live ingested news events
- **Cache**: Redis 7.0 (Alpine)
- **Frontend**: Node.js 20.11.0, Next.js 14.1.0 (App Router), TypeScript 5.3.3

---

## 1. Experiment 1: News Relevance Classification Reproduction

### 1.1 Methodology & Execution
To determine the empirical accuracy of the news relevance classifier, tests were executed against real records stored in the live PostgreSQL database rather than synthetic mock strings.

- **Classifier Code**: `apps/api/app/services/classification.py:KeywordDomainClassifier`
- **Relevance Scoring**: `apps/api/app/services/exam_intelligence.py:ExamIntelligenceService.score_event_for_exam`
- **Feed Exclusion Rule**: `apps/api/app/repositories/event_repository.py` (~Event.domain.in_(["Entertainment", "Crime", "Lifestyle", "Gossip", "Cinema"]))

### 1.2 Execution Commands
```bash
docker compose exec api python -c "
from app.core.database import SessionLocal
from app.models.event import Event
from app.services.classification import KeywordDomainClassifier

db = SessionLocal()
classifier = KeywordDomainClassifier()

# Experiment A: Pure Crime vs Pure Government
crime_events = db.query(Event).filter(Event.domain == 'Crime').all()
govt_events = db.query(Event).filter(Event.domain == 'Government').limit(len(crime_events)).all()
...
"
```

### 1.3 Empirical Results

#### Experiment A: Pure Crime vs Government Records ($N = 50$)
Evaluates the classifier's ability to discriminate between explicit localized crime reports and governmental policy developments.

| Ground Truth Category | Sample Size | Classified Correctly | Misclassified | Raw Outcome |
| :--- | :---: | :---: | :---: | :---: |
| **Exam Relevant (Government)** | 25 | 25 | 0 | True Positives (TP) = 25, False Negatives (FN) = 0 |
| **Non-Exam Relevant (Crime)** | 25 | 25 | 0 | True Negatives (TN) = 25, False Positives (FP) = 0 |

- **Accuracy**: 100.0%
- **Precision**: 100.0%
- **Recall**: 100.0%
- **F1 Score**: 1.0000

#### Experiment B: Heterogeneous Multi-Domain Noise Filtering ($N = 200$)
Evaluates the classifier across a broad cross-section of 100 non-exam events (25 Crime + 48 Entertainment + 27 Sports) and 100 core exam events (40 Government + 20 Economy + 20 Environment + 20 Science).

```
Confusion Matrix (N = 200):
                 Predicted Relevant    Predicted Non-Relevant
Actual Relevant         98 (TP)                2 (FN)
Actual Non-Relevant     65 (FP)               35 (TN)
```

- **Accuracy**: **66.50%**
- **Precision**: **60.12%** ($98 / (98 + 65)$)
- **Recall**: **98.00%** ($98 / (98 + 2)$)
- **F1 Score**: **0.7452** ($2 \times 0.6012 \times 0.98 / (0.6012 + 0.98)$)

### 1.4 Critical Findings on Data Leakage
1. **Train/Test Contamination**: Specific substrings from the negative test prompt (`"4 போன்கள்"`, `"செல்போன் கடை ஊழியரை ஏமாற்றி"`) were hardcoded in `title_rules` within `classification.py`. While this guaranteed a pass on that isolated unit test, it introduces data leakage that does not generalize to novel crime phrasings.
2. **False Positive Dominance in Broad Feed**: Entertainment and sports reporting often mentions government ministers or regulatory bodies, causing 65 of 100 non-exam articles to be classified as Technology or Government, degrading multi-domain precision to 60.12%.

---

## 2. Experiment 2: Indic / Tamil Unicode Normalization Benchmark

### 2.1 Methodology & Execution
Evaluating character preservation and token collision resistance between standard ASCII normalization (`re.sub(r'[^\w\s]', '', text)`) and FlashFacts Indic Normalization (`normalize_text()`).

- **Source Code**: `apps/api/app/utils/hashing.py:normalize_text`
- **Dataset**: Systematic inflection grid comprising 10 primary Tamil consonant roots (`க, ச, த, ப, ம, வ, ந, ர, ல, ய`), 12 vowel modifiers, and 6 terminal consonants (`ல், ர், ன், ம், ட், ப்`), generating **720 distinct lexical forms**.

### 2.2 Execution Command
```bash
python -c "
import sys, re
sys.path.insert(0, 'apps/api')
from app.utils.hashing import normalize_text
...
"
```

### 2.3 Empirical Results ($N = 720$)

| Metric | Naive ASCII Normalization (`[^\w\s]`) | FlashFacts Indic Normalization (`\u0900-\u0d7f`) |
| :--- | :---: | :---: |
| **Input Tokens Evaluated** | 720 | 720 |
| **Unique Hashes Generated** | 60 | **720** |
| **Colliding Token Pairs** | 660 | **0** |
| **Collision Rate** | **91.67%** | **0.00%** |
| **Vowel Sign Category Preservation** | Stripped (Mn/Mc dropped) | Preserved Intact |

- **Finding**: Naive regex stripping strips all Category `Mn` (combining mark, nonspacing) and Category `Mc` (combining mark, spacing) characters from Dravidian text. All 12 vowel variants of each consonant root collapse into identical 2-character consonant skeletons (e.g. `கால்`, `கில்`, `குல்`, `கேல்` all collapse to `கல`), producing 91.67% token collision. FlashFacts preserves 100% of distinct tokens.

---

## 3. Experiment 3: Live API Latency Benchmarks

### 3.1 Measurement Protocol
- **Client**: Python `urllib` HTTP client on host machine.
- **Target**: `http://localhost:8000` (Docker bridged network).
- **Procedure**: 5 warm-up requests per endpoint, followed by 50 timed consecutive requests.
- **Metrics**: Mean, Median, 95th Percentile (P95), Min, Max, and Standard Deviation.

### 3.2 Measured Distributions

| Endpoint | Status | Sample Count | Mean Latency | Median | P95 | Min / Max | StdDev |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `/health` | 200 | 50 | 10.74 ms | 10.66 ms | 18.25 ms | 5.40 / 19.41 ms | 3.62 ms |
| `/ready` | 200 | 50 | 11.26 ms | 11.42 ms | 15.09 ms | 7.70 / 15.51 ms | 2.17 ms |
| `/api/v1/pyqs/papers` | 200 | 50 | 21.37 ms | 20.11 ms | 30.15 ms | 14.59 / 46.03 ms | 5.68 ms |
| `/api/v1/pyqs/papers/filters` | 200 | 50 | 21.94 ms | 17.93 ms | 41.37 ms | 12.43 / 43.07 ms | 9.35 ms |
| `/api/v1/pyqs/papers/{id}` | 200 | 50 | 16.68 ms | 14.60 ms | 29.76 ms | 9.33 / 30.99 ms | 6.55 ms |
| `/api/v1/pyqs/papers/{id}/pdf` | 200 | 50 | 15.36 ms | 15.12 ms | 18.62 ms | 11.42 / 20.37 ms | 2.04 ms |
| `/api/v1/events?limit=20` | 200 | 50 | 91.40 ms | 86.82 ms | 133.30 ms | 67.30 / 167.61 ms | 21.68 ms |
| `/api/v1/domains` | 200 | 50 | 16.53 ms | 15.32 ms | 23.16 ms | 11.69 / 38.12 ms | 4.67 ms |

- **Analysis**: Direct streaming of verified PDF files (`/papers/{id}/pdf`) achieves a low, consistent mean latency of **15.36 ms** (P95: 18.62 ms) with minimal variance ($\sigma = 2.04$ ms), validating the path-containment streaming architecture.

---

## 4. Experiment 4: PYQ PDF Integrity & Document Verification

### 4.1 Ingestion & Checksum Verification
- **Storage Location**: `data/pyq_pdfs/`
- **Validation Engine**: `%PDF-1.4` magic byte header and SHA-256 cryptographic digests.

| Paper ID | Authority | Byte Length | Header Verified | SHA-256 Digest | Status |
| :--- | :--- | :---: | :---: | :--- | :---: |
| `tnpsc-group4-2024-gen-studies-tamil` | TNPSC | 2,813 bytes | `%PDF-1.4` | `28c687bcc37b13f0...` | **PASSED** |
| `tnpsc-group2-2024-prelims-gen-studies` | TNPSC | 2,724 bytes | `%PDF-1.4` | `64fd81cfbb3f2adc...` | **PASSED** |
| `tnpsc-group4-2022-gen-studies-tamil` | TNPSC | 2,581 bytes | `%PDF-1.4` | `1b16c441264afe08...` | **PASSED** |
| `upsc-cse-prelims-2024-gs1` | UPSC | 2,730 bytes | `%PDF-1.4` | `4209e627c40c210b...` | **PASSED** |
| `upsc-cse-prelims-2024-csat` | UPSC | 2,611 bytes | `%PDF-1.4` | `b14bf90f83d479e2...` | **PASSED** |
| `upsc-cds-2024-gk` | UPSC | 2,595 bytes | `%PDF-1.4` | `94c9c3c9cdc8196b...` | **PASSED** |
| `rrb-ntpc-2021-cbt1-ga` | RRB | 2,597 bytes | `%PDF-1.4` | `9a1b95c85a5ea895...` | **PASSED** |
| `ssc-cgl-2023-tier1-shift1` | SSC | 2,602 bytes | `%PDF-1.4` | `097a93428a61351f...` | **PASSED** |

- **Total Corpus Size**: **21,253 bytes (~21.7 KB)**.
- **Clarification**: Documents are valid, generated PDF sample test fixtures containing authentic syllabus questions and official authority metadata, referencing traceable source portal URLs.

---

## 5. Experiment 5: Software Integration Test Execution

### 5.1 Backend Pytest Execution
- **Command**: `docker compose exec api pytest tests/`
- **Duration**: 93.32 seconds
- **Pass Count**: **110 passed**, 0 failed, 9 harmless deprecation warnings.
- **Coverage**: Covers dual authentication, guest merging, Indic encoding, security isolation, timed tests, and question paper cataloging.

### 5.2 Frontend Compilation & Type Safety
- **Typecheck**: `npx tsc -p apps/web/tsconfig.json --noEmit` &rarr; **0 errors**.
- **Production Build**: `npm --prefix apps/web run build` &rarr; **16/16 routes compiled successfully**.
- **Live Serving**: Production server active and serving HTTP 200 responses on `http://localhost:3000`.
