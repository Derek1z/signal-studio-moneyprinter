from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

AVAILABLE_VOICES = {
    "en-US-JennyNeural-Female": {"id": "en-US-JennyNeural", "gender": "Female", "accent": "US", "style": "Conversational"},
    "en-US-GuyNeural-Male": {"id": "en-US-GuyNeural", "gender": "Male", "accent": "US", "style": "Authoritative"},
    "en-US-AriaNeural-Female": {"id": "en-US-AriaNeural", "gender": "Female", "accent": "US", "style": "Energetic"},
    "en-GB-SoniaNeural-Female": {"id": "en-GB-SoniaNeural", "gender": "Female", "accent": "UK", "style": "Sophisticated"},
    "en-US-DavisNeural-Male": {"id": "en-US-DavisNeural", "gender": "Male", "accent": "US", "style": "Documentary"},
    "en-US-ChristopherNeural-Male": {"id": "en-US-ChristopherNeural", "gender": "Male", "accent": "US", "style": "Storyteller"},
}


async def _synthesize_edge_tts_async(
    text: str,
    voice_id: str,
    output_mp3: Path,
    output_srt: Path | None = None,
    rate_pct: int = 0,
) -> list[dict[str, Any]]:
    """Asynchronous Edge-TTS speech and word-boundary subtitle generation."""
    import edge_tts  # type: ignore

    rate_str = f"+{rate_pct}%" if rate_pct >= 0 else f"{rate_pct}%"
    communicate = edge_tts.Communicate(text, voice_id, rate=rate_str)

    word_boundaries: list[dict[str, Any]] = []

    with open(output_mp3, "wb") as mp3_file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                mp3_file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                # offset and duration in 100ns units
                start_sec = chunk["offset"] / 10_000_000
                dur_sec = chunk["duration"] / 10_000_000
                word_boundaries.append({
                    "word": chunk["text"],
                    "start": round(start_sec, 2),
                    "end": round(start_sec + dur_sec, 2),
                })

    # Generate SRT if path provided
    if output_srt:
        srt_lines = []
        if word_boundaries:
            # Group into 4-word chunks for subtitles
            chunk_size = 4
            for i in range(0, len(word_boundaries), chunk_size):
                sub_chunk = word_boundaries[i : i + chunk_size]
                start_t = sub_chunk[0]["start"]
                end_t = sub_chunk[-1]["end"]
                sub_text = " ".join(item["word"] for item in sub_chunk)

                s_h, s_m, s_s, s_ms = int(start_t // 3600), int((start_t % 3600) // 60), int(start_t % 60), int((start_t % 1) * 1000)
                e_h, e_m, e_s, e_ms = int(end_t // 3600), int((end_t % 3600) // 60), int(end_t % 60), int((end_t % 1) * 1000)

                srt_lines.append(f"{len(srt_lines) + 1}\n{s_h:02d}:{s_m:02d}:{s_s:02d},{s_ms:03d} --> {e_h:02d}:{e_m:02d}:{e_s:02d},{e_ms:03d}\n{sub_text}\n")
            output_srt.write_text("\n".join(srt_lines), encoding="utf-8")
        else:
            # Fallback simple SRT
            words = text.split()
            dur = max(5.0, len(words) / 2.3)
            output_srt.write_text(f"1\n00:00:00,000 --> 00:00:{int(dur):02d},000\n{text[:80]}...\n", encoding="utf-8")

    return word_boundaries


def synthesize_speech(
    text: str,
    voice_name: str = "en-US-JennyNeural-Female",
    output_dir: Path | None = None,
    rate_factor: float = 1.0,
) -> dict[str, Any]:
    """Synthesize speech audio and subtitle timestamps using edge-tts."""
    clean_text = text.strip()
    if not clean_text:
        return {"success": False, "error": "Empty text provided"}

    out_dir = output_dir or Path(__file__).parent.parent / "studio_outputs" / "audio"
    out_dir.mkdir(parents=True, exist_ok=True)

    voice_meta = AVAILABLE_VOICES.get(voice_name, AVAILABLE_VOICES["en-US-JennyNeural-Female"])
    voice_id = voice_meta["id"]

    rate_pct = int((rate_factor - 1.0) * 100)
    hash_id = hashlib.md5(f"{clean_text}_{voice_id}_{rate_pct}".encode("utf-8")).hexdigest()[:12]
    mp3_path = out_dir / f"voice_{hash_id}.mp3"
    srt_path = out_dir / f"subs_{hash_id}.srt"

    # Reuse cached audio if already generated
    if mp3_path.exists() and mp3_path.stat().st_size > 500:
        words = clean_text.split()
        dur = max(3.0, round(len(words) / (2.3 * rate_factor), 1))
        return {
            "success": True,
            "mp3_path": str(mp3_path),
            "srt_path": str(srt_path),
            "duration": dur,
            "voice_name": voice_name,
            "word_count": len(words),
            "cached": True,
        }

    try:
        # Run async synthesis
        word_bounds = asyncio.run(
            _synthesize_edge_tts_async(clean_text, voice_id, mp3_path, srt_path, rate_pct)
        )
        total_duration = word_bounds[-1]["end"] if word_bounds else round(len(clean_text.split()) / 2.3, 1)
        return {
            "success": True,
            "mp3_path": str(mp3_path),
            "srt_path": str(srt_path),
            "duration": total_duration,
            "word_boundaries": word_bounds,
            "voice_name": voice_name,
            "word_count": len(clean_text.split()),
            "cached": False,
        }
    except Exception as exc:
        logger.warning(f"edge-tts synthesis failed ({exc}). Creating simulation placeholder.")
        # Fallback simulation
        words = clean_text.split()
        dur = max(3.0, round(len(words) / (2.3 * rate_factor), 1))
        # Write dummy/silent placeholder if edge-tts not installed in environment
        mp3_path.write_bytes(b"")
        return {
            "success": False,
            "error": str(exc),
            "mp3_path": str(mp3_path),
            "srt_path": str(srt_path),
            "duration": dur,
            "word_count": len(words),
        }
