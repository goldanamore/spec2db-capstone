"""
src/extractor.py — Feature A: PDF text extraction.

Accepts a file-like object (e.g. from st.file_uploader or io.BytesIO),
extracts all text via pypdf, and returns a structured result dict.
"""

from __future__ import annotations

import io
from typing import Union

import pypdf


def extract_text(file_obj: Union[io.BytesIO, object]) -> dict:
    """Extract text from a PDF file-like object.

    Args:
        file_obj: A file-like object containing PDF bytes.

    Returns:
        {
            "success": bool,
            "text": str,          # concatenated page text
            "page_count": int,
            "error": str | None,
        }
    """
    result = {"success": False, "text": "", "page_count": 0, "error": None}

    try:
        reader = pypdf.PdfReader(file_obj)
    except Exception as exc:
        result["error"] = f"Could not read PDF: {exc}"
        return result

    page_count = len(reader.pages)
    result["page_count"] = page_count

    if page_count == 0:
        result["error"] = "The PDF contains no pages."
        return result

    pages_text: list[str] = []
    for page in reader.pages:
        try:
            page_text = page.extract_text() or ""
        except Exception:
            page_text = ""
        pages_text.append(page_text)

    full_text = "\n\n".join(pages_text).strip()

    if not full_text:
        result["error"] = (
            "No text could be extracted. The PDF may be scanned, "
            "image-only, or password-protected."
        )
        return result

    result["success"] = True
    result["text"] = full_text
    return result
