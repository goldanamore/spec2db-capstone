# Spec2DB — Prompt Architecture and Iteration Log

This document records the design decisions, structure, and iteration history
of the five-layer prompt system used in Spec2DB.

---

## Architecture Overview

The prompt is assembled from five independent modules at runtime.
Each module is a separate Python file in `src/prompts/` and serves a distinct role:

| Layer | File | Role |
|---|---|---|
| 1 | `role_context.py` | Sets the AI persona as a Senior Database Architect |
| 2 | `document_understanding.py` | Instructs entity/attribute/relationship extraction |
| 3 | `schema_generation.py` | Instructs normalized SQLite DDL production |
| 4 | `validation_safety.py` | Instructs self-audit, assumption logging, and SQL safety |
| 5 | `structured_output.py` | Enforces the exact JSON output contract |

The five layers are joined with double newlines and sent as a single `contents`
string to `client.models.generate_content()`.

---

## Layer 1 — Role and Context (`role_context.py`)

**Purpose:** Ground the model in the correct domain before it reads any document.

**Design decision:** Explicitly naming the output format requirement ("no markdown
fences, no prose outside the JSON") in layer 1, and repeating it in layer 5,
reduces the frequency of markdown-fenced responses. This was the primary failure
mode during early manual testing.

**Current version (v1.0):**
```
You are a Senior Database Architect and Software Engineer with deep expertise in:
- Relational database design and normalization (1NF, 2NF, 3NF)
- SQL schema design for enterprise applications
- Analyzing natural-language software requirements documents
- SQLite database design and syntax
...
```

---

## Layer 2 — Document Understanding (`document_understanding.py`)

**Purpose:** Tell the model exactly what to extract from the document.

**Design decision:** The layer uses a numbered list of extraction targets
(entities, attributes, PKs, FKs, relationships, business rules, assumptions)
to structure the model's reasoning before it produces output. This reduces
hallucinated attributes.

**Key instruction:** "Do not invent requirements that are not present in the
document." This reduces schema noise on sparse requirement documents.

---

## Layer 3 — Schema Generation (`schema_generation.py`)

**Purpose:** Convert the extracted understanding into DDL SQL.

**Design decisions:**
- Explicitly naming "SQLite-compatible data types" prevents the model from
  using `VARCHAR(255)` or `SERIAL` which are not native SQLite types.
- The normalization instruction (3NF) pushes the model toward junction tables
  for many-to-many relationships rather than comma-separated columns.
- The explicit allowlist at the end of this layer ("No extra statements —
  output only CREATE TABLE and CREATE INDEX") is the first of two places this
  constraint appears (the second is layer 4).

---

## Layer 4 — Validation and Safety (`validation_safety.py`)

**Purpose:** Instruct the model to self-audit and document assumptions.

**Design decisions:**
- The "Safety check" instruction explicitly names the banned statement types
  (DROP, ALTER, INSERT, UPDATE, DELETE, TRUNCATE, EXEC, PRAGMA, ATTACH).
  Naming them explicitly is more reliable than a general "no DML" instruction.
- The "No fabrication" instruction was added after observing that without it
  the model sometimes adds audit tables or lookup tables not mentioned in the
  document.

---

## Layer 5 — Structured Output (`structured_output.py`)

**Purpose:** Lock the output format to a machine-parseable JSON schema.

**Design decisions:**
- The output contract includes all required keys with inline type annotations
  in the JSON template. This substantially reduces missing-key failures.
- The `sql` key is included in the same response (rather than a separate API
  call) to reduce latency and keep analysis + DDL consistent.
- "Do NOT wrap it in markdown code fences" is stated twice — once in the
  opening and once is implied by the format. Despite this, some model responses
  still include fences; `_strip_fences()` in `analyzer.py` handles this.

---

## Known Prompt Limitations

1. **Large documents:** Very long PDFs may push the prompt past the model's
   effective context window, causing incomplete entity extraction.
   Mitigation: truncate extracted text to ~12,000 characters before sending.

2. **Ambiguous cardinality:** When a document says "employees have assets" without
   specifying one-to-many vs. many-to-many, the model makes a reasonable guess
   but logs it as an assumption. Always review the `assumptions` array.

3. **SQLite dialect compliance:** The model occasionally produces `SERIAL` or
   `AUTO_INCREMENT` (MySQL syntax) instead of `INTEGER PRIMARY KEY AUTOINCREMENT`.
   The validator will pass `CREATE TABLE` statements either way; sqlglot normalizes
   the dialect internally. The executor relies on SQLite's native parser.

4. **Markdown fences:** Despite explicit instructions, Gemini 2.0 Flash sometimes
   wraps responses in ```json ... ```. `_strip_fences()` handles this at parse time.

---

## Iteration Log

| Version | Change | Reason |
|---|---|---|
| v1.0 | Initial five-layer design | Baseline implementation |
| — | Future iterations recorded here after live testing | — |

*Note: This log is updated with real observed outputs during development.
No fabricated results are included.*
