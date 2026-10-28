# Spec2DB — System Architecture

## Overview

Spec2DB is implemented as a linear pipeline of independent Python modules orchestrated by a Streamlit web application. Each module has a single responsibility and a clearly defined interface. This separation allows each component to be tested, replaced, or extended independently.

---

## Component Map

```
┌──────────────────────────────────────────────────────────────────┐
│                        STREAMLIT UI  (app.py)                    │
│  Session state:  extracted_text → analysis → schema_result       │
│                  validation_result → approved → execution_result  │
└───────┬──────────────────────────────────────────────────────────┘
        │
        ▼ Stage 1: PDF Upload
┌───────────────────┐
│   src/extractor   │  pypdf.PdfReader → plain text string
└───────┬───────────┘
        │ {"success", "text", "page_count", "error"}
        ▼ Stage 2: AI Analysis
┌───────────────────┐       ┌──────────────────────────┐
│  src/analyzer     │──────▶│  src/prompts/            │
│  google.genai     │       │   role_context.py        │
│  Client.models    │       │   document_understanding │
│  .generate_content│       │   schema_generation      │
└───────┬───────────┘       │   validation_safety      │
        │                   │   structured_output      │
        │ {"success","entities","attributes",           │
        │  "primary_keys","foreign_keys",               │
        │  "relationships","business_rules",            │
        │  "assumptions","sql"}                         │
        ▼ Stage 3: Schema Generation
┌───────────────────┐
│  src/schema_gen   │  strips fences, splits on ";"
└───────┬───────────┘
        │ {"success","sql","statements[]","error"}
        ▼ Stage 4: SQL Validation
┌───────────────────┐
│  src/validator    │  sqlglot.parse() → AST node check
│  allowlist:       │  approved: CREATE TABLE, CREATE INDEX
│  {Create/TABLE,   │  rejected: everything else
│   Create/INDEX}   │
└───────┬───────────┘
        │ {"valid","approved_statements[]","rejected_statements[]","errors[]"}
        ▼ Stage 5: User Approval (UI gate)
        │  st.checkbox + st.button  (no code path bypasses this)
        ▼ Stage 6: Database Execution
┌───────────────────┐
│  src/executor     │  sqlite3.connect(data/demo_<ts>.db)
│  execute_schema() │  executes approved_statements[] only
└───────┬───────────┘
        │ {"success","tables_created[]","statements_executed","error"}
        ▼ Stage 7: Result Verification
┌───────────────────┐
│  src/executor     │  PRAGMA table_info("<table>")
│  inspect_table()  │  PRAGMA foreign_key_list("<table>")
└───────────────────┘
```

---

## Module Reference

### `app.py` — Streamlit UI Entry Point

- Manages a seven-stage workflow using `st.session_state`
- Each stage is gated: later stages are inaccessible until earlier stages complete
- Calls each `src/` module with structured inputs and handles error returns
- Wraps all Gemini API calls in `st.spinner` for UX feedback
- Requires explicit `st.checkbox` confirmation before calling `execute_schema`

### `src/extractor.py` — PDF Extraction

- **Input:** file-like object (from `st.file_uploader`)
- **Output:** `{"success", "text", "page_count", "error"}`
- Uses `pypdf.PdfReader`; catches all exceptions; never evaluates extracted text
- Returns `success: False` for empty PDFs, password-protected PDFs, and non-PDF bytes

### `src/analyzer.py` — AI Requirement Analysis

- **Input:** plain-text document string
- **Output:** structured dict with entities, attributes, keys, relationships, rules, assumptions, and SQL
- Reads `GEMINI_API_KEY` from environment; raises `EnvironmentError` if absent
- Reads `GEMINI_MODEL` from environment; defaults to `gemini-2.5-flash`
- Detects 404/NOT_FOUND errors and returns actionable guidance
- Strips markdown code fences from Gemini responses before JSON parsing

### `src/prompts/` — Prompt Architecture (5 Layers)

See `docs/PROMPT_ARCHITECTURE.md` for full detail.

| File | Layer | Role |
|---|---|---|
| `role_context.py` | 1 | AI persona and domain authority |
| `document_understanding.py` | 2 | Extraction task instructions |
| `schema_generation.py` | 3 | DDL generation rules |
| `validation_safety.py` | 4 | Self-audit and safety constraints |
| `structured_output.py` | 5 | JSON output contract |

### `src/schema_gen.py` — Schema Generation

- **Input:** analysis dict from `analyzer.py`
- **Output:** `{"success", "sql", "statements[]", "error"}`
- Extracts the `sql` field from the analysis result
- Strips markdown code fences (```` ```sql ``` ````), splits on `;`
- Does not call Gemini; pure text processing

### `src/validator.py` — SQL Validation

- **Input:** SQL string (one or more statements)
- **Output:** `{"valid", "approved_statements[]", "rejected_statements[]", "errors[]"}`
- Uses `sqlglot.parse(sql, dialect="sqlite")` to produce an AST for each statement
- Allowlist: `sqlglot.exp.Create` nodes with `kind` in `{"TABLE", "INDEX"}`
- Malformed SQL that fails to parse is treated as rejected
- `valid: True` only when all statements are approved and at least one exists

### `src/executor.py` — Controlled Database Execution

- **Input:** `approved_statements[]` list + `db_path` string
- **Output:** `{"success", "tables_created[]", "statements_executed", "error"}`
- Creates parent directory if it does not exist
- Executes each statement individually; rolls back and returns error on any failure
- Queries `sqlite_master` after execution to return actual table names
- `inspect_table(db_path, table_name)` uses PRAGMA introspection to return column and FK metadata

---

## Data Flow

```
PDF bytes
  → [extractor] → text string
  → [analyzer + prompts] → JSON dict (entities + SQL string)
  → [schema_gen] → SQL statements[]
  → [validator] → approved_statements[]
  → [UI approval gate]
  → [executor] → tables_created[]
  → [inspector] → columns[], foreign_keys[]
```

---

## Security Boundaries

| Boundary | Mechanism |
|---|---|
| API key isolation | Never in source; loaded from `.env` only via `python-dotenv` |
| LLM output → database | Blocked: raw LLM text never reaches `sqlite3.execute()` |
| Intermediate validation | sqlglot AST check is fully deterministic; not bypassable via prompt |
| User gate | `execute_schema()` is only called if the approval flag is `True` in session state |
| Database isolation | Each session creates a new uniquely-named file in `data/`; no shared state |
| Error containment | All exceptions are caught at module level; stack traces do not reach the UI |

---

## Dependency Graph

```
app.py
├── src.extractor       → pypdf
├── src.analyzer        → google.genai, src.prompts.*
├── src.schema_gen      (stdlib only)
├── src.validator       → sqlglot
└── src.executor        (stdlib sqlite3 only)
```

External network calls: **only `src.analyzer`** communicates with the Gemini API.  
All other modules are fully offline.
