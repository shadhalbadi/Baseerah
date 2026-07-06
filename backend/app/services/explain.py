"""LLM explanation layer.

Turns a deterministic `AnalysisResult` into a short, plain-language, bilingual
explanation. The model only *phrases* the numbers produced by the analysis
engine — it is explicitly instructed not to invent figures — so recommendations
stay auditable. When no API key is configured the layer is disabled and the app
works exactly as before.
"""

import json

from app.config import get_settings
from app.schemas.analysis import AnalysisResult

_LANG_NAMES = {"en": "English", "ar": "Arabic"}

SYSTEM_PROMPT = (
    "You are Baseerah, a utility-bill advisor for households in Oman. "
    "You are given a JSON analysis of one property's water or electricity usage that was "
    "computed deterministically by the application. Write a short, friendly explanation "
    "(2-4 sentences) that helps the user understand what is going on and what to do next.\n"
    "STRICT RULES:\n"
    "- Only use the numbers present in the JSON. Never invent or estimate figures, costs, or percentages.\n"
    "- Refer to money in the currency given in the JSON.\n"
    "- If a leak is suspected, mention the verification step.\n"
    "- Be concrete and encouraging, not alarming. No preamble, no markdown, no bullet points — just prose."
)


def build_user_prompt(result: AnalysisResult, lang: str) -> str:
    lang_name = _LANG_NAMES.get(lang, "English")
    payload = result.model_dump(mode="json")
    return (
        f"Write the explanation in {lang_name}.\n\n"
        f"Analysis JSON:\n{json.dumps(payload, ensure_ascii=False)}"
    )


def explanations_enabled() -> bool:
    return bool(get_settings().anthropic_api_key)


def explain(result: AnalysisResult, lang: str = "en") -> str | None:
    """Return a natural-language explanation, or None if the layer is disabled/unavailable."""
    settings = get_settings()
    if not settings.anthropic_api_key:
        return None

    # Imported lazily so the dependency is only needed when the feature is enabled.
    import anthropic

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    try:
        message = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=512,
            system=SYSTEM_PROMPT,
            output_config={"effort": "low"},
            messages=[{"role": "user", "content": build_user_prompt(result, lang)}],
        )
    except anthropic.AnthropicError:
        return None

    return "".join(block.text for block in message.content if block.type == "text").strip() or None
