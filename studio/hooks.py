from __future__ import annotations

import json
import logging
import re
from typing import Any

from studio.ai_providers import BaseLLMProvider, DemoLLMProvider

logger = logging.getLogger(__name__)


def generate_hook_variations(
    topic: str,
    niche: str = "",
    audience: str = "",
    llm_provider: BaseLLMProvider | None = None,
) -> list[dict[str, Any]]:
    """Generate 5 tailored psychological hook variations for the exact topic/niche."""
    subject = topic.strip() or "AI video creation"
    niche_clean = niche.strip() or "content creation"

    # Use live LLM when available
    if llm_provider and llm_provider.configured and not isinstance(llm_provider, DemoLLMProvider):
        try:
            prompt = f"""Generate 5 high-converting, psychological YouTube opening hooks specifically for this video topic:
Topic: "{subject}"
Niche: {niche_clean}
Audience: {audience or 'YouTube viewers looking for actionable insights'}

Return a valid JSON array of 5 objects with these exact keys:
[
  {{
    "archetype": "Negative Constraint",
    "tag": "STOP DOING THIS",
    "hook": "Spoken hook sentence under 16 words",
    "hold_rate": 93,
    "curiosity": 9,
    "clarity": 10,
    "rationale": "Why this creates immediate loss aversion"
  }},
  {{
    "archetype": "Curiosity Gap",
    "tag": "THE HIDDEN RULE",
    "hook": "Spoken hook sentence under 16 words",
    "hold_rate": 91,
    "curiosity": 10,
    "clarity": 9,
    "rationale": "Why this compels viewers to stay"
  }},
  {{
    "archetype": "Bold Confession",
    "tag": "EXPERIMENT PROOF",
    "hook": "Spoken hook sentence under 16 words",
    "hold_rate": 89,
    "curiosity": 8,
    "clarity": 10,
    "rationale": "Immediate personal authority"
  }},
  {{
    "archetype": "High Contrast",
    "tag": "AMATEUR VS PRO",
    "hook": "Spoken hook sentence under 16 words",
    "hold_rate": 95,
    "curiosity": 9,
    "clarity": 9,
    "rationale": "Extreme numbers-driven transformation"
  }},
  {{
    "archetype": "Urgency Trigger",
    "tag": "PATTERN INTERRUPT",
    "hook": "Spoken hook sentence under 16 words",
    "hold_rate": 88,
    "curiosity": 8,
    "clarity": 9,
    "rationale": "Pattern interrupt"
  }}
]
Return ONLY raw JSON, no markdown."""
            raw = llm_provider._call(prompt, "You are a master YouTube retention scientist and viral hook copywriter.")  # type: ignore
            clean = re.sub(r"```(?:json)?\s*([\s\S]*?)\s*```", r"\1", raw).strip()
            data = json.loads(clean)
            if isinstance(data, list) and len(data) >= 3:
                return data[:5]
        except Exception as e:
            logger.warning(f"Live hook generation failed: {e}")

    # Fallback to dynamic template interpolation
    return [
        {
            "archetype": "Negative Constraint",
            "tag": "STOP DOING THIS",
            "hook": f"Stop doing {subject.lower()} until you fix this one invisible bottleneck.",
            "hold_rate": 93,
            "curiosity": 9,
            "clarity": 10,
            "rationale": "Loss aversion triggers instant attention within the first 1.5 seconds.",
        },
        {
            "archetype": "Curiosity Gap",
            "tag": "THE HIDDEN RULE",
            "hook": f"There's a reason why the top 1% never approach {subject.lower()} the way tutorials teach.",
            "hold_rate": 91,
            "curiosity": 10,
            "clarity": 9,
            "rationale": "Creates an open loop that compels viewers to watch until the revelation.",
        },
        {
            "archetype": "Bold Confession",
            "tag": "EXPERIMENT PROOF",
            "hook": f"I spent 30 days testing {subject.lower()} so you don't waste 100 hours making my mistakes.",
            "hold_rate": 89,
            "curiosity": 8,
            "clarity": 10,
            "rationale": "Establishes immediate personal authority and authentic proof.",
        },
        {
            "archetype": "High Contrast",
            "tag": "AMATEUR VS PRO",
            "hook": f"Average creators spend 8 hours on {niche_clean.lower()}. Top creators do it in 45 minutes.",
            "hold_rate": 95,
            "curiosity": 9,
            "clarity": 9,
            "rationale": "Numbers-driven contrast creates an irresistible transformation promise.",
        },
        {
            "archetype": "Urgency Trigger",
            "tag": "PATTERN INTERRUPT",
            "hook": f"If you're still relying on old {niche_clean.lower()} advice in 2026, pause and watch this.",
            "hold_rate": 88,
            "curiosity": 8,
            "clarity": 9,
            "rationale": "Time-sensitive pattern interrupt triggers Fear Of Missing Out (FOMO).",
        },
    ]


def replace_script_hook(script: str, new_hook: str) -> str:
    """Replace the first sentence or hook paragraph of the script with the new hook."""
    clean_script = script.strip()
    if not clean_script:
        return new_hook

    sentences = re.split(r"(?<=[.!?])\s+", clean_script, maxsplit=1)
    if len(sentences) > 1:
        return f"{new_hook.strip()}\n\n{sentences[1].strip()}"
    return f"{new_hook.strip()}\n\n{clean_script}"
