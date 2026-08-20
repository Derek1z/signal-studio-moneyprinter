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
from studio.hooks import generate_hook_variations, replace_script_hook
from studio.live_data import YouTubeTrendProvider, fetch_live_youtube_competitors, get_research_pack
from studio.renderer import render_video_pipeline
from studio.retention import analyze_retention, split_into_sentences
from studio.simulator import render_live_video_simulator
from studio.social import export_moneyprinter_payload, generate_social_package, generate_youtube_chapters
from studio.stock_media import get_clips_for_scenes
from studio.storage import delete_project_draft, list_saved_projects, load_project_draft, save_project_draft
from studio.storyboard import compile_storyboard_to_broll_terms, segment_script_into_scenes
from studio.thumbnails import generate_ai_image_prompt, generate_thumbnail_svg
from studio.voice import AVAILABLE_VOICES, synthesize_speech

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
    competitors: list[dict[str, Any]] | None = None,
    citations: list[dict[str, Any]] | None = None,
) -> tuple[list[dict[str, str]], int, str]:
    """Gather multi-perspective proposals from the 3-advisor council and judge selection."""
    provider = llm_provider or DemoLLMProvider()
    return provider.run_council(
        topic=topic,
        niche=niche,
        audience=audience,
        competitors=competitors,
        citations=citations,
    )


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
    competitors: list[dict[str, Any]] | None = None,
    citations: list[dict[str, Any]] | None = None,
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
        competitors=competitors,
        citations=citations,
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
