from __future__ import annotations

import json
import logging
import re
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from typing import Any

from studio.retention import get_tone_prompt_guidance

logger = logging.getLogger(__name__)

# Preferred Gemini models in fallback order
GEMINI_MODELS = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-2.0-flash", "gemini-3.6-flash", "gemini-flash-latest"]


def _clean_json_text(text: str) -> str:
    """Strip markdown code fences and extraneous text from JSON LLM responses."""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        return match.group(1).strip()
    start_bracket = min((text.find("[") if "[" in text else 999999), (text.find("{") if "{" in text else 999999))
    if start_bracket < 999999:
        end_bracket = max(text.rfind("]"), text.rfind("}"))
        if end_bracket > start_bracket:
            return text[start_bracket : end_bracket + 1].strip()
    return text


class BaseLLMProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @property
    @abstractmethod
    def configured(self) -> bool:
        pass

    @abstractmethod
    def generate_topics(self, niche: str, audience: str, goal: str) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    def run_council(
        self,
        topic: str,
        niche: str,
        audience: str,
        competitors: list[dict[str, Any]] | None = None,
        citations: list[dict[str, Any]] | None = None,
    ) -> tuple[list[dict[str, str]], int, str]:
        pass

    @abstractmethod
    def generate_script(
        self,
        topic: str,
        angle: str,
        thesis: str,
        hook: str,
        niche: str,
        audience: str,
        duration_sec: int = 60,
        tone_preset: str = "balanced",
        competitors: list[dict[str, Any]] | None = None,
        citations: list[dict[str, Any]] | None = None,
    ) -> str:
        pass

    @abstractmethod
    def generate_packaging(self, topic: str, script: str) -> dict[str, Any]:
        pass

    @abstractmethod
    def generate_hooks(self, topic: str, niche: str = "", clean_subj: str = "") -> list[dict[str, Any]]:
        pass


class DemoLLMProvider(BaseLLMProvider):
    """Deterministic, high-quality fallback generator that requires no API keys."""

    @property
    def provider_name(self) -> str:
        return "Demo (Zero API Keys)"

    @property
    def configured(self) -> bool:
        return True

    def generate_topics(self, niche: str, audience: str, goal: str) -> list[dict[str, Any]]:
        subject = niche.strip() or "Productivity"
        audience_hint = audience.strip() or "creators"
        templates = [
            (f"I tested 5 {subject} habits for 30 days (The brutal results)", 95, "Real experiment format with measured proof"),
            (f"Why most {subject} advice fails after 1 week (And what actually works)", 92, "Contrarian tension and high audience pull"),
            (f"The 7-minute {subject} routine that saves 10 hours a week", 94, "High intent and clear transformation promise"),
        ]
        return [
            {"topic": title, "score": score, "signal": signal, "audience": audience_hint}
            for title, score, signal in templates
        ]

    def run_council(
        self,
        topic: str,
        niche: str,
        audience: str,
        competitors: list[dict[str, Any]] | None = None,
        citations: list[dict[str, Any]] | None = None,
    ) -> tuple[list[dict[str, str]], int, str]:
        proposals = [
            {
                "advisor": "Story Architect",
                "angle": "The 30-Day Lived Experiment",
                "hook": f"I spent 30 days testing {topic.lower()} so you don't waste 100 hours making my mistakes.",
                "thesis": f"Transform {topic} into a real-world case study with measured benchmarks and authentic friction points.",
            },
            {
                "advisor": "Audience Advocate",
                "angle": "The High-Contrast Shortcut",
                "hook": f"Average creators spend 8 hours on {niche or 'this'}. Top creators do it in 45 minutes with this exact rule.",
                "thesis": f"Focus purely on time-saving constraints for {audience or 'creators'}, delivering an actionable 3-step system.",
            },
            {
                "advisor": "Skeptical Editor",
                "angle": "The Contrarian Audit",
                "hook": f"Stop doing {topic.lower()} until you fix this one invisible bottleneck.",
                "thesis": "Deconstruct why generic tutorials fail in production and reveal the single operational constraint that matters.",
            },
        ]
        return proposals, 1, "Audience Advocate selected: Delivers maximum retention velocity and differentiated audience value."

    def generate_script(
        self,
        topic: str,
        angle: str,
        thesis: str,
        hook: str,
        niche: str,
        audience: str,
        duration_sec: int = 60,
        tone_preset: str = "balanced",
        competitors: list[dict[str, Any]] | None = None,
        citations: list[dict[str, Any]] | None = None,
    ) -> str:
        preset_clean = tone_preset.lower()
        if "hormozi" in preset_clean:
            return f"""{hook}

Here is the brutal truth about {topic.lower()}: 90% of people fail because they automate the output instead of fixing the bottleneck.

I spent months testing 20 different approaches. They didn't make me faster—they just produced faster junk.

Then I set one non-negotiable rule:
Rule 1: Never start without a verified audience constraint.
Rule 2: Pitch 3 competing angles, then pick the one with zero fluff.
Rule 3: Check every single claim before executing.

The result? Production time dropped from 8 hours to 45 minutes.

Speed gives you volume. Human checkpoints give you authority. If you want leverage, focus on the gate, not the button."""

        elif "veritasium" in preset_clean:
            return f"""{hook}

If you search for advice on {topic.lower()}, you will find thousands of tutorials offering identical instructions. But when you examine how the top performers actually work, you discover a fascinating contradiction.

To test this hypothesis, I conducted an experiment over the course of four weeks.

The first variable was volume versus constraint. Standard intuition suggests that more speed equals more progress. But counter-intuitively, unrestricted generation introduces exponential error rates.

The second variable was verification latency. By placing human review gates at the exact inflection points, total project completion time dropped by nearly seventy percent.

The surprising conclusion is that leverage does not come from removing human judgment. It comes from directing that judgment where automated systems are fundamentally blind."""

        elif "shorts" in preset_clean or "reels" in preset_clean:
            return f"""{hook}

Stop doing {topic.lower()} the hard way. Here is the 3-step cheat code.

Step 1: Set your viewer constraint before touching any tool.
Step 2: Generate 3 competing hooks and test the highest retention angle.
Step 3: Verify every single claim before you hit render.

Amateurs spend 8 hours. Pros do this in 45 minutes. Save this workflow and ship higher quality today."""

        else:
            return f"""{hook}

Most people approach {topic.lower()} by collecting more tools and adding friction to their day. I did too—and it only slowed down real progress.

So I tested a lean approach: one week, one repeatable workflow, and one rule: every step had to leave room for a clear human decision.

Step one: Start with the viewer's exact constraint, not a vague keyword.
Step two: Generate multiple competing angles, then filter aggressively for originality and practical proof.
Step three: Verify every claim and citation before any production button is pressed.

The surprising takeaway? The speed didn't come from removing human judgment—it came from having clear checkpoints where low-quality ideas get rejected immediately.

If you try this, start with a single experiment. Add something only you can contribute: an authentic test, a failure, or a measured comparison.

AI widens your options. Human judgment narrows them. That's the system that scales."""

    def generate_packaging(self, topic: str, script: str) -> dict[str, Any]:
        return {
            "titles": [
                f"The {topic} System I Actually Kept",
                f"Stop Doing {topic} The Hard Way",
                f"How I Fixed My {topic} Workflow in 7 Days",
            ],
            "thumbnail_text": "AUTOMATE LESS. SHIP BETTER.",
            "thumbnail_visual": "Split screen comparison: messy complex flowchart vs. clean 3-step checklist with bold green checkmark.",
            "broll_tags": ["creator desk", "focused typing", "analytics dashboard", "editing timeline", "coffee cup"],
        }

    def generate_hooks(self, topic: str, niche: str = "", clean_subj: str = "") -> list[dict[str, Any]]:
        subj = clean_subj or topic.lower()
        niche_clean = niche.strip().lower() or "content creation"
        return [
            {
                "archetype": "Negative Constraint",
                "tag": "STOP DOING THIS",
                "hook": f"Stop approaching {subj} the traditional way until you fix this one bottleneck.",
                "hold_rate": 93,
                "curiosity": 9,
                "clarity": 10,
                "rationale": "Loss aversion triggers instant attention within the first 1.5 seconds.",
            },
            {
                "archetype": "Curiosity Gap",
                "tag": "THE HIDDEN RULE",
                "hook": f"There's a reason why the top 1% never handle {subj} the way tutorials teach.",
                "hold_rate": 91,
                "curiosity": 10,
                "clarity": 9,
                "rationale": "Creates an open loop that compels viewers to watch until the revelation.",
            },
            {
                "archetype": "Bold Confession",
                "tag": "EXPERIMENT PROOF",
                "hook": f"I spent 30 days testing real {subj} workflows so you don't waste 100 hours.",
                "hold_rate": 89,
                "curiosity": 8,
                "clarity": 10,
                "rationale": "Establishes immediate personal authority and authentic proof.",
            },
            {
                "archetype": "High Contrast",
                "tag": "AMATEUR VS PRO",
                "hook": f"Amateurs spend 8 hours on {subj}. Top creators do it in 45 minutes with this rule.",
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


class GeminiLLMProvider(BaseLLMProvider):
    """Google Gemini API Provider using direct REST requests with multi-model fallback."""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key.strip()
        self.model_name = model_name.strip() or "gemini-2.5-flash"

    @property
    def provider_name(self) -> str:
        return f"Google Gemini ({self.model_name})"

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def _call(self, prompt: str, system_instruction: str = "") -> str:
        if not self.configured:
            raise ValueError("Gemini API key is not configured.")

        # Try active model then fallback models
        models_to_try = [self.model_name] + [m for m in GEMINI_MODELS if m != self.model_name]
        last_err = None

        for m_name in models_to_try:
            url = f"{self.BASE_URL}/{m_name}:generateContent?key={self.api_key}"
            body: dict[str, Any] = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.75, "maxOutputTokens": 2048},
            }
            if system_instruction:
                body["systemInstruction"] = {"parts": [{"text": system_instruction}]}

            req = urllib.request.Request(
                url,
                data=json.dumps(body).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=25) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        return "".join(part.get("text", "") for part in parts).strip()
            except urllib.error.HTTPError as err:
                err_msg = err.read().decode("utf-8", errors="replace")
                logger.warning(f"Gemini API model {m_name} failed ({err.code}): {err_msg[:100]}")
                last_err = err_msg
            except Exception as e:
                logger.warning(f"Gemini request on {m_name} failed: {e}")
                last_err = str(e)

        raise RuntimeError(f"All Gemini models failed. Last error: {last_err}")

    def generate_topics(self, niche: str, audience: str, goal: str) -> list[dict[str, Any]]:
        prompt = f"""Generate 3 high-converting, viral YouTube video topic ideas for:
Niche: {niche}
Target Audience: {audience or 'viewers looking for actionable value'}
Goal: {goal or 'high retention, viral reach, and high CTR'}

Guidelines:
- Zero generic listicles. Focus on high-stakes experiments, counter-intuitive methods, and extreme contrast.
- Each title must be punchy, curiosity-inducing, and specific.

Return ONLY a valid JSON array of 3 objects with these exact keys:
[
  {{"topic": "Punchy YouTube Video Title", "score": 95, "signal": "Specific reason why this has viral retention potential", "audience": "{audience or niche}"}},
  ...
]
Return ONLY raw JSON, no markdown."""
        try:
            raw = self._call(prompt, "You are a master YouTube content strategist and viral packaging expert.")
            parsed = json.loads(_clean_json_text(raw))
            if isinstance(parsed, list) and len(parsed) >= 3:
                return parsed[:3]
        except Exception as e:
            logger.warning(f"Gemini generate_topics fallback: {e}")
        return DemoLLMProvider().generate_topics(niche, audience, goal)

    def run_council(
        self,
        topic: str,
        niche: str,
        audience: str,
        competitors: list[dict[str, Any]] | None = None,
        citations: list[dict[str, Any]] | None = None,
    ) -> tuple[list[dict[str, str]], int, str]:
        comp_text = ""
        if competitors:
            comp_text = "\nRanking YouTube Competitor Videos:\n" + "\n".join(
                [f"- \"{c.get('title')}\" ({c.get('channel')} · {c.get('views')})" for c in competitors[:3]]
            )

        prompt = f"""Topic: {topic}
Niche: {niche}
Audience: {audience}
{comp_text}

Form a 3-advisor editorial council with these personas:
1. Story Architect (Focus: emotional transformation, narrative arc, personal experiment)
2. Audience Advocate (Focus: immediate utility, friction reduction, 3-step actionable frameworks)
3. Skeptical Editor (Focus: myth busting, contrarian truth, boundary conditions)

MANDATE: Propose angles that directly outperform and differentiate from the ranking competitor videos above. Avoid generic corporate fluff.

Return ONLY a JSON object with this exact schema:
{{
  "proposals": [
    {{"advisor": "Story Architect", "angle": "Short punchy angle title", "hook": "First 5-second spoken hook line", "thesis": "Core editorial premise"}},
    {{"advisor": "Audience Advocate", "angle": "Short punchy angle title", "hook": "First 5-second spoken hook line", "thesis": "Core editorial premise"}},
    {{"advisor": "Skeptical Editor", "angle": "Short punchy angle title", "hook": "First 5-second spoken hook line", "thesis": "Core editorial premise"}}
  ],
  "winner": 0,
  "judge_reasoning": "Explanation for why the winner was chosen"
}}"""
        try:
            raw = self._call(prompt, "You are an executive YouTube editorial council focused on original high-retention storytelling.")
            parsed = json.loads(_clean_json_text(raw))
            if "proposals" in parsed and isinstance(parsed["proposals"], list):
                return parsed["proposals"], int(parsed.get("winner", 0)), str(parsed.get("judge_reasoning", ""))
        except Exception as e:
            logger.warning(f"Gemini run_council fallback: {e}")
        return DemoLLMProvider().run_council(topic, niche, audience, competitors, citations)

    def generate_script(
        self,
        topic: str,
        angle: str,
        thesis: str,
        hook: str,
        niche: str,
        audience: str,
        duration_sec: int = 60,
        tone_preset: str = "balanced",
        competitors: list[dict[str, Any]] | None = None,
        citations: list[dict[str, Any]] | None = None,
    ) -> str:
        target_words = int((duration_sec / 60) * 140)
        tone_guidance = get_tone_prompt_guidance(tone_preset)

        prompt = f"""Write a high-retention YouTube video narration script.
Topic: {topic}
Selected Angle: {angle}
Thesis: {thesis}
Mandatory Hook Line (first sentence): "{hook}"
Target Audience: {audience}
Target Length: Approx {target_words} words (around {duration_sec} seconds spoken).

Tone Guidance:
{tone_guidance}

Guidelines:
- Spoken, conversational, punchy human tone (avoid cliché AI corporate jargon like 'game changer', 'unleash', 'dive in').
- 3 clear actionable points or moments.
- Must include a call for human judgment / personal proof.
- Return ONLY the narration text (no stage directions, no [music], no timestamps)."""
        try:
            script = self._call(prompt, "You are an award-winning YouTube scriptwriter.")
            if script and len(script.split()) > 40:
                return script
        except Exception as e:
            logger.warning(f"Gemini generate_script fallback: {e}")
        return DemoLLMProvider().generate_script(topic, angle, thesis, hook, niche, audience, duration_sec, tone_preset, competitors, citations)

    def generate_packaging(self, topic: str, script: str) -> dict[str, Any]:
        prompt = f"""For this YouTube topic and script, produce packaging concepts:
Topic: {topic}
Script excerpt: {script[:400]}

Return ONLY a JSON object:
{{
  "titles": [
    "High CTR Title 1",
    "High CTR Title 2",
    "High CTR Title 3"
  ],
  "thumbnail_text": "3-5 WORD PUNCHY ALL-CAPS TEXT",
  "thumbnail_visual": "Visual layout and subject description for the thumbnail artist",
  "broll_tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}}"""
        try:
            raw = self._call(prompt, "You are a master YouTube packaging and thumbnail designer.")
            parsed = json.loads(_clean_json_text(raw))
            if "titles" in parsed and "thumbnail_text" in parsed:
                return parsed
        except Exception as e:
            logger.warning(f"Gemini packaging fallback: {e}")
        return DemoLLMProvider().generate_packaging(topic, script)

    def generate_hooks(self, topic: str, niche: str = "", clean_subj: str = "") -> list[dict[str, Any]]:
        clean_s = clean_subj or topic.lower()
        niche_clean = niche.strip().lower() or "content creation"
        prompt = f"""Generate 5 high-converting, psychological YouTube opening hooks specifically for this video topic:
Topic Title: "{topic}"
Core Subject: "{clean_s}"
Niche: "{niche_clean}"

MANDATE: Every hook must be a single, natural, complete spoken English sentence under 16 words.
Do NOT just paste the raw title inside quotes. Write creative, punchy spoken lines.

Return ONLY a valid JSON array of 5 objects:
[
  {{
    "archetype": "Negative Constraint",
    "tag": "STOP DOING THIS",
    "hook": "Stop approaching {clean_s} the traditional way until you fix this one bottleneck.",
    "hold_rate": 93,
    "curiosity": 9,
    "clarity": 10,
    "rationale": "Loss aversion triggers instant focus"
  }},
  {{
    "archetype": "Curiosity Gap",
    "tag": "THE HIDDEN RULE",
    "hook": "There is a reason the top 1% never handle {clean_s} like standard tutorials teach.",
    "hold_rate": 91,
    "curiosity": 10,
    "clarity": 9,
    "rationale": "Creates open loop"
  }},
  {{
    "archetype": "Bold Confession",
    "tag": "EXPERIMENT PROOF",
    "hook": "I tracked 30 days of real {clean_s} experiments so you don't waste 100 hours.",
    "hold_rate": 89,
    "curiosity": 8,
    "clarity": 10,
    "rationale": "Authentic personal proof"
  }},
  {{
    "archetype": "High Contrast",
    "tag": "AMATEUR VS PRO",
    "hook": "Amateurs spend 8 hours on {clean_s}. Top creators finish in 45 minutes with this rule.",
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
]"""
        try:
            raw = self._call(prompt, "You are a master YouTube retention scientist and viral copywriter.")
            clean = _clean_json_text(raw)
            data = json.loads(clean)
            if isinstance(data, dict) and "hooks" in data:
                data = data["hooks"]
            if isinstance(data, list) and len(data) >= 3:
                return data[:5]
        except Exception as e:
            logger.warning(f"Gemini generate_hooks fallback: {e}")
        return DemoLLMProvider().generate_hooks(topic, niche, clean_subj)


class OpenAILLMProvider(BaseLLMProvider):
    """OpenAI API Provider supporting GPT-4o, GPT-4o-mini, and local Ollama/OpenRouter endpoints."""

    def __init__(
        self,
        api_key: str = "",
        model_name: str = "gpt-4o-mini",
        base_url: str = "https://api.openai.com/v1",
    ):
        self.api_key = api_key.strip()
        self.model_name = model_name.strip() or "gpt-4o-mini"
        self.base_url = (base_url.strip() or "https://api.openai.com/v1").rstrip("/")

    @property
    def provider_name(self) -> str:
        return f"OpenAI ({self.model_name})"

    @property
    def configured(self) -> bool:
        return bool(self.api_key or "localhost" in self.base_url or "127.0.0.1" in self.base_url)

    def _call(self, prompt: str, system_instruction: str = "") -> str:
        url = f"{self.base_url}/chat/completions"
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        body = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.7,
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=35) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                choices = data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "").strip()
                return ""
        except Exception as e:
            logger.error(f"OpenAI call failed: {e}")
            raise

    def generate_topics(self, niche: str, audience: str, goal: str) -> list[dict[str, Any]]:
        prompt = f"""Generate 3 high-potential YouTube video topic ideas for:
Niche: {niche}
Target Audience: {audience}
Goal: {goal}

Return ONLY raw JSON array of 3 objects with keys 'topic', 'score', 'signal', 'audience'."""
        try:
            raw = self._call(prompt, "You are a world-class YouTube content strategist.")
            parsed = json.loads(_clean_json_text(raw))
            if isinstance(parsed, list) and len(parsed) >= 3:
                return parsed[:3]
        except Exception as e:
            logger.warning(f"OpenAI generate_topics fallback: {e}")
        return DemoLLMProvider().generate_topics(niche, audience, goal)

    def run_council(
        self,
        topic: str,
        niche: str,
        audience: str,
        competitors: list[dict[str, Any]] | None = None,
        citations: list[dict[str, Any]] | None = None,
    ) -> tuple[list[dict[str, str]], int, str]:
        comp_text = ""
        if competitors:
            comp_text = "\nRanking Competitor Videos:\n" + "\n".join(
                [f"- \"{c.get('title')}\" ({c.get('channel')} · {c.get('views')})" for c in competitors[:3]]
            )

        prompt = f"""Topic: {topic}
Niche: {niche}
Audience: {audience}
{comp_text}

Form a 3-advisor editorial council with these personas:
1. Story Architect (Focus: emotional transformation, narrative arc, personal experiment)
2. Audience Advocate (Focus: immediate utility, friction reduction, 3-step actionable frameworks)
3. Skeptical Editor (Focus: myth busting, contrarian truth, boundary conditions)

Return ONLY a JSON object with this exact schema:
{{
  "proposals": [
    {{"advisor": "Story Architect", "angle": "Short punchy angle title", "hook": "First 5-second spoken hook line", "thesis": "Core editorial premise"}},
    {{"advisor": "Audience Advocate", "angle": "Short punchy angle title", "hook": "First 5-second spoken hook line", "thesis": "Core editorial premise"}},
    {{"advisor": "Skeptical Editor", "angle": "Short punchy angle title", "hook": "First 5-second spoken hook line", "thesis": "Core editorial premise"}}
  ],
  "winner": 0,
  "judge_reasoning": "Explanation for why the winner was chosen"
}}"""
        try:
            raw = self._call(prompt, "You are an executive YouTube editorial council.")
            parsed = json.loads(_clean_json_text(raw))
            if "proposals" in parsed and isinstance(parsed["proposals"], list):
                return parsed["proposals"], int(parsed.get("winner", 0)), str(parsed.get("judge_reasoning", ""))
        except Exception as e:
            logger.warning(f"OpenAI run_council fallback: {e}")
        return DemoLLMProvider().run_council(topic, niche, audience, competitors, citations)

    def generate_script(
        self,
        topic: str,
        angle: str,
        thesis: str,
        hook: str,
        niche: str,
        audience: str,
        duration_sec: int = 60,
        tone_preset: str = "balanced",
        competitors: list[dict[str, Any]] | None = None,
        citations: list[dict[str, Any]] | None = None,
    ) -> str:
        target_words = int((duration_sec / 60) * 140)
        tone_guidance = get_tone_prompt_guidance(tone_preset)
        prompt = f"""Write a high-retention YouTube video narration script.
Topic: {topic}
Selected Angle: {angle}
Thesis: {thesis}
Mandatory Hook Line (first sentence): "{hook}"
Target Audience: {audience}
Target Length: Approx {target_words} words (around {duration_sec} seconds spoken).

Tone Guidance:
{tone_guidance}

Return ONLY the narration text (no stage directions, no [music], no timestamps)."""
        try:
            script = self._call(prompt, "You are an award-winning YouTube scriptwriter.")
            if script and len(script.split()) > 30:
                return script
        except Exception as e:
            logger.warning(f"OpenAI generate_script fallback: {e}")
        return DemoLLMProvider().generate_script(topic, angle, thesis, hook, niche, audience, duration_sec, tone_preset, competitors, citations)

    def generate_packaging(self, topic: str, script: str) -> dict[str, Any]:
        prompt = f"""For this YouTube topic and script, produce packaging concepts:
Topic: {topic}
Script excerpt: {script[:400]}

Return ONLY a JSON object:
{{
  "titles": [
    "High CTR Title 1",
    "High CTR Title 2",
    "High CTR Title 3"
  ],
  "thumbnail_text": "3-5 WORD PUNCHY ALL-CAPS TEXT",
  "thumbnail_visual": "Visual layout and subject description for thumbnail artist",
  "broll_tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}}"""
        try:
            raw = self._call(prompt, "You are a master YouTube packaging and thumbnail designer.")
            parsed = json.loads(_clean_json_text(raw))
            if "titles" in parsed and "thumbnail_text" in parsed:
                return parsed
        except Exception as e:
            logger.warning(f"OpenAI generate_packaging fallback: {e}")
        return DemoLLMProvider().generate_packaging(topic, script)

    def generate_hooks(self, topic: str, niche: str = "", clean_subj: str = "") -> list[dict[str, Any]]:
        clean_s = clean_subj or topic.lower()
        niche_clean = niche.strip().lower() or "content creation"
        prompt = f"""Generate 5 high-converting, psychological YouTube opening hooks for:
Topic Title: "{topic}"
Subject: "{clean_s}"
Niche: "{niche_clean}"

Return ONLY a valid JSON array of 5 objects with keys: archetype, tag, hook, hold_rate, curiosity, clarity, rationale."""
        try:
            raw = self._call(prompt, "You are a YouTube retention scientist.")
            clean = _clean_json_text(raw)
            data = json.loads(clean)
            if isinstance(data, dict) and "hooks" in data:
                data = data["hooks"]
            if isinstance(data, list) and len(data) >= 3:
                return data[:5]
        except Exception as e:
            logger.warning(f"OpenAI generate_hooks fallback: {e}")
        return DemoLLMProvider().generate_hooks(topic, niche, clean_subj)


def get_llm_provider(
    provider_type: str,
    api_key: str = "",
    model_name: str = "",
    base_url: str = "",
) -> BaseLLMProvider:
    """Factory to instantiate the appropriate LLM provider with fallback to Demo."""
    provider_type_clean = (provider_type or "demo").lower()
    if "gemini" in provider_type_clean or (api_key and "AIza" in api_key):
        if api_key.strip():
            return GeminiLLMProvider(api_key=api_key, model_name=model_name or "gemini-2.5-flash")
    elif "openai" in provider_type_clean or base_url.strip():
        if api_key.strip() or base_url.strip():
            return OpenAILLMProvider(api_key=api_key, model_name=model_name or "gpt-4o-mini", base_url=base_url)
    return DemoLLMProvider()
