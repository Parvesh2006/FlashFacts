import hashlib
from datetime import date
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.api.v1.pyqs import resolve_safe_pdf_path, verify_pdf_magic_bytes
from app.models.pyq_paper import PYQPaper
from app.schemas.pyq_paper import PYQPaperCreate
from app.repositories.pyq_paper_repository import PYQPaperRepository


@pytest.fixture(autouse=True)
def seed_test_papers(db_session, tmp_path, monkeypatch):
    """Seed verified paper records and valid PDF binary documents for tests."""
    repo = PYQPaperRepository(db_session)

    # Set up a temporary test PDF storage directory
    test_pdf_dir = tmp_path / "data" / "pyq_pdfs"
    test_pdf_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("app.api.v1.pyqs.get_base_storage_dir", lambda: test_pdf_dir)

    raw_papers = [
        {
            "id": "tnpsc-group4-2024-gen-studies-tamil",
            "exam_name": "TNPSC Group 4",
            "exam_category": "TNPSC",
            "year": 2024,
            "exam_date": date(2024, 6, 9),
            "subject": "General Studies & General Tamil",
            "language": "ta",
            "shift_session": "Forenoon",
            "paper_code": "CCS4-2024",
            "title": "TNPSC Group IV Combined Civil Services Examination 2024",
            "source_url": "https://www.tnpsc.gov.in",
            "pdf_url": "https://www.tnpsc.gov.in/document/QP_CCS4_2024.pdf",
            "authority": "Tamil Nadu Public Service Commission (TNPSC)",
            "verification_status": "verified_official",
            "redistribution_status": "official_open_access",
            "availability_status": "available",
        },
        {
            "id": "upsc-cse-prelims-2024-gs1",
            "exam_name": "UPSC CSE Prelims",
            "exam_category": "UPSC",
            "year": 2024,
            "exam_date": date(2024, 6, 16),
            "subject": "General Studies Paper - I",
            "language": "bilingual",
            "shift_session": "Paper I",
            "paper_code": "CSP-2024-GS1",
            "title": "UPSC Civil Services (Preliminary) Examination 2024 General Studies Paper - I",
            "source_url": "https://upsc.gov.in",
            "pdf_url": "https://www.upsc.gov.in/sites/default/files/QP-CSM-26-010926-GS1.pdf",
            "authority": "Union Public Service Commission (UPSC)",
            "verification_status": "verified_official",
            "redistribution_status": "official_open_access",
            "availability_status": "available",
        },
        {
            "id": "ssc-cgl-2023-tier1-shift1",
            "exam_name": "SSC CGL",
            "exam_category": "SSC",
            "year": 2023,
            "exam_date": date(2023, 7, 14),
            "subject": "General Intelligence & General Awareness",
            "language": "en",
            "shift_session": "Shift 1",
            "paper_code": "CGL-2023-T1",
            "title": "Staff Selection Commission Combined Graduate Level Examination (Tier-1) 2023",
            "source_url": "https://ssc.gov.in",
            "pdf_url": "https://ssc.gov.in/api/archive/SSC_CGL_2023.pdf",
            "authority": "Staff Selection Commission (SSC)",
            "verification_status": "verified_official",
            "redistribution_status": "official_open_access",
            "availability_status": "available",
        },
        {
            "id": "rrb-ntpc-2021-cbt1-ga",
            "exam_name": "RRB NTPC",
            "exam_category": "RRB",
            "year": 2021,
            "exam_date": date(2021, 1, 18),
            "subject": "General Awareness & Mathematics",
            "language": "en",
            "shift_session": "Shift 1",
            "paper_code": "CEN-01-2019",
            "title": "Railway Recruitment Boards NTPC Stage-1 CBT 2021",
            "source_url": "https://www.rrbcdg.gov.in",
            "pdf_url": "https://www.rrbcdg.gov.in/archive/RRB_NTPC_2021.pdf",
            "authority": "Railway Recruitment Boards (RRB)",
            "verification_status": "verified_official",
            "redistribution_status": "official_open_access",
            "availability_status": "available",
        },
    ]

    for p in raw_papers:
        # Create standard valid PDF binary
        pdf_file = test_pdf_dir / f"{p['id']}.pdf"
        pdf_bytes = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF\n"
        pdf_file.write_bytes(pdf_bytes)

        checksum = hashlib.sha256(pdf_bytes).hexdigest()
        paper_in = PYQPaperCreate(
            **p,
            checksum_sha256=checksum,
            file_size_bytes=len(pdf_bytes),
            mime_type="application/pdf",
            download_count=0,
            storage_path=f"data/pyq_pdfs/{p['id']}.pdf",
        )
        repo.create(paper_in)


def test_list_pyq_papers(client: TestClient):
    res = client.get("/api/v1/pyqs/papers")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 4
    categories = {p["exam_category"] for p in data["items"]}
    assert "TNPSC" in categories
    assert "UPSC" in categories
    assert "SSC" in categories
    assert "RRB" in categories


def test_filter_and_search_pyq_papers(client: TestClient):
    # Filter by TNPSC category
    tnpsc_res = client.get("/api/v1/pyqs/papers?category=TNPSC")
    assert tnpsc_res.status_code == 200
    for p in tnpsc_res.json()["items"]:
        assert p["exam_category"] == "TNPSC"

    # Filter by year 2024
    y24_res = client.get("/api/v1/pyqs/papers?year=2024")
    assert y24_res.status_code == 200
    for p in y24_res.json()["items"]:
        assert p["year"] == 2024

    # Search keyword
    search_res = client.get("/api/v1/pyqs/papers?q=Civil")
    assert search_res.status_code == 200
    assert len(search_res.json()["items"]) >= 1


def test_get_paper_filters(client: TestClient):
    res = client.get("/api/v1/pyqs/papers/filters")
    assert res.status_code == 200
    filters = res.json()
    assert "TNPSC" in filters["categories"]
    assert "UPSC" in filters["categories"]
    assert 2024 in filters["years"]
    assert len(filters["subjects"]) >= 4


def test_get_paper_metadata_and_provenance(client: TestClient):
    paper_id = "tnpsc-group4-2024-gen-studies-tamil"
    res = client.get(f"/api/v1/pyqs/papers/{paper_id}")
    assert res.status_code == 200
    paper = res.json()
    assert paper["id"] == paper_id
    assert paper["exam_name"] == "TNPSC Group 4"
    assert paper["year"] == 2024
    assert paper["authority"] == "Tamil Nadu Public Service Commission (TNPSC)"
    assert paper["verification_status"] == "verified_official"
    assert paper["redistribution_status"] == "official_open_access"
    assert paper["mime_type"] == "application/pdf"
    assert paper["checksum_sha256"] is not None
    assert paper["has_local_file"] is True


def test_view_pyq_paper_pdf(client: TestClient):
    paper_id = "tnpsc-group4-2024-gen-studies-tamil"
    res = client.get(f"/api/v1/pyqs/papers/{paper_id}/pdf")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert res.content.startswith(b"%PDF-")


def test_download_pyq_paper_pdf(client: TestClient):
    paper_id = "tnpsc-group4-2024-gen-studies-tamil"
    res = client.get(f"/api/v1/pyqs/papers/{paper_id}/download")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert "attachment; filename=" in res.headers["content-disposition"]
    assert res.content.startswith(b"%PDF-")


def test_missing_paper_returns_404(client: TestClient):
    res = client.get("/api/v1/pyqs/papers/non_existent_paper_id_xyz")
    assert res.status_code == 404
    assert "not found" in res.json().get("detail", "").lower()

    pdf_res = client.get("/api/v1/pyqs/papers/non_existent_paper_id_xyz/pdf")
    assert pdf_res.status_code == 404


def test_path_traversal_protection():
    unsafe_path = "../../etc/passwd"
    resolved = resolve_safe_pdf_path(unsafe_path)
    assert resolved is None

    unsafe_win_path = "..\\..\\Windows\\System32\\cmd.exe"
    resolved_win = resolve_safe_pdf_path(unsafe_win_path)
    assert resolved_win is None


def test_verify_pdf_magic_bytes(tmp_path: Path):
    valid_pdf = tmp_path / "valid.pdf"
    valid_pdf.write_bytes(b"%PDF-1.4\n%real pdf content")
    assert verify_pdf_magic_bytes(valid_pdf) is True

    fake_pdf = tmp_path / "fake.pdf"
    fake_pdf.write_bytes(b"NOT A REAL PDF FILE")
    assert verify_pdf_magic_bytes(fake_pdf) is False


def test_admin_only_curation_endpoint(client: TestClient):
    payload = {
        "id": "unauthorized-paper-test",
        "exam_name": "TNPSC Group 4",
        "exam_category": "TNPSC",
        "year": 2025,
        "subject": "General Studies",
        "language": "en",
        "title": "Unauthorized User Paper Submission",
        "source_url": "https://example.com/fake.pdf",
        "authority": "Self Submitted",
    }
    res = client.post("/api/v1/pyqs/papers", json=payload)
    assert res.status_code == 403


def test_duplicate_checksum_rejection(client: TestClient):
    existing = client.get("/api/v1/pyqs/papers/tnpsc-group4-2024-gen-studies-tamil").json()
    duplicate_payload = {
        "id": "duplicate-paper-id-xyz",
        "exam_name": "TNPSC Group 4 Duplicate",
        "exam_category": "TNPSC",
        "year": 2024,
        "subject": "Duplicate Subject",
        "language": "ta",
        "title": "Duplicate Paper Title",
        "source_url": "https://example.com/dup",
        "authority": "TNPSC",
        "checksum_sha256": existing["checksum_sha256"],
    }
    headers = {"X-Admin-Key": "flashfacts_secure_exam_portal_key_2026"}
    res = client.post("/api/v1/pyqs/papers", json=duplicate_payload, headers=headers)
    assert res.status_code == 400
    assert "duplicate" in res.json().get("detail", "").lower()
