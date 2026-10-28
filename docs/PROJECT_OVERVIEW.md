# Spec2DB — Project Overview

## Project Title
**Spec2DB: AI-Powered Document to Database Generator**

## Program
IBM SkillsBuild University Education × Hacktiv8  
Development Environment: IBM Bob

---

## Project Summary

Spec2DB is a functional AI-powered web application that converts natural-language software requirement documents (PDFs) into normalized relational database schemas and executable SQLite SQL. The application uses Google Gemini as its LLM backend and Streamlit as its user interface.

The application implements a complete Document-to-Database pipeline:
1. Users upload a PDF requirements document
2. Google Gemini analyzes it using a structured five-layer prompt architecture
3. A normalized SQLite DDL schema is generated
4. Every SQL statement is validated against a strict AST-based allowlist
5. The user approves execution with an explicit confirmation
6. The database is created and its structure is verified

---

## Problem Statement

Converting software requirements documents into relational database schemas is a critical but time-consuming and error-prone task in every software project. Developers and analysts must:

- Manually identify business entities and their attributes from natural-language text
- Determine appropriate data types for each attribute
- Define primary and foreign key relationships
- Apply normalization rules to eliminate redundancy
- Write syntactically correct DDL SQL for the target database system
- Review and revise the schema across multiple iterations

This process demands both database design expertise and time, making it a bottleneck especially for junior developers, students, and teams working on multiple projects simultaneously.

Spec2DB automates the first-pass schema design, reducing hours of manual work to minutes, while maintaining human control through a validation and approval gate.

---

## Target Users

| User Group | Primary Use Case |
|---|---|
| Software Developers | Rapidly prototype database schemas from requirement specifications |
| Database Designers | Automate repetitive first-pass normalization work |
| Systems Analysts | Validate that schemas cover all documented requirements |
| IT / Computer Science Students | Learn how requirements translate into database design |
| Academic Lecturers | Demonstrate AI-assisted database design in coursework |
| Capstone / Thesis Students | Quickly scaffold databases for described systems |
| Startup Teams | Accelerate early-stage database design without a dedicated DBA |

---

## Project Objectives

1. **Automate requirement extraction** — use LLM to identify entities, attributes, relationships, keys, and business rules from natural-language documents
2. **Generate normalized schemas** — produce 3NF-compliant SQLite DDL automatically
3. **Enforce execution safety** — validate all generated SQL before execution using AST parsing
4. **Maintain human oversight** — require explicit user approval before creating any database
5. **Demonstrate modular prompt engineering** — implement a versioned, five-layer prompt architecture
6. **Provide a reproducible pipeline** — ensure the application works from a fresh clone with any valid Gemini API key

---

## Key Features

| Feature | Status |
|---|---|
| PDF upload and text extraction | ✅ Implemented |
| Five-layer Gemini prompt architecture | ✅ Implemented |
| Structured JSON response parsing | ✅ Implemented |
| Normalized SQLite DDL generation | ✅ Implemented |
| AST-based SQL validation (allowlist) | ✅ Implemented |
| Explicit user approval gate | ✅ Implemented |
| Isolated SQLite database execution | ✅ Implemented |
| Table/column/FK result verification | ✅ Implemented |
| Graceful error handling throughout | ✅ Implemented |
| 62-test automated test suite | ✅ Implemented |
| Configurable Gemini model via env var | ✅ Implemented |
| Professional Streamlit UI | ✅ Implemented |

---

## Expected Impact

- **Time saving:** First-pass schema design reduced from hours to minutes
- **Learning tool:** Students see how LLMs map natural language to structured database design
- **Quality baseline:** Generated schemas include constraints and foreign keys that are frequently omitted by hand
- **Safety demonstration:** Shows how LLM-generated code can be safely constrained by deterministic validation layers before execution
