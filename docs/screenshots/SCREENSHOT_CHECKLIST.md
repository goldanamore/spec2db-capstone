# Screenshots — Manual Capture Checklist

This checklist identifies every screenshot required for the capstone submission. Screenshots cannot be captured automatically because they require the live Streamlit application with a real Gemini API call.

**Before capturing:** Start the application with `streamlit run app.py` and ensure your `.env` file contains a valid `GEMINI_API_KEY`.

**Important:** Do NOT capture any screen that shows an API key, password, token, or private account information.

---

## Required Screenshots

### 1. Application Main Interface
**Filename:** `01_main_interface.png`  
**What to capture:** The Streamlit application landing page at `http://localhost:8501` before any file is uploaded.  
**Shows:** Application title, subtitle, Step 1 upload widget, overall layout.

---

### 2. PDF Upload — Success
**Filename:** `02_pdf_upload_success.png`  
**What to capture:** After uploading a PDF requirements document.  
**Shows:** Green success message "Extracted X page(s) — N characters", the preview expander open with extracted text visible.  
**Note:** Use a requirements document that does not contain any personal or sensitive information.

---

### 3. AI Requirement Analysis — Result
**Filename:** `03_ai_analysis_result.png`  
**What to capture:** After clicking "Analyze Requirements" and the Gemini response has loaded.  
**Shows:** The entities list, relationships, business rules, and assumptions — all populated from the real Gemini response.  
**Note:** This is the screen that proves the live AI integration works.

---

### 4. Full Analysis JSON
**Filename:** `04_analysis_json.png`  
**What to capture:** The "Full analysis JSON" expander opened.  
**Shows:** The complete structured JSON response from Gemini including entities, attributes, PKs, FKs.

---

### 5. Generated Database Schema (SQL)
**Filename:** `05_generated_schema_sql.png`  
**What to capture:** After clicking "Generate Schema SQL".  
**Shows:** The `st.code` block containing the complete CREATE TABLE and CREATE INDEX DDL.

---

### 6. SQL Validation Result
**Filename:** `06_sql_validation_result.png`  
**What to capture:** The validation metrics section.  
**Shows:** "Approved statements: N", "Rejected statements: 0", "Valid: ✅ Yes" — confirming all statements passed.

---

### 7. User Approval Gate
**Filename:** `07_approval_gate.png`  
**What to capture:** The Step 5 approval section with the approved SQL displayed and the checkbox visible.  
**Shows:** The warning message, the SQL code block, and the confirmation checkbox (unchecked).

---

### 8. Database Creation Success
**Filename:** `08_database_created.png`  
**What to capture:** After approving and clicking "Create Database".  
**Shows:** Green success message "Database created at data/demo_TIMESTAMP.db — N statements executed, N tables created."

---

### 9. Database Verification Results
**Filename:** `09_database_verification.png`  
**What to capture:** Step 7 result section with tables expanded.  
**Shows:** At least one expanded table expander showing the column dataframe (name, type, NOT NULL, Primary Key) and any foreign key references listed below.

---

### 10. Error Handling — Missing API Key
**Filename:** `10_error_missing_api_key.png`  
**What to capture:** Temporarily rename `.env` to `.env.bak`, restart the app, capture the error banner.  
**Shows:** The red error message "GEMINI_API_KEY is not set."  
**After capturing:** Rename `.env.bak` back to `.env`.

---

## IBM Bob Development Evidence

The following screenshots of IBM Bob are requested but **cannot be captured automatically** by this tool. They must be captured manually from the IBM Bob interface.

### 11. IBM Bob — Prompt Configuration
**Filename:** `11_ibm_bob_prompt_config.png`  
**What to capture:** The IBM Bob task interface showing the initial project prompt or plan message sent to Bob.

### 12. IBM Bob — Development Conversation (Representative)
**Filename:** `12_ibm_bob_development.png`  
**What to capture:** A representative portion of the Bob conversation showing code generation or a feature implementation exchange.

### 13. IBM Bob — Test Results in Bob
**Filename:** `13_ibm_bob_test_results.png`  
**What to capture:** The Bob conversation turn where tests were run and results were reported (62 passed).

---

## Capture Instructions

1. Use your operating system's screenshot tool:
   - **Windows:** `Win + Shift + S` (Snip & Sketch) or `PrintScreen`
   - **macOS:** `Cmd + Shift + 4`
2. Save all screenshots to `docs/screenshots/` using the exact filenames above
3. Use PNG format
4. Ensure no API keys, tokens, or passwords are visible in any screenshot
5. Crop screenshots to show only the relevant application area

---

## Status

| Screenshot | Status |
|---|---|
| 01_main_interface.png | ⬜ Needs manual capture |
| 02_pdf_upload_success.png | ⬜ Needs manual capture |
| 03_ai_analysis_result.png | ⬜ Needs manual capture |
| 04_analysis_json.png | ⬜ Needs manual capture |
| 05_generated_schema_sql.png | ⬜ Needs manual capture |
| 06_sql_validation_result.png | ⬜ Needs manual capture |
| 07_approval_gate.png | ⬜ Needs manual capture |
| 08_database_created.png | ⬜ Needs manual capture |
| 09_database_verification.png | ⬜ Needs manual capture |
| 10_error_missing_api_key.png | ⬜ Needs manual capture |
| 11_ibm_bob_prompt_config.png | ⬜ Needs manual capture (IBM Bob interface) |
| 12_ibm_bob_development.png | ⬜ Needs manual capture (IBM Bob interface) |
| 13_ibm_bob_test_results.png | ⬜ Needs manual capture (IBM Bob interface) |
