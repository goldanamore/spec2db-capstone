"""tests/test_extractor.py — Unit tests for src/extractor.py"""

from __future__ import annotations

import io
import struct

import pytest

from src.extractor import extract_text


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _minimal_pdf_bytes(text: str = "Hello, Spec2DB!") -> bytes:
    """Build the smallest valid single-page PDF containing `text`.

    This constructs a real PDF binary so pypdf can parse it without
    depending on any external fixture files.
    """
    # Object stream contents
    content_stream = f"BT /F1 12 Tf 100 700 Td ({text}) Tj ET".encode()
    content_length = len(content_stream)

    # Build objects
    obj1 = b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    obj2 = b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
    obj3 = (
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R "
        b"/MediaBox [0 0 612 792] "
        b"/Contents 4 0 R "
        b"/Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >> "
        b">>\nendobj\n"
    )
    obj4 = (
        f"4 0 obj\n<< /Length {content_length} >>\nstream\n".encode()
        + content_stream
        + b"\nendstream\nendobj\n"
    )

    header = b"%PDF-1.4\n"
    body = obj1 + obj2 + obj3 + obj4
    xref_offset = len(header) + len(body)

    # Cross-reference table (minimal, positional)
    offsets = []
    pos = len(header)
    for obj in [obj1, obj2, obj3, obj4]:
        offsets.append(pos)
        pos += len(obj)

    xref = b"xref\n0 5\n0000000000 65535 f \n"
    for off in offsets:
        xref += f"{off:010d} 00000 n \n".encode()

    trailer = (
        b"trailer\n<< /Size 5 /Root 1 0 R >>\n"
        b"startxref\n"
        + str(xref_offset).encode()
        + b"\n%%EOF"
    )

    return header + body + xref + trailer


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestExtractText:
    def test_valid_single_page_pdf(self):
        pdf_bytes = _minimal_pdf_bytes("Spec2DB test document")
        result = extract_text(io.BytesIO(pdf_bytes))
        assert result["success"] is True
        assert result["page_count"] == 1
        assert result["error"] is None
        assert isinstance(result["text"], str)
        assert len(result["text"]) > 0

    def test_non_pdf_bytes_returns_failure(self):
        garbage = io.BytesIO(b"this is not a pdf")
        result = extract_text(garbage)
        assert result["success"] is False
        assert result["error"] is not None
        assert result["text"] == ""

    def test_empty_bytes_returns_failure(self):
        result = extract_text(io.BytesIO(b""))
        assert result["success"] is False
        assert result["error"] is not None

    def test_result_keys_always_present(self):
        result = extract_text(io.BytesIO(b"bad"))
        assert "success" in result
        assert "text" in result
        assert "page_count" in result
        assert "error" in result

    def test_page_count_is_integer(self):
        result = extract_text(io.BytesIO(b"bad"))
        assert isinstance(result["page_count"], int)
