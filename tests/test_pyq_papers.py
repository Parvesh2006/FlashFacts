import hashlib
from datetime import date
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.api.v1.pyqs import resolve_safe_pdf_path, verify_pdf_magic_bytes, _safe_authority_source_url
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
    # Verify initial download count
    initial_res = client.get(f"/api/v1/pyqs/papers/{paper_id}")
    assert initial_res.status_code == 200
    initial_downloads = initial_res.json()["download_count"]

    res = client.get(f"/api/v1/pyqs/papers/{paper_id}/pdf")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert "inline; filename=" in res.headers.get("content-disposition", "")
    assert res.headers.get("accept-ranges") == "bytes"
    assert res.content.startswith(b"%PDF-")

    # Verify viewing does NOT increment download count
    after_res = client.get(f"/api/v1/pyqs/papers/{paper_id}")
    assert after_res.json()["download_count"] == initial_downloads


def test_download_pyq_paper_pdf(client: TestClient):
    paper_id = "tnpsc-group4-2024-gen-studies-tamil"
    # Verify initial download count
    initial_res = client.get(f"/api/v1/pyqs/papers/{paper_id}")
    assert initial_res.status_code == 200
    initial_downloads = initial_res.json()["download_count"]

    res = client.get(f"/api/v1/pyqs/papers/{paper_id}/download")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert "attachment; filename=" in res.headers.get("content-disposition", "")
    assert res.content.startswith(b"%PDF-")

    # Verify download DOES increment download count
    after_res = client.get(f"/api/v1/pyqs/papers/{paper_id}")
    assert after_res.json()["download_count"] == initial_downloads + 1


def test_view_pyq_paper_pdf_range_request(client: TestClient):
    paper_id = "tnpsc-group4-2024-gen-studies-tamil"
    res = client.get(f"/api/v1/pyqs/papers/{paper_id}/pdf", headers={"Range": "bytes=0-4"})
    assert res.status_code == 206
    assert res.headers["content-type"] == "application/pdf"
    assert "bytes 0-4/" in res.headers.get("content-range", "")
    assert res.content == b"%PDF-"


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



@pytest.mark.parametrize(
    ("category", "source_url", "expected"),
    [
        ("TNPSC", "https://www.tnpsc.gov.in", "https://www.tnpsc.gov.in"),
        ("UPSC", "https://upsc.gov.in/examinations/previous-question-papers",
         "https://upsc.gov.in/examinations/previous-question-papers"),
        ("SSC", "https://ssc.gov.in", "https://ssc.gov.in"),
        ("RRB", "https://www.rrbcdg.gov.in", "https://www.rrbcdg.gov.in"),
        ("TNPSC", "http://www.tnpsc.gov.in", None),
        ("TNPSC", "https://evil.example", None),
        ("TNPSC", "https://www.tnpsc.gov.in.evil.example", None),
        ("TNPSC", "https://user@www.tnpsc.gov.in", None),
        ("UNKNOWN", "https://unknown.gov.in", None),
        ("TNPSC", "javascript:alert(1)", None),
    ],
)
def test_safe_authority_source_url(category, source_url, expected):
    from types import SimpleNamespace

    paper = SimpleNamespace(exam_category=category, source_url=source_url)
    assert _safe_authority_source_url(paper) == expected


def test_html_disguised_as_pdf_rejected(tmp_path: Path):
    from app.api.v1.pyqs import verify_pdf_structure, verify_pdf_magic_bytes

    # HTML page saved with .pdf extension
    fake_html = tmp_path / "page.pdf"
    fake_html.write_bytes(b"<!DOCTYPE html>\n<html><head><title>404 Not Found</title></head><body>Error</body></html>")
    assert verify_pdf_magic_bytes(fake_html) is False
    assert verify_pdf_structure(fake_html) is False

    # HTML disguised with fake magic bytes header
    disguised = tmp_path / "disguised.pdf"
    disguised.write_bytes(b"%PDF-1.4\n<!DOCTYPE html>\n<html><body>Login Required</body></html>")
    assert verify_pdf_magic_bytes(disguised) is False
    assert verify_pdf_structure(disguised) is False


def test_source_link_only_record_behavior(client: TestClient, db_session):
    repo = PYQPaperRepository(db_session)
    paper_in = PYQPaperCreate(
        id="test-source-link-only-paper",
        exam_name="TNPSC Group 4",
        exam_category="TNPSC",
        year=2024,
        subject="General Studies",
        language="ta",
        title="TNPSC Source Link Only Paper",
        source_url="https://www.tnpsc.gov.in/English/previous_question_papers.aspx",
        authority="TNPSC",
        verification_status="verified_official",
        redistribution_status="unknown",
        availability_status="source_link_only",
        storage_path=None,
    )
    repo.create(paper_in)

    # Metadata check
    res = client.get("/api/v1/pyqs/papers/test-source-link-only-paper")
    assert res.status_code == 200
    data = res.json()
    assert data["has_local_file"] is False
    assert data["availability_status"] == "source_link_only"

    # View endpoint redirects to official source URL
    view_res = client.get("/api/v1/pyqs/papers/test-source-link-only-paper/pdf", follow_redirects=False)
    assert view_res.status_code == 307
    assert view_res.headers["location"] == "https://www.tnpsc.gov.in/English/previous_question_papers.aspx"

    # Download endpoint redirects to official source URL
    dl_res = client.get("/api/v1/pyqs/papers/test-source-link-only-paper/download", follow_redirects=False)
    assert dl_res.status_code == 307
    assert dl_res.headers["location"] == "https://www.tnpsc.gov.in/English/previous_question_papers.aspx"


def test_restricted_document_forbidden(client: TestClient, db_session):
    repo = PYQPaperRepository(db_session)
    paper_in = PYQPaperCreate(
        id="test-restricted-paper",
        exam_name="UPSC CSE Prelims",
        exam_category="UPSC",
        year=2024,
        subject="General Studies",
        language="en",
        title="UPSC Restricted Paper",
        source_url="https://upsc.gov.in/examinations/previous-question-papers",
        authority="UPSC",
        verification_status="verified_official",
        redistribution_status="restricted",
        availability_status="restricted",
    )
    repo.create(paper_in)

    view_res = client.get("/api/v1/pyqs/papers/test-restricted-paper/pdf", follow_redirects=False)
    assert view_res.status_code == 403
    assert "restricted" in view_res.json()["detail"].lower()

    dl_res = client.get("/api/v1/pyqs/papers/test-restricted-paper/download", follow_redirects=False)
    assert dl_res.status_code == 403


def test_invalid_local_file_rejected_from_viewing(client: TestClient, db_session, tmp_path, monkeypatch):
    test_pdf_dir = tmp_path / "data" / "pyq_pdfs"
    test_pdf_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("app.api.v1.pyqs.get_base_storage_dir", lambda: test_pdf_dir)

    # Write corrupted non-PDF file
    corrupt_file = test_pdf_dir / "corrupted.pdf"
    corrupt_file.write_bytes(b"THIS IS NOT A VALID PDF CORRUPTED DATA")

    repo = PYQPaperRepository(db_session)
    paper_in = PYQPaperCreate(
        id="test-corrupted-paper",
        exam_name="SSC CGL",
        exam_category="SSC",
        year=2023,
        subject="General Intelligence",
        language="en",
        title="SSC Corrupted Paper Test",
        source_url="https://ssc.gov.in/for-candidates/tentative-answer-keys",
        authority="SSC",
        verification_status="verified_official",
        redistribution_status="official_open_access",
        availability_status="available",
        storage_path="data/pyq_pdfs/corrupted.pdf",
    )
    repo.create(paper_in)

    # Metadata must indicate has_local_file is False because file is invalid
    res = client.get("/api/v1/pyqs/papers/test-corrupted-paper")
    assert res.status_code == 200
    assert res.json()["has_local_file"] is False

    # Viewing it should NOT serve corrupt file, but redirect to approved source
    view_res = client.get("/api/v1/pyqs/papers/test-corrupted-paper/pdf", follow_redirects=False)
    assert view_res.status_code == 307
    assert view_res.headers["location"] == "https://ssc.gov.in/for-candidates/tentative-answer-keys"


def test_checksum_and_size_validation(client: TestClient, db_session, tmp_path, monkeypatch):
    test_pdf_dir = tmp_path / "data" / "pyq_pdfs"
    test_pdf_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("app.api.v1.pyqs.get_base_storage_dir", lambda: test_pdf_dir)

    pdf_file = test_pdf_dir / "valid_full.pdf"
    content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [] /Count 0 >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF\n"
    pdf_file.write_bytes(content)

    actual_hash = hashlib.sha256(content).hexdigest()
    actual_len = len(content)

    repo = PYQPaperRepository(db_session)
    paper_in = PYQPaperCreate(
        id="test-valid-checksum-paper",
        exam_name="TNPSC Group 4",
        exam_category="TNPSC",
        year=2024,
        subject="General Studies",
        language="ta",
        title="Valid Checksum Paper",
        source_url="https://www.tnpsc.gov.in/English/previous_question_papers.aspx",
        authority="TNPSC",
        verification_status="verified_official",
        redistribution_status="official_open_access",
        availability_status="available",
        storage_path="data/pyq_pdfs/valid_full.pdf",
        checksum_sha256=actual_hash,
        file_size_bytes=actual_len,
    )
    repo.create(paper_in)

    res = client.get("/api/v1/pyqs/papers/test-valid-checksum-paper")
    assert res.status_code == 200
    data = res.json()
    assert data["checksum_sha256"] == actual_hash
    assert data["file_size_bytes"] == actual_len
    assert data["has_local_file"] is True


def test_path_traversal_extended_defense():
    from app.api.v1.pyqs import resolve_safe_pdf_path

    assert resolve_safe_pdf_path("../../etc/passwd") is None
    assert resolve_safe_pdf_path("..\\..\\Windows\\System32\\cmd.exe") is None
    assert resolve_safe_pdf_path("/etc/passwd\x00.pdf") is None
    assert resolve_safe_pdf_path("data/pyq_pdfs/../../etc/shadow") is None
    assert resolve_safe_pdf_path(None) is None
    assert resolve_safe_pdf_path("") is None


def test_verified_external_pdf_redirect(client: TestClient, db_session):
    repo = PYQPaperRepository(db_session)
    paper_in = PYQPaperCreate(
        id="test-external-pdf-paper",
        exam_name="TNPSC Group 2",
        exam_category="TNPSC",
        year=2024,
        subject="General Studies & General Tamil",
        language="bilingual",
        title="TNPSC Group 2 External PDF Test",
        source_url="https://www.tnpsc.gov.in/English/answerkeys.aspx",
        pdf_url="https://www.tnpsc.gov.in/Tentative/Document/08_2024_CCSEII_IIA_GS_GT.pdf",
        authority="TNPSC",
        verification_status="verified_official",
        redistribution_status="unknown",
        availability_status="external_pdf",
        file_size_bytes=8390925,
    )
    repo.create(paper_in)

    res = client.get("/api/v1/pyqs/papers/test-external-pdf-paper")
    assert res.status_code == 200
    data = res.json()
    assert data["has_local_file"] is False
    assert data["availability_status"] == "external_pdf"
    assert data["source_status"] == "verified_external_pdf"
    assert data["pdf_url"] == "https://www.tnpsc.gov.in/Tentative/Document/08_2024_CCSEII_IIA_GS_GT.pdf"

    # View endpoint redirects to official direct PDF URL
    view_res = client.get("/api/v1/pyqs/papers/test-external-pdf-paper/pdf", follow_redirects=False)
    assert view_res.status_code == 307
    assert view_res.headers["location"] == "https://www.tnpsc.gov.in/Tentative/Document/08_2024_CCSEII_IIA_GS_GT.pdf"

    # Download endpoint redirects to official direct PDF URL
    dl_res = client.get("/api/v1/pyqs/papers/test-external-pdf-paper/download", follow_redirects=False)
    assert dl_res.status_code == 307
    assert dl_res.headers["location"] == "https://www.tnpsc.gov.in/Tentative/Document/08_2024_CCSEII_IIA_GS_GT.pdf"


def test_unavailable_source_returns_503(client: TestClient, db_session):
    repo = PYQPaperRepository(db_session)
    paper_in = PYQPaperCreate(
        id="test-unavailable-paper",
        exam_name="RRB NTPC",
        exam_category="RRB",
        year=2021,
        subject="General Awareness",
        language="en",
        title="RRB Temporarily Unavailable Test",
        source_url="https://rrb.indianrailways.gov.in/chandigarh",
        authority="RRB",
        verification_status="verified_official",
        redistribution_status="unknown",
        availability_status="unavailable",
    )
    repo.create(paper_in)

    res = client.get("/api/v1/pyqs/papers/test-unavailable-paper")
    assert res.status_code == 200
    data = res.json()
    assert data["availability_status"] == "unavailable"
    assert data["source_status"] == "temporarily_unavailable"

    view_res = client.get("/api/v1/pyqs/papers/test-unavailable-paper/pdf", follow_redirects=False)
    assert view_res.status_code == 503
    assert "temporarily unavailable" in view_res.json()["detail"].lower()

    dl_res = client.get("/api/v1/pyqs/papers/test-unavailable-paper/download", follow_redirects=False)
    assert dl_res.status_code == 503


def test_extended_authority_hosts():
    from types import SimpleNamespace
    from app.api.v1.pyqs import _safe_authority_source_url

    # RRB on Indian Railways
    rrb_paper = SimpleNamespace(exam_category="RRB", source_url="https://rrb.indianrailways.gov.in/chandigarh")
    assert _safe_authority_source_url(rrb_paper) == "https://rrb.indianrailways.gov.in/chandigarh"

    # UPSC with www
    upsc_paper = SimpleNamespace(exam_category="UPSC", source_url="https://www.upsc.gov.in/examinations/previous-question-papers")
    assert _safe_authority_source_url(upsc_paper) == "https://www.upsc.gov.in/examinations/previous-question-papers"

    # Direct TNPSC PDF target
    tnpsc_paper = SimpleNamespace(exam_category="TNPSC", source_url="https://www.tnpsc.gov.in/English/answerkeys.aspx")
    assert _safe_authority_source_url(tnpsc_paper, "https://www.tnpsc.gov.in/Tentative/Document/08_2024_CCSEII_IIA_GS_GT.pdf") == "https://www.tnpsc.gov.in/Tentative/Document/08_2024_CCSEII_IIA_GS_GT.pdf"

    # Disallowed scheme
    assert _safe_authority_source_url(rrb_paper, "http://rrb.indianrailways.gov.in/chandigarh") is None

    # Disallowed host
    assert _safe_authority_source_url(rrb_paper, "https://malicious-site.com/test.pdf") is None


def test_tnpsc_group4_2024_and_2022_records_and_viewing(client: TestClient, db_session, tmp_path, monkeypatch):
    test_pdf_dir = tmp_path / "data" / "pyq_pdfs"
    test_pdf_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("app.api.v1.pyqs.get_base_storage_dir", lambda: test_pdf_dir)

    repo = PYQPaperRepository(db_session)

    # 1. TNPSC Group 4 2024
    pdf_2024 = test_pdf_dir / "tnpsc-group4-2024-gen-studies-tamil.pdf"
    pdf_bytes_2024 = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF\n"
    pdf_2024.write_bytes(pdf_bytes_2024)

    # 2. TNPSC Group 4 2022
    pdf_2022 = test_pdf_dir / "tnpsc-group4-2022-gen-studies-tamil.pdf"
    pdf_bytes_2022 = b"%PDF-1.7\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF\n"
    pdf_2022.write_bytes(pdf_bytes_2022)

    paper_2022 = PYQPaperCreate(
        id="tnpsc-group4-2022-gen-studies-tamil",
        exam_name="TNPSC Group 4",
        exam_category="TNPSC",
        year=2022,
        subject="General Studies & General Tamil",
        language="ta",
        shift_session="Forenoon (09:30 AM to 12:30 PM)",
        paper_code="CCS4-2022",
        title="TNPSC Group IV Combined Civil Services Examination 2022 Question Booklet",
        source_url="https://www.tnpsc.gov.in/English/answerkeys.aspx",
        pdf_url="https://www.tnpsc.gov.in/Tentative/Document/CCS4T_2022_OPT.pdf",
        authority="Tamil Nadu Public Service Commission (TNPSC)",
        verification_status="verified_official",
        redistribution_status="official_open_access",
        availability_status="available",
        storage_path="data/pyq_pdfs/tnpsc-group4-2022-gen-studies-tamil.pdf",
        file_size_bytes=len(pdf_bytes_2022),
        checksum_sha256=hashlib.sha256(pdf_bytes_2022).hexdigest(),
        mime_type="application/pdf",
    )
    repo.create(paper_2022)

    # Test 2024 view & download
    v24 = client.get("/api/v1/pyqs/papers/tnpsc-group4-2024-gen-studies-tamil/pdf")
    assert v24.status_code == 200
    assert v24.headers["content-type"] == "application/pdf"
    assert "inline; filename=" in v24.headers.get("content-disposition", "")
    assert v24.content.startswith(b"%PDF-")

    d24 = client.get("/api/v1/pyqs/papers/tnpsc-group4-2024-gen-studies-tamil/download")
    assert d24.status_code == 200
    assert "attachment; filename=" in d24.headers.get("content-disposition", "")

    # Test 2022 view & download
    v22 = client.get("/api/v1/pyqs/papers/tnpsc-group4-2022-gen-studies-tamil/pdf")
    assert v22.status_code == 200
    assert v22.headers["content-type"] == "application/pdf"
    assert "inline; filename=" in v22.headers.get("content-disposition", "")
    assert v22.content.startswith(b"%PDF-")

    d22 = client.get("/api/v1/pyqs/papers/tnpsc-group4-2022-gen-studies-tamil/download")
    assert d22.status_code == 200
    assert "attachment; filename=" in d22.headers.get("content-disposition", "")


def test_ssc_cgl_and_rrb_ntpc_unavailable_handling(client: TestClient, db_session):
    repo = PYQPaperRepository(db_session)

    ssc_paper = PYQPaperCreate(
        id="ssc-cgl-2023-tier1-shift1-test",
        exam_name="SSC CGL",
        exam_category="SSC",
        year=2023,
        subject="General Intelligence & General Awareness (Tier-1)",
        language="en",
        shift_session="Shift 1 (09:00 AM to 10:00 AM)",
        paper_code="CGL-2023-T1-S1",
        title="Staff Selection Commission Combined Graduate Level Examination (Tier-1) 2023",
        source_url="https://ssc.gov.in/for-candidates/tentative-answer-keys",
        authority="Staff Selection Commission (SSC)",
        verification_status="verified_official",
        redistribution_status="restricted",
        availability_status="unavailable",
    )
    repo.create(ssc_paper)

    rrb_paper = PYQPaperCreate(
        id="rrb-ntpc-2021-cbt1-ga-test",
        exam_name="RRB NTPC",
        exam_category="RRB",
        year=2021,
        subject="General Awareness & Mathematics (CBT-1)",
        language="en",
        shift_session="Shift 1 (10:30 AM to 12:00 PM)",
        paper_code="CEN-01-2019-S1",
        title="Railway Recruitment Boards Non-Technical Popular Categories (NTPC) Stage-1 CBT 2021",
        source_url="https://rrb.indianrailways.gov.in/chandigarh",
        authority="Railway Recruitment Boards (RRB)",
        verification_status="verified_official",
        redistribution_status="restricted",
        availability_status="unavailable",
    )
    repo.create(rrb_paper)

    # SSC View & Download must return 503
    ssc_meta = client.get("/api/v1/pyqs/papers/ssc-cgl-2023-tier1-shift1-test")
    assert ssc_meta.status_code == 200
    assert ssc_meta.json()["availability_status"] == "unavailable"
    assert ssc_meta.json()["has_local_file"] is False

    ssc_v = client.get("/api/v1/pyqs/papers/ssc-cgl-2023-tier1-shift1-test/pdf")
    assert ssc_v.status_code == 503
    assert "temporarily unavailable" in ssc_v.json()["detail"].lower()

    ssc_d = client.get("/api/v1/pyqs/papers/ssc-cgl-2023-tier1-shift1-test/download")
    assert ssc_d.status_code == 503

    # RRB View & Download must return 503
    rrb_meta = client.get("/api/v1/pyqs/papers/rrb-ntpc-2021-cbt1-ga-test")
    assert rrb_meta.status_code == 200
    assert rrb_meta.json()["availability_status"] == "unavailable"
    assert rrb_meta.json()["has_local_file"] is False

    rrb_v = client.get("/api/v1/pyqs/papers/rrb-ntpc-2021-cbt1-ga-test/pdf")
    assert rrb_v.status_code == 503

    rrb_d = client.get("/api/v1/pyqs/papers/rrb-ntpc-2021-cbt1-ga-test/download")
    assert rrb_d.status_code == 503


def test_pdf_availability_filter(client: TestClient, db_session):
    repo = PYQPaperRepository(db_session)
    # Query with availability=available
    avail_res = client.get("/api/v1/pyqs/papers?availability=available")
    assert avail_res.status_code == 200
    items = avail_res.json()["items"]
    assert len(items) >= 1
    for p in items:
        assert p["availability_status"] == "available"

    # Query with availability=unavailable
    unavail_res = client.get("/api/v1/pyqs/papers?availability=unavailable")
    assert unavail_res.status_code == 200
    unavail_items = unavail_res.json()["items"]
    for p in unavail_items:
        assert p["availability_status"] == "unavailable"
