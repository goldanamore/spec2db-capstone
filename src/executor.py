"""
src/executor.py — Feature E: Controlled Database Execution.

Executes only pre-validated, pre-approved SQL statements against an
isolated local SQLite database file. Never accepts raw LLM output.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


def execute_schema(statements: list[str], db_path: str) -> dict:
    """Execute validated DDL statements against an isolated SQLite database.

    Args:
        statements: List of pre-validated SQL statements (from validator's
                    approved_statements). Each statement ends with a semicolon.
        db_path: Path to the SQLite database file to create/use.
                 Must be inside the data/ directory.

    Returns:
        {
            "success": bool,
            "tables_created": list[str],  # names of tables that now exist
            "statements_executed": int,
            "error": str | None,
        }
    """
    result: dict = {
        "success": False,
        "tables_created": [],
        "statements_executed": 0,
        "error": None,
    }

    if not statements:
        result["error"] = "No statements to execute."
        return result

    # Ensure the parent directory exists
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)

    conn: sqlite3.Connection | None = None
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON;")

        for stmt in statements:
            try:
                conn.execute(stmt)
                result["statements_executed"] += 1
            except sqlite3.Error as exc:
                conn.rollback()
                result["error"] = f"SQL execution error: {exc}\nStatement: {stmt[:200]}"
                return result

        conn.commit()

        # Retrieve the list of tables that were created
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
        )
        result["tables_created"] = [row[0] for row in cursor.fetchall()]
        result["success"] = True

    except sqlite3.Error as exc:
        result["error"] = f"Database connection error: {exc}"
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

    return result


def inspect_table(db_path: str, table_name: str) -> dict:
    """Return column metadata for a single table.

    Args:
        db_path: Path to the SQLite database file.
        table_name: Name of the table to inspect.

    Returns:
        {
            "success": bool,
            "columns": list[dict],  # {name, type, notnull, pk}
            "foreign_keys": list[dict],  # {from, table, to}
            "error": str | None,
        }
    """
    result: dict = {
        "success": False,
        "columns": [],
        "foreign_keys": [],
        "error": None,
    }

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        cols = conn.execute(f'PRAGMA table_info("{table_name}");').fetchall()
        result["columns"] = [
            {
                "name": row["name"],
                "type": row["type"],
                "notnull": bool(row["notnull"]),
                "pk": bool(row["pk"]),
            }
            for row in cols
        ]

        fks = conn.execute(f'PRAGMA foreign_key_list("{table_name}");').fetchall()
        result["foreign_keys"] = [
            {"from": row["from"], "table": row["table"], "to": row["to"]}
            for row in fks
        ]

        conn.close()
        result["success"] = True

    except sqlite3.Error as exc:
        result["error"] = f"Inspection error: {exc}"

    return result
