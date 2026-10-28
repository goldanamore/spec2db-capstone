# Spec2DB — AI-Powered Document to Database Generator

> **IBM SkillsBuild University Education × Hacktiv8 Capstone Project**  
> Built with IBM Bob · Google Gemini · Python · Streamlit · SQLite

---

## 1. Project Overview

**Spec2DB** is an AI-powered web application that converts natural-language software requirement documents into relational database schemas and executable SQLite SQL — automatically.

Users upload a PDF requirements document, and the application uses Google Gemini to identify business entities, attributes, relationships, and constraints, then generates a normalized database schema, validates it, and creates a real SQLite database — all through a guided, approval-gated workflow.

---

## 2. Problem Statement

Software development projects routinely begin with natural-language requirements documents written by analysts, product owners, or business stakeholders. Translating these documents into relational database schemas is a repetitive, time-intensive, and error-prone manual task that requires:

- Deep understanding of normalization principles
- Careful identification of entities, attributes, and relationships
- Experience in writing correct SQL DDL for the target database
- Multiple review cycles to catch missing constraints or incorrect types

Junior developers and students are especially vulnerable to missing foreign keys, choosing incorrect data types, or under-specifying constraints. Senior engineers spend time on work that should be automatable.

Spec2DB addresses this gap.

---

## 3. Proposed Solution

Spec2DB automates the document-to-schema pipeline using a five-layer LLM prompt architecture:

1. A PDF requirements document is uploaded and its text is extracted.
2. A structured Gemini prompt analyzes the document and identifies entities, attributes, keys, relationships, business rules, and design assumptions.
3. The same call returns a complete SQLite DDL schema embedded in a structured JSON response.
4. The generated SQL is parsed by `sqlglot` and validated against an explicit allowlist — only `CREATE TABLE` and `CREATE INDEX` statements are permitted.
5. The user reviews the SQL and approves execution with an explicit confirmation.
6. The validated SQL is executed against an isolated local SQLite database.
7. The resulting tables, columns, primary keys, and foreign keys are displayed for verification.

---

## 4. Target Users

| User | Use Case |
|---|---|
| Software developers | Rapidly prototype database schemas from requirement specs |
| Database designers | Automate the first-pass normalization work |
| Systems analysts | Validate schema coverage against written requirements |
| IT students | Learn how requirements map to database design |
| Lecturers / educators | Demonstrate LLM-assisted database design in class |
| Capstone / thesis students | Quickly scaffold a database for a described system |

---

## 5. Key Features

| Feature | Description |
|---|---|
| **PDF Upload & Extraction** | Upload any PDF requirements document; text is extracted with `pypdf` |
| **AI Requirement Analysis** | Gemini identifies entities, attributes, PKs, FKs, relationships, business rules, and design assumptions |
| **Schema Generation** | A normalized SQLite DDL schema is generated from the analysis |
| **SQL Validation** | Every statement is parsed by `sqlglot`; only `CREATE TABLE` and `CREATE INDEX` are approved |
| **Approval Gate** | The user must explicitly review and confirm SQL before any database is touched |
| **Isolated Execution** | SQL runs against a uniquely named local SQLite file — never a production database |
| **Result Verification** | Tables, columns, types, and foreign keys are displayed after creation |
| **Graceful Error Handling** | Invalid PDFs, missing API keys, API failures, and SQL errors all surface as clear messages |
| **Configurable Model** | Gemini model is configurable via `GEMINI_MODEL` environment variable |

---

## 6. Technology Stack

| Component | Technology |
|---|---|
| Language | Python 3.11+ |
| UI Framework | Streamlit 1.35+ |
| LLM API | Google Gemini via `google-genai` SDK 2.x |
| PDF Extraction | `pypdf` 4.x |
| SQL Parsing & Validation | `sqlglot` 25+ |
| Database | SQLite (via Python `sqlite3` stdlib) |
| Environment Config | `python-dotenv` |
| Testing | `pytest` 8+ |
| Development Environment | IBM Bob |

---

## 7. System Architecture

The application is structured as a linear pipeline of independent modules:

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│  PDF Upload  │───▶│  extractor   │───▶│   analyzer      │
│  (Streamlit) │    │  (pypdf)     │    │  (Gemini API)   │
└─────────────┘    └──────────────┘    └────────┬────────┘
                                                 │ JSON + SQL
                                        ┌────────▼────────┐
                                        │   schema_gen    │
                                        │  (DDL parser)   │
                                        └────────┬────────┘
                                                 │ statements[]
                                        ┌────────▼────────┐
                                        │   validator     │
                                        │  (sqlglot AST)  │
                                        └────────┬────────┘
                                                 │ approved_statements[]
                                        ┌────────▼────────┐
                                        │  User Approval  │
                                        │  (Streamlit UI) │
                                        └────────┬────────┘
                                                 │
                                        ┌────────▼────────┐
                                        │    executor     │
                                        │  (sqlite3)      │
                                        └────────┬────────┘
                                                 │
                                        ┌────────▼────────┐
                                        │  Result View    │
                                        │  (PRAGMA scan)  │
                                        └─────────────────┘
```

**Module responsibilities:**

| Module | File | Responsibility |
|---|---|---|
| PDF Extractor | `src/extractor.py` | Extracts text from uploaded PDF using `pypdf` |
| AI Analyzer | `src/analyzer.py` | Assembles 5-layer prompt, calls Gemini, parses JSON response |
| Prompt Layers | `src/prompts/` | Five separate prompt template modules |
| Schema Generator | `src/schema_gen.py` | Extracts and normalizes DDL SQL from the analysis result |
| SQL Validator | `src/validator.py` | AST-parses every statement; enforces CREATE-only allowlist |
| DB Executor | `src/executor.py` | Executes approved statements against isolated SQLite file |
| Streamlit UI | `app.py` | Seven-stage workflow UI with session state management |

---

## 8. Application Workflow

```
Step 1 ─ Upload PDF
         │  User uploads a requirements document (PDF)
         ▼
Step 2 ─ Extract Text
         │  pypdf extracts all page text
         ▼
Step 3 ─ Analyze Requirements  [Gemini API call]
         │  5-layer prompt → entities, attributes, PKs, FKs,
         │  relationships, business rules, assumptions, SQL
         ▼
Step 4 ─ Generate Schema
         │  DDL SQL extracted from the analysis JSON,
         │  markdown fences stripped, split into statements
         ▼
Step 5 ─ Validate SQL
         │  sqlglot parses each statement into an AST
         │  Allowlist: CREATE TABLE, CREATE INDEX only
         │  Rejected: DROP, ALTER, INSERT, UPDATE, DELETE, PRAGMA…
         ▼
Step 6 ─ User Approval
         │  SQL displayed for review
         │  User must check confirmation checkbox
         ▼
Step 7 ─ Execute SQL
         │  Approved statements run against data/demo_<timestamp>.db
         ▼
Step 8 ─ Verify Results
         PRAGMA table_info and PRAGMA foreign_key_list
         display all created tables, columns, and FKs
```

---

## 9. Project Structure

```
spec2db-capstone/
├── app.py                      # Streamlit UI entry point
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable template (no secrets)
├── .gitignore
├── README.md
├── PROMPTS.md                  # Prompt architecture and iteration log
├── plans/
│   └── spec2db-plan.md         # Original implementation plan
├── src/
│   ├── extractor.py            # Feature A: PDF text extraction
│   ├── analyzer.py             # Feature B: AI requirement analysis
│   ├── schema_gen.py           # Feature C: DDL schema generation
│   ├── validator.py            # Feature D: SQL AST validation
│   ├── executor.py             # Feature E: Controlled SQLite execution
│   └── prompts/
│       ├── role_context.py     # Layer 1: AI persona
│       ├── document_understanding.py  # Layer 2: Extraction instructions
│       ├── schema_generation.py       # Layer 3: DDL generation rules
│       ├── validation_safety.py       # Layer 4: Self-audit instructions
│       └── structured_output.py       # Layer 5: JSON output contract
├── tests/
│   ├── test_extractor.py
│   ├── test_analyzer.py
│   ├── test_schema_gen.py
│   ├── test_validator.py
│   ├── test_executor.py
│   └── test_integration.py
├── docs/
│   ├── PROJECT_OVERVIEW.md
│   ├── SYSTEM_ARCHITECTURE.md
│   ├── PROMPT_ARCHITECTURE.md
│   ├── PROMPT_ITERATION.md
│   ├── TEST_REPORT.md
│   ├── SUBMISSION_GUIDE.md
│   ├── FINAL_SUBMISSION_CHECKLIST.md
│   └── screenshots/            # Application screenshots (see checklist)
└── data/                       # Runtime SQLite databases (gitignored)
```

---

## 10. Installation

### Prerequisites

- Python **3.11 or later**
- A Google Gemini API key — [get a free key here](https://aistudio.google.com/app/apikey)
- Git

### Windows (PowerShell)

```powershell
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/spec2db-capstone.git
cd spec2db-capstone

# 2. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create your local .env from the template
Copy-Item .env.example .env
```

### macOS / Linux

```bash
git clone https://github.com/YOUR_USERNAME/spec2db-capstone.git
cd spec2db-capstone
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

---

## 11. Gemini API Configuration

1. Visit [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Click **Create API key**
3. Open your local `.env` file (never commit this file) and set:

```env
GEMINI_API_KEY=your_actual_api_key_here
```

Optionally override the default model:

```env
GEMINI_MODEL=gemini-2.5-flash
```

The application loads these values at startup via `python-dotenv`. If `GEMINI_API_KEY` is missing, the UI displays a clear error message.

---

## 12. Running the Application

```bash
streamlit run app.py
```

The app opens at **http://localhost:8501**.

### Running Tests

```bash
pytest tests/ -v
```

All 62 tests run without a Gemini API key — they use mocks for LLM calls.

---

## 13. Example Use Case — IT Asset Inventory Management

**Scenario:** An IT department needs to track computers, peripherals, and other assets assigned to employees across multiple office locations.

**Input document describes:**
- Assets with serial numbers, categories, purchase dates, and status
- Employees with departments and email addresses
- Locations with building and floor information
- Assignment records linking assets to employees

**Spec2DB output (representative):**
- `employees` table with NOT NULL and UNIQUE constraints on email
- `locations` table
- `asset_categories` table with a UNIQUE constraint on name
- `assets` table with a CHECK constraint on status (`Active`, `Retired`, `In Repair`) and foreign keys to categories and locations
- `asset_assignments` junction table with foreign keys to assets and employees
- Indexes on all foreign key columns for query performance

The exact schema is generated live by Gemini and varies based on the document content.

---

## 14. Testing and Validation

The automated test suite contains **62 tests** across 6 test files:

| File | Tests | Coverage |
|---|---|---|
| `test_extractor.py` | 5 | Valid PDF, empty PDF, non-PDF input, key structure |
| `test_analyzer.py` | 15 | Prompt assembly, JSON parsing, API errors, 404 detection, model config |
| `test_schema_gen.py` | 8 | DDL extraction, fence stripping, statement splitting |
| `test_validator.py` | 16 | CREATE TABLE/INDEX approved; DROP/INSERT/UPDATE/ALTER/PRAGMA/ATTACH/VIEW/TRIGGER rejected |
| `test_executor.py` | 9 | Table creation, index creation, FK inspection, rollback on error, empty input guard |
| `test_integration.py` | 6 | Full pipeline: generate → validate → execute → inspect; injection rejection |

All 62 tests pass. LLM calls are mocked; no Gemini API quota is consumed by the test suite.

---

## 15. Security Considerations

| Control | Implementation |
|---|---|
| API key protection | Loaded from `.env` only; never in source code; `.env` is gitignored |
| SQL validation | `sqlglot` AST parser enforces CREATE-only allowlist before execution |
| User approval gate | Explicit checkbox confirmation required before any SQL runs |
| Database isolation | Execution targets a uniquely named `data/demo_<timestamp>.db`; no production connection |
| Prompt injection mitigation | Document text is passed as data in the user prompt layer, not as system instructions |
| Error message safety | Exceptions are caught; stack traces are not surfaced to the UI |
| 404 / retired model detection | Specific error message instructs the user to set `GEMINI_MODEL` |

---

## 16. Limitations

- **Non-deterministic output:** Gemini responses vary between runs; schema quality depends on document clarity
- **No scanned PDFs:** Image-only PDFs without embedded text cannot be processed (OCR is not included)
- **Context window:** Very long PDFs may produce incomplete schemas if text exceeds the model's effective context
- **SQLite only:** The demo database is SQLite; PostgreSQL/MySQL export is not yet implemented
- **Single-user local:** The application is not designed for concurrent multi-user sessions
- **English language:** Prompts and responses are in English; other languages are untested

---

## 17. Future Development

| Enhancement | Description |
|---|---|
| ERD generation | Auto-generate Entity-Relationship Diagrams using Mermaid or Graphviz |
| Multi-dialect export | Export schema as PostgreSQL, MySQL, or MSSQL DDL |
| Schema comparison | Diff two generated schemas to detect requirement changes |
| SQL migration generation | Generate `ALTER TABLE` migrations between schema versions |
| RAG-enhanced analysis | Use retrieval-augmented generation for domain-specific terminology |
| OCR support | Process scanned PDF documents using Tesseract or Google Cloud Vision |
| Multi-document merge | Combine requirements from multiple PDF files into one schema |
| Schema version history | Track schema evolution across multiple document versions |

---

## 18. Capstone Information

| Field | Detail |
|---|---|
| **Program** | IBM SkillsBuild University Education × Hacktiv8 |
| **Development Environment** | IBM Bob (AI-assisted development platform) |
| **Project Type** | AI Application Development Capstone |
| **Domain** | AI + Database Engineering + Full-Stack Python |
| **LLM** | Google Gemini 2.5 Flash |
| **Submission** | See `docs/SUBMISSION_GUIDE.md` for form answers |

---

## License

This project is submitted as an academic capstone. All application code is original work developed using IBM Bob.
