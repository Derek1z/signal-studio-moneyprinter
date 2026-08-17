from __future__ import annotations

import json
import logging
import re
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from studio.ai_providers import BaseLLMProvider, DemoLLMProvider, get_llm_provider
from studio.live_data import YouTubeTrendProvider, get_research_pack
from studio.retention import analyze_retention
from studio.social import generate_social_package, generate_youtube_chapters
from studio.storage import delete_project_draft, list_saved_projects, load_project_draft, save_project_draft
from studio.thumbnails import generate_ai_image_prompt, generate_thumbnail_svg

logger = logging.getLogger(__name__)


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
    provider_info: dict[str, str] | None = None
    packaging: dict[str, Any] | None = None
    social_package: dict[str, Any] | None = None
    retention_score: int | None = None


def score_topics(
    niche: str,
    audience: str,
    goal: str = "",
    llm_provider: BaseLLMProvider | None = None,
    youtube_api_key: str = "",
    region: str = "US",
) -> list[dict[str, Any]]:
    """Score candidate topics using configured LLM and optional YouTube Data API metrics."""
    provider = llm_provider or DemoLLMProvider()
    topics = provider.generate_topics(niche=niche, audience=audience, goal=goal)

    if youtube_api_key.strip():
        yt_provider = YouTubeTrendProvider(api_key=youtube_api_key)
        if yt_provider.configured:
            return yt_provider.score(topics, region=region)

    return topics


def run_council(
    topic: str,
    niche: str = "",
    audience: str = "",
    llm_provider: BaseLLMProvider | None = None,
) -> tuple[list[dict[str, str]], int, str]:
    """Gather multi-perspective proposals from the 3-advisor council and judge selection."""
    provider = llm_provider or DemoLLMProvider()
    return provider.run_council(topic=topic, niche=niche, audience=audience)


def make_script(
    topic: str,
    angle: str,
    thesis: str = "",
    hook: str = "",
    niche: str = "",
    audience: str = "",
    duration_sec: int = 60,
    tone_preset: str = "balanced",
    llm_provider: BaseLLMProvider | None = None,
) -> str:
    """Generate a high-retention narration script for the selected angle with tone styling."""
    provider = llm_provider or DemoLLMProvider()
    return provider.generate_script(
        topic=topic,
        angle=angle,
        thesis=thesis,
        hook=hook,
        niche=niche,
        audience=audience,
        duration_sec=duration_sec,
        tone_preset=tone_preset,
    )


def generate_packaging(
    topic: str,
    script: str,
    llm_provider: BaseLLMProvider | None = None,
) -> dict[str, Any]:
    """Generate high-CTR title variations, thumbnail design concepts, and visual prompts."""
    provider = llm_provider or DemoLLMProvider()
    pkg = provider.generate_packaging(topic=topic, script=script)
    thumb_text = pkg.get("thumbnail_text", "AUTOMATE LESS. SHIP BETTER.")
    pkg["image_prompt"] = generate_ai_image_prompt(topic=topic, thumbnail_text=thumb_text)
    return pkg


def fetch_research_pack(
    topic: str,
    provider_type: str = "demo",
    google_api_key: str = "",
    google_cx: str = "",
) -> list[dict[str, str]]:
    """Fetch factual claims and primary research sources."""
    return get_research_pack(
        topic=topic,
        provider_type=provider_type,
        google_api_key=google_api_key,
        google_cx=google_cx,
    )


def audit_script_retention(script: str) -> dict[str, Any]:
    """Perform sentence-level pacing, retention drop-off, and cliché audit."""
    return analyze_retention(script)


def create_social_package(
    topic: str,
    script: str,
    niche: str,
    research_claims: list[dict[str, str]],
    title: str = "",
    tone_preset: str = "balanced",
) -> dict[str, Any]:
    """Generate full YouTube description with timestamps, chapters, citations, and social copy."""
    return generate_social_package(
        topic=topic,
        script=script,
        niche=niche,
        research_claims=research_claims,
        title=title,
        tone_preset=tone_preset,
    )


def risk_check(
    script: str,
    title: str,
    personal_evidence: bool,
    sources_approved: bool,
) -> dict[str, Any]:
    """Perform YouTube monetization and inauthentic/repetitive content risk assessment."""
    words = re.findall(r"\b\w+\b", script.lower())
    total_words = len(words)
    unique_words = len(set(words))
    lexical_ratio = (unique_words / total_words) if total_words else 0.0

    findings = []
    remediation_tips = []
    score = 15

    if total_words < 120:
        score += 25
        findings.append("Script length is under 120 words — video may be flagged as thin/low-effort content.")
        remediation_tips.append("Expand the narrative with a concrete step-by-step example or case study.")
    elif total_words < 180:
        score += 10
        findings.append("Script is slightly short (< 180 words).")

    if lexical_ratio < 0.45 and total_words > 50:
        score += 20
        findings.append("Low vocabulary diversity detected — repetitive or template-like language pattern.")
        remediation_tips.append("Vary sentence structures and reduce repetitive buzzwords.")

    if not personal_evidence:
        score += 25
        findings.append("No first-hand experience, experiment, or original creator point-of-view declared.")
        remediation_tips.append("Check the personal evidence box and add an authentic test result or personal comparison.")

    if not sources_approved:
        score += 30
        findings.append("Research & fact-check checkpoint has not been verified.")
        remediation_tips.append("Review and check off verified primary claims in Stage 04.")

    if not title.strip():
        score += 10
        findings.append("No packaging title defined.")
        remediation_tips.append("Select or input an approved YouTube title.")

    final_score = min(score, 100)
    level = "Low Risk" if final_score < 30 else "Moderate Review" if final_score < 60 else "High Risk"

    return {
        "score": final_score,
        "level": level,
        "findings": findings or ["No material repetition or authenticity flags detected. Excellent creator guardrails."],
        "tips": remediation_tips,
        "lexical_diversity": round(lexical_ratio * 100, 1),
        "word_count": total_words,
    }


def moneyprinter_payload(topic: str, script: str, settings: dict[str, Any]) -> dict[str, Any]:
    """Generate a clean VideoParams JSON payload conforming to MoneyPrinterTurbo Extended specifications."""
    broll_tags = settings.get("video_terms", ["creator workflow", "editing desk", "analytics", "screen capture"])
    if isinstance(broll_tags, str):
        broll_tags = [t.strip() for t in broll_tags.split(",") if t.strip()]

    return {
        "video_subject": topic,
        "video_script": script,
        "video_terms": broll_tags,
        "video_aspect": settings.get("video_aspect", "16:9"),
        "video_concat_mode": settings.get("video_concat_mode", "semantic"),
        "video_clip_duration": settings.get("video_clip_duration", 5),
        "video_source": settings.get("video_source", "pexels"),
        "voice_name": settings.get("voice_name", "en-US-JennyNeural-Female"),
        "voice_rate": float(settings.get("voice_rate", 1.0)),
        "voice_volume": float(settings.get("voice_volume", 1.0)),
        "subtitle_enabled": bool(settings.get("subtitle_enabled", True)),
        "subtitle_position": settings.get("subtitle_position", "bottom"),
        "enable_word_highlighting": bool(settings.get("enable_word_highlighting", True)),
        "bgm_type": settings.get("bgm_type", "random"),
        "bgm_volume": float(settings.get("bgm_volume", 0.16)),
        "font_size": int(settings.get("font_size", 54)),
        "video_count": 1,
    }


def validate_payload(payload: dict[str, Any]) -> tuple[bool, str]:
    """Validate MoneyPrinterTurbo payload structure against upstream contract."""
    try:
        from app.models.schema import VideoParams

        VideoParams(**payload)
        return True, "Validated against upstream MoneyPrinterTurbo VideoParams schema"
    except ImportError:
        required = {"video_subject", "video_script", "voice_name", "video_aspect"}
        if required.issubset(payload.keys()):
            return True, "Validated against lightweight VideoParams schema (standalone mode)"
        missing = required - set(payload.keys())
        return False, f"Missing required payload keys: {missing}"
    except Exception as exc:
        return False, str(exc)


def save_handoff(output_dir: Path, project: Project, payload: dict[str, Any]) -> Path:
    """Save handoff JSON artifact to local disk."""
    output_dir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", project.topic.lower()).strip("-")[:42] or "studio-project"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = output_dir / f"{slug}_{timestamp}_handoff.json"
    full_export = {
        "studio_version": "2.2.0",
        "project": asdict(project),
        "moneyprinter_payload": payload,
    }
    path.write_text(json.dumps(full_export, indent=2), encoding="utf-8")
    return path


def dispatch_to_moneyprinter(
    payload: dict[str, Any],
    endpoint_url: str = "http://127.0.0.1:8080/api/v1/generate",
    timeout_sec: int = 15,
) -> tuple[bool, str, dict[str, Any]]:
    """Dispatch payload directly to running MoneyPrinterTurbo instance via REST API."""
    endpoint = endpoint_url.strip() or "http://127.0.0.1:8080/api/v1/generate"
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            resp_body = resp.read().decode("utf-8")
            try:
                data = json.loads(resp_body)
            except Exception:
                data = {"raw": resp_body}
            return True, f"Successfully dispatched to MoneyPrinterTurbo ({resp.status} OK)", data
    except urllib.error.HTTPError as err:
        err_text = err.read().decode("utf-8", errors="replace")
        return False, f"MoneyPrinterTurbo returned HTTP {err.code}: {err_text}", {}
    except urllib.error.URLError as err:
        return (
            False,
            f"Could not connect to MoneyPrinterTurbo at '{endpoint}'. Is the server running locally? ({err.reason})",
            {},
        )
    except Exception as exc:
        return False, f"Dispatch failed: {exc}", {}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
