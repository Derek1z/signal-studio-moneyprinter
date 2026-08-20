from __future__ import annotations

import json
import logging
import re
from typing import Any

from studio.ai_providers import BaseLLMProvider, DemoLLMProvider

logger = logging.getLogger(__name__)


def clean_topic_for_hook(topic: str, niche: str = "") -> str:
    """Clean full YouTube video titles into concise grammatical subject phrases."""
    text = topic.strip()
    # Remove parentheticals like (the brutal results), (here's what happened)
    text = re.sub(r"\([^)]*\)", "", text).strip()
    text = re.sub(r"\[[^\]]*\]", "", text).strip()

    # Strip common title prefixes
    prefixes = [
        r"^i tested \d+ ",
        r"^i spent \d+ (?:days|hours|months) (?:testing|doing|using) ",
        r"^i tried ",
        r"^why most ",
        r"^why ",
        r"^how i (?:fixed|automated|built|grew|made) ",
        r"^the \d+-minute ",
        r"^how to (?:master|fix|do|learn|scale) ",
        r"^stop doing ",
    ]
    for p in prefixes:
        text = re.sub(p, "", text, flags=re.IGNORECASE).strip()

    # Strip trailing clauses
    text = re.sub(r"\s+that (?:gives|saves|works|scales|fails).*$", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"\s+for \d+ (?:days|months|weeks).*$", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"^(?:my|the|your)\s+", "", text, flags=re.IGNORECASE).strip()

    if len(text.split()) < 1 or len(text) < 3:
        return (niche.strip() or "this system").lower()

    return text.strip().lower()


def generate_hook_variations(
    topic: str,
    niche: str = "",
    audience: str = "",
    llm_provider: BaseLLMProvider | None = None,
) -> list[dict[str, Any]]:
    """Generate 5 tailored psychological hook variations with natural, grammatically correct phrasing."""
    clean_subj = clean_topic_for_hook(topic, niche)
    provider = llm_provider or DemoLLMProvider()

    try:
        hooks = provider.generate_hooks(topic=topic, niche=niche, clean_subj=clean_subj)
        if hooks and isinstance(hooks, list) and len(hooks) >= 3:
            return hooks[:5]
    except Exception as e:
        logger.info(f"Hook generation provider fallback: {e}")

    return DemoLLMProvider().generate_hooks(topic, niche, clean_subj)


def replace_script_hook(script: str, new_hook: str) -> str:
    """Replace the first sentence or hook paragraph of the script with the new hook cleanly."""
    clean_script = script.strip()
    if not clean_script:
        return new_hook

    # If script starts with a quote, find end of first line or sentence
    lines = clean_script.split("\n\n", 1)
    if len(lines) > 1:
        return f"{new_hook.strip()}\n\n{lines[1].strip()}"

    sentences = re.split(r"(?<=[.!?])\s+", clean_script, maxsplit=1)
    if len(sentences) > 1:
        return f"{new_hook.strip()}\n\n{sentences[1].strip()}"
    return f"{new_hook.strip()}\n\n{clean_script}"
