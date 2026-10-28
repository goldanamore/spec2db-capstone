"""tests/test_validator.py — Unit tests for src/validator.py

Covers:
- Happy path: valid CREATE TABLE / CREATE INDEX
- Injection attacks: DROP, DELETE, INSERT, UPDATE, EXEC, PRAGMA, ATTACH
- Mixed valid/invalid
- Malformed SQL
- Empty input
- Multi-statement strings
"""

from __future__ import annotations

import pytest

from src.validator import validate_sql


# ── Happy path ────────────────────────────────────────────────────────────────

class TestApprovedStatements:
    def test_create_table_is_approved(self):
        sql = "CREATE TABLE assets (id INTEGER PRIMARY KEY);"
        result = validate_sql(sql)
        assert result["valid"] is True
        assert len(result["approved_statements"]) == 1
        assert result["rejected_statements"] == []

    def test_create_index_is_approved(self):
        sql = "CREATE INDEX idx_assets_name ON assets(name);"
        result = validate_sql(sql)
        assert result["valid"] is True
        assert len(result["approved_statements"]) == 1

    def test_multiple_valid_statements(self):
        sql = (
            "CREATE TABLE employees (id INTEGER PRIMARY KEY, name TEXT);\n"
            "CREATE TABLE assets (id INTEGER PRIMARY KEY, owner_id INTEGER);\n"
            "CREATE INDEX idx_owner ON assets(owner_id);"
        )
        result = validate_sql(sql)
        assert result["valid"] is True
        assert len(result["approved_statements"]) == 3
        assert result["rejected_statements"] == []


# ── Injection / rejection tests ───────────────────────────────────────────────

class TestRejectedStatements:
    def test_drop_table_is_rejected(self):
        result = validate_sql("DROP TABLE assets;")
        assert result["valid"] is False
        assert len(result["rejected_statements"]) == 1
        assert result["approved_statements"] == []

    def test_delete_is_rejected(self):
        result = validate_sql("DELETE FROM assets WHERE id = 1;")
        assert result["valid"] is False
        assert result["rejected_statements"]

    def test_insert_is_rejected(self):
        result = validate_sql("INSERT INTO assets (name) VALUES ('test');")
        assert result["valid"] is False
        assert result["rejected_statements"]

    def test_update_is_rejected(self):
        result = validate_sql("UPDATE assets SET name = 'x' WHERE id = 1;")
        assert result["valid"] is False

    def test_alter_table_is_rejected(self):
        result = validate_sql("ALTER TABLE assets ADD COLUMN notes TEXT;")
        assert result["valid"] is False

    def test_pragma_is_rejected(self):
        result = validate_sql("PRAGMA foreign_keys = ON;")
        assert result["valid"] is False

    def test_create_view_is_rejected(self):
        result = validate_sql("CREATE VIEW v AS SELECT * FROM assets;")
        assert result["valid"] is False

    def test_create_trigger_is_rejected(self):
        sql = (
            "CREATE TRIGGER trg AFTER INSERT ON assets "
            "BEGIN SELECT 1; END;"
        )
        result = validate_sql(sql)
        assert result["valid"] is False

    def test_attach_is_rejected(self):
        result = validate_sql("ATTACH DATABASE 'other.db' AS other;")
        assert result["valid"] is False


# ── Mixed input ───────────────────────────────────────────────────────────────

class TestMixedInput:
    def test_mixed_valid_and_invalid_is_not_valid(self):
        sql = (
            "CREATE TABLE assets (id INTEGER PRIMARY KEY);\n"
            "DROP TABLE assets;\n"
            "CREATE INDEX idx ON assets(id);"
        )
        result = validate_sql(sql)
        assert result["valid"] is False
        # Approved and rejected both have entries
        assert len(result["approved_statements"]) >= 1
        assert len(result["rejected_statements"]) >= 1

    def test_empty_input_is_invalid(self):
        result = validate_sql("")
        assert result["valid"] is False
        assert result["errors"]

    def test_whitespace_only_is_invalid(self):
        result = validate_sql("   \n  ")
        assert result["valid"] is False


# ── Result structure ──────────────────────────────────────────────────────────

class TestResultStructure:
    def test_always_returns_required_keys(self):
        result = validate_sql("garbage input !!!")
        assert "valid" in result
        assert "approved_statements" in result
        assert "rejected_statements" in result
        assert "errors" in result

    def test_approved_statements_each_end_with_semicolon(self):
        sql = "CREATE TABLE x (id INTEGER PRIMARY KEY);"
        result = validate_sql(sql)
        for stmt in result["approved_statements"]:
            assert stmt.rstrip().endswith(";"), f"Missing semicolon: {stmt!r}"
