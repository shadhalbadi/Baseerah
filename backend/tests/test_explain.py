"""Explanation layer — the deterministic parts (prompt building + no-key fallback).

The live Claude call is not exercised here (needs a network + key); those are
covered by the prompt contract and the disabled-path guarantees.
"""

from app.models.bill import UtilityType
from app.services.analysis import BillPoint, analyze
from app.services.explain import build_user_prompt, explain, explanations_enabled


def _result():
    points = [BillPoint(c, c * 2.5) for c in (10, 10, 10, 10, 22)]
    return analyze(1, UtilityType.water, points)


def test_prompt_includes_language_and_numbers():
    result = _result()
    prompt = build_user_prompt(result, "ar")
    assert "Arabic" in prompt
    assert "22" in prompt  # the latest consumption must reach the model
    assert "water" in prompt


def test_prompt_defaults_to_english_for_unknown_lang():
    assert "English" in build_user_prompt(_result(), "fr")


def test_disabled_without_api_key(monkeypatch):
    monkeypatch.delenv("BASEERAH_ANTHROPIC_API_KEY", raising=False)
    from app.config import get_settings

    get_settings.cache_clear()
    assert explanations_enabled() is False
    assert explain(_result(), "en") is None
    get_settings.cache_clear()
