"""tests/test_analyzer.py — Unit tests for src/analyzer.py (Gemini mocked)"""

from __future__ import annotations

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from src.analyzer import analyze_requirements, _build_prompt, _strip_fences


# ── Fixtures ──────────────────────────────────────────────────────────────────

VALID_ANALYSIS = {
    "entities": [{"name": "Asset", "description": "An IT asset"}],
    "attributes": {
        "Asset": [
            {"name": "id", "type": "INTEGER", "required": True, "description": "PK"}
        ]
    },
    "primary_keys": {"Asset": "id"},
    "foreign_keys": [],
    "relationships": [],
    "business_rules": ["Assets must have serial numbers"],
    "assumptions": ["Surrogate integer PK assumed"],
    "sql": "CREATE TABLE assets (id INTEGER PRIMARY KEY AUTOINCREMENT);",
}


def _make_mock_response(payload: dict) -> MagicMock:
    mock_response = MagicMock()
    mock_response.text = json.dumps(payload)
    return mock_response


# ── Prompt assembly tests ──────────────────────────────────────────────────────

class TestBuildPrompt:
    def test_prompt_contains_document_text(self):
        prompt = _build_prompt("IT Asset inventory requirements")
        assert "IT Asset inventory requirements" in prompt

    def test_prompt_contains_all_layers(self):
        prompt = _build_prompt("test doc")
        # Each layer should contribute content
        assert "Senior Database Architect" in prompt  # role_context
        assert "Business Entities" in prompt          # document_understanding
        assert "Normalization" in prompt               # schema_generation
        assert "Safety" in prompt                      # validation_safety
        assert '"sql"' in prompt                       # structured_output


class TestStripFences:
    def test_strips_json_fence(self):
        assert _strip_fences("```json\n{}\n```") == "{}"

    def test_strips_plain_fence(self):
        assert _strip_fences("```\n{}\n```") == "{}"

    def test_no_fence_unchanged(self):
        assert _strip_fences('{"a": 1}') == '{"a": 1}'

    def test_strips_whitespace(self):
        assert _strip_fences("  {} ") == "{}"


# ── analyze_requirements tests ────────────────────────────────────────────────

class TestAnalyzeRequirements:
    def test_raises_on_missing_api_key(self, monkeypatch):
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        with pytest.raises(EnvironmentError, match="GEMINI_API_KEY"):
            analyze_requirements("some document text")

    def test_happy_path_returns_structured_dict(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "test-key-123")
        mock_response = _make_mock_response(VALID_ANALYSIS)

        with patch("src.analyzer.genai.Client") as MockClient:
            MockClient.return_value.models.generate_content.return_value = mock_response
            result = analyze_requirements("IT Asset Management requirements document")

        assert result["success"] is True
        assert "entities" in result
        assert "sql" in result
        assert result["entities"][0]["name"] == "Asset"

    def test_api_error_returns_failure_dict(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "test-key-123")

        with patch("src.analyzer.genai.Client") as MockClient:
            MockClient.return_value.models.generate_content.side_effect = Exception(
                "Network error"
            )
            result = analyze_requirements("some text")

        assert result["success"] is False
        assert "Gemini API error" in result["error"]

    def test_non_json_response_returns_failure(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "test-key-123")
        mock_response = MagicMock()
        mock_response.text = "Sorry, I cannot help with that."

        with patch("src.analyzer.genai.Client") as MockClient:
            MockClient.return_value.models.generate_content.return_value = mock_response
            result = analyze_requirements("some text")

        assert result["success"] is False
        assert "non-JSON" in result["error"]

    def test_missing_keys_response_returns_failure(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "test-key-123")
        incomplete = {"entities": [], "sql": ""}  # missing many required keys
        mock_response = _make_mock_response(incomplete)

        with patch("src.analyzer.genai.Client") as MockClient:
            MockClient.return_value.models.generate_content.return_value = mock_response
            result = analyze_requirements("some text")

        assert result["success"] is False
        assert "missing required keys" in result["error"]

    def test_json_with_markdown_fences_is_parsed(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "test-key-123")
        fenced_json = "```json\n" + json.dumps(VALID_ANALYSIS) + "\n```"
        mock_response = MagicMock()
        mock_response.text = fenced_json

        with patch("src.analyzer.genai.Client") as MockClient:
            MockClient.return_value.models.generate_content.return_value = mock_response
            result = analyze_requirements("some text")

        assert result["success"] is True

    def test_gemini_model_env_var_is_used(self, monkeypatch):
        """GEMINI_MODEL env var should override the hardcoded default."""
        monkeypatch.setenv("GEMINI_API_KEY", "test-key-123")
        monkeypatch.setenv("GEMINI_MODEL", "gemini-2.5-pro")
        mock_response = _make_mock_response(VALID_ANALYSIS)

        with patch("src.analyzer.genai.Client") as MockClient:
            mock_instance = MockClient.return_value
            mock_instance.models.generate_content.return_value = mock_response
            result = analyze_requirements("some text")

        # Confirm the custom model name was passed to generate_content
        call_kwargs = mock_instance.models.generate_content.call_args
        assert call_kwargs is not None
        model_used = call_kwargs.kwargs.get("model") or call_kwargs.args[0] if call_kwargs.args else None
        # Either positional or keyword — check both
        all_args = list(call_kwargs.args) + list(call_kwargs.kwargs.values())
        assert any("gemini-2.5-pro" in str(a) for a in all_args), (
            f"Expected gemini-2.5-pro in call args, got: {call_kwargs}"
        )
        assert result["success"] is True

    def test_404_error_returns_friendly_message(self, monkeypatch):
        """A 404 NOT_FOUND from the API should return a clear, actionable error."""
        monkeypatch.setenv("GEMINI_API_KEY", "test-key-123")
        monkeypatch.delenv("GEMINI_MODEL", raising=False)

        with patch("src.analyzer.genai.Client") as MockClient:
            MockClient.return_value.models.generate_content.side_effect = Exception(
                "404 NOT_FOUND: models/gemini-2.0-flash is no longer available."
            )
            result = analyze_requirements("some text")

        assert result["success"] is False
        assert "404" in result["error"] or "not available" in result["error"]
        assert "GEMINI_MODEL" in result["error"]

    def test_default_model_is_gemini_25_flash(self, monkeypatch):
        """When GEMINI_MODEL is unset the default must be gemini-2.5-flash."""
        monkeypatch.setenv("GEMINI_API_KEY", "test-key-123")
        monkeypatch.delenv("GEMINI_MODEL", raising=False)
        mock_response = _make_mock_response(VALID_ANALYSIS)

        with patch("src.analyzer.genai.Client") as MockClient:
            mock_instance = MockClient.return_value
            mock_instance.models.generate_content.return_value = mock_response
            analyze_requirements("some text")

        call_kwargs = mock_instance.models.generate_content.call_args
        all_args = list(call_kwargs.args) + list(call_kwargs.kwargs.values())
        assert any("gemini-2.5-flash" in str(a) for a in all_args), (
            f"Expected gemini-2.5-flash as default, got: {call_kwargs}"
        )
