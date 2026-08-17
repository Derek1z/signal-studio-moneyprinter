from __future__ import annotations

import json
import logging
import re
from typing import Any

from studio.ai_providers import BaseLLMProvider, DemoLLMProvider

logger = logging.getLogger(__name__)

HOOK_ARCHETYPES = [
    {
        "archetype": "Negative Constraint",
        "tag": "STOP DOING THIS",
        "template": "Stop doing {topic} until you fix this one invisible bottleneck.",
        "hold_rate": 92,
        "curiosity": 9,
        "clarity": 10,
        "rationale": "Loss aversion triggers instant attention within the first 1.5 seconds.",
    },
    {
        "archetype": "Curiosity Gap",
        "tag": "THE HIDDEN RULE",
        "template": "There's a reason why the top 1% never approach {topic} the way tutorials teach.",
        "hold_rate": 89,
        "curiosity": 10,
        "clarity": 8,
        "rationale": "Creates an open loop that compels viewers to watch until the revelation.",
    },
    {
        "archetype": "Bold Confession",
        "tag": "EXPERIMENT PROOF",
        "template": "I spent 30 days testing {topic} so you don't waste 100 hours making my mistakes.",
        "hold_rate": 88,
        "curiosity": 8,
        "clarity": 10,
        "rationale": "Establishes immediate personal authority and authentic proof.",
    },
    {
        "archetype": "High Contrast",
        "tag": "AMATEUR VS PRO",
        "template": "Average creators spend 8 hours on {topic}. Top creators do it in 45 minutes.",
        "hold_rate": 94,
        "curiosity": 9,
        "clarity": 9,
        "rationale": "Numbers-driven contrast creates an irresistible transformation promise.",
    },
    {
        "archetype": "Urgency Trigger",
        "tag": "PATTERN INTERRUPT",
        "template": "If you're still relying on old {niche} advice in 2026, pause and watch this.",
        "hold_rate": 86,
        "curiosity": 8,
        "clarity": 9,
        "rationale": "Time-sensitive pattern interrupt triggers Fear Of Missing Out (FOMO).",
    },
]


def generate_hook_variations(
    topic: str,
    niche: str = "",
    audience: str = "",
    llm_provider: BaseLLMProvider | None = None,
) -> list[dict[str, Any]]:
    """Generate 5 psychological hook variations with retention predictions."""
    subject = topic.strip() or "AI video creation"
    niche_clean = niche.strip() or "content creation"

    # If live LLM is configured, ask for dynamic tailored hooks
    if llm_provider and llm_provider.configured and not isinstance(llm_provider, DemoLLMProvider):
        try:
            prompt = f"""Generate 5 psychological YouTube video opening hooks for:
Topic: {subject}
Niche: {niche_clean}
Audience: {audience}

Return a valid JSON array of 5 objects with these exact keys:
[
  {{
    "archetype": "Negative Constraint",
    "tag": "STOP DOING THIS",
    "hook": "Spoken hook sentence (under 16 words)",
    "hold_rate": 92,
    "curiosity": 9,
    "clarity": 10,
    "rationale": "Psychological reason why viewers stay"
  }},
  ...
]
Archetypes to include: Negative Constraint, Curiosity Gap, Bold Confession, High Contrast, Urgency Trigger.
Return ONLY raw JSON."""
            # Use private call if available
            raw = llm_provider._call(prompt, "You are a master of YouTube 3-second retention hooks.")  # type: ignore
            # Strip fences
            clean = re.sub(r"```(?:json)?\s*([\s\S]*?)\s*```", r"\1", raw).strip()
            data = json.loads(clean)
            if isinstance(data, list) and len(data) >= 3:
                return data[:5]
        except Exception as e:
            logger.warning(f"Live hook generation fallback: {e}")

    # Fallback to high-converting archetypes
    results = []
    for item in HOOK_ARCHETYPES:
        hook_text = item["template"].format(topic=subject.lower(), niche=niche_clean.lower())
        results.append({
            "archetype": item["archetype"],
            "tag": item["tag"],
            "hook": hook_text,
            "hold_rate": item["hold_rate"],
            "curiosity": item["curiosity"],
            "clarity": item["clarity"],
            "rationale": item["rationale"],
        })
    return results


def replace_script_hook(script: str, new_hook: str) -> str:
    """Replace the first sentence or hook paragraph of the script with the new hook."""
    clean_script = script.strip()
    if not clean_script:
        return new_hook

    # Split by first sentence boundary or first paragraph
    sentences = re.split(r"(?<=[.!?])\s+", clean_script, maxsplit=1)
    if len(sentences) > 1:
        return f"{new_hook.strip()}\n\n{sentences[1].strip()}"
    return f"{new_hook.strip()}\n\n{clean_script}"
