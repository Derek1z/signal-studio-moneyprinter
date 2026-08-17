from __future__ import annotations

import re
from typing import Any


def generate_youtube_chapters(script: str, total_duration_sec: int = 75) -> list[tuple[str, str]]:
    """Compute realistic timestamp chapters based on script paragraphs."""
    paragraphs = [p.strip() for p in script.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [p.strip() for p in script.split("\n") if len(p.strip().split()) > 8]

    if len(paragraphs) <= 1:
        return [("00:00", "Introduction & Hook"), ("00:30", "Core Workflow"), ("01:00", "Key Takeaway")]

    total_words = len(re.findall(r"\b\w+\b", script)) or 1
    chapters = [("00:00", "Introduction & Hook")]

    accumulated_words = 0
    default_titles = [
        "The Core Problem",
        "The 1-Week Experiment",
        "The 3-Step Framework",
        "Verification & Checkpoints",
        "The Key Takeaway",
        "Final Verdict",
    ]

    for idx, p in enumerate(paragraphs[:-1]):
        p_words = len(re.findall(r"\b\w+\b", p))
        accumulated_words += p_words
        sec = int((accumulated_words / total_words) * total_duration_sec)
        minutes = sec // 60
        seconds = sec % 60
        time_str = f"{minutes:02d}:{seconds:02d}"

        title = default_titles[idx % len(default_titles)]
        # Try to infer title from first few words if descriptive
        first_words = p.split()[:4]
        if first_words and len(" ".join(first_words)) < 30:
            candidate = " ".join(first_words).strip(".,!?:;")
            if candidate.lower() not in ["first", "second", "third", "so", "if you"]:
                title = candidate.capitalize()

        chapters.append((time_str, title))

    return chapters


def generate_social_package(
    topic: str,
    script: str,
    niche: str,
    research_claims: list[dict[str, str]],
    title: str = "",
    tone_preset: str = "balanced",
) -> dict[str, Any]:
    """Generate complete YouTube SEO metadata, chapters, citations, and multi-platform companion posts."""
    approved_title = title or topic
    words = len(re.findall(r"\b\w+\b", script))
    est_duration_sec = max(30, round(words / 2.3))
    chapters = generate_youtube_chapters(script, total_duration_sec=est_duration_sec)

    # Format Chapters Block
    chapters_text = "\n".join(f"{time_str} - {chap_title}" for time_str, chap_title in chapters)

    # Format Citations Block
    sources_lines = []
    for r in research_claims:
        if r.get("url"):
            sources_lines.append(f"• {r.get('claim', '')} — {r.get('source', '')}: {r.get('url')}")
        else:
            sources_lines.append(f"• {r.get('claim', '')} (Verified via {r.get('source', 'Internal Review')})")
    sources_text = "\n".join(sources_lines) if sources_lines else "• Original creator experimentation and workflow analysis."

    # YouTube Description
    yt_description = f"""{approved_title}

Most people approach {niche or 'content creation'} by collecting more tools and adding unnecessary friction. In this video, we break down a lean, repeatable workflow with human checkpoints to ship higher quality work in less time.

⏱️ TIMESTAMPS:
{chapters_text}

📚 RESEARCH & PRIMARY CITATIONS:
{sources_text}

⚙️ WORKFLOW TECH & SYSTEM:
• Video engine orchestrated via Signal Studio × MoneyPrinterTurbo
• Scripting & Editorial: Human-curated AI Council
• Voice & B-Roll: Semantic stock synchronization

#AIProductivity #CreatorEconomy #WorkflowAutomation #YouTubeGrowth
"""

    # SEO Tags & Hashtags
    niche_clean = re.sub(r"[^\w\s]", "", niche).lower()
    base_tags = [
        approved_title.lower(),
        niche_clean,
        f"{niche_clean} tutorial",
        "creator workflow",
        "ai video editing",
        "moneyprinter turbo",
        "signal studio",
        "youtube automation",
        "ethical ai content",
        "video creation system",
        "productivity tips",
    ]
    seo_tags = ", ".join(list(dict.fromkeys(base_tags))[:14])

    # X / Twitter Thread Post
    x_post = f"""Most creators spend 80% of their time on the wrong part of video production.

Here's the 3-step workflow that cuts creation time in half (without sacrificing quality):

1. Start with the viewer's real constraint, not just a keyword.
2. Use AI to widen your angle options—then use human judgment to filter them.
3. Fact-check every claim before hitting render.

Full breakdown in today's video 🧵👇"""

    # LinkedIn Post
    linkedin_post = f"""AI won't replace creators. But creators who use AI with disciplined human checkpoints will outpace those who don't.

In my latest project on '{approved_title}', I tested a minimalist 3-step production framework:

🔹 Filter 1: Constraint-First Ideation
🔹 Filter 2: Multi-Advisor Council Evaluation
🔹 Filter 3: Pre-Production Research Verification

The surprising lesson? Speed doesn't come from total automation. It comes from having clear gates where mediocre ideas get rejected early.

What is the biggest bottleneck in your current creation workflow?"""

    # TikTok / Shorts Caption
    shorts_caption = f"Stop automating the wrong part of your workflow 🛑 Here's the 3-step system that actually works. #{niche_clean.replace(' ', '')} #creatortips #productivity #workflow"

    return {
        "youtube_description": yt_description.strip(),
        "chapters": chapters,
        "seo_tags": seo_tags,
        "x_post": x_post,
        "linkedin_post": linkedin_post,
        "shorts_caption": shorts_caption,
    }
