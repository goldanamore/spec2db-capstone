"""tests/test_integration.py — End-to-end integration test for the core pipeline.

Tests the flow: generate_schema → validate_sql → execute_schema using a
realistic analysis dict (Gemini is not called; the analysis dict is pre-built).
"""

from __future__ import annotations

import sqlite3

import pytest

from src.schema_gen import generate_schema
from src.validator import validate_sql
from src.executor import execute_schema, inspect_table


# Realistic analysis output representing an IT Asset Inventory domain
IT_ASSET_ANALYSIS = {
    "success": True,
    "entities": [
        {"name": "Employee", "description": "A company employee who may be assigned assets"},
        {"name": "Location", "description": "A physical location where assets are kept"},
        {"name": "AssetCategory", "description": "A category classifying asset types"},
        {"name": "Asset", "description": "An IT asset tracked by the system"},
        {"name": "AssetAssignment", "description": "A record of an asset assigned to an employee"},
    ],
    "attributes": {},
    "primary_keys": {},
    "foreign_keys": [],
    "relationships": [],
    "business_rules": ["Assets must have unique serial numbers"],
    "assumptions": ["Surrogate integer PKs assumed throughout"],
    "sql": """\
CREATE TABLE employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    department TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    building TEXT,
    floor INTEGER
);

CREATE TABLE asset_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    serial_number TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    category_id INTEGER NOT NULL,
    location_id INTEGER,
    status TEXT NOT NULL DEFAULT 'Active' CHECK(status IN ('Active', 'Retired', 'In Repair')),
    purchase_date TEXT,
    purchase_price REAL,
    FOREIGN KEY (category_id) REFERENCES asset_categories(id),
    FOREIGN KEY (location_id) REFERENCES locations(id)
);

CREATE TABLE asset_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL,
    employee_id INTEGER NOT NULL,
    assigned_date TEXT NOT NULL DEFAULT (date('now')),
    returned_date TEXT,
    FOREIGN KEY (asset_id) REFERENCES assets(id),
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);

CREATE INDEX idx_assets_serial ON assets(serial_number);
CREATE INDEX idx_assets_category ON assets(category_id);
CREATE INDEX idx_assets_location ON assets(location_id);
CREATE INDEX idx_assignments_asset ON asset_assignments(asset_id);
CREATE INDEX idx_assignments_employee ON asset_assignments(employee_id);""",
}


class TestFullPipeline:
    def test_generate_schema_from_analysis(self):
        result = generate_schema(IT_ASSET_ANALYSIS)
        assert result["success"] is True
        assert len(result["statements"]) > 0
        assert "CREATE TABLE" in result["sql"].upper()

    def test_validate_generated_schema(self):
        schema = generate_schema(IT_ASSET_ANALYSIS)
        result = validate_sql(schema["sql"])
        assert result["valid"] is True
        assert result["rejected_statements"] == []
        assert result["errors"] == []

    def test_execute_validated_schema(self, tmp_path):
        db_path = str(tmp_path / "it_assets.db")
        schema = generate_schema(IT_ASSET_ANALYSIS)
        validation = validate_sql(schema["sql"])

        assert validation["valid"], f"Validation failed: {validation['errors']}"

        exec_result = execute_schema(validation["approved_statements"], db_path)
        assert exec_result["success"] is True
        assert "employees" in exec_result["tables_created"]
        assert "assets" in exec_result["tables_created"]
        assert "asset_assignments" in exec_result["tables_created"]
        assert "locations" in exec_result["tables_created"]
        assert "asset_categories" in exec_result["tables_created"]

    def test_inspect_tables_after_execution(self, tmp_path):
        db_path = str(tmp_path / "inspect_it.db")
        schema = generate_schema(IT_ASSET_ANALYSIS)
        validation = validate_sql(schema["sql"])
        execute_schema(validation["approved_statements"], db_path)

        # Inspect the assets table
        info = inspect_table(db_path, "assets")
        assert info["success"] is True

        col_names = [c["name"] for c in info["columns"]]
        assert "serial_number" in col_names
        assert "category_id" in col_names

        fk_tables = [fk["table"] for fk in info["foreign_keys"]]
        assert "asset_categories" in fk_tables

    def test_execute_rejects_empty_statements(self, tmp_path):
        db_path = str(tmp_path / "empty_exec.db")
        result = execute_schema([], db_path)
        assert result["success"] is False

    def test_validate_rejects_injection_in_pipeline(self):
        """Ensure injected DROP survives into the pipeline and is caught by validator."""
        injected_sql = (
            "CREATE TABLE safe (id INTEGER PRIMARY KEY);\n"
            "DROP TABLE safe;\n"
            "CREATE INDEX idx_safe ON safe(id);"
        )
        result = validate_sql(injected_sql)
        assert result["valid"] is False
        rejected = " ".join(result["rejected_statements"]).upper()
        assert "DROP" in rejected
