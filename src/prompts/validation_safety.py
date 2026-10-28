"""
src/prompts/validation_safety.py — Layer 4: Validation and Safety

Instructs the model to audit its own analysis for gaps, ambiguities,
and design decisions that require explicit assumptions.
"""

VALIDATION_SAFETY = """\
## Validation and Safety Instructions

Before producing your final output, perform the following self-audit:

1. **Completeness check** — does the requirements document provide enough
   information to build each table you have identified? List any missing details.

2. **Ambiguity check** — are any terms, relationships, or rules ambiguous?
   If so, document the interpretation you have chosen.

3. **Assumption audit** — for every design decision not directly supported
   by the document (e.g. choosing a surrogate key, inferring cardinality),
   record it in the `assumptions` list of your output.

4. **Safety check** — your SQL output must contain ONLY:
   - CREATE TABLE statements
   - CREATE INDEX statements
   Do NOT include DROP, ALTER, INSERT, UPDATE, DELETE, TRUNCATE, EXEC,
   PRAGMA, ATTACH, or any other SQL command. If you find yourself about
   to write any such statement, stop and omit it.

5. **No fabrication** — do not invent business rules, entities, or attributes
   that are not implied by the document. Mark inferred items as assumptions.
"""
