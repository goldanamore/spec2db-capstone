"""tests/test_schema_gen.py — Unit tests for src/schema_gen.py"""

from __future__ import annotations

import pytest

from src.schema_gen import generate_schema, _strip_fences, _split_statements


VALID_ANALYSIS = {
    "success": True,
    "entities": [],
    "attributes": {},
    "primary_keys": {},
    "foreign_keys": [],
    "relationships": [],
    "business_rules": [],
    "assumptions": [],
    "sql": (
        "CREATE TABLE assets (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL);\n"
        "CREATE INDEX idx_assets_name ON assets(name);"
    ),
}


class TestStripFences:
    def test_strips_sql_fence(self):
        assert _strip_fences("```sql\nCREATE TABLE t (id INTEGER);\n```") == "CREATE TABLE t (id INTEGER);"

    def test_no_fence_unchanged(self):
        assert _strip_fences("CREATE TABLE t (id INTEGER);") == "CREATE TABLE t (id INTEGER);"


class TestSplitStatements:
    def test_splits_two_statements(self):
        sql = "CREATE TABLE a (id INTEGER);\nCREATE TABLE b (id INTEGER);"
        stmts = _split_statements(sql)
        assert len(stmts) == 2
        assert all(s.endswith(";") for s in stmts)

    def test_empty_string_returns_empty_list(self):
        assert _split_statements("") == []

    def test_single_statement(self):
        stmts = _split_statements("CREATE TABLE a (id INTEGER);")
        assert len(stmts) == 1


class TestGenerateSchema:
    def test_happy_path_returns_statements(self):
        result = generate_schema(VALID_ANALYSIS)
        assert result["success"] is True
        assert len(result["statements"]) == 2
        assert result["error"] is None

    def test_strips_markdown_fences_in_sql(self):
        analysis = {**VALID_ANALYSIS, "sql": "```sql\nCREATE TABLE x (id INTEGER);\n```"}
        result = generate_schema(analysis)
        assert result["success"] is True
        assert "```" not in result["sql"]

    def test_failed_analysis_returns_failure(self):
        result = generate_schema({"success": False, "error": "Analysis failed"})
        assert result["success"] is False
        assert result["statements"] == []

    def test_missing_sql_key_returns_failure(self):
        analysis = {**VALID_ANALYSIS, "sql": ""}
        result = generate_schema(analysis)
        assert result["success"] is False

    def test_result_always_has_required_keys(self):
        result = generate_schema({"success": False})
        assert "success" in result
        assert "sql" in result
        assert "statements" in result
        assert "error" in result
