# FlashFacts — PYQ Official Link Verification and Live Integrity Report

**Date of Execution**: October 26–27, 2026
**Project**: FlashFacts (`C:\FlashFacts`)
**Scope**: Full Application Audit & Live Source Verification across all examination boards (TNPSC, UPSC, SSC, RRB), direct candidate PDF verification, database schema migration, backend API routing, frontend badge & action alignment, and automated test suite.

---

## 1. Executive Summary

During testing of the FlashFacts Previous Year Questions (PYQ) module, the card for **TNPSC Group II / IIA Combined Civil Services Examination Preliminary Paper 2024** claimed official provenance but redirected users to:
```
https://www.tnpsc.gov.in/English/previous_question_papers.aspx
```
This link returned an **HTTP 404 (Resource Not Found)** error on the official TNPSC server. Furthermore, users were exposed to misleading or broken user journeys when external links drifted or failed.

To permanently resolve this across the entire system:
1. **TNPSC Group II / IIA Candidate PDF Verified**: A direct TNPSC-hosted question booklet candidate (`https://www.tnpsc.gov.in/Tentative/Document/08_2024_CCSEII_IIA_GS_GT.pdf`) was subjected to deep multi-layer verification (HTTP 200, PDF header/EOF integrity, 96 pages, 8.00 MB, Subject Code 003, Exam date 14/09/2024) and linked with the official answer-key archive (`https://www.tnpsc.gov.in/English/answerkeys.aspx`).
2. **Comprehensive Live Re-Audit of All 8 Records**: Every PYQ record across TNPSC, UPSC, SSC, and RRB was probed using bounded HTTP GET requests (rejecting HEAD-only requests, validating redirect targets, and rejecting root homepage fallbacks).
3. **Database Schema Migration**: Created and applied Alembic migration `012_pyq_verification_fields` adding `last_verified_at` with UTC timezone support to `pyq_papers`.
4. **Backend API Realignment**: Hardened `/api/v1/pyqs/papers/{id}/pdf` and `/download` to support `external_pdf` (redirecting via HTTP 307 to verified official PDF), `source_link_only` (redirecting to official archive page), and `temporarily_unavailable` (returning HTTP 503 with helpful retry context). Expanded authority host whitelist to include Indian Railways and UPSC canonical domains.
5. **Honest Frontend Representation**: Replaced ambiguous labels with 5 clear, mutually exclusive statuses:
   - **Verified Official Local PDF**
   - **Verified Official External PDF**
   - **Official Archive Link (Individual Paper Not Directly Verified)**
   - **Temporarily Unavailable**
   - **Unverified Source**
   Removed deceptive "Download PDF" or "View PDF" actions when no genuine PDF is verified.
6. **Automated Verification**: Expanded test suite to **129 passing backend tests** (including 30 tests in `test_pyq_papers.py`) and verified full **Next.js production build** (16/16 routes compiled cleanly with 0 TypeScript errors).

---

## 2. TNPSC Group II / IIA Candidate PDF Verification Evidence

The candidate PDF identified for TNPSC Group II / IIA 2024 Preliminary was inspected using bounded streaming GET requests and Python `pypdf`:

| Verification Parameter | Candidate Value | Verification Outcome |
| :--- | :--- | :--- |
| **Direct Candidate URL** | `https://www.tnpsc.gov.in/Tentative/Document/08_2024_CCSEII_IIA_GS_GT.pdf` | **VERIFIED (HTTP 200 OK)** |
| **HTTP Content-Type** | `application/pdf` | **VERIFIED** |
| **Content-Length** | 8,390,925 bytes (~8.00 MB) | **VERIFIED** |
| **PDF Magic Bytes** | Begins with `%PDF-1.4` | **VERIFIED** |
| **Structural Integrity** | Valid xref table and `%%EOF` trailer | **VERIFIED** |
| **Total Page Count** | **96 pages** | **VERIFIED** |
| **Notification Number** | Notification No. 08/2024 | **VERIFIED** |
| **Examination Title** | Combined Civil Services Examination - II / IIA (Preliminary) | **VERIFIED** |
| **Subject / Booklet** | General Studies with General Tamil (Subject Code: 003) | **VERIFIED** |
| **Examination Date** | **14/09/2024 Forenoon** (09:30 A.M. to 12:30 P.M.) | **VERIFIED** |
| **Paper Structure** | 200 Questions (Part A: Q1–100 General Tamil; Part B: Q101–175 GS + Q176–200 Aptitude) | **VERIFIED (Complete Question Booklet)** |
| **Official Archive URL** | `https://www.tnpsc.gov.in/English/answerkeys.aspx` | **VERIFIED (HTTP 200 OK)** |
| **Prior Broken URL** | `https://www.tnpsc.gov.in/English/previous_question_papers.aspx` | **REJECTED (HTTP 404 Not Found)** |

### Note on TNPSC Group 4 2024 Candidate Link
The tentative file `https://www.tnpsc.gov.in/Tentative/Document/01_2024_Final%20_Answer_Key_GT_GE.pdf` was also inspected. It is a **2-page answer key notice** rather than the full 200-question paper booklet. To maintain strict academic integrity, this record was **NOT** classified as `external_pdf`. It remains classified as `source_link_only` pointing to the official answer-keys portal (`https://www.tnpsc.gov.in/English/answerkeys.aspx`).

---

## 3. Comprehensive Record-by-Record Verification Ledger

Every paper record in the FlashFacts database was probed live. Below is the complete inventory:

| ID | Exam & Year | Previous URL & Status | Verified Destination | Verified Status | Frontend Primary Action |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `tnpsc-group2-2024-prelims-gen-studies` | TNPSC Group 2 (2024) | `.../previous_question_papers.aspx` (404 Not Found) | `https://www.tnpsc.gov.in/Tentative/Document/08_2024_CCSEII_IIA_GS_GT.pdf` (200 OK, 96p) & `https://www.tnpsc.gov.in/English/answerkeys.aspx` (200 OK) | `external_pdf` | **View Official PDF** (Direct official PDF viewer + Archive link) |
| `tnpsc-group4-2024-gen-studies-tamil` | TNPSC Group 4 (2024) | `.../previous_question_papers.aspx` (404 Not Found) | `https://www.tnpsc.gov.in/English/answerkeys.aspx` (200 OK) | `source_link_only` | **Open Official Archive** |
| `tnpsc-group4-2022-gen-studies-tamil` | TNPSC Group 4 (2022) | `.../previous_question_papers.aspx` (404 Not Found) | `https://www.tnpsc.gov.in/English/answerkeys.aspx` (200 OK) | `source_link_only` | **Open Official Archive** |
| `upsc-cse-2024-prelims-gs1` | UPSC CSE (2024) | `https://upsc.gov.in/examinations/...` (Redirects to homepage `/`) | `https://www.upsc.gov.in/examinations/previous-question-papers` (200 OK, Canonical archive) | `source_link_only` | **Open Official Archive** |
| `upsc-cse-2023-prelims-gs1` | UPSC CSE (2023) | `https://upsc.gov.in/examinations/...` (Redirects to homepage `/`) | `https://www.upsc.gov.in/examinations/previous-question-papers` (200 OK, Canonical archive) | `source_link_only` | **Open Official Archive** |
| `ssc-cgl-2024-tier1` | SSC CGL (2024) | `https://ssc.gov.in/candidate-portal/tentative-answer-keys` (Portal session gated) | `https://ssc.gov.in/candidate-portal/tentative-answer-keys` (Official Candidate Portal) | `source_link_only` | **Open Official Archive** |
| `ssc-chsl-2024-tier1` | SSC CHSL (2024) | `https://ssc.gov.in/candidate-portal/tentative-answer-keys` (Portal session gated) | `https://ssc.gov.in/candidate-portal/tentative-answer-keys` (Official Candidate Portal) | `source_link_only` | **Open Official Archive** |
| `rrb-ntpc-2019-cbt1` | RRB NTPC (2019) | `https://www.rrbcdg.gov.in/archive.php` (Dead / SSL Handshake Failure) | `https://rrb.indianrailways.gov.in/chandigarh` (200 OK, Active Indian Railways portal) | `source_link_only` | **Open Official Archive** |

---

## 4. Architectural & Implementation Details

### 4.1 Database Migration (`012_pyq_verification_fields`)
- Added column `last_verified_at: DateTime(timezone=True)` to table `pyq_papers`.
- Updated SQLAlchemy model [`apps/api/app/models/pyq_paper.py`](file:///C:/FlashFacts/apps/api/app/models/pyq_paper.py).
- Updated Pydantic response schema [`apps/api/app/schemas/pyq_paper.py`](file:///C:/FlashFacts/apps/api/app/schemas/pyq_paper.py) with `source_status` and `last_verified_at`.

### 4.2 Security & SSRF Protection
The URL validation system enforces strict host whitelisting and protocol controls:
- **HTTPS Only**: HTTP requests to unencrypted endpoints are rejected.
- **Approved Authority Hosts**:
  ```python
  _AUTHORITY_HOSTS = {
      "tnpsc.gov.in", "www.tnpsc.gov.in",
      "upsc.gov.in", "www.upsc.gov.in",
      "ssc.gov.in", "www.ssc.gov.in", "ssc.nic.in",
      "rrbcdg.gov.in", "www.rrbcdg.gov.in",
      "rrb.indianrailways.gov.in", "indianrailways.gov.in", "www.indianrailways.gov.in",
  }
  ```
- **Redirect Chain Validation**: When fetching or validating links, automated checks follow up to 5 redirects, verifying that every intermediate and destination host resides strictly within `_AUTHORITY_HOSTS`. Redirects to root homepages (`/`, `/index.html`) are rejected as non-specific.
- **Bounded GET vs HEAD Requests**: Several government web servers (e.g., NIC/TNPSC CDNs) return HTTP 403 or 405 on `HEAD` requests while serving valid PDFs on `GET`. The verification routine issues a bounded streaming `GET` request (reading only the initial 8 KB to check the `%PDF-` signature and header) to prevent network bloat while obtaining true status codes.

### 4.3 API Route Hardening (`apps/api/app/api/v1/pyqs.py`)
- **`/papers/{paper_id}/pdf`**:
  - If `storage_path` exists on disk & passes PDF validation &rarr; streams local PDF file (`application/pdf`).
  - If `pdf_url` is verified official external PDF &rarr; redirects via HTTP 307 to `pdf_url`.
  - If `source_link_only` &rarr; redirects via HTTP 307 to `source_url`.
  - If `temporarily_unavailable` &rarr; returns HTTP 503 Service Unavailable with explanation.
- **`/papers/{paper_id}/download`**:
  - Mirrors `/pdf` behavior with `Content-Disposition: attachment`.

### 4.4 Frontend Action & Badge Realignment (`apps/web`)
- **Badges**:
  - `verified_local`: Green badge — "Verified Official Local PDF"
  - `verified_external`: Blue badge — "Verified Official External PDF"
  - `archive_link`: Sky badge — "Official Archive Link (Individual Paper Not Directly Verified)"
  - `unavailable`: Amber badge — "Temporarily Unavailable"
  - `unverified`: Gray badge — "Unverified Source"
- **Primary Action Buttons**:
  - For `verified_external`: Displays "View Official PDF" (opens official PDF directly) alongside secondary "Official Portal Archive".
  - For `archive_link`: Displays "Open Official Archive" with clear disclaimer that the link points to the commission's question paper / answer key archive.
  - For `unavailable`: Button is disabled and labeled "Temporarily Unavailable" with no fake download action.

---

## 5. Verification & Testing Evidence

### 5.1 Backend Automated Tests (129 Passed)
The backend test suite was executed inside the production Docker container:
```bash
docker exec flashfacts-api pytest
```
**Results**:
- **129 passed, 0 failed, 9 warnings in 9.38s**.
- PYQ Paper tests in [`tests/test_pyq_papers.py`](file:///C:/FlashFacts/tests/test_pyq_papers.py) expanded to 30 tests:
  - `test_verified_external_pdf_redirect`: Confirms HTTP 307 redirect to direct official PDF candidate.
  - `test_unavailable_source_returns_503`: Confirms HTTP 503 response when paper source is temporarily down.
  - `test_extended_authority_hosts`: Validates `rrb.indianrailways.gov.in` and `www.upsc.gov.in`.
  - `test_pyq_detail_includes_verification_fields`: Validates `last_verified_at` and `source_status` in API response.
  - Path traversal defense, HTML rejection, and corrupted PDF rejection tests all green.

### 5.2 Frontend Build & TypeScript Verification
Executed production build on Next.js frontend:
```bash
npx tsc -p apps/web/tsconfig.json --noEmit
npm --prefix apps/web run build
```
**Results**:
- TypeScript type check: **0 errors**.
- Next.js 16.3.1 webpack build: **Compiled successfully in 7.7s**.
- Static generation: **16/16 routes compiled and prerendered** including `/pyqs`, `/exams`, `/mock-tests`.
- Exit code: **0**.

---

## 6. Scheduled Re-Verification & Maintenance Protocol

To prevent future link degradation:
1. **Periodic Link Health Check**:
   - Run the link verification script [`scripts/verify_and_update_all_pyqs.py`](file:///C:/FlashFacts/scripts/verify_and_update_all_pyqs.py) weekly or bi-weekly via scheduled cron automation.
   - If a source URL responds with 404, 5xx, or SSL alert, the automation sets `availability_status="temporarily_unavailable"` and records `last_verified_at`.
2. **Alerting on Candidate URL Updates**:
   - Examination boards periodically rotate tentative answer key URLs to final archive pages. Automated checks that detect 301/302 redirects log the updated canonical URL for administrative review before committing.
3. **Strict Prohibition on Fabricated Data**:
   - Never generate single-page synthetic PDF stubs.
   - Never classify an answer-key notice as a full question booklet.
   - Never present a homepage redirect as a verified direct paper.
