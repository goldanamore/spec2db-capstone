"""
src/schema_gen.py — Feature C: Database Schema Generation.

Extracts the SQL DDL produced by the analyzer and normalizes it for validation.
The SQL is already embedded in the analyzer's structured output; this module
cleans and splits it into individual executable statements.
"""

from __future__ import annotations

import re


def _strip_fences(text: str) -> str:
    """Remove markdown code fences if present."""
    text = text.strip()
    text = re.sub(r"^```(?:sql)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _split_statements(sql: str) -> list[str]:
    """Split a SQL string into individual statements, dropping empty ones."""
    raw = sql.split(";")
    statements = []
    for stmt in raw:
        cleaned = stmt.strip()
        if cleaned:
            statements.append(cleaned + ";")
    return statements


def generate_schema(analysis: dict) -> dict:
    """Extract and normalize the SQL DDL from an analysis result dict.

    Args:
        analysis: The dict returned by analyzer.analyze_requirements().
                  Must contain a "sql" key.

    Returns:
        {
            "success": bool,
            "sql": str,               # cleaned full SQL string
            "statements": list[str],  # individual statements (each ends with ;)
            "error": str | None,
        }
    """
    if not analysis.get("success"):
        return {
            "success": False,
            "sql": "",
            "statements": [],
            "error": "Cannot generate schema: analysis was not successful.",
        }

    raw_sql = analysis.get("sql", "").strip()
    if not raw_sql:
        return {
            "success": False,
            "sql": "",
            "statements": [],
            "error": "The analysis result contains no SQL.",
        }

    cleaned_sql = _strip_fences(raw_sql)
    statements = _split_statements(cleaned_sql)

    if not statements:
        return {
            "success": False,
            "sql": cleaned_sql,
            "statements": [],
            "error": "No executable SQL statements found after parsing.",
        }

    return {
        "success": True,
        "sql": cleaned_sql,
        "statements": statements,
        "error": None,
    }
