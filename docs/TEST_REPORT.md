# Spec2DB — Test Report

## Summary

| Metric | Value |
|---|---|
| **Test framework** | pytest 9.2.0 |
| **Python version** | 3.12.5 |
| **Total tests** | 62 |
| **Passed** | 62 |
| **Failed** | 0 |
| **Execution time** | ~1.8 seconds |
| **LLM calls in test suite** | 0 (all mocked) |
| **External dependencies required** | None |
| **Last executed** | Phase 6 QA run (see below) |

---

## Test Files

### `tests/test_extractor.py` — PDF Extraction (5 tests)

| Test | Type | Input | Expected | Actual | Status |
|---|---|---|---|---|---|
| `test_valid_single_page_pdf` | Unit | Minimal valid PDF bytes | `success: True`, `page_count: 1` | Matches | ✅ PASS |
| `test_non_pdf_bytes_returns_failure` | Unit | `b"this is not a pdf"` | `success: False`, error message | Matches | ✅ PASS |
| `test_empty_bytes_returns_failure` | Unit | `b""` | `success: False`, error message | Matches | ✅ PASS |
| `test_result_keys_always_present` | Unit | Invalid bytes | Dict with all 4 keys present | Matches | ✅ PASS |
| `test_page_count_is_integer` | Unit | Invalid bytes | `page_count` is `int` | Matches | ✅ PASS |

**Notes:**
- Tests use a programmatically constructed minimal valid PDF (no external fixture files)
- The PDF fixture is built in `io.BytesIO` so no disk I/O is required

---

### `tests/test_analyzer.py` — AI Requirement Analysis (15 tests)

| Test | Type | Scenario | Status |
|---|---|---|---|
| `test_prompt_contains_document_text` | Unit | Document text appears in assembled prompt | ✅ PASS |
| `test_prompt_contains_all_layers` | Unit | All 5 layer signatures present in prompt | ✅ PASS |
| `test_strips_json_fence` | Unit | ` ```json{}``` ` → `{}` | ✅ PASS |
| `test_strips_plain_fence` | Unit | ` ```{}``` ` → `{}` | ✅ PASS |
| `test_no_fence_unchanged` | Unit | `{"a": 1}` unchanged | ✅ PASS |
| `test_strips_whitespace` | Unit | Leading/trailing whitespace stripped | ✅ PASS |
| `test_raises_on_missing_api_key` | Unit | `GEMINI_API_KEY` unset → `EnvironmentError` | ✅ PASS |
| `test_happy_path_returns_structured_dict` | Unit (mocked) | Valid JSON response → `success: True` + all keys | ✅ PASS |
| `test_api_error_returns_failure_dict` | Unit (mocked) | SDK raises exception → `success: False` | ✅ PASS |
| `test_non_json_response_returns_failure` | Unit (mocked) | Non-JSON response → `success: False` | ✅ PASS |
| `test_missing_keys_response_returns_failure` | Unit (mocked) | Incomplete JSON → `success: False` | ✅ PASS |
| `test_json_with_markdown_fences_is_parsed` | Unit (mocked) | Fenced JSON → `success: True` after stripping | ✅ PASS |
| `test_gemini_model_env_var_is_used` | Unit (mocked) | `GEMINI_MODEL=gemini-2.5-pro` → passed to SDK call | ✅ PASS |
| `test_404_error_returns_friendly_message` | Unit (mocked) | `404 NOT_FOUND` exception → error mentions `GEMINI_MODEL` | ✅ PASS |
| `test_default_model_is_gemini_25_flash` | Unit (mocked) | No `GEMINI_MODEL` set → `gemini-2.5-flash` used | ✅ PASS |

**Notes:**
- All Gemini API calls are mocked using `unittest.mock.patch`
- No API quota is consumed by this test file
- `monkeypatch` is used for all environment variable manipulation

---

### `tests/test_schema_gen.py` — Schema Generation (8 tests)

| Test | Status |
|---|---|
| `test_strips_sql_fence` — ` ```sql...``` ` removed | ✅ PASS |
| `test_no_fence_unchanged` — clean SQL passes through | ✅ PASS |
| `test_splits_two_statements` — semicolon split | ✅ PASS |
| `test_empty_string_returns_empty_list` | ✅ PASS |
| `test_single_statement` | ✅ PASS |
| `test_happy_path_returns_statements` — 2 statements from valid analysis | ✅ PASS |
| `test_strips_markdown_fences_in_sql` — fences in `sql` field removed | ✅ PASS |
| `test_failed_analysis_returns_failure` — propagates upstream failure | ✅ PASS |
| `test_missing_sql_key_returns_failure` — empty `sql` field → failure | ✅ PASS |
| `test_result_always_has_required_keys` — all 4 keys always present | ✅ PASS |

---

### `tests/test_validator.py` — SQL Validation (16 tests)

#### Approved Statements (Positive Tests)

| Statement | Status |
|---|---|
| `CREATE TABLE assets (id INTEGER PRIMARY KEY);` | ✅ APPROVED |
| `CREATE INDEX idx_name ON assets(name);` | ✅ APPROVED |
| Multiple valid statements in one string | ✅ ALL APPROVED |

#### Security / Rejection Tests

| Statement | Expected | Status |
|---|---|---|
| `DROP TABLE assets;` | REJECTED | ✅ PASS |
| `DELETE FROM assets WHERE id = 1;` | REJECTED | ✅ PASS |
| `INSERT INTO assets (name) VALUES ('test');` | REJECTED | ✅ PASS |
| `UPDATE assets SET name = 'x' WHERE id = 1;` | REJECTED | ✅ PASS |
| `ALTER TABLE assets ADD COLUMN notes TEXT;` | REJECTED | ✅ PASS |
| `PRAGMA foreign_keys = ON;` | REJECTED | ✅ PASS |
| `CREATE VIEW v AS SELECT * FROM assets;` | REJECTED | ✅ PASS |
| `CREATE TRIGGER trg AFTER INSERT...` | REJECTED | ✅ PASS |
| `ATTACH DATABASE 'other.db' AS other;` | REJECTED | ✅ PASS |

#### Mixed / Edge Cases

| Scenario | Status |
|---|---|
| Valid + `DROP TABLE` → `valid: False` | ✅ PASS |
| Empty string input | ✅ PASS |
| Whitespace-only input | ✅ PASS |
| All 4 result keys always present | ✅ PASS |
| Approved statements end with `;` | ✅ PASS |

---

### `tests/test_executor.py` — Database Execution (9 tests)

| Test | Scenario | Status |
|---|---|---|
| `test_creates_tables_successfully` | 2-table schema with FK | ✅ PASS |
| `test_creates_index_successfully` | Table + index | ✅ PASS |
| `test_empty_statements_returns_failure` | Empty list → `success: False` | ✅ PASS |
| `test_bad_sql_returns_failure_and_no_tables` | Invalid SQL → `success: False` | ✅ PASS |
| `test_creates_parent_directory_if_missing` | Nested path created | ✅ PASS |
| `test_tables_created_list_matches_actual_db` | PASS: verified via sqlite3 directly | ✅ PASS |
| `test_returns_columns` | PRAGMA table_info works | ✅ PASS |
| `test_returns_foreign_keys` | PRAGMA foreign_key_list works | ✅ PASS |
| `test_nonexistent_table_returns_empty_columns` | Missing table → empty list, not error | ✅ PASS |

**Notes:**
- All tests use `tmp_path` pytest fixture — no permanent database files are created
- Tests are isolated; no shared state between runs

---

### `tests/test_integration.py` — Full Pipeline (6 tests)

| Test | Pipeline Steps Covered | Status |
|---|---|---|
| `test_generate_schema_from_analysis` | schema_gen | ✅ PASS |
| `test_validate_generated_schema` | schema_gen → validator | ✅ PASS |
| `test_execute_validated_schema` | schema_gen → validator → executor | ✅ PASS |
| `test_inspect_tables_after_execution` | Full pipeline + inspect | ✅ PASS |
| `test_execute_rejects_empty_statements` | executor guard | ✅ PASS |
| `test_validate_rejects_injection_in_pipeline` | Injection test: DROP in mixed SQL | ✅ PASS |

**IT Asset Inventory schema used:** 5 tables (employees, locations, asset_categories, assets, asset_assignments), 5 indexes. All generated from a pre-built analysis dict without any Gemini API call.

---

## Manual Testing

### Application Startup Smoke Test

**Command:** `streamlit run app.py`  
**Result:** Application started successfully at `http://localhost:8501`  
**Startup log confirmed:**
```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
Network URL: http://192.168.18.75:8501
```

### End-to-End Workflow

The full workflow was exercised manually during development:

| Step | Status |
|---|---|
| PDF upload and text extraction | ✅ Verified manually |
| AI requirement analysis (live Gemini call) | ✅ Verified manually |
| Schema generation | ✅ Verified manually |
| SQL validation display | ✅ Verified manually |
| User approval gate | ✅ Verified manually (checkbox required) |
| SQLite database creation | ✅ Verified manually — `data/demo_20261028_233129.db` exists |
| Result verification (tables displayed) | ✅ Verified manually |

**Note:** The database file `data/demo_20261028_233129.db` in the project directory is direct evidence of a successful end-to-end execution. This file is excluded from Git by `.gitignore`.

---

## Outstanding Issues and Known Limitations

| Issue | Severity | Status |
|---|---|---|
| Gemini may generate non-SQLite-native types (VARCHAR, SERIAL) | Low | Known; sqlglot accepts them; documented as limitation |
| Gemini occasionally adds markdown fences despite instructions | Low | Mitigated by `_strip_fences()` |
| Scanned / image-only PDFs cannot be processed | Medium | Documented limitation; OCR not in scope |
| Model availability changes require `GEMINI_MODEL` env var update | Medium | Mitigated by configurable env var + 404 detection |
| No live integration test (Gemini API not called in test suite) | Medium | By design — avoids API quota consumption |
