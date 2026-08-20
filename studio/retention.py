from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

CLICHE_BUZZWORDS = [
    "game changer", "game-changer", "dive in", "dive deep", "delve", "unleash",
    "supercharge", "embark", "revolutionize", "testament", "tapestry", "in today's video",
    "without further ado", "let's get right into it", "seamlessly", "harness the power",
    "at the end of the day", "skyrocket", "unlock your potential", "paradigm shift",
]

PASSIVE_INDICATORS = [
    r"\bis being\b", r"\bwas being\b", r"\bhas been\b", r"\bhave been\b",
    r"\bwere conducted\b", r"\bwas created\b", r"\bis utilized\b",
]


@dataclass
class SentenceAudit:
    text: str
    word_count: int
    flags: list[str]
    risk_level: str  # 'green', 'yellow', 'red'


def split_into_sentences(text: str) -> list[str]:
    """Split text into sentences while protecting decimals, abbreviations, and URLs."""
    clean = text.strip()
    if not clean:
        return []
    # Protect decimal numbers like 3.5 or 4.0
    clean = re.sub(r"(\d)\.(\d)", r"\1<DECIMAL_DOT>\2", clean)
    # Protect common abbreviations
    for abbrev in [r"\be\.g\.", r"\bi\.e\.", r"\bvs\.", r"\bdr\.", r"\bmr\.", r"\bmrs\.", r"\binc\.", r"\betc\."]:
        clean = re.sub(abbrev, lambda m: m.group(0).replace(".", "<ABBREV_DOT>"), clean, flags=re.IGNORECASE)
    # Split on sentence boundaries
    raw_sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", clean) if s.strip()]
    # Restore protected dots
    return [s.replace("<DECIMAL_DOT>", ".").replace("<ABBREV_DOT>", ".") for s in raw_sentences]


def analyze_retention(script: str) -> dict[str, Any]:
    """Perform sentence-level pacing, retention drop-off, and cliché audit."""
    raw_sentences = split_into_sentences(script)
    if not raw_sentences:
        return {
            "score": 80,
            "grade": "B",
            "pacing_verdict": "Empty script",
            "cliches_found": [],
            "sentences": [],
            "stats": {"total_words": 0, "total_sentences": 0, "avg_sentence_len": 0},
            "recommendations": ["Add script narration text to begin analysis."],
        }

    total_words = len(re.findall(r"\b\w+\b", script))
    cliches_found = []
    audited_sentences: list[SentenceAudit] = []
    penalty = 0

    for s in raw_sentences:
        s_words = len(re.findall(r"\b\w+\b", s))
        flags = []

        # Check cliches
        for cliche in CLICHE_BUZZWORDS:
            if re.search(r"\b" + re.escape(cliche) + r"\b", s.lower()):
                flags.append(f"AI cliché: '{cliche}'")
                if cliche not in cliches_found:
                    cliches_found.append(cliche)
                penalty += 6

        # Check passive voice
        for pattern in PASSIVE_INDICATORS:
            if re.search(pattern, s.lower()):
                flags.append("Passive phrasing")
                penalty += 4
                break

        # Check sentence pacing
        if s_words > 28:
            flags.append("Run-on sentence (>28 words)")
            penalty += 5
            risk = "red"
        elif s_words > 22 or flags:
            risk = "yellow"
        else:
            risk = "green"

        audited_sentences.append(
            SentenceAudit(
                text=s,
                word_count=s_words,
                flags=flags,
                risk_level=risk,
            )
        )

    # Check first sentence hook
    hook_len = audited_sentences[0].word_count if audited_sentences else 0
    if hook_len > 18:
        penalty += 8
        audited_sentences[0].flags.append("Hook is too long (>18 words)")
        audited_sentences[0].risk_level = "red"

    base_score = 98 - penalty
    final_score = max(35, min(100, base_score))

    grade = "A+" if final_score >= 92 else "A" if final_score >= 85 else "B" if final_score >= 75 else "C" if final_score >= 60 else "D"

    recommendations = []
    if cliches_found:
        recommendations.append(f"Remove generic AI buzzwords: {', '.join(cliches_found[:3])}.")
    if any("Run-on" in flag for audit in audited_sentences for flag in audit.flags):
        recommendations.append("Break up long compound sentences into crisp, punchy one-liners.")
    if hook_len > 18:
        recommendations.append("Shorten your opening hook line to under 15 words for maximum 3-second hold rate.")
    if not recommendations:
        recommendations.append("Pacing and sentence flow are crisp with high retention potential.")

    avg_len = round(total_words / max(1, len(raw_sentences)), 1)
    pacing_verdict = (
        "Crisp, rapid-fire velocity with excellent hold potential."
        if final_score >= 90
        else "Solid pacing with minor friction points to tighten."
        if final_score >= 75
        else "High risk of drop-off due to long sentences or generic buzzwords."
    )

    return {
        "score": final_score,
        "grade": grade,
        "pacing_verdict": pacing_verdict,
        "cliches_found": cliches_found,
        "sentences": [
            {
                "text": a.text,
                "words": a.word_count,
                "flags": a.flags,
                "risk": a.risk_level,
            }
            for a in audited_sentences
        ],
        "stats": {
            "total_words": total_words,
            "total_sentences": len(raw_sentences),
            "avg_sentence_len": avg_len,
        },
        "recommendations": recommendations,
    }



def get_tone_prompt_guidance(tone_preset: str) -> str:
    """Return specific prompt instructions for different creator tones."""
    preset = (tone_preset or "balanced").lower()
    if "hormozi" in preset:
        return """Style: Alex Hormozi Framework.
- Tone: High-energy, crisp, authoritative, zero corporate fluff.
- Structure: Start with the painful constraint, state the counter-intuitive rule, give 3 tangible steps with zero jargon, end with a direct takeaway.
- Pacing: Short sentences, high contrast words, active verbs only."""
    elif "veritasium" in preset:
        return """Style: Veritasium Investigative Essay.
- Tone: Curious, thoughtful, hypothesis-driven, evidence-backed.
- Structure: Open with a counter-intuitive mystery or question, break down a specific experiment, reveal the surprising twist, conclude with philosophical nuance.
- Pacing: Measured, narrative build-up with vivid sensory analogies."""
    elif "shorts" in preset or "reels" in preset:
        return """Style: Viral Shorts / TikTok High Retention.
- Tone: Extremely urgent, dynamic, conversational.
- Structure: 3-second pattern interrupt hook, immediate proof in sentence 2, 3 micro-tips under 10 seconds each, strong loop-back ending.
- Pacing: Rapid-fire, sub-12 word sentences."""
    else:
        return """Style: Balanced Human-Led Editorial.
- Tone: Professional, direct, authentic, peer-to-peer creator.
- Structure: Practical constraint, AI ideation vs. human checkpoint, verified lesson."""
