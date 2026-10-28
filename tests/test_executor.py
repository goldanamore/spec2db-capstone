"""tests/test_executor.py — Unit tests for src/executor.py"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from src.executor import execute_schema, inspect_table


class TestExecuteSchema:
    def test_creates_tables_successfully(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        statements = [
            "CREATE TABLE employees (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL);",
            "CREATE TABLE assets (id INTEGER PRIMARY KEY, employee_id INTEGER, "
            "FOREIGN KEY (employee_id) REFERENCES employees(id));",
        ]
        result = execute_schema(statements, db_path)
        assert result["success"] is True
        assert "employees" in result["tables_created"]
        assert "assets" in result["tables_created"]
        assert result["error"] is None
        assert result["statements_executed"] == 2

    def test_creates_index_successfully(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        statements = [
            "CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT);",
            "CREATE INDEX idx_items_name ON items(name);",
        ]
        result = execute_schema(statements, db_path)
        assert result["success"] is True
        assert result["statements_executed"] == 2

    def test_empty_statements_returns_failure(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        result = execute_schema([], db_path)
        assert result["success"] is False
        assert result["error"] is not None

    def test_bad_sql_returns_failure_and_no_tables(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        statements = ["THIS IS NOT VALID SQL AT ALL;"]
        result = execute_schema(statements, db_path)
        assert result["success"] is False
        assert result["error"] is not None

    def test_creates_parent_directory_if_missing(self, tmp_path):
        deep_path = str(tmp_path / "nested" / "deep" / "test.db")
        statements = ["CREATE TABLE t (id INTEGER PRIMARY KEY);"]
        result = execute_schema(statements, deep_path)
        assert result["success"] is True
        assert Path(deep_path).exists()

    def test_tables_created_list_matches_actual_db(self, tmp_path):
        db_path = str(tmp_path / "verify.db")
        statements = [
            "CREATE TABLE alpha (id INTEGER PRIMARY KEY);",
            "CREATE TABLE beta (id INTEGER PRIMARY KEY);",
        ]
        result = execute_schema(statements, db_path)
        assert set(result["tables_created"]) == {"alpha", "beta"}

        # Independently verify via sqlite3
        conn = sqlite3.connect(db_path)
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
        ).fetchall()
        conn.close()
        assert {r[0] for r in rows} == {"alpha", "beta"}


class TestInspectTable:
    def test_returns_columns(self, tmp_path):
        db_path = str(tmp_path / "inspect.db")
        conn = sqlite3.connect(db_path)
        conn.execute(
            "CREATE TABLE things (id INTEGER PRIMARY KEY, label TEXT NOT NULL);"
        )
        conn.commit()
        conn.close()

        result = inspect_table(db_path, "things")
        assert result["success"] is True
        names = [c["name"] for c in result["columns"]]
        assert "id" in names
        assert "label" in names

    def test_returns_foreign_keys(self, tmp_path):
        db_path = str(tmp_path / "fk_test.db")
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("CREATE TABLE parents (id INTEGER PRIMARY KEY);")
        conn.execute(
            "CREATE TABLE children (id INTEGER PRIMARY KEY, "
            "parent_id INTEGER, FOREIGN KEY (parent_id) REFERENCES parents(id));"
        )
        conn.commit()
        conn.close()

        result = inspect_table(db_path, "children")
        assert result["success"] is True
        fk_targets = [fk["table"] for fk in result["foreign_keys"]]
        assert "parents" in fk_targets

    def test_nonexistent_table_returns_empty_columns(self, tmp_path):
        db_path = str(tmp_path / "empty.db")
        conn = sqlite3.connect(db_path)
        conn.close()

        result = inspect_table(db_path, "nonexistent_table")
        assert result["success"] is True
        assert result["columns"] == []
