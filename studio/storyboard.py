from __future__ import annotations

import re
from typing import Any

from studio.retention import split_into_sentences

CAMERA_MOTIONS = [
    "Cinematic Slow Push In",
    "Dynamic Lateral Pan",
    "Static Crisp Macro Focus",
    "Over-The-Shoulder POV",
    "Fast Cut Pattern Interrupt",
    "Wide Angle Establishing Drift",
]

DEFAULT_VISUAL_THEMES = [
    ("creator desk, laptop typing, warm lighting", "Focused creator examining analytics or editing"),
    ("complex flowchart diagram, chaotic screen", "Visual illustration of the confusing bottleneck"),
    ("clean minimalist checklist, glowing green checkmark", "Simple repeatable 3-step solution"),
    ("split screen comparison, side-by-side test", "Evidence and before/after proof"),
    ("futuristic holographic interface, smooth data stream", "Leverage and automated checkpoints"),
    ("confident creator smiling, cinematic shallow depth of field", "Empowered takeaway and call to action"),
]


def segment_script_into_scenes(
    script: str,
    target_clip_duration_sec: int = 5,
) -> list[dict[str, Any]]:
    """Segment script narration into timed visual scene blocks with stock keywords."""
    clean = script.strip()
    if not clean:
        return []

    # Split into sentences with boundary preservation
    sentences = split_into_sentences(clean)
    if not sentences:
        sentences = [clean]

    words_per_sec = 2.3
    words_per_scene = int(target_clip_duration_sec * words_per_sec)

    scenes: list[dict[str, Any]] = []
    current_words: list[str] = []
    current_sentences: list[str] = []
    current_time = 0.0
    scene_idx = 1

    def make_scene_payload(s_idx: int, s_text: str, s_words: list[str], start_t: float) -> dict[str, Any]:
        dur = max(3.0, round(len(s_words) / words_per_sec, 1))
        end_t = start_t + dur
        theme_kw, theme_desc = DEFAULT_VISUAL_THEMES[(s_idx - 1) % len(DEFAULT_VISUAL_THEMES)]
        motion = CAMERA_MOTIONS[(s_idx - 1) % len(CAMERA_MOTIONS)]

        # Extract top keywords from narration
        clean_words = [w.lower() for w in re.findall(r"\b[a-zA-Z]{4,}\b", s_text)]
        top_kws = [w for w in clean_words if w not in ["this", "that", "with", "from", "most", "people", "start", "rule", "step", "first", "second", "third"]]
        combined_tags = [theme_kw.split(",")[0].strip()] + top_kws[:3]

        start_m, start_s = int(start_t // 60), int(start_t % 60)
        end_m, end_s = int(end_t // 60), int(end_t % 60)

        return {
            "scene_idx": s_idx,
            "time_start": round(start_t, 1),
            "time_end": round(end_t, 1),
            "time_label": f"{start_m:02d}:{start_s:02d} - {end_m:02d}:{end_s:02d}",
            "duration": dur,
            "narration": s_text,
            "visual_concept": theme_desc,
            "broll_keywords": list(dict.fromkeys(combined_tags)),
            "broll_query": ", ".join(list(dict.fromkeys(combined_tags))[:3]),
            "camera_motion": motion,
        }

    for sentence in sentences:
        s_words = sentence.split()
        if len(current_words) + len(s_words) >= words_per_scene and current_words:
            narration_text = " ".join(current_sentences)
            scene_data = make_scene_payload(scene_idx, narration_text, current_words, current_time)
            scenes.append(scene_data)
            current_time = scene_data["time_end"]
            scene_idx += 1
            current_words = []
            current_sentences = []

        current_words.extend(s_words)
        current_sentences.append(sentence)

    if current_words:
        narration_text = " ".join(current_sentences)
        scene_data = make_scene_payload(scene_idx, narration_text, current_words, current_time)
        scenes.append(scene_data)

    return scenes


def compile_storyboard_to_broll_terms(scenes: list[dict[str, Any]]) -> list[str]:
    """Aggregate unique B-roll search terms from all scenes for MoneyPrinter payload."""
    all_terms: list[str] = []
    for sc in scenes:
        for kw in sc.get("broll_keywords", []):
            if kw and kw not in all_terms:
                all_terms.append(kw)
    return all_terms[:12] or ["creator workflow", "editing desk", "analytics dashboard"]
