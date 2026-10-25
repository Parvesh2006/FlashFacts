#!/usr/bin/env python3
"""
FlashFacts PYQ PDF Ingestion & Verification Engine.

Reads approved examination authority records, verifies PDF documents,
computes SHA-256 cryptographic checksums, detects duplicate papers,
persists records to the PostgreSQL database, and generates provenance reports.
"""

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Dict, List, Any

# Ensure project root is in python path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "apps" / "api"))

from app.core.database import SessionLocal
from app.models.pyq_paper import PYQPaper
from app.repositories.pyq_paper_repository import PYQPaperRepository
from app.schemas.pyq_paper import PYQPaperCreate

PDF_STORAGE_DIR = ROOT_DIR / "data" / "pyq_pdfs"
DOCS_DIR = ROOT_DIR / "docs"

# Approved Curated Official Papers Registry
APPROVED_PAPERS: List[Dict[str, Any]] = [
    {
        "id": "tnpsc-group4-2024-gen-studies-tamil",
        "exam_name": "TNPSC Group 4",
        "exam_category": "TNPSC",
        "year": 2024,
        "exam_date": date(2024, 6, 9),
        "subject": "General Studies & General Tamil",
        "language": "ta",
        "shift_session": "Forenoon (09:30 AM to 12:30 PM)",
        "paper_code": "CCS4-2024",
        "title": "TNPSC Group IV Combined Civil Services Examination 2024 Question Booklet",
        "source_url": "https://www.tnpsc.gov.in",
        "pdf_url": "https://www.tnpsc.gov.in/document/QP_CCS4_2024.pdf",
        "authority": "Tamil Nadu Public Service Commission (TNPSC)",
        "verification_status": "unverified",
        "redistribution_status": "unknown",
        "availability_status": "source_link_only",
        "sample_questions": [
            "1. Tamil Nadu State Policy on Women was formulated in which year? (A) 2021 (B) 2022 (C) 2023 (D) 2024",
            "2. Match the Archaeological Sites with river valleys: Keeladi, Kodumanal, Adichanallur, Mayiladumparai.",
            "3. Article 21A was inserted into the Constitution of India by which Constitutional Amendment Act?",
            "4. Thirukkural - 'Karka Kasadara Karpavai': What does Thiruvalluvar emphasize regarding learning?",
            "5. What is the unit of electric current in SI system? (A) Ampere (B) Volt (C) Ohm (D) Watt",
        ],
    },
    {
        "id": "tnpsc-group2-2024-prelims-gen-studies",
        "exam_name": "TNPSC Group 2",
        "exam_category": "TNPSC",
        "year": 2024,
        "exam_date": date(2024, 9, 14),
        "subject": "General Studies & General Tamil (Preliminary)",
        "language": "bilingual",
        "shift_session": "Forenoon (09:30 AM to 12:30 PM)",
        "paper_code": "CCS2-2024-PRE",
        "title": "TNPSC Group II / IIA Combined Civil Services Examination Preliminary Paper 2024",
        "source_url": "https://www.tnpsc.gov.in",
        "pdf_url": "https://www.tnpsc.gov.in/document/QP_CCS2_2024_PRE.pdf",
        "authority": "Tamil Nadu Public Service Commission (TNPSC)",
        "verification_status": "unverified",
        "redistribution_status": "unknown",
        "availability_status": "source_link_only",
        "sample_questions": [
            "1. Periyar E.V. Ramasamy started Self-Respect Movement in: (A) 1920 (B) 1925 (C) 1930 (D) 1935",
            "2. The Finance Commission of India is constituted under which Article of the Constitution?",
            "3. Explain the primary objective of Tamil Nadu 'Naan Mudhalvan' youth skilling initiative.",
            "4. Gross State Domestic Product (GSDP) growth rate of Tamil Nadu for the fiscal year 2023-24.",
        ],
    },
    {
        "id": "upsc-cse-prelims-2024-gs1",
        "exam_name": "UPSC CSE Prelims",
        "exam_category": "UPSC",
        "year": 2024,
        "exam_date": date(2024, 6, 16),
        "subject": "General Studies Paper - I",
        "language": "bilingual",
        "shift_session": "Paper I (09:30 AM to 11:30 AM)",
        "paper_code": "CSP-2024-GS1",
        "title": "UPSC Civil Services (Preliminary) Examination 2024 General Studies Paper - I",
        "source_url": "https://upsc.gov.in/examinations/previous-question-papers",
        "pdf_url": "https://www.upsc.gov.in/sites/default/files/QP-CSM-26-010926-GENERAL%20STUDIES%20PAPER%20-%20I.pdf",
        "authority": "Union Public Service Commission (UPSC)",
        "verification_status": "unverified",
        "redistribution_status": "unknown",
        "availability_status": "source_link_only",
        "sample_questions": [
            "1. Consider the following: Red Sea, Black Sea, Caspian Sea, Mediterranean Sea bordering nations.",
            "2. With reference to the Indian economy, consider Repo Rate, Reverse Repo Rate and Monetary Policy.",
            "3. Which Article of the Constitution guarantees the Right to Privacy as an intrinsic part of Life and Liberty?",
            "4. Carbon Capture and Storage (CCS) technologies and their environmental feasibility.",
        ],
    },
    {
        "id": "upsc-cse-prelims-2024-csat",
        "exam_name": "UPSC CSE Prelims",
        "exam_category": "UPSC",
        "year": 2024,
        "exam_date": date(2024, 6, 16),
        "subject": "General Studies Paper - II (CSAT)",
        "language": "bilingual",
        "shift_session": "Paper II (02:30 PM to 04:30 PM)",
        "paper_code": "CSP-2024-CSAT",
        "title": "UPSC Civil Services (Preliminary) Examination 2024 General Studies Paper - II (CSAT)",
        "source_url": "https://upsc.gov.in/examinations/previous-question-papers",
        "pdf_url": "https://www.upsc.gov.in/sites/default/files/QP-CSM-26-010926-GENERAL-STUDIES-PAPER%20-%20II.pdf",
        "authority": "Union Public Service Commission (UPSC)",
        "verification_status": "unverified",
        "redistribution_status": "unknown",
        "availability_status": "source_link_only",
        "sample_questions": [
            "1. Reading Comprehension: Sustainable development vs industrialized resource consumption.",
            "2. Number Theory: Find the remainder when 91*92*93*...*99 is divided by 1261.",
            "3. Logical Reasoning: Five friends A, B, C, D, E seated in a row facing north.",
        ],
    },
    {
        "id": "upsc-cds-2024-gk",
        "exam_name": "UPSC CDS",
        "exam_category": "UPSC",
        "year": 2024,
        "exam_date": date(2024, 9, 1),
        "subject": "General Knowledge",
        "language": "en",
        "shift_session": "Paper II (12:00 PM to 02:00 PM)",
        "paper_code": "CDSE-II-2024-GK",
        "title": "UPSC Combined Defence Services Examination (II) 2024 General Knowledge",
        "source_url": "https://upsc.gov.in/examinations/previous-question-papers",
        "pdf_url": "https://www.upsc.gov.in/sites/default/files/QP-CDSE-II-26-GENERAL-KNOWLEDGE-140926.pdf",
        "authority": "Union Public Service Commission (UPSC)",
        "verification_status": "unverified",
        "redistribution_status": "unknown",
        "availability_status": "source_link_only",
        "sample_questions": [
            "1. Operation Kaveri was launched by Government of India to evacuate citizens from which conflict zone?",
            "2. Which island in the Indian Ocean houses the naval communication facility Diego Garcia?",
            "3. The Chief of Defence Staff (CDS) functions as the Permanent Chairman of the Chiefs of Staff Committee.",
        ],
    },
    {
        "id": "rrb-ntpc-2021-cbt1-ga",
        "exam_name": "RRB NTPC",
        "exam_category": "RRB",
        "year": 2021,
        "exam_date": date(2021, 1, 18),
        "subject": "General Awareness & Mathematics (CBT-1)",
        "language": "en",
        "shift_session": "Shift 1 (10:30 AM to 12:00 PM)",
        "paper_code": "CEN-01-2019-S1",
        "title": "Railway Recruitment Boards Non-Technical Popular Categories (NTPC) Stage-1 CBT 2021",
        "source_url": "https://www.rrbcdg.gov.in",
        "pdf_url": "https://www.rrbcdg.gov.in/archive/RRB_NTPC_CBT1_2021.pdf",
        "authority": "Railway Recruitment Boards (RRB), Ministry of Railways",
        "verification_status": "unverified",
        "redistribution_status": "unknown",
        "availability_status": "source_link_only",
        "sample_questions": [
            "1. Where is the headquarters of South Central Railway located? (A) Secunderabad (B) Hubli (C) Chennai (D) Bilaspur",
            "2. What is the full form of URL in computer science? (Uniform Resource Locator)",
            "3. Who was the Viceroy of India when Indian National Congress was founded in 1885? (Lord Dufferin)",
        ],
    },
    {
        "id": "ssc-cgl-2023-tier1-shift1",
        "exam_name": "SSC CGL",
        "exam_category": "SSC",
        "year": 2023,
        "exam_date": date(2023, 7, 14),
        "subject": "General Intelligence & General Awareness (Tier-1)",
        "language": "en",
        "shift_session": "Shift 1 (09:00 AM to 10:00 AM)",
        "paper_code": "CGL-2023-T1-S1",
        "title": "Staff Selection Commission Combined Graduate Level Examination (Tier-1) 2023",
        "source_url": "https://ssc.gov.in",
        "pdf_url": "https://ssc.gov.in/api/archive/SSC_CGL_2023_Tier1.pdf",
        "authority": "Staff Selection Commission (SSC), Government of India",
        "verification_status": "unverified",
        "redistribution_status": "unknown",
        "availability_status": "source_link_only",
        "sample_questions": [
            "1. Which classical dance form originated in the temples of Tamil Nadu? (Bharatanatyam)",
            "2. Which Constitutional Amendment lowered the voting age from 21 to 18 years? (61st Amendment 1988)",
            "3. Who among the following won the Nobel Prize in Physics for Raman Effect in 1930? (Sir C.V. Raman)",
        ],
    },
    {
        "id": "tnpsc-group4-2022-gen-studies-tamil",
        "exam_name": "TNPSC Group 4",
        "exam_category": "TNPSC",
        "year": 2022,
        "exam_date": date(2022, 7, 24),
        "subject": "General Studies & General Tamil",
        "language": "ta",
        "shift_session": "Forenoon (09:30 AM to 12:30 PM)",
        "paper_code": "CCS4-2022",
        "title": "TNPSC Group IV Combined Civil Services Examination 2022 Question Booklet",
        "source_url": "https://www.tnpsc.gov.in",
        "pdf_url": "https://www.tnpsc.gov.in/document/QP_CCS4_2022.pdf",
        "authority": "Tamil Nadu Public Service Commission (TNPSC)",
        "verification_status": "unverified",
        "redistribution_status": "unknown",
        "availability_status": "source_link_only",
        "sample_questions": [
            "1. Valluvar describes which of the following as the supreme virtue in Illaram? (Anbudaimai)",
            "2. Which city hosted the 44th FIDE Chess Olympiad in Tamil Nadu? (Mamallapuram / Chennai)",
            "3. First Governor-General of independent India was: (C. Rajagopalachari / Lord Mountbatten)",
        ],
    },
]


def generate_standard_pdf(paper: Dict[str, Any]) -> bytes:
    """Synthetic papers are prohibited: only ingest genuine source PDF bytes."""
    raise RuntimeError(
        "Synthetic PYQ PDF generation is disabled. Obtain and verify the original "
        "PDF from an authoritative source; never substitute generated content."
    )
def run_ingestion(dry_run: bool = False) -> Dict[str, Any]:
    print(f"=== FlashFacts PYQ PDF Ingestion Engine (Dry Run: {dry_run}) ===")
    os.makedirs(PDF_STORAGE_DIR, exist_ok=True)
    os.makedirs(DOCS_DIR, exist_ok=True)

    db = SessionLocal()
    repo = PYQPaperRepository(db)

    stats = {
        "total_curated": len(APPROVED_PAPERS),
        "ingested": 0,
        "updated": 0,
        "skipped_duplicate": 0,
        "errors": 0,
        "skipped_unverified": 0,
        "papers": [],
    }

    try:
        for p in APPROVED_PAPERS:
            paper_id = p["id"]
            pdf_filename = f"{paper_id}.pdf"
            pdf_path = PDF_STORAGE_DIR / pdf_filename

            # Safety gate: this registry contains source metadata, not original PDF bytes.
            # Never generate synthetic papers or overwrite records without reviewed source PDFs.
            stats["skipped_unverified"] += 1
            stats["papers"].append({
                "id": paper_id,
                "exam": p["exam_name"],
                "year": p["year"],
                "subject": p["subject"],
                "language": p["language"],
                "authority": p["authority"],
                "checksum": None,
                "size_bytes": 0,
                "status": "SKIPPED_NO_VERIFIED_SOURCE_PDF",
            })
            print(f"[SKIPPED] {paper_id}: original source PDF has not been reviewed and supplied.")
            continue

            # Synthetic PDF generation remains prohibited.
            pdf_bytes = generate_standard_pdf(p)
            if not pdf_bytes.startswith(b"%PDF-"):
                print(f"[ERROR] Invalid PDF signature for {paper_id}")
                stats["errors"] += 1
                continue

            # 2. Compute SHA-256 Checksum and File Size
            checksum = hashlib.sha256(pdf_bytes).hexdigest()
            file_size = len(pdf_bytes)

            if not dry_run:
                with open(pdf_path, "wb") as f:
                    f.write(pdf_bytes)

            rel_storage_path = str(Path("data") / "pyq_pdfs" / pdf_filename).replace("\\", "/")

            # 3. Check duplicate by checksum or ID
            existing = repo.get(paper_id)
            if existing:
                if not dry_run:
                    existing.title = p["title"]
                    existing.subject = p["subject"]
                    existing.language = p["language"]
                    existing.shift_session = p["shift_session"]
                    existing.paper_code = p["paper_code"]
                    existing.source_url = p["source_url"]
                    existing.pdf_url = p["pdf_url"]
                    existing.authority = p["authority"]
                    existing.checksum_sha256 = checksum
                    existing.file_size_bytes = file_size
                    existing.storage_path = rel_storage_path
                    existing.verification_status = p["verification_status"]
                    existing.redistribution_status = p["redistribution_status"]
                    existing.availability_status = p["availability_status"]
                    db.commit()
                stats["updated"] += 1
                status_label = "UPDATED"
            else:
                create_payload = PYQPaperCreate(
                    id=paper_id,
                    exam_name=p["exam_name"],
                    exam_category=p["exam_category"],
                    year=p["year"],
                    exam_date=p["exam_date"],
                    subject=p["subject"],
                    language=p["language"],
                    shift_session=p["shift_session"],
                    paper_code=p["paper_code"],
                    title=p["title"],
                    source_url=p["source_url"],
                    pdf_url=p["pdf_url"],
                    authority=p["authority"],
                    checksum_sha256=checksum,
                    verification_status=p["verification_status"],
                    redistribution_status=p["redistribution_status"],
                    file_size_bytes=file_size,
                    mime_type="application/pdf",
                    availability_status=p["availability_status"],
                    download_count=0,
                    storage_path=rel_storage_path,
                )
                if not dry_run:
                    repo.create(create_payload)
                stats["ingested"] += 1
                status_label = "INGESTED"

            stats["papers"].append({
                "id": paper_id,
                "exam": p["exam_name"],
                "year": p["year"],
                "subject": p["subject"],
                "language": p["language"],
                "authority": p["authority"],
                "checksum": checksum,
                "size_bytes": file_size,
                "status": status_label,
            })
            print(f"[{status_label}] {p['exam_name']} ({p['year']}) - {p['title'][:45]}... (SHA-256: {checksum[:12]}...)")

    finally:
        db.close()

    # 4. Generate docs/PYQ_LIBRARY_SOURCES.md
    generate_sources_documentation(APPROVED_PAPERS)

    # 5. Generate docs/PYQ_INGESTION_REPORT.md
    generate_ingestion_report(stats, dry_run)

    print("\n=== Ingestion Summary ===")
    print(f"Total Curated: {stats['total_curated']}")
    print(f"Ingested: {stats['ingested']}")
    print(f"Updated: {stats['updated']}")
    print(f"Duplicates Skipped: {stats['skipped_duplicate']}")
    print(f"Errors: {stats['errors']}")
    print(f"Documentation generated in {DOCS_DIR}")
    return stats


def generate_sources_documentation(papers: List[Dict[str, Any]]):
    path = DOCS_DIR / "PYQ_LIBRARY_SOURCES.md"
    lines = [
        "# FlashFacts - PYQ Library Source Registry",
        "",
        "This document details every curated previous-year examination paper in FlashFacts,",
        "This registry lists candidate paper sources and their current verification and redistribution status.",
        "",
        "## Official Authorities & Source Registry",
        "",
        "| Examination | Year | Subject / Paper Code | Language | Official Issuing Authority | Source URL | Verification Status | Redistribution Status |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]
    for p in papers:
        date_str = str(p["exam_date"]) if p.get("exam_date") else "N/A"
        lines.append(
            f"| **{p['exam_name']}** | {p['year']} | {p['subject']} (`{p['paper_code']}`) | {p['language'].upper()} | {p['authority']} | [{p['source_url']}]({p['source_url']}) | `{p['verification_status']}` | `{p['redistribution_status']}` |"
        )

    lines.extend([
        "",
        "## Authenticity Verification Standards",
        "",
        "1. **Source Review**: Verify each source with the relevant examination authority before approving a paper.",
        "2. **Checksum**: Calculate SHA-256 only from the original PDF bytes.",
        "3. **PDF Validation**: Validate the original PDF signature and content before accepting a source.",
        "4. **No Synthetic Papers**: Never present illustrative questions or generated PDFs as official examination papers.",
        "5. **Access & Redistribution**: Confirm permission before hosting a local copy; otherwise retain a source link only.",
        "",
        f"*Report generated automatically on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')} by FlashFacts Ingestion Engine.*",
    ])
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def generate_ingestion_report(stats: Dict[str, Any], dry_run: bool):
    path = DOCS_DIR / "PYQ_INGESTION_REPORT.md"
    lines = [
        "# FlashFacts — PYQ PDF Ingestion & Verification Report",
        "",
        f"**Execution Mode**: `{'DRY RUN' if dry_run else 'PRODUCTION COMMIT'}`  ",
        f"**Timestamp**: `{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}`  ",
        f"**Total Papers Processed**: `{stats['total_curated']}`  ",
        f"**Ingested / Created**: `{stats['ingested']}`  ",
        f"**Updated Existing**: `{stats['updated']}`  ",
        f"**Errors / Invalid Documents**: `{stats['errors']}`  ",
        f"**Skipped: Unverified Source PDFs**: `{stats['skipped_unverified']}`  ",
        "",
        "## Processed Question Papers Detail",
        "",
        "| Paper ID | Examination | Year | Subject | Size | SHA-256 Digest | Status |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]
    for p in stats["papers"]:
        checksum = p.get("checksum")
        checksum_display = f"{checksum[:16]}..." if checksum else "N/A"
        lines.append(
            f"| `{p['id']}` | {p['exam']} | {p['year']} | {p['subject']} | {p['size_bytes']} B | `{checksum_display}` | **{p['status']}** |"
        )

    lines.extend([
        "",
        "## Document Integrity Checks",
        "- PDF signature validation: not established by this report.",
        "- Path safety: not measured by this ingestion run.",
        "- Database uniqueness: not measured by this report.",
        "",
        f"*Generated by `scripts/ingest_pyq_pdfs.py`.*",
    ])
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FlashFacts PYQ PDF Ingestion Script")
    parser.add_argument("--dry-run", action="store_true", help="Perform dry run without committing database or file writes")
    args = parser.parse_args()
    run_ingestion(dry_run=args.dry_run)
