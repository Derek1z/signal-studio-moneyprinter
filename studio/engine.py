from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TOPIC_FIXTURES = [
    ("The 7-minute {niche} workflow that gives creators their Fridays back", 92, "High intent + clear transformation"),
    ("I tested 5 {niche} research habits for 30 days", 87, "Experiment format + personal proof"),
    ("Why most {niche} systems fail after one week", 82, "Contrarian tension + broad relevance"),
]


@dataclass
class Project:
    niche: str
    audience: str
    goal: str
    topic: str
    script: str
    research_approved: bool
    script_approved: bool
    settings: dict[str, Any]
    risk_score: int
    created_at: str


def score_topics(niche: str, audience: str) -> list[dict[str, Any]]:
    subject = niche.strip() or "AI productivity"
    audience_hint = audience.strip() or "busy creators"
    return [
        {"topic": title.format(niche=subject), "score": score, "signal": signal, "audience": audience_hint}
        for title, score, signal in TOPIC_FIXTURES
    ]


def council(topic: str) -> tuple[list[dict[str, str]], int, str]:
    proposals = [
        {
            "advisor": "Story architect",
            "angle": "The lived experiment",
            "hook": f"I gave {topic.lower()} one week—and the result wasn't what the tutorials promised.",
            "thesis": "Turn the topic into a specific before/after story with visible evidence and a creator's point of view.",
        },
        {
            "advisor": "Audience advocate",
            "angle": "The useful shortcut",
            "hook": "You don't need another tool. You need one workflow that survives a busy Tuesday.",
            "thesis": "Lead with the viewer's constraint, then teach a repeatable three-step system.",
        },
        {
            "advisor": "Skeptical editor",
            "angle": "The myth audit",
            "hook": "The most popular advice here gets one crucial thing backwards.",
            "thesis": "Challenge the generic claim, show the boundary conditions, and end with a measured recommendation.",
        },
    ]
    return proposals, 1, "Best balance of originality, viewer utility, and evidence-friendly claims."


def make_script(topic: str, angle: str) -> str:
    return f"""Most people approach {topic.lower()} by collecting more tools. I did too—and it made the work slower.

So I ran a smaller experiment. One week, one repeatable workflow, and one rule: every automated step had to leave room for a human decision.

First, I started with the viewer's real problem, not a keyword. Second, I used AI to generate competing approaches, then judged them against usefulness, originality, and evidence. Third, I stopped before publishing and checked every factual claim.

The surprising part was that the automation wasn't the advantage. The advantage was having better checkpoints. Research could be rejected. The script could be rewritten. Visuals had to earn their place instead of filling time.

If you try this, begin with one video. Keep the source notes. Add something only you can know: a test, a failure, a comparison, or a real opinion. That is what turns a generated asset into authored work.

The takeaway is simple: use AI to widen your options, then use judgment to narrow them. That's the workflow worth repeating."""


def research_pack(topic: str) -> list[dict[str, str]]:
    return [
        {"claim": "AI assistance is not, by itself, a monetization disqualifier.", "status": "Needs live verification", "source": "YouTube Help — monetization policies"},
        {"claim": "Repetitive, mass-produced, or minimally transformed content is higher risk.", "status": "Needs live verification", "source": "YouTube Help — channel monetization policies"},
        {"claim": f"Viewer interest exists for: {topic}", "status": "Demo signal", "source": "Deterministic prototype trend fixture"},
    ]


def risk_check(script: str, title: str, personal_evidence: bool, sources_approved: bool) -> dict[str, Any]:
    generic = len(set(re.findall(r"\b\w+\b", script.lower()))) / max(1, len(re.findall(r"\b\w+\b", script.lower())))
    findings = []
    score = 18
    if generic < 0.45:
        score += 20
        findings.append("Language has a repetitive/template-like pattern.")
    if not personal_evidence:
        score += 26
        findings.append("No first-hand example, test, or original evidence is declared.")
    if not sources_approved:
        score += 28
        findings.append("Research checkpoint is not approved.")
    if len(script.split()) < 180:
        score += 12
        findings.append("Script is short enough to feel thin or interchangeable.")
    if not title.strip():
        score += 8
        findings.append("Packaging has no approved title.")
    return {"score": min(score, 100), "level": "Low" if score < 30 else "Review" if score < 60 else "High", "findings": findings or ["No material repetition or authenticity flags detected."]}


def moneyprinter_payload(topic: str, script: str, settings: dict[str, Any]) -> dict[str, Any]:
    return {
        "video_subject": topic,
        "video_script": script,
        "video_terms": settings.get("video_terms", ["creator workflow", "AI research", "editing desk", "fact checking"]),
        "video_aspect": settings.get("video_aspect", "16:9"),
        "video_concat_mode": settings.get("video_concat_mode", "semantic"),
        "video_clip_duration": settings.get("video_clip_duration", 5),
        "video_source": settings.get("video_source", "pexels"),
        "voice_name": settings.get("voice_name", "en-US-JennyNeural-Female"),
        "voice_rate": settings.get("voice_rate", 1.0),
        "subtitle_enabled": settings.get("subtitle_enabled", True),
        "subtitle_position": settings.get("subtitle_position", "bottom"),
        "enable_word_highlighting": settings.get("enable_word_highlighting", True),
        "bgm_type": settings.get("bgm_type", "random"),
        "bgm_volume": settings.get("bgm_volume", 0.16),
        "font_size": settings.get("font_size", 54),
        "video_count": 1,
    }


def validate_payload(payload: dict[str, Any]) -> tuple[bool, str]:
    try:
        from app.models.schema import VideoParams
        VideoParams(**payload)
        return True, "Validated against upstream VideoParams"
    except ImportError:
        required = {"video_subject", "video_script", "voice_name", "video_aspect"}
        return required.issubset(payload), "Validated with lightweight contract (upstream dependencies unavailable)"
    except Exception as exc:
        return False, str(exc)


def save_handoff(output_dir: Path, project: Project, payload: dict[str, Any]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", project.topic.lower()).strip("-")[:42] or "studio-project"
    path = output_dir / f"{slug}-handoff.json"
    path.write_text(json.dumps({"studio": asdict(project), "moneyprinter": payload}, indent=2), encoding="utf-8")
    return path


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
