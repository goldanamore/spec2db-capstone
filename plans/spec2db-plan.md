# Spec2DB — Implementation Plan

## Top-Level Overview

**Goal:** Build a functional AI-powered web application that converts natural-language software requirement documents (PDFs) into relational database schemas and executable SQLite SQL.

**Scope:** A single-user local Python application with a Streamlit UI, Google Gemini API integration, a modular prompt architecture, and a controlled SQL execution pipeline. The first domain is IT Asset Inventory Management.

**Approach:** Build the application incrementally across six sub-tasks, each independently testable. The prompt engine, validation layer, and execution pipeline are each isolated components so they can be developed, tested, and replaced independently. No SQL is ever hardcoded; all schema output is generated live by the LLM.

**Non-goals:**
- Multi-user or cloud deployment
- Production database connectivity
- Authentication or access control
- Fine-tuning or training models

---

## Sub-Task 1 — Project Scaffolding and Environment Setup

**Status:** [ ] pending

### Intent
Establish the complete project directory structure, dependency manifest, environment variable convention, and development tooling before any feature code is written. This ensures every subsequent sub-task drops files into a pre-agreed layout.

### Expected Outcomes
- `spec2db-capstone/` contains the full agreed directory skeleton
- `requirements.txt` lists all required packages with minimum versions pinned
- `.env.example` documents every required environment variable without values
- `.gitignore` excludes `.env`, `__pycache__`, `*.db`, and `.pytest_cache`
- `README.md` contains local setup instructions (clone → env → install → run)

### Todo List
1. Create the root directory structure as documented in the Directory Structure section below
2. Write `requirements.txt` with pinned minimum versions for: `streamlit`, `google-genai`, `pypdf`, `sqlglot`, `pytest`, `python-dotenv`
3. Write `.env.example` with `GEMINI_API_KEY=` as the only required variable
4. Write `.gitignore` covering Python, Streamlit, SQLite, and secrets
5. Write `README.md` with local setup instructions
6. Create empty `__init__.py` files in each Python package directory

### Relevant Context
- All credentials come from environment variables; `python-dotenv` loads them from `.env` at startup
- The `data/` directory is gitignored; all SQLite demo databases live there
- `tests/` mirrors the `src/` structure for discoverability

### Directory Structure
```
spec2db-capstone/
├── plans/
│   └── spec2db-plan.md
├── src/
│   ├── __init__.py
│   ├── extractor.py        # Feature A: PDF text extraction
│   ├── analyzer.py         # Feature B: AI requirement analysis
│   ├── schema_gen.py       # Feature C: Schema generation
│   ├── validator.py        # Feature D: SQL validation
│   ├── executor.py         # Feature E: Controlled DB execution
│   └── prompts/
│       ├── __init__.py
│       ├── role_context.py
│       ├── document_understanding.py
│       ├── schema_generation.py
│       ├── validation_safety.py
│       └── structured_output.py
├── tests/
│   ├── __init__.py
│   ├── test_extractor.py
│   ├── test_analyzer.py
│   ├── test_schema_gen.py
│   ├── test_validator.py
│   └── test_executor.py
├── data/                   # gitignored; runtime SQLite databases
├── app.py                  # Streamlit entrypoint
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## Sub-Task 2 — PDF Extraction Module (Feature A)

**Status:** [ ] pending

### Intent
Implement `src/extractor.py`: a stateless module that accepts an uploaded file object (from Streamlit's `file_uploader`), extracts all text pages using `pypdf`, and returns a structured result. This is the first stage in the pipeline and must handle bad input without crashing the UI.

### Expected Outcomes
- `extract_text(file_obj) -> dict` returns `{"success": bool, "text": str, "page_count": int, "error": str | None}`
- Empty or password-protected PDFs return `success: False` with a descriptive error message
- Non-PDF bytes return `success: False` cleanly
- `tests/test_extractor.py` covers: valid PDF, empty PDF, non-PDF input, multi-page PDF

### Todo List
1. Implement `extract_text(file_obj)` in `src/extractor.py` using `pypdf.PdfReader`
2. Wrap all reader operations in try/except to catch `pypdf` exceptions and generic IOErrors
3. Concatenate page text with double newline separators; strip leading/trailing whitespace
4. Return the structured dict with page count
5. Write unit tests using a minimal synthetic PDF fixture and `io.BytesIO`

### Relevant Context
- `file_obj` is a `BytesIO`-compatible object from `st.file_uploader`
- `pypdf.PdfReader` accepts file-like objects directly
- Treat all uploaded content as untrusted; do not evaluate or execute extracted text

---

## Sub-Task 3 — Prompt Architecture and AI Analysis Module (Feature B)

**Status:** [ ] pending

### Intent
Build the five-layer prompt system in `src/prompts/` and implement `src/analyzer.py`, which calls the Gemini API and returns a structured analysis of the requirement document. The prompt layers are composable so each can be tested and iterated independently.

### Expected Outcomes
- Five prompt modules each export a single string template or a `build_*(context) -> str` function
- `analyze_requirements(text: str) -> dict` in `src/analyzer.py` assembles the full prompt, calls Gemini, and returns a parsed structured dict
- The returned dict has keys: `entities`, `attributes`, `primary_keys`, `foreign_keys`, `relationships`, `business_rules`, `assumptions`
- API key is read from `os.environ["GEMINI_API_KEY"]`; the function raises `EnvironmentError` if absent
- API failures return `{"success": False, "error": "..."}` without raising
- `tests/test_analyzer.py` mocks the Gemini client and tests both happy path and API error

### Todo List
1. Write `src/prompts/role_context.py` — defines the AI's role as a senior database architect analyzing requirements documents
2. Write `src/prompts/document_understanding.py` — instructs the model to identify entities, attributes, types, and relationships from the supplied text
3. Write `src/prompts/schema_generation.py` — instructs the model to produce a normalized relational schema suitable for SQLite
4. Write `src/prompts/validation_safety.py` — instructs the model to flag missing info, ambiguous requirements, and design assumptions
5. Write `src/prompts/structured_output.py` — specifies the exact JSON output format the model must return, including all required keys
6. Write `src/analyzer.py` to: load `GEMINI_API_KEY`, instantiate the `google.genai` client, assemble the layered prompt, call `client.models.generate_content`, parse the JSON response, and return the structured dict
7. Write unit tests mocking `google.genai.Client` to validate prompt assembly and response parsing

### Prompt Layer Design

| Layer | File | Responsibility |
|---|---|---|
| 1 — Role & Context | `role_context.py` | Sets model persona and authority domain |
| 2 — Document Understanding | `document_understanding.py` | Instructs entity/attribute extraction |
| 3 — Schema Generation | `schema_generation.py` | Instructs normalized SQLite schema creation |
| 4 — Validation & Safety | `validation_safety.py` | Instructs assumption flagging and gap detection |
| 5 — Structured Output | `structured_output.py` | Enforces JSON output contract |

### Relevant Context
- Official SDK: `google-genai` (not `google-generativeai`)
- Client instantiation: `google.genai.Client(api_key=os.environ["GEMINI_API_KEY"])`
- Generation call: `client.models.generate_content(model="gemini-2.0-flash", contents=prompt)`
- Response text: `response.text`
- Use `json.loads()` on the response text; prompt must instruct the model to return only valid JSON with no markdown fences

---

## Sub-Task 4 — Schema Generation and SQL Validation Modules (Features C and D)

**Status:** [ ] pending

### Intent
Implement `src/schema_gen.py` (Feature C) to convert the analyzer output into DDL SQL strings, and `src/validator.py` (Feature D) to parse and structurally validate those strings before any execution is attempted. These two modules form the safety boundary between LLM output and the database.

### Expected Outcomes
- `generate_schema(analysis: dict) -> dict` returns `{"success": bool, "sql": str, "statements": list[str], "error": str | None}`
- The SQL string contains only `CREATE TABLE` and `CREATE INDEX` statements
- `validate_sql(sql: str) -> dict` returns `{"valid": bool, "approved_statements": list[str], "rejected_statements": list[str], "errors": list[str]}`
- `validate_sql` uses `sqlglot.parse()` to structurally check each statement
- Any statement that is not `CREATE TABLE` or `CREATE INDEX` is added to `rejected_statements` and causes `valid: False`
- `tests/test_validator.py` tests: valid DDL, DROP TABLE injection, INSERT injection, mixed valid/invalid, malformed SQL

### Todo List
1. Implement `generate_schema(analysis)` in `src/schema_gen.py`: call Gemini again with a schema-specific prompt, request only DDL SQL, strip any markdown code fences from the response, split into individual statements
2. Implement `validate_sql(sql)` in `src/validator.py`: split SQL into statements, parse each with `sqlglot.parse()`, check statement type via the AST node class, collect approved and rejected sets
3. Define an explicit allowlist: `{sqlglot.exp.Create}` — only `CREATE` nodes whose `kind` is `TABLE` or `INDEX` are approved
4. Write unit tests for `validate_sql` with adversarial inputs including `DROP`, `DELETE`, `INSERT`, `UPDATE`, `EXEC`, `--` comment injections, and semicolon-separated multi-statement strings

### SQL Safety Allowlist
Only the following AST node kinds are approved for execution:
- `CREATE TABLE`
- `CREATE INDEX`

Everything else — including `DROP`, `ALTER`, `INSERT`, `UPDATE`, `DELETE`, `TRUNCATE`, `EXEC`, `PRAGMA`, `ATTACH` — is rejected.

### Relevant Context
- `sqlglot.parse(sql, dialect="sqlite")` returns a list of AST expression objects
- Each expression has a class name accessible via `type(expr).__name__` or `isinstance(expr, sqlglot.exp.Create)`
- A `CREATE` node's `kind` attribute distinguishes `TABLE` vs `INDEX` vs `VIEW`
- Malformed SQL that fails to parse is treated as rejected, not approved

---

## Sub-Task 5 — Database Execution Module and Streamlit UI (Features E and F)

**Status:** [ ] pending

### Intent
Implement `src/executor.py` (Feature E) for controlled SQLite execution, and build `app.py` (Feature F) as the complete Streamlit UI wiring all modules together into the full pipeline workflow.

### Expected Outcomes
- `execute_schema(statements: list[str], db_path: str) -> dict` in `src/executor.py` executes only pre-validated statements against a local SQLite file in `data/`
- The function never accepts raw unvalidated SQL; it only operates on the `approved_statements` list from `validate_sql`
- Returns `{"success": bool, "tables_created": list[str], "error": str | None}`
- `app.py` implements the seven-stage Streamlit workflow with `st.session_state` to carry data between stages
- Each stage shows clear status messages; errors surface in `st.error()` boxes without exposing stack traces to the user
- The UI requires explicit checkbox + button confirmation before executing SQL

### Todo List
1. Implement `execute_schema(statements, db_path)` in `src/executor.py`:
   - Open a `sqlite3.connect(db_path)` connection
   - Execute each statement individually inside a try/except
   - On any error, rollback and return `success: False` with the error message
   - On success, query `sqlite_master` to retrieve created table names and return them
2. Implement `app.py` with the following Streamlit stages managed via `st.session_state`:
   - **Stage 1 — Upload:** `st.file_uploader`, call `extract_text`, display text preview in expander
   - **Stage 2 — Analyze:** Button triggers `analyze_requirements`, display entity/relationship summary in structured `st.json` or formatted cards
   - **Stage 3 — Generate Schema:** Button triggers `generate_schema`, display raw SQL in `st.code` block
   - **Stage 4 — Validate SQL:** Auto-triggers after generation; show approved/rejected statement counts with color-coded badges
   - **Stage 5 — Approve Execution:** Show `st.warning` with SQL preview, require `st.checkbox` "I confirm I want to create this database" + button
   - **Stage 6 — Execute:** Call `execute_schema` only after approval flag is set; show spinner during execution
   - **Stage 7 — Results:** Display tables using `st.dataframe` queried from the created database; show column names, types, PK/FK indicators

### UI Workflow State Machine
```
[Upload PDF] → [Extract Text] → [Analyze Requirements] → [Generate Schema]
     → [Validate SQL] → [User Approval] → [Execute SQL] → [View Results]
```

### Relevant Context
- Use `st.session_state` keys: `extracted_text`, `analysis`, `schema_sql`, `validation_result`, `approved`, `execution_result`
- Database file: `data/demo_{timestamp}.db` to avoid conflicts across sessions
- Never pass raw LLM output to `execute_schema`; always pass `validation_result["approved_statements"]`
- `st.spinner` wraps all Gemini API calls

---

## Sub-Task 6 — Testing, Validation, and Documentation

**Status:** [ ] pending

### Intent
Complete the test suite across all modules, verify the full end-to-end pipeline works with a real IT Asset Inventory PDF, and finalize README documentation including prompt iteration notes.

### Expected Outcomes
- `pytest` passes all tests with no failures
- At least one integration test exercises the full pipeline with a mocked Gemini response
- SQL injection adversarial tests confirm the validator correctly rejects all destructive statements
- README documents actual Gemini prompt iterations observed during development (no fabricated results)
- `PROMPTS.md` captures the prompt evolution log with version notes

### Todo List
1. Write `tests/test_executor.py`: test successful table creation, test rollback on bad SQL, test that `execute_schema` refuses an empty statement list
2. Write an integration test in `tests/test_integration.py` that feeds a sample analysis dict through `generate_schema → validate_sql → execute_schema` with a temp SQLite database
3. Run the full pytest suite and fix any failures
4. Manually test the Streamlit app with a real IT Asset Inventory PDF (e.g., a short requirements document covering assets, employees, locations, assignments)
5. Document actual prompt outputs and iterations in `PROMPTS.md`
6. Finalize `README.md` with: prerequisites, environment setup, running the app, running tests, and known limitations

### Testing Strategy

| Layer | Tool | What is Tested |
|---|---|---|
| Extraction | pytest + BytesIO fixture | Valid PDF, empty PDF, non-PDF, multi-page |
| Analysis | pytest + mock | Prompt assembly, JSON parsing, API error handling |
| Schema Gen | pytest + mock | DDL output, markdown fence stripping |
| Validation | pytest | Allowlist enforcement, injection rejection, malformed SQL |
| Execution | pytest + tmp_path | Table creation, rollback, empty input guard |
| Integration | pytest + tmp_path + mock | Full pipeline happy path |
| Security | pytest | Adversarial SQL: DROP, DELETE, INSERT, EXEC, PRAGMA, ATTACH |

---

## Database Execution Safety Strategy

The application enforces a multi-layer safety model to ensure LLM-generated SQL never reaches a database without explicit validation and user approval.

**Layer 1 — Prompt constraint:** The schema generation prompt instructs Gemini to output only `CREATE TABLE` and `CREATE INDEX` statements and nothing else.

**Layer 2 — Static AST validation:** Every statement is parsed by `sqlglot` into an AST. Only nodes whose type and kind match the allowlist pass. This check is independent of the LLM and cannot be bypassed by prompt injection.

**Layer 3 — User approval gate:** The UI requires an explicit checkbox confirmation before the executor is called. The executor function itself receives only the pre-validated `approved_statements` list.

**Layer 4 — Isolated database:** Execution targets a uniquely named file in the `data/` directory. There is no connection string to any external or production database.

**Layer 5 — No DDL against existing tables:** The executor operates on a freshly created database file, so there are no existing tables to drop or corrupt.

---

## Required Dependencies

```
streamlit>=1.35.0
google-genai>=1.0.0
pypdf>=4.2.0
sqlglot>=25.0.0
python-dotenv>=1.0.0
pytest>=8.2.0
```

---

## Local Development Instructions

1. **Clone / open** the project in your editor
2. **Create a virtual environment:** `python -m venv .venv && .venv\Scripts\activate`
3. **Install dependencies:** `pip install -r requirements.txt`
4. **Copy env file:** `copy .env.example .env` (Windows) or `cp .env.example .env` (Mac/Linux)
5. **Add your Gemini API key** to `.env`: `GEMINI_API_KEY=your_key_here`
6. **Run the app:** `streamlit run app.py`
7. **Run tests:** `pytest tests/ -v`

---

## Open Questions / Decisions Made

| Decision | Choice | Rationale |
|---|---|---|
| LLM model | `gemini-2.0-flash` | Fast, cost-efficient for structured output tasks |
| SQL dialect | SQLite | No server setup; self-contained demo database |
| JSON output enforcement | Prompt-level instruction, no markdown fences | Simplest reliable approach before tool-calling |
| DB file naming | `data/demo_{timestamp}.db` | Prevents session collisions |
| Streamlit state management | `st.session_state` dict | Standard Streamlit pattern for multi-stage UIs |
| Test fixtures | `io.BytesIO` + temp PDFs | No file system dependency in unit tests |
