# Spec2DB — Prompt Architecture

## Overview

Spec2DB uses a **five-layer modular prompt architecture**. Instead of one large unstructured prompt, the instructions are split into five separate Python modules in `src/prompts/`. The `analyzer.py` module assembles them at runtime by joining them with double newlines and sending the result as a single `contents` string to `client.models.generate_content()`.

This separation allows each layer to be:
- Independently read, understood, and version-controlled
- Tested individually (the test suite verifies each layer contributes content)
- Modified without affecting the other layers

---

## Assembly

```python
# src/analyzer.py — _build_prompt()
prompt = "\n\n".join([
    ROLE_CONTEXT,
    build_document_understanding(document_text),
    SCHEMA_GENERATION,
    VALIDATION_SAFETY,
    STRUCTURED_OUTPUT,
])
```

The assembled prompt is sent as a single `contents` argument:

```python
response = client.models.generate_content(
    model=model,   # default: gemini-2.5-flash
    contents=prompt,
)
```

---

## Layer 1 — Role and Context

**File:** `src/prompts/role_context.py`  
**Variable:** `ROLE_CONTEXT` (constant string)

**Purpose:** Establishes the AI's domain identity, constraints, and output discipline before it reads any document. This grounds subsequent instructions in a clear expert persona.

**Key instructions:**
- Identifies the model as a Senior Database Architect
- Specifies expertise domains: normalization, SQLite, requirements analysis
- Instructs conservative behavior: "You do not invent requirements that are not present in the document"
- Pre-declares the output format expectation: "no markdown fences, no prose explanations outside the JSON structure"

**Actual content (abridged):**
```
You are a Senior Database Architect and Software Engineer with deep expertise in:
- Relational database design and normalization (1NF, 2NF, 3NF)
- SQL schema design for enterprise applications
- Analyzing natural-language software requirements documents
- SQLite database design and syntax
...
You always produce output in the exact JSON format requested — no markdown fences,
no prose explanations outside the JSON structure.
```

---

## Layer 2 — Document Understanding

**File:** `src/prompts/document_understanding.py`  
**Function:** `build_document_understanding(document_text: str) -> str`

**Purpose:** Embeds the actual document text and instructs the model on what to extract from it. This is the only layer that is parameterized (it wraps the document text).

**Key instructions:**
1. Business Entities — main objects the system must track
2. Attributes — per entity, with name, SQLite data type, and nullability
3. Primary Keys — with fallback instruction to propose a surrogate integer PK
4. Foreign Keys — explicit column-to-column references with notation format
5. Entity Relationships — cardinality (one-to-one, one-to-many, many-to-many)
6. Business Rules — constraints and validations mentioned in the document
7. Missing Information and Assumptions — gaps to be documented rather than silently filled

**Design note:** Including the document text in this layer (rather than Layer 1) means the persona instructions are processed before the document text, improving grounding.

---

## Layer 3 — Schema Generation

**File:** `src/prompts/schema_generation.py`  
**Variable:** `SCHEMA_GENERATION` (constant string)

**Purpose:** Translates the extraction output into concrete DDL design decisions. This layer converts understanding into schema.

**Key instructions:**
1. Normalization to 3NF — eliminating repeating groups, partial dependencies, transitive dependencies
2. SQLite-compatible types only — TEXT, INTEGER, REAL, BLOB, NUMERIC (prevents MySQL/PostgreSQL type leakage)
3. Primary key rules — `INTEGER PRIMARY KEY AUTOINCREMENT` as default for surrogate keys
4. Foreign key syntax — explicit `FOREIGN KEY (...) REFERENCES ...` inside `CREATE TABLE`
5. Constraint application — NOT NULL, UNIQUE, CHECK, DEFAULT where requirements indicate
6. Index creation — `CREATE INDEX` on FK columns and frequently filtered columns
7. Naming conventions — `snake_case` for tables and columns; plural noun table names
8. Output restriction — "output only CREATE TABLE and CREATE INDEX statements"

---

## Layer 4 — Validation and Safety

**File:** `src/prompts/validation_safety.py`  
**Variable:** `VALIDATION_SAFETY` (constant string)

**Purpose:** Instructs the model to self-audit before producing output. This layer addresses the two most common LLM failure modes for this task: hallucinated requirements and dangerous SQL.

**Key instructions:**
1. Completeness check — does the document provide enough information for each table?
2. Ambiguity check — document any term or relationship that requires interpretation
3. Assumption audit — record every design decision not directly supported by the document
4. Safety check — explicit enumeration of banned SQL command types:
   `DROP, ALTER, INSERT, UPDATE, DELETE, TRUNCATE, EXEC, PRAGMA, ATTACH`
5. No fabrication — "do not invent business rules, entities, or attributes that are not implied by the document"

**Design note:** This layer names banned SQL types explicitly rather than using a general "no DML" instruction. Explicit enumeration is more reliable with instruction-following models.

---

## Layer 5 — Structured Output

**File:** `src/prompts/structured_output.py`  
**Variable:** `STRUCTURED_OUTPUT` (constant string)

**Purpose:** Enforces the exact JSON contract that the application's parser expects. This is the most critical layer for reliability — if the output format drifts, the entire pipeline fails.

**Key instructions:**
- Return a single JSON object with exactly 8 required keys
- Do NOT wrap in markdown code fences
- Do NOT add text before or after the JSON
- The `sql` field must contain complete, ready-to-execute SQLite DDL

**Required output keys:**
```json
{
  "entities": [...],
  "attributes": {...},
  "primary_keys": {...},
  "foreign_keys": [...],
  "relationships": [...],
  "business_rules": [...],
  "assumptions": [...],
  "sql": "..."
}
```

**Resilience:** Despite this instruction, Gemini occasionally wraps responses in ` ```json ``` ` fences. The `_strip_fences()` function in `src/analyzer.py` handles this at parse time as a defensive fallback.

---

## Validation in Code

The parsed response is validated in `src/analyzer.py`:

```python
_REQUIRED_KEYS = {
    "entities", "attributes", "primary_keys", "foreign_keys",
    "relationships", "business_rules", "assumptions", "sql",
}

missing = _REQUIRED_KEYS - set(data.keys())
if missing:
    return {"success": False, "error": f"Gemini response is missing required keys: {missing}"}
```

If any required key is absent, the pipeline returns a failure result rather than crashing.

---

## Prompt Testing

The test suite in `tests/test_analyzer.py` validates prompt assembly:

```python
def test_prompt_contains_all_layers(self):
    prompt = _build_prompt("test doc")
    assert "Senior Database Architect" in prompt  # role_context
    assert "Business Entities" in prompt          # document_understanding
    assert "Normalization" in prompt              # schema_generation
    assert "Safety" in prompt                     # validation_safety
    assert '"sql"' in prompt                      # structured_output
```
