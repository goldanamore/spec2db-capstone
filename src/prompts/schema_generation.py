"""
src/prompts/schema_generation.py — Layer 3: Schema Generation

Instructs the model to produce a normalized relational schema in SQLite DDL.
"""

SCHEMA_GENERATION = """\
## Schema Generation Instructions

Based on your analysis of the document, design a normalized relational database
schema that satisfies the requirements. Apply these rules:

1. **Normalization** — ensure the schema is in Third Normal Form (3NF).
   Eliminate repeating groups, partial dependencies, and transitive dependencies.

2. **SQLite Compatibility** — use only SQLite-compatible data types:
   TEXT, INTEGER, REAL, BLOB, NUMERIC.

3. **Primary Keys** — every table must have a PRIMARY KEY.
   Prefer INTEGER PRIMARY KEY AUTOINCREMENT for surrogate keys.

4. **Foreign Keys** — declare all foreign key relationships explicitly using
   FOREIGN KEY (...) REFERENCES ... syntax inside the CREATE TABLE statement.

5. **Constraints** — apply NOT NULL, UNIQUE, CHECK, and DEFAULT constraints
   where the requirements or your analysis indicate they are needed.

6. **Indexes** — create CREATE INDEX statements for foreign key columns and
   any columns that will be frequently searched or filtered.

7. **Naming** — use snake_case for all table and column names.
   Table names should be plural nouns (e.g. assets, employees, locations).

8. **No extra statements** — output only CREATE TABLE and CREATE INDEX statements.
   Do not output DROP, ALTER, INSERT, UPDATE, DELETE, PRAGMA, or any other SQL.
"""
