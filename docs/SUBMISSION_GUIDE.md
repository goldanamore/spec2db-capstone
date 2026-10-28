# Spec2DB — IBM SkillsBuild Submission Guide

This document provides draft answers for the IBM SkillsBuild University Education capstone submission form. Copy and adapt these answers as needed.

---

## 1. Capstone Project Title

**Spec2DB: AI-Powered Document to Database Generator**

---

## 2. Project Summary

Spec2DB is a functional AI-powered web application that converts natural-language software requirement documents (PDFs) into normalized relational database schemas and executable SQLite SQL. 

The application uses Google Gemini with a five-layer modular prompt architecture to extract entities, attributes, relationships, business rules, and design assumptions from an uploaded PDF. It generates a complete SQLite DDL schema, validates every SQL statement using the `sqlglot` AST parser against an explicit allowlist, requires user approval before any execution, and verifies the created database structure.

The project was built using IBM Bob as the development environment, with Python, Streamlit, the Google GenAI SDK, and SQLite as the core stack.

---

## 3. Problem Statement

Converting software requirements documents into relational database schemas is a time-intensive and error-prone manual process. Developers and analysts must manually identify entities, attributes, and relationships from natural-language text; determine appropriate data types; define primary and foreign key constraints; apply normalization rules; and write syntactically correct DDL SQL.

This process is repetitive, requires specialized expertise, and is a common bottleneck in early-stage software projects — especially for students and junior developers who may miss constraints, foreign keys, or normalization requirements.

Spec2DB automates the first-pass schema design, reducing a multi-hour task to minutes while maintaining human control through a validation and approval gate.

---

## 4. Target Users

- **Software developers:** Rapidly prototype database schemas from requirement specs
- **Database designers:** Automate repetitive first-pass normalization work
- **Systems analysts:** Validate that database schemas cover all documented requirements
- **IT / Computer Science students:** Learn how natural-language requirements map to database design
- **Academic lecturers:** Demonstrate AI-assisted database design in coursework
- **Capstone and thesis students:** Quickly scaffold databases for systems they are describing

---

## 5. Prompt Layering Architecture

Spec2DB uses a five-layer modular prompt architecture implemented as separate, version-controlled Python modules in `src/prompts/`:

**Layer 1 — Role and Context** (`role_context.py`)  
Establishes the AI as a Senior Database Architect. Instructs conservative behavior: "You do not invent requirements that are not present in the document." Pre-declares that output must be plain JSON with no markdown fences.

**Layer 2 — Document Understanding** (`document_understanding.py`)  
Embeds the actual document text. Instructs the model to identify seven specific elements: business entities, attributes with types, primary keys, foreign keys, relationships with cardinality, business rules, and missing information requiring assumptions.

**Layer 3 — Schema Generation** (`schema_generation.py`)  
Instructs normalized (3NF) schema design using SQLite-compatible types only. Specifies primary key conventions, foreign key syntax, constraint application, index creation rules, naming conventions (snake_case, plural nouns), and explicitly restricts output to CREATE TABLE and CREATE INDEX statements only.

**Layer 4 — Validation and Safety** (`validation_safety.py`)  
Instructs the model to self-audit before producing output: check completeness, flag ambiguity, record all assumptions, and verify that banned SQL types (DROP, ALTER, INSERT, UPDATE, DELETE, TRUNCATE, EXEC, PRAGMA, ATTACH) are absent from the output.

**Layer 5 — Structured Output** (`structured_output.py`)  
Specifies the exact JSON schema the application expects, including all 8 required keys and their types. Repeats the "no markdown fences" instruction. The `sql` field in the response contains the complete DDL.

Each layer is independently testable. The test suite verifies that each layer's content appears in the assembled prompt.

---

## 6. Prompt Iteration

The prompt architecture underwent three documented revisions during development:

**Revision R1 — Model Configuration:**  
The hardcoded `gemini-2.0-flash` model caused 404 NOT_FOUND errors after the model was deprecated. The model was made configurable via the `GEMINI_MODEL` environment variable, defaulting to `gemini-2.5-flash`.

**Revision R2 — 404 Error Detection:**  
A specific exception handler was added to detect `404 / NOT_FOUND / no longer available` errors and return a user-friendly message that instructs users to update their `GEMINI_MODEL` environment variable.

**Revision R3 — Fence Stripping:**  
Despite explicit instructions in Layers 1 and 5 that responses must not use markdown code fences, Gemini 2.x models occasionally wrapped JSON responses in ` ```json ``` ` fences. A `_strip_fences()` function was added to `src/analyzer.py` as a defensive fallback before JSON parsing.

Full documentation of iterations is in `docs/PROMPT_ITERATION.md`. All three revisions are traceable to actual code in the repository.

---

## 7. Future Development

The current implementation demonstrates the core Document-to-Database pipeline using SQLite. Planned extensions include:

1. **ERD generation** — Automatically generate Entity-Relationship Diagrams from the analysis output using Mermaid or Graphviz
2. **Multi-dialect SQL export** — Export the generated schema as PostgreSQL, MySQL, or MSSQL DDL
3. **Schema comparison and diff** — Compare two generated schemas to identify additions, removals, and modifications when requirements evolve
4. **SQL migration generation** — Automatically generate `ALTER TABLE` migration scripts between schema versions
5. **OCR support** — Process scanned PDF documents using Tesseract or Google Cloud Vision for image-only PDFs
6. **Retrieval-Augmented Generation** — Enhance analysis accuracy for domain-specific documents using RAG over a terminology database
7. **Multi-document merge** — Combine requirements from multiple PDF documents into a unified schema
8. **Schema version history** — Track and display the evolution of schema design across multiple document versions

---

## 8. GitHub Project Link

```
https://github.com/YOUR_USERNAME/spec2db-capstone
```

*(Replace `YOUR_USERNAME` with your actual GitHub username after publication.)*

The repository is public and includes:
- Complete source code
- Automated test suite (62 tests, 0 failures)
- Professional README with installation instructions
- Capstone documentation in `docs/`
- Prompt architecture documentation
- No exposed API credentials

---

## Submission Checklist

Before submitting, verify:

- [ ] GitHub repository is public and accessible
- [ ] `README.md` is complete with installation instructions
- [ ] `GEMINI_API_KEY` is not present in any committed file
- [ ] `docs/PROMPT_ARCHITECTURE.md` is complete
- [ ] `docs/PROMPT_ITERATION.md` is complete
- [ ] `docs/TEST_REPORT.md` shows 62/62 pass
- [ ] Screenshots are captured and in `docs/screenshots/`
- [ ] GitHub link is pasted correctly in the submission form
- [ ] `docs/FINAL_SUBMISSION_CHECKLIST.md` shows no BLOCKED items
