"""
src/analyzer.py — Feature B: AI Requirement Analysis.

Assembles the five-layer prompt, calls the Gemini API, and returns a
structured dict with entities, attributes, relationships, and SQL.

Model selection (in priority order):
  1. GEMINI_MODEL environment variable (set in .env)
  2. Hard-coded default: gemini-2.5-flash
"""

from __future__ import annotations

import json
import os
import re

import google.genai as genai
from dotenv import load_dotenv

from src.prompts.role_context import ROLE_CONTEXT
from src.prompts.document_understanding import build_document_understanding
from src.prompts.schema_generation import SCHEMA_GENERATION
from src.prompts.validation_safety import VALIDATION_SAFETY
from src.prompts.structured_output import STRUCTURED_OUTPUT

load_dotenv()

_DEFAULT_MODEL = "gemini-2.5-flash"

# Keys that must be present in a valid analysis response
_REQUIRED_KEYS = {
    "entities",
    "attributes",
    "primary_keys",
    "foreign_keys",
    "relationships",
    "business_rules",
    "assumptions",
    "sql",
}


def _build_prompt(document_text: str) -> str:
    """Assemble the five prompt layers into a single prompt string."""
    return "\n\n".join(
        [
            ROLE_CONTEXT,
            build_document_understanding(document_text),
            SCHEMA_GENERATION,
            VALIDATION_SAFETY,
            STRUCTURED_OUTPUT,
        ]
    )


def _strip_fences(text: str) -> str:
    """Remove markdown code fences if the model added them despite instructions."""
    text = text.strip()
    # Remove ```json ... ``` or ``` ... ```
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def analyze_requirements(document_text: str) -> dict:
    """Analyze a requirements document and return structured schema information.

    Args:
        document_text: The plain-text content extracted from the PDF.

    Returns:
        On success:
            {
                "success": True,
                "entities": [...],
                "attributes": {...},
                "primary_keys": {...},
                "foreign_keys": [...],
                "relationships": [...],
                "business_rules": [...],
                "assumptions": [...],
                "sql": "...",
            }
        On failure:
            {"success": False, "error": "..."}

    Raises:
        EnvironmentError: if GEMINI_API_KEY is not set.
    """
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise EnvironmentError(
            "GEMINI_API_KEY environment variable is not set. "
            "Copy .env.example to .env and add your key."
        )

    model = os.environ.get("GEMINI_MODEL", "").strip() or _DEFAULT_MODEL
    prompt = _build_prompt(document_text)

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model,
            contents=prompt,
        )
        raw_text = response.text
    except Exception as exc:
        exc_str = str(exc)
        # Detect model-not-found / retired-model errors and give an actionable message
        if "404" in exc_str or "NOT_FOUND" in exc_str or "no longer available" in exc_str:
            return {
                "success": False,
                "error": (
                    f"Model '{model}' is not available (404 NOT_FOUND). "
                    f"Set the GEMINI_MODEL environment variable in your .env file to a "
                    f"valid model name (e.g. gemini-2.5-flash) and restart the app."
                ),
            }
        return {"success": False, "error": f"Gemini API error: {exc}"}

    cleaned = _strip_fences(raw_text)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        return {
            "success": False,
            "error": (
                f"Gemini returned non-JSON output: {exc}. "
                f"Raw response (first 500 chars): {raw_text[:500]}"
            ),
        }

    missing = _REQUIRED_KEYS - set(data.keys())
    if missing:
        return {
            "success": False,
            "error": f"Gemini response is missing required keys: {missing}",
        }

    data["success"] = True
    return data
