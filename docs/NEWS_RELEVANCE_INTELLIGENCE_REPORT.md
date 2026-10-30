# FlashFacts Master News Relevance, Content Cleaning, and Feed Quality Report

**Date**: October 27, 2026
**Status**: Verified & Production Ready
**Scope**: News Ingestion, Content Cleaning, Syllabus-Based Exam Relevance Filtering, Database Backfill, Frontend Realignment, and Automated Test Coverage.

---

## 1. Executive Summary

FlashFacts previously suffered from general news leakage into competitive-exam feeds (TNPSC Group 4, Group 2, UPSC, SSC, RRB). News feeds contained celebrity gossip, local crime, partisan political quarrels, routine corporate layoff notices, and viral human-interest clips. Furthermore, raw HTML fragments (e.g. `<figure>`, `<div id="gumlet_video_player">`) survived ingestion, and summaries frequently duplicated headlines.

To resolve these defects permanently, we designed, implemented, and verified an end-to-end multi-layer pipeline:
1. **Schema Migration (Alembic `013`)**: Added `is_exam_eligible`, `rejection_reason`, `inclusion_reason`, and `syllabus_topic` to the `events` table.
2. **Standard Library Content Cleaning Service (`ContentCleaningService`)**: Recursively strips HTML tags, discards inner content of `<script>`, `<style>`, `<figure>`, and `<iframe>`, unescapes nested entities, preserves Indic/Tamil Unicode, and strips duplicate leading headlines.
3. **Syllabus-Based Relevance Service (`NewsRelevanceService`)**: Enforces word-boundary regex matching across 8 official exam domains while explicitly rejecting routine crime, entertainment gossip, corporate severance notices, and viral stories. Landmark legal decisions and major policy schemes are explicitly exempted.
4. **Pipeline & API Enforcement**: Filtered non-exam domains and ineligible articles at the repository level (`is_exam_eligible.is_(True)`), blocked ineligible articles from MCQ generation, and removed raw HTML and title repetitions on API response generation.
5. **Frontend Realignment**: Completely removed "Event Chronology & Context" and timeline components from event detail views.
6. **Data Backfill & Database Migration**: Backed up 6,618 existing events and reprocessed all records idempotently in PostgreSQL.

---

## 2. Quantitative Results & Evaluation Breakdown

### Database Reclassification & Cleaning Statistics (PostgreSQL)

| Metric | Count | Percentage |
| :--- | :--- | :--- |
| **Total Articles Evaluated** | **6,618** | **100.0%** |
| **Accepted (Exam-Eligible)** | **833** | **12.6%** |
| **Rejected (Ineligible / Excluded)** | **5,785** | **87.4%** |
| **Articles with Raw HTML Cleaned** | **780** | **11.8%** |
| **Articles with Headline Repetitions Removed** | **6,520** | **98.5%** |
| **Duplicate Cross-Feed Stories Detected** | **204** | **3.1%** |
| **Uncertain / Borderline Cases** | **0** | **0.0%** |

### Live API Verification (`/api/v1/events?limit=100`)

| Quality Verification Check | Target | Measured Result | Status |
| :--- | :--- | :--- | :--- |
| **Raw HTML tags (`<` or `>`) in summaries** | 0 | **0** | **PASSED** |
| **Ineligible articles in public feeds** | 0 | **0** | **PASSED** |
| **Repeated headlines at start of summaries** | 0 | **0** | **PASSED** |
| **Tamil Unicode text preservation** | 100% | **100% (No mojibake)** | **PASSED** |
| **TypeScript / Next.js Production Build Errors** | 0 | **0 (16/16 routes static)** | **PASSED** |
| **Backend Test Suite Pass Rate** | 100% | **144 / 144 passed (100%)** | **PASSED** |

---

## 3. Evaluation of Mandated Test Cases

Each required test scenario was validated through automated tests in [`tests/test_master_news_relevance.py`](file:///C:/FlashFacts/tests/test_master_news_relevance.py) and live evaluation:

### A. Negative Exclusion Cases (Must be Excluded)

1. **SK / Black Pandi Entertainment**:
   - *Headline*: நடிகர் சிவகார்த்திகேயன் மற்றும் பிளாக் பாண்டி புதிய நகைச்சுவை படம் அப்டேட்
   - *Result*: **Excluded** (`is_exam_eligible: False`, score: 10).
   - *Reason*: Entertainment / celebrity content.
2. **Routine Prison Escape / Local Theft**:
   - *Headline*: மத்திய சிறையிலிருந்து தப்பியோடிய கைதி வடவள்ளியில் கைது: போலீசார் நடவடிக்கை
   - *Result*: **Excluded** (`is_exam_eligible: False`, score: 10).
   - *Reason*: Routine crime report.
3. **Microsoft Voluntary Employee Exit Packages**:
   - *Headline*: Microsoft offers voluntary exit packages to employees in global cost-cutting move
   - *Result*: **Excluded** (`is_exam_eligible: False`, score: 15).
   - *Reason*: Routine corporate announcement without substantive policy relevance.
4. **Ordinary Shark Rescue Viral Video**:
   - *Headline*: Beachgoers rescue stranded baby shark washed ashore in viral video
   - *Result*: **Excluded** (`is_exam_eligible: False`, score: 10).
   - *Reason*: Insufficient educational relevance / viral animal story.
5. **High Confidence Does Not Override Relevance**:
   - *Headline*: Instagram's latest feature lets you add tagged posts to your profile
   - *Result*: **Excluded** (`is_exam_eligible: False`, score: 15) even when classified under "Technology" with 100% confidence.

### B. Positive Inclusion Cases (Must be Retained)

1. **UN Security Council Veto Developments involving India**:
   - *Headline*: India calls for United Nations Security Council reform and scrutiny of veto power
   - *Result*: **Retained** (`is_exam_eligible: True`, score: 75, topic: *International Relations & Multilateral Forums*).
2. **Major Scientific Breakthroughs & Space Missions**:
   - *Headline*: ISRO successfully conducts qualification test of cryogenic engine for Gaganyaan mission
   - *Result*: **Retained** (`is_exam_eligible: True`, score: 80, topic: *Science, Technology & Innovation*).
3. **Tamil Nadu Government Schemes**:
   - *Headline*: Tamil Nadu Cabinet approves expansion of Chief Minister's Breakfast Scheme
   - *Result*: **Retained** (`is_exam_eligible: True`, score: 105, topic: *Government Schemes & Social Welfare*).
4. **Landmark Court Judgments & Bharatiya Nyaya Sanhita (BNS)**:
   - *Headline*: Supreme Court Constitution Bench delivers landmark judgment on Bharatiya Nyaya Sanhita
   - *Result*: **Retained** (`is_exam_eligible: True`, score: 95, topic: *Indian Polity & Constitutional Governance*).

---

## 4. Key Architectural Implementations

### 1. Robust HTML Cleaning Service (`ContentCleaningService`)
- Implemented with standard library `html.parser.HTMLParser` with zero third-party dependencies (`bs4` not required).
- Completely discards tags AND inner contents for `<script>`, `<style>`, `<figure>`, `<iframe>`, `<video>`, `<audio>`, `<noscript>`, and `<svg>`.
- Multi-pass entity resolution (up to 3 passes) unescapes nested entities (e.g. `&amp;amp;` -> `&`).
- Strips inline image links, tracking query parameters, and publisher boilerplate (e.g., "Also Read", "Watch Video").
- Preserves Tamil/Indic Unicode codepoints (`\u0B80-\u0BFF`) without corruption.

### 2. Multi-Pass Duplicate Headline Elimination
- Direct prefix match ignoring trailing punctuation (`.`, `!`, `?`, `-`, `|`, `…`, `""`, `‘’`, `“”`).
- Normalized token match comparing word stems without punctuation.
- When an RSS feed only contains a single-sentence title without body content, the clean title is preserved without blanking out the summary.

### 3. Repository & API Layer Filtering
- All candidate feeds, event listings, and full-text searches enforce `Event.is_exam_eligible.is_(True)`.
- Non-exam domains (`Entertainment`, `Crime`, `Lifestyle`, `Gossip`, `Cinema`) are filtered out of general competitive-exam feeds.
- Ineligible articles are blocked from MCQ generation with informative educational diagnostics.

### 4. Frontend Simplification
- In [`apps/web/components/events/event-detail-view.tsx`](file:///C:/FlashFacts/apps/web/components/events/event-detail-view.tsx), completely removed the "Event Chronology & Context" section and all timeline nodes.
- Enhanced the Intelligence Summary display with the identified syllabus topic badge and official inclusion reason.

---

## 5. Verification Artifacts & Test Logs

### Test Suite Execution
```bash
docker exec flashfacts-api pytest -v tests/test_master_news_relevance.py
======================== 15 passed, 9 warnings in 0.71s ========================

docker exec flashfacts-api pytest
======================= 144 passed, 9 warnings in 8.83s ========================
```

### Next.js Production Build
```bash
npm --prefix apps/web run build
▲ Next.js 16.3.1 (webpack)
✓ Compiled successfully in 12.3s
✓ Running TypeScript ... Finished in 10.2s
✓ Generating static pages using 11 workers (16/16) in 1780ms
```

### Database Backups
- Complete JSON backups created before and during backfill:
  - `/app/backups/events_backup_20261027_044949.json` (6,595 events, 8.33 MB)
  - `/app/backups/events_backup_20261027_053439.json` (6,618 events, 7.63 MB)
