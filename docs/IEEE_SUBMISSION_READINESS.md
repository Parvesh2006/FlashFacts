# FlashFacts — IEEE Research Manuscript Submission Readiness Audit

**Audit Date**: October 2026
**Target Venue**: IEEE Conference on Artificial Intelligence in Education / IEEE International Conference on Advanced Learning Technologies (ICALT)
**Manuscript Location**: `docs/IEEE_PAPER_DRAFT.md`
**Current Readiness Status**: **SUBMISSION-READY (AFTER INTEGRATING EMPIRICAL AUDIT REVISIONS)**

---

## 1. Compliance Checklist with IEEE Standards

| Section / Dimension | Standard IEEE Requirement | Current Draft Status | Required Revision / Action Taken |
| :--- | :--- | :---: | :--- |
| **Title & Scope** | Concise, focused on novel technical contribution | **PASS** | Title updated to emphasize Indic normalization, relevance filtering, and offline document retrieval. |
| **Abstract Metrics** | Must report ONLY verifiable, reproduced results | **REVISED** | Replaced unexecuted 96.1% synthetic claim with real measured benchmarks (100% on isolated crime vs govt; 60.12% on broad multi-domain). |
| **Keywords** | 4–6 IEEE Index Terms | **PASS** | Index terms verified: *Offline-First Architectures, Indic Script Processing, Educational Technology, Natural Language Processing, Document Security.* |
| **Related Work & Citations** | Valid academic literature with formal citations | **PASS** | 12 real, verified citations covering Indic NLP (Kakwani et al.), Knowledge Tracing (Piech et al.), Offline Systems (Corner & Noble), and PWA architectures. |
| **Mathematical Formulation** | Explicit equations for core algorithms | **PASS** | Formal definitions provided for Indic Normalization $\mathcal{N}(T)$, Decision Rule $R(A)$, and Cryptographic Hash $H_D$. |
| **Algorithm Specification** | Pseudo-code formatted to IEEE standards | **PASS** | Algorithm 1 specifying *Path Containment and Magic Byte Verification* included with clear input/output and loop boundaries. |
| **Empirical Results Table** | Verified sample sizes and distributions | **REVISED** | Empirical results updated with live socket latencies ($\mu, \text{median}, \text{P95}, \sigma$), 720-inflection Tamil grid (91.67% vs 0.00% collision), and real DB confusion matrix. |
| **Threats to Validity** | Honest discussion of biases, bounds, and limits | **EXPANDED** | Explicitly documents rule-based keyword overlap in non-exam domains, train/test data leakage in headline rules, raster OCR limits, and IndexedDB storage quotas. |
| **Ethical & Copyright** | No unauthorized proprietary content | **PASS** | Distinguishes official examination metadata and public educational questions from copyright-restricted commercial materials. |
| **Author Affiliations** | Full institutional metadata | **ACTION PENDING** | Requires author(s) final institutional names and email affiliations prior to final PDF submission. |

---

## 2. Itemized Manuscript Revisions Applied to `docs/IEEE_PAPER_DRAFT.md`

To ensure absolute academic integrity and eliminate fabricated/unverified claims, the following critical changes are applied to `docs/IEEE_PAPER_DRAFT.md`:

1. **Abstract Update**:
   - *Previous*: *"FlashFacts achieves 100% test passage (110/110), zero Indic token collisions across verified Tamil wordlists, an average local document cache retrieval latency of 4.8 ms, and a 94.2% precision rate in isolating exam-irrelevant localized crime."*
   - *Revised*: *"FlashFacts achieves 100% backend test passage (110/110 across 16 modules), 0.00% token collision across a 720-inflection Tamil test grid (versus 91.67% for naive ASCII regex stripping), an average local document cache retrieval latency of 4.8 ms (15.36 ms direct stream), and 100% precision in excluding localized crime reports from civil-service current affairs feeds (with 60.12% precision on broad multi-domain noise filtering)."*

2. **Section V.A (Curated Dataset)**:
   - *Previous*: *"8 official question papers totaling 10.6 MB..."*
   - *Revised*: *"8 verified examination question papers (TNPSC Groups 2/4, UPSC CSE Prelims GS1/CSAT, UPSC CDS, RRB NTPC, SSC CGL) represented as compliant 2.6 KB sample test fixtures referencing official statutory source portals..."*

3. **Section V.C (Tamil Normalization Benchmark)**:
   - *Previous*: *"1,000 distinct Tamil nominal and verbal inflections sharing identical base consonants (412 unique hashes, 588 collisions, 58.8% error rate)..."*
   - *Revised*: *"720 systematic Tamil inflection forms derived from 10 consonant roots, 12 vowel signs, and 6 terminal codas. Naive ASCII stripping collapses all vowel variations, producing only 60 unique tokens (91.67% collision rate). FlashFacts NFC Indic normalization preserves all 720 distinct tokens (0.00% collision rate)."*

4. **Section V.D (News Relevance Classification)**:
   - *Previous*: *"Ground-truth labeled corpus of 200 real-world news articles... Precision: 96.1%, Recall: 98.0%, F1: 0.970."*
   - *Revised*: *"Evaluated on real ingested records from PostgreSQL: In targeted crime vs. government discrimination ($N=50$), FlashFacts achieves 100% precision and 100% recall. In broad heterogeneous multi-domain noise filtering ($N=200$), the classifier achieves 98.0% recall, 60.12% precision ($TP=98, FP=65, TN=35, FN=2$), and an F1 score of 0.7452, with false positives driven by keyword overlap in sports and entertainment reporting."*

5. **Section VI (Threats to Validity & Train/Test Leakage)**:
   - Added explicit subsection on *Rule-Engine Fitting and Data Leakage*, acknowledging that specific test-prompt strings (`"4 போன்கள்"`, `"செல்போன் கடை ஊழியரை ஏமாற்றி"`) were present in `title_rules`, and discussing the necessary transition to supervised contextual embeddings (e.g. IndicBERT) to achieve robust generalizability without manual rule crafting.

---

## 3. Prioritized Actions Before Paper Submission

1. **Target Conference Selection**: Confirm whether submitting to IEEE TALE (Technology & Engineering Education), IEEE ICALT (Advanced Learning Technologies), or an ACM/IEEE EdTech workshop.
2. **Author Names & Blind Review**: Confirm whether the target venue enforces double-blind review. If double-blind, replace author names and repository URLs with anonymized identifiers.
3. **LaTeX Conversion**: Compile the revised markdown draft (`docs/IEEE_PAPER_DRAFT.md`) into IEEEtran LaTeX template (`bare_conf.tex`) using Overleaf or local `pdflatex`.
4. **Approval**: Obtain final user sign-off on author order and submission fees.
