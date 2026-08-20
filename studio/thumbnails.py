from __future__ import annotations

import html
import re
from typing import Any


def generate_thumbnail_svg(
    headline: str,
    subtitle: str = "WORKFLOW EXPERIMENT",
    badge: str = "AI × HUMAN",
    aspect_ratio: str = "16:9",
    theme: str = "emerald",
) -> str:
    """Generate high-contrast, scalable SVG thumbnail mockup for YouTube and Shorts."""
    is_vertical = aspect_ratio == "9:16"
    width = 720 if is_vertical else 1280
    height = 1280 if is_vertical else 720

    # Color themes
    themes = {
        "emerald": {"bg1": "#091a13", "bg2": "#143828", "accent": "#d2f866", "text": "#ffffff", "badge_bg": "#1d5c47"},
        "cyber": {"bg1": "#0b0f19", "bg2": "#1e293b", "accent": "#38bdf8", "text": "#f8fafc", "badge_bg": "#0369a1"},
        "amber": {"bg1": "#180d04", "bg2": "#361b07", "accent": "#fbbf24", "text": "#fffbeb", "badge_bg": "#b45309"},
        "crimson": {"bg1": "#180608", "bg2": "#3b0c11", "accent": "#f87171", "text": "#fff1f2", "badge_bg": "#991b1b"},
    }
    t = themes.get(theme, themes["emerald"])

    # Clean and split headline into punchy lines (max 3-4 words per line)
    clean_headline = html.escape(headline.upper().strip() or "AUTOMATE LESS. SHIP BETTER.")
    words = clean_headline.split()
    lines: list[str] = []
    curr: list[str] = []
    for w in words:
        curr.append(w)
        if len(curr) >= 3 or (len(" ".join(curr)) > 14 and len(curr) >= 2):
            lines.append(" ".join(curr))
            curr = []
    if curr:
        lines.append(" ".join(curr))
    lines = lines[:4]

    # Dynamically scale font size if many lines or long text
    max_line_chars = max([len(l) for l in lines], default=10)
    base_font = 60 if is_vertical else (76 if max_line_chars > 16 or len(lines) >= 3 else 84)
    font_size = base_font
    line_height = font_size * 1.15
    start_y = (480 if is_vertical else 330) if len(lines) <= 2 else (440 if is_vertical else 300)

    text_spans = []
    for idx, line in enumerate(lines):
        y_pos = start_y + (idx * line_height)
        color = t["accent"] if idx == 0 else t["text"]
        text_spans.append(
            f'<text x="80" y="{y_pos}" fill="{color}" font-size="{font_size}" font-weight="900" font-family="\'Manrope\', Impact, sans-serif" filter="url(#drop-shadow)">{line}</text>'
        )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="auto" style="border-radius:12px;box-shadow:0 12px 30px rgba(0,0,0,0.35);">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{t['bg1']}" />
      <stop offset="100%" stop-color="{t['bg2']}" />
    </linearGradient>
    <linearGradient id="accentGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{t['accent']}" />
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0.8" />
    </linearGradient>
    <filter id="drop-shadow" x="-10%" y="-10%" width="130%" height="130%">
      <feDropShadow dx="3" dy="6" stdDeviation="5" flood-color="#000000" flood-opacity="0.8" />
    </filter>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="80" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
  </defs>

  <!-- Background Layer -->
  <rect width="{width}" height="{height}" fill="url(#bgGrad)" />

  <!-- Ambient Glow Effect -->
  <circle cx="{width * 0.85}" cy="{height * 0.3}" r="{width * 0.35}" fill="{t['accent']}" opacity="0.16" filter="url(#glow)" />
  <circle cx="{width * 0.15}" cy="{height * 0.8}" r="{width * 0.25}" fill="{t['bg2']}" opacity="0.4" filter="url(#glow)" />

  <!-- Top Badge -->
  <g transform="translate(80, 110)">
    <rect width="180" height="42" rx="21" fill="{t['badge_bg']}" stroke="{t['accent']}" stroke-width="1.5" />
    <text x="90" y="27" fill="#ffffff" font-size="16" font-weight="800" font-family="'Manrope', sans-serif" text-anchor="middle" letter-spacing="2">{html.escape(badge.upper())}</text>
  </g>

  <!-- Subtitle / Category -->
  <text x="80" y="220" fill="{t['accent']}" font-size="22" font-weight="800" font-family="'Manrope', sans-serif" letter-spacing="4" opacity="0.9">{html.escape(subtitle.upper())}</text>

  <!-- Main Punchy Headline -->
  {"".join(text_spans)}

  <!-- Bottom Accent Stripe -->
  <rect x="80" y="{height - 50}" width="{width - 160}" height="8" rx="4" fill="url(#accentGrad)" />

  <!-- Verified Icon Badge -->
  <g transform="translate({width - 160}, 100)">
    <circle cx="30" cy="30" r="28" fill="{t['accent']}" />
    <path d="M20 30 L27 37 L41 23" stroke="{t['bg1']}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round" fill="none" />
  </g>
</svg>"""
    return svg


def generate_ai_image_prompt(topic: str, thumbnail_text: str, visual_style: str = "minimal high-contrast") -> str:
    """Generate ready-to-use prompt for Midjourney, DALL-E 3, or Imagen 3."""
    return (
        f"YouTube thumbnail background visual for a video titled '{topic}'. "
        f"Concept: {visual_style}. Bold cinematic lighting, high contrast, clean minimalist framing with negative space on the left for text. "
        f"Subject: Modern creator desk, futuristic sleek interface elements, sharp focus, 8k resolution, professional photography aesthetic, no text in image."
    )
