"""
src/prompts/structured_output.py — Layer 5: Structured Output

Specifies the exact JSON schema the model must return.
The model must return ONLY this JSON — no prose, no markdown fences.
"""

STRUCTURED_OUTPUT = """\
## Output Format

Return your response as a single JSON object with exactly the following structure.
Do NOT wrap it in markdown code fences. Do NOT add any text before or after the JSON.

{
  "entities": [
    {
      "name": "string — entity name (singular, PascalCase)",
      "description": "string — one-sentence description of what this entity represents"
    }
  ],
  "attributes": {
    "<EntityName>": [
      {
        "name": "string — column name in snake_case",
        "type": "string — SQLite type: TEXT | INTEGER | REAL | BLOB | NUMERIC",
        "required": true,
        "description": "string — what this attribute stores"
      }
    ]
  },
  "primary_keys": {
    "<EntityName>": "string — column name of the primary key"
  },
  "foreign_keys": [
    {
      "from_entity": "string",
      "from_column": "string",
      "to_entity": "string",
      "to_column": "string",
      "relationship": "string — e.g. many-to-one"
    }
  ],
  "relationships": [
    {
      "entities": ["string", "string"],
      "cardinality": "string — one-to-one | one-to-many | many-to-many",
      "description": "string — plain-English description of the relationship"
    }
  ],
  "business_rules": [
    "string — each business rule as a plain-English sentence"
  ],
  "assumptions": [
    "string — each design assumption or gap as a plain-English sentence"
  ],
  "sql": "string — complete DDL SQL containing only CREATE TABLE and CREATE INDEX statements, with each statement separated by a semicolon and newline"
}

All keys are required. Use empty arrays [] or empty objects {} when there is nothing
to report for a section. The `sql` field must contain the complete ready-to-execute
SQLite DDL for all tables and indexes.
"""
