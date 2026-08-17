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
    niche_clean = niche.strip().lower() or "content creation"

    # 1. Try Live LLM when available and configured
    if llm_provider and llm_provider.configured and not isinstance(llm_provider, DemoLLMProvider):
        try:
            prompt = f"""Generate 5 high-converting, psychological YouTube opening hooks specifically for this video topic:
Topic Title: "{topic}"
Core Subject: "{clean_subj}"
Niche: "{niche_clean}"

MANDATE: Every hook must be a single, natural, complete spoken English sentence under 16 words.
Do NOT just paste the raw title inside quotes. Write creative, punchy spoken lines.

Return a JSON array of 5 objects:
[
  {{
    "archetype": "Negative Constraint",
    "tag": "STOP DOING THIS",
    "hook": "Stop approaching {clean_subj} the traditional way until you fix this one bottleneck.",
    "hold_rate": 93,
    "curiosity": 9,
    "clarity": 10,
    "rationale": "Loss aversion triggers instant focus"
  }},
  {{
    "archetype": "Curiosity Gap",
    "tag": "THE HIDDEN RULE",
    "hook": "There is a reason the top 1% never handle {clean_subj} like standard tutorials teach.",
    "hold_rate": 91,
    "curiosity": 10,
    "clarity": 9,
    "rationale": "Creates open loop"
  }},
  {{
    "archetype": "Bold Confession",
    "tag": "EXPERIMENT PROOF",
    "hook": "I tracked 30 days of real {clean_subj} experiments so you don't waste 100 hours.",
    "hold_rate": 89,
    "curiosity": 8,
    "clarity": 10,
    "rationale": "Authentic personal proof"
  }},
  {{
    "archetype": "High Contrast",
    "tag": "AMATEUR VS PRO",
    "hook": "Amateurs spend 8 hours on {clean_subj}. Top creators finish in 45 minutes with this rule.",
    "hold_rate": 95,
    "curiosity": 9,
    "clarity": 9,
    "rationale": "Extreme numbers contrast"
  }},
  {{
    "archetype": "Urgency Trigger",
    "tag": "PATTERN INTERRUPT",
    "hook": "If you are still relying on outdated {niche_clean} advice in 2026, pause and watch this.",
    "hold_rate": 88,
    "curiosity": 8,
    "clarity": 9,
    "rationale": "FOMO trigger"
  }}
]
Return ONLY raw JSON."""
            raw = llm_provider._call(prompt, "You are a master YouTube retention scientist and viral copywriter.")  # type: ignore
            clean = re.sub(r"```(?:json)?\s*([\s\S]*?)\s*```", r"\1", raw).strip()
            data = json.loads(clean)
            if isinstance(data, dict) and "hooks" in data:
                data = data["hooks"]
            if isinstance(data, list) and len(data) >= 3:
                return data[:5]
        except Exception as e:
            logger.info(f"Live hook generation fallback: {e}")

    # 2. Intelligent, Grammatically Perfect Contextual Fallbacks
    return [
        {
            "archetype": "Negative Constraint",
            "tag": "STOP DOING THIS",
            "hook": f"Stop approaching {clean_subj} the traditional way until you fix this one bottleneck.",
            "hold_rate": 93,
            "curiosity": 9,
            "clarity": 10,
            "rationale": "Loss aversion triggers instant attention within the first 1.5 seconds.",
        },
        {
            "archetype": "Curiosity Gap",
            "tag": "THE HIDDEN RULE",
            "hook": f"There's a reason why the top 1% never handle {clean_subj} the way tutorials teach.",
            "hold_rate": 91,
            "curiosity": 10,
            "clarity": 9,
            "rationale": "Creates an open loop that compels viewers to watch until the revelation.",
        },
        {
            "archetype": "Bold Confession",
            "tag": "EXPERIMENT PROOF",
            "hook": f"I spent 30 days testing real {clean_subj} workflows so you don't waste 100 hours.",
            "hold_rate": 89,
            "curiosity": 8,
            "clarity": 10,
            "rationale": "Establishes immediate personal authority and authentic proof.",
        },
        {
            "archetype": "High Contrast",
            "tag": "AMATEUR VS PRO",
            "hook": f"Amateurs spend 8 hours on {clean_subj}. Top creators do it in 45 minutes with this rule.",
            "hold_rate": 95,
            "curiosity": 9,
            "clarity": 9,
            "rationale": "Numbers-driven contrast creates an irresistible transformation promise.",
        },
        {
            "archetype": "Urgency Trigger",
            "tag": "PATTERN INTERRUPT",
            "hook": f"If you're still relying on outdated {niche_clean} advice in 2026, pause and watch this.",
            "hold_rate": 88,
            "curiosity": 8,
            "clarity": 9,
            "rationale": "Time-sensitive pattern interrupt triggers Fear Of Missing Out (FOMO).",
        },
    ]


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
