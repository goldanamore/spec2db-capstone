"""
src/prompts/document_understanding.py — Layer 2: Document Understanding

Instructs the model on how to read and decompose the requirements document
into structured database design elements.
"""


def build_document_understanding(document_text: str) -> str:
    """Build the document understanding prompt with the supplied text embedded."""
    return f"""\
## Document to Analyze

Carefully read the following software requirements document:

---
{document_text}
---

## Extraction Instructions

From the document above, identify and extract the following:

1. **Business Entities** — the main objects or concepts the system must track
   (e.g. Asset, Employee, Location, Department).

2. **Attributes** — for each entity, list its properties/fields with:
   - attribute name
   - data type (TEXT, INTEGER, REAL, BLOB, or NUMERIC for SQLite)
   - whether it is required (NOT NULL) or optional

3. **Primary Keys** — identify the unique identifier for each entity.
   If none is stated, propose a surrogate integer primary key.

4. **Foreign Keys** — identify relationships between entities where one entity
   references another (e.g. Asset.assigned_to_employee_id → Employee.id).

5. **Entity Relationships** — describe the cardinality of each relationship
   (one-to-one, one-to-many, many-to-many).

6. **Business Rules** — any constraints, validations, or rules mentioned
   (e.g. "an asset must have a serial number", "status must be Active or Retired").

7. **Missing Information and Assumptions** — list any information needed for
   schema design that is absent from the document, and state the assumption
   you will use in its place.
"""
