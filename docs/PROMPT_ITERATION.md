# Spec2DB — Prompt Iteration Log

## Transparency Statement

This document records verifiable prompt design decisions made during the development of Spec2DB. Where a specific revision was made for an identified reason, that revision is documented with evidence from the source files.

This document does **not** contain fabricated iteration histories, invented test outputs, or speculative "what the model said" narratives. All claims refer to actual code in the repository.

For historical iteration logs captured during live Gemini testing, see the **Live Testing Observations** section below.

---

## Version History

### v1.0 — Initial Five-Layer Architecture

**When:** Initial implementation (Sub-Task 3, implementation phase)

**Design:** A single monolithic prompt was considered and rejected in favor of five separate modules. The rationale documented in `plans/spec2db-plan.md` is:

> "The prompt engine, validation layer, and execution pipeline are each isolated components so they can be developed, tested, and replaced independently."

**Resulting structure:**
```
src/prompts/
├── role_context.py           # Layer 1
├── document_understanding.py # Layer 2
├── schema_generation.py      # Layer 3
├── validation_safety.py      # Layer 4
└── structured_output.py      # Layer 5
```

---

### Revision R1 — Model Configuration Made Configurable

**Change:** Hardcoded `_MODEL = "gemini-2.0-flash"` replaced with:
```python
_DEFAULT_MODEL = "gemini-2.5-flash"
model = os.environ.get("GEMINI_MODEL", "").strip() or _DEFAULT_MODEL
```

**Reason:** The `gemini-2.0-flash` model was deprecated and returned a 404 NOT_FOUND error during live testing, breaking the Analyze Requirements step.

**Evidence:** Commit-traceable change in `src/analyzer.py` lines 25 and 94–95.

**Impact:** The model is now configurable without code changes. Users set `GEMINI_MODEL=` in `.env`.

---

### Revision R2 — 404 Error Detection Added

**Change:** Added explicit detection of `404 / NOT_FOUND / no longer available` in the exception handler:

```python
if "404" in exc_str or "NOT_FOUND" in exc_str or "no longer available" in exc_str:
    return {
        "success": False,
        "error": (
            f"Model '{model}' is not available (404 NOT_FOUND). "
            f"Set the GEMINI_MODEL environment variable in your .env file..."
        ),
    }
```

**Reason:** Without this check, users saw an opaque API error with no actionable guidance.

**Evidence:** `src/analyzer.py` lines 104–112. Covered by `test_404_error_returns_friendly_message` in `tests/test_analyzer.py`.

---

### Revision R3 — Fence Stripping Defensive Layer Added

**Change:** `_strip_fences()` function added to `src/analyzer.py`:
```python
text = re.sub(r"^```(?:json)?\s*", "", text)
text = re.sub(r"\s*```$", "", text)
```

**Reason:** Despite explicit instructions in both Layer 1 and Layer 5 that "no markdown fences" should be used, Gemini 2.x models occasionally wrap JSON responses in ` ```json ``` ` fences. Without stripping, `json.loads()` would fail.

**Evidence:** `src/analyzer.py` `_strip_fences()` function. Covered by `test_json_with_markdown_fences_is_parsed` and `test_strips_json_fence` tests.

**Design note:** This is documented in `PROMPTS.md` under "Known Prompt Limitations — Markdown fences."

---

## Known Prompt Behavior Observations

These observations were noted during development and are reflected in the implementation:

### Observation 1 — SQLite Type Compliance

**Issue:** Without the explicit instruction "use only SQLite-compatible data types: TEXT, INTEGER, REAL, BLOB, NUMERIC," Gemini sometimes generates `VARCHAR(255)` or `SERIAL` (MySQL/PostgreSQL syntax).

**Mitigation:** Layer 3 (`schema_generation.py`) explicitly names the permitted SQLite types and bans implicit dialect switching.

**Current status:** Still occasionally observed; `sqlglot` parses these without error (SQLite accepts them), but they are non-canonical. Documented as a known limitation.

---

### Observation 2 — Missing Key Validation

**Issue:** Early response parsing assumed all required keys would always be present. A response that was missing any key would cause a `KeyError` in downstream code.

**Mitigation:** `src/analyzer.py` performs an explicit key presence check before returning:
```python
missing = _REQUIRED_KEYS - set(data.keys())
if missing:
    return {"success": False, "error": f"...missing required keys: {missing}"}
```

---

### Observation 3 — Assumption Logging Effectiveness

**Observation:** Layer 4's "No fabrication" instruction ("do not invent business rules, entities, or attributes that are not implied by the document") combined with Layer 4's "Assumption audit" instruction produces more transparent schemas.

**Evidence:** The `assumptions` key in the response JSON routinely contains entries like "Surrogate integer PKs assumed throughout" and "Email assumed to be unique per employee," reflecting genuine design decisions rather than silent choices.

---

## Evaluation Protocol for Future Iterations

For each future prompt change, record the following:

| Field | Description |
|---|---|
| **Version** | Increment from current version |
| **Layer changed** | Which of the 5 layers was modified |
| **Change** | What text was added, removed, or modified |
| **Reason** | What problem or observation triggered the change |
| **Test document** | Which PDF or text was used to evaluate the change |
| **Before output** | Relevant excerpt from the JSON response before the change |
| **After output** | Relevant excerpt from the JSON response after the change |
| **Verdict** | Improved / No change / Regression |
| **Committed** | Yes / No |

This protocol ensures future iterations are evidence-based and reproducible.
