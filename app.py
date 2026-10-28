"""
app.py — Spec2DB Streamlit Application

Seven-stage pipeline:
  Upload PDF → Extract Text → Analyze Requirements → Generate Schema
  → Validate SQL → Approve Execution → Execute → View Results
"""

from __future__ import annotations

import os
import time
from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from src.extractor import extract_text
from src.analyzer import analyze_requirements
from src.schema_gen import generate_schema
from src.validator import validate_sql
from src.executor import execute_schema, inspect_table

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Spec2DB — AI Document to Database",
    page_icon="🗄️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Session state defaults ────────────────────────────────────────────────────
_DEFAULTS = {
    "extracted_text": None,
    "page_count": 0,
    "analysis": None,
    "schema_result": None,
    "validation_result": None,
    "approved": False,
    "execution_result": None,
    "db_path": None,
}
for key, val in _DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = val


def _reset_from(stage: str) -> None:
    """Clear all downstream state when a new input arrives at `stage`."""
    order = [
        "extracted_text",
        "analysis",
        "schema_result",
        "validation_result",
        "approved",
        "execution_result",
        "db_path",
    ]
    clear = False
    for key in order:
        if key == stage:
            clear = True
        if clear:
            st.session_state[key] = _DEFAULTS[key]


# ── Header ────────────────────────────────────────────────────────────────────
st.title("🗄️ Spec2DB")
st.caption("AI-Powered Document to Database Generator · IBM SkillsBuild Capstone")

# ── API key check ─────────────────────────────────────────────────────────────
api_key = os.environ.get("GEMINI_API_KEY", "").strip()
if not api_key:
    st.error(
        "**GEMINI_API_KEY is not set.** "
        "Copy `.env.example` to `.env` and add your Google Gemini API key, "
        "then restart the app."
    )
    st.stop()

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# STAGE 1 — Upload PDF
# ══════════════════════════════════════════════════════════════════════════════
st.subheader("Step 1 — Upload Requirements Document")

uploaded_file = st.file_uploader(
    "Upload a PDF requirements document",
    type=["pdf"],
    help="Upload a natural-language software requirements document in PDF format.",
)

if uploaded_file is not None:
    # Re-extract whenever a new file is uploaded
    if st.session_state.extracted_text is None:
        with st.spinner("Extracting text from PDF…"):
            result = extract_text(uploaded_file)

        if not result["success"]:
            st.error(f"❌ PDF extraction failed: {result['error']}")
            _reset_from("extracted_text")
        else:
            st.session_state.extracted_text = result["text"]
            st.session_state.page_count = result["page_count"]
            _reset_from("analysis")  # clear downstream on new upload

    if st.session_state.extracted_text:
        st.success(
            f"✅ Extracted {st.session_state.page_count} page(s) — "
            f"{len(st.session_state.extracted_text):,} characters"
        )
        with st.expander("Preview extracted text", expanded=False):
            st.text(st.session_state.extracted_text[:3000])
            if len(st.session_state.extracted_text) > 3000:
                st.caption("… (truncated for display; full text sent to AI)")
else:
    _reset_from("extracted_text")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# STAGE 2 — AI Requirement Analysis
# ══════════════════════════════════════════════════════════════════════════════
st.subheader("Step 2 — Analyze Requirements with AI")

if st.session_state.extracted_text is None:
    st.info("Upload a PDF document above to enable analysis.")
else:
    if st.button("🔍 Analyze Requirements", use_container_width=True):
        with st.spinner("Sending document to Gemini for analysis… (this may take 15–30 s)"):
            try:
                analysis = analyze_requirements(st.session_state.extracted_text)
            except EnvironmentError as exc:
                st.error(f"❌ Configuration error: {exc}")
                analysis = None

        if analysis is None:
            pass  # error already shown
        elif not analysis.get("success"):
            st.error(f"❌ Analysis failed: {analysis.get('error')}")
            _reset_from("analysis")
        else:
            st.session_state.analysis = analysis
            _reset_from("schema_result")

    if st.session_state.analysis:
        analysis = st.session_state.analysis
        st.success("✅ Analysis complete")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Entities identified**")
            for ent in analysis.get("entities", []):
                st.markdown(f"- **{ent['name']}** — {ent.get('description', '')}")

            st.markdown("**Relationships**")
            for rel in analysis.get("relationships", []):
                entities = " ↔ ".join(rel.get("entities", []))
                st.markdown(f"- {entities} ({rel.get('cardinality', '')})")

        with col2:
            st.markdown("**Business rules**")
            for rule in analysis.get("business_rules", []):
                st.markdown(f"- {rule}")

            st.markdown("**Assumptions made**")
            for assumption in analysis.get("assumptions", []):
                st.markdown(f"- ⚠️ {assumption}")

        with st.expander("Full analysis JSON", expanded=False):
            # Show without the SQL key to keep it readable here
            display = {k: v for k, v in analysis.items() if k not in {"sql", "success"}}
            st.json(display)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# STAGE 3 — Generate Schema SQL
# ══════════════════════════════════════════════════════════════════════════════
st.subheader("Step 3 — Generate Database Schema")

if st.session_state.analysis is None:
    st.info("Complete the analysis step above to generate a schema.")
else:
    if st.button("⚙️ Generate Schema SQL", use_container_width=True):
        with st.spinner("Generating SQL schema…"):
            schema_result = generate_schema(st.session_state.analysis)

        if not schema_result["success"]:
            st.error(f"❌ Schema generation failed: {schema_result['error']}")
            _reset_from("schema_result")
        else:
            st.session_state.schema_result = schema_result
            # Auto-validate immediately
            validation = validate_sql(schema_result["sql"])
            st.session_state.validation_result = validation
            _reset_from("approved")

    if st.session_state.schema_result:
        schema = st.session_state.schema_result
        st.success(
            f"✅ {len(schema['statements'])} statement(s) generated"
        )
        st.code(schema["sql"], language="sql")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# STAGE 4 — SQL Validation
# ══════════════════════════════════════════════════════════════════════════════
st.subheader("Step 4 — SQL Validation")

if st.session_state.validation_result is None:
    st.info("Generate a schema above to see validation results.")
else:
    vr = st.session_state.validation_result
    approved_count = len(vr["approved_statements"])
    rejected_count = len(vr["rejected_statements"])

    col1, col2, col3 = st.columns(3)
    col1.metric("Approved statements", approved_count)
    col2.metric("Rejected statements", rejected_count, delta_color="inverse")
    col3.metric("Valid", "✅ Yes" if vr["valid"] else "❌ No")

    if vr["valid"]:
        st.success("✅ All statements passed validation — only CREATE TABLE and CREATE INDEX detected.")
    else:
        st.error("❌ Validation failed — some statements were rejected.")
        for err in vr["errors"]:
            st.warning(err)
        if vr["rejected_statements"]:
            with st.expander("Rejected statements"):
                for stmt in vr["rejected_statements"]:
                    st.code(stmt, language="sql")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# STAGE 5 — User Approval Gate
# ══════════════════════════════════════════════════════════════════════════════
st.subheader("Step 5 — Approve Database Creation")

vr = st.session_state.validation_result

if vr is None:
    st.info("Complete validation above before approving execution.")
elif not vr["valid"]:
    st.error("❌ Cannot approve execution — the SQL did not pass validation.")
else:
    st.warning(
        "⚠️ **Review the SQL above carefully.** "
        "Clicking the button below will create a new SQLite database file "
        "in the `data/` directory and execute the approved statements."
    )

    approved_sql = "\n\n".join(vr["approved_statements"])
    with st.expander("Approved statements to be executed", expanded=True):
        st.code(approved_sql, language="sql")

    confirmed = st.checkbox(
        "I have reviewed the SQL and confirm I want to create this demonstration database."
    )
    st.session_state.approved = confirmed

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# STAGE 6 — Execute
# ══════════════════════════════════════════════════════════════════════════════
st.subheader("Step 6 — Create Database")

if not st.session_state.approved:
    st.info("Check the approval box above to enable execution.")
else:
    if st.button("🚀 Create Database", type="primary", use_container_width=True):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        db_path = str(Path("data") / f"demo_{timestamp}.db")
        st.session_state.db_path = db_path

        with st.spinner("Executing SQL against isolated SQLite database…"):
            exec_result = execute_schema(
                st.session_state.validation_result["approved_statements"],
                db_path,
            )

        st.session_state.execution_result = exec_result

    if st.session_state.execution_result:
        er = st.session_state.execution_result
        if er["success"]:
            st.success(
                f"✅ Database created at `{st.session_state.db_path}` — "
                f"{er['statements_executed']} statement(s) executed, "
                f"{len(er['tables_created'])} table(s) created."
            )
        else:
            st.error(f"❌ Execution failed: {er['error']}")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# STAGE 7 — Results Verification
# ══════════════════════════════════════════════════════════════════════════════
st.subheader("Step 7 — Verify Database Results")

er = st.session_state.execution_result

if er is None or not er["success"]:
    st.info("Execute the database creation above to see results.")
else:
    tables = er["tables_created"]
    st.success(f"✅ {len(tables)} table(s) found in the database.")

    for table_name in tables:
        with st.expander(f"📋 Table: `{table_name}`", expanded=True):
            info = inspect_table(st.session_state.db_path, table_name)
            if not info["success"]:
                st.error(info["error"])
                continue

            if info["columns"]:
                import pandas as pd
                col_df = pd.DataFrame(info["columns"])
                col_df.columns = ["Column", "Type", "NOT NULL", "Primary Key"]
                st.dataframe(col_df, use_container_width=True, hide_index=True)
            else:
                st.caption("No columns found.")

            if info["foreign_keys"]:
                st.markdown("**Foreign Keys:**")
                for fk in info["foreign_keys"]:
                    st.markdown(
                        f"- `{table_name}.{fk['from']}` → `{fk['table']}.{fk['to']}`"
                    )

    st.info(
        f"Database file: `{st.session_state.db_path}`  \n"
        "This is an isolated demonstration database. "
        "It is not connected to any production system."
    )

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption("Spec2DB · IBM SkillsBuild University Education Capstone · Built with Google Gemini, Streamlit, and SQLite")
