"""
src/validator.py — Feature D: SQL Validation.

Parses every SQL statement with sqlglot and enforces an allowlist of
approved statement types before any execution is permitted.

Approved: CREATE TABLE, CREATE INDEX
Rejected: everything else including DROP, ALTER, INSERT, UPDATE, DELETE,
          TRUNCATE, EXEC, PRAGMA, ATTACH, CREATE VIEW, CREATE TRIGGER, etc.
"""

from __future__ import annotations

import sqlglot
import sqlglot.expressions as exp

# Approved sqlglot expression types and their permitted 'kind' values
_APPROVED: dict[type, set[str] | None] = {
    exp.Create: {"TABLE", "INDEX"},
}


def _is_approved(expression: exp.Expression) -> bool:
    """Return True if the AST expression is on the approved allowlist."""
    for expr_type, allowed_kinds in _APPROVED.items():
        if isinstance(expression, expr_type):
            if allowed_kinds is None:
                return True
            kind = getattr(expression, "kind", None)
            if kind and kind.upper() in allowed_kinds:
                return True
    return False


def validate_sql(sql: str) -> dict:
    """Validate SQL against the approved statement allowlist.

    Args:
        sql: One or more SQL statements as a single string.

    Returns:
        {
            "valid": bool,                      # True only if ALL statements are approved
            "approved_statements": list[str],   # statements that passed
            "rejected_statements": list[str],   # statements that failed
            "errors": list[str],                # parse errors or rejection reasons
        }
    """
    result: dict = {
        "valid": False,
        "approved_statements": [],
        "rejected_statements": [],
        "errors": [],
    }

    if not sql or not sql.strip():
        result["errors"].append("Empty SQL input.")
        return result

    # Split on semicolons to handle multi-statement strings
    raw_parts = [s.strip() for s in sql.split(";") if s.strip()]

    for raw_stmt in raw_parts:
        stmt_with_semi = raw_stmt + ";"
        try:
            parsed = sqlglot.parse(stmt_with_semi, dialect="sqlite")
        except Exception as exc:
            result["rejected_statements"].append(stmt_with_semi)
            result["errors"].append(f"Parse error: {exc} — statement: {raw_stmt[:80]}")
            continue

        if not parsed:
            result["rejected_statements"].append(stmt_with_semi)
            result["errors"].append(f"Could not parse statement: {raw_stmt[:80]}")
            continue

        for expression in parsed:
            if expression is None:
                continue
            if _is_approved(expression):
                result["approved_statements"].append(stmt_with_semi)
            else:
                stmt_type = type(expression).__name__
                result["rejected_statements"].append(stmt_with_semi)
                result["errors"].append(
                    f"Rejected '{stmt_type}' statement — only CREATE TABLE and "
                    f"CREATE INDEX are permitted."
                )

    has_approved = len(result["approved_statements"]) > 0
    has_rejected = len(result["rejected_statements"]) > 0

    result["valid"] = has_approved and not has_rejected
    return result
