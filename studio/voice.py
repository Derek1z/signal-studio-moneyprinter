from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
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


def _find_ffmpeg() -> str | None:
    sys_ffmpeg = shutil.which("ffmpeg")
    if sys_ffmpeg:
        return sys_ffmpeg
    search_paths = [
        Path(__file__).parent.parent / "studio_outputs" / "bin" / "ffmpeg.exe",
        Path(__file__).parent.parent / "studio_outputs" / "test_run" / "bin" / "ffmpeg.exe",
    ]
    for p in search_paths:
        if p.exists() and p.stat().st_size > 1_000_000:
            return str(p.resolve())
    root_outputs = Path(__file__).parent.parent / "studio_outputs"
    for found in root_outputs.glob("**/ffmpeg.exe"):
        if found.stat().st_size > 1_000_000:
            return str(found.resolve())
    return None


def _synthesize_windows_sapi(text: str, output_mp3: Path, output_srt: Path | None = None) -> float:
    """Synthesize real spoken speech using Windows native SpeechSynthesizer and convert to MP3."""
    clean_text = text.replace('"', '`"').replace("'", "''").strip()
    wav_path = output_mp3.with_suffix(".wav")

    ps_script = f"""
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.Rate = 0
$synth.SetOutputToWaveFile('{wav_path.resolve().as_posix()}')
$synth.Speak(@'
{clean_text}
'@)
$synth.Dispose()
"""
    ps_file = output_mp3.parent / f"temp_{output_mp3.stem}.ps1"
    ps_file.write_text(ps_script, encoding="utf-8")

    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps_file.resolve())],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    finally:
        if ps_file.exists():
            ps_file.unlink()

    ffmpeg_bin = _find_ffmpeg()
    if wav_path.exists() and wav_path.stat().st_size > 1000:
        if ffmpeg_bin:
            cmd = [ffmpeg_bin, "-y", "-i", str(wav_path.resolve()), "-c:a", "libmp3lame", "-q:a", "2", str(output_mp3.resolve())]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            shutil.copy(wav_path, output_mp3)

        if wav_path.exists():
            wav_path.unlink()

    words = text.split()
    total_dur = max(4.0, round(len(words) / 2.3, 1))

    if output_srt:
        # Generate SRT
        chunk_size = 4
        srt_lines = []
        word_dur = total_dur / max(1, len(words))
        for idx, i in enumerate(range(0, len(words), chunk_size)):
            chunk = words[i : i + chunk_size]
            s_t = i * word_dur
            e_t = min(total_dur, s_t + (len(chunk) * word_dur))
            s_m, s_s, s_ms = int(s_t // 60), int(s_t % 60), int((s_t % 1) * 1000)
            e_m, e_s, e_ms = int(e_t // 60), int(e_t % 60), int((e_t % 1) * 1000)
            srt_lines.append(f"{idx+1}\n00:{s_m:02d}:{s_s:02d},{s_ms:03d} --> 00:{e_m:02d}:{e_s:02d},{e_ms:03d}\n{' '.join(chunk)}\n")
        output_srt.write_text("\n".join(srt_lines), encoding="utf-8")

    return total_dur


def synthesize_speech(
    text: str,
    voice_name: str = "en-US-JennyNeural-Female",
    output_dir: Path | None = None,
    rate_factor: float = 1.0,
) -> dict[str, Any]:
    """Synthesize real spoken speech audio and subtitle timestamps."""
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

    # 1. Reuse cached audio if already generated
    if mp3_path.exists() and mp3_path.stat().st_size > 5000:
        words = clean_text.split()
        dur = max(3.0, round(len(words) / (2.3 * rate_factor), 1))
        return {
            "success": True,
            "mp3_path": str(mp3_path.resolve()),
            "srt_path": str(srt_path.resolve()),
            "duration": dur,
            "voice_name": voice_name,
            "word_count": len(words),
            "cached": True,
        }

    # 2. Try Edge-TTS if installed
    try:
        import edge_tts  # type: ignore

        rate_str = f"+{rate_pct}%" if rate_pct >= 0 else f"{rate_pct}%"
        communicate = edge_tts.Communicate(clean_text, voice_id, rate=rate_str)

        async def _run_edge():
            word_boundaries = []
            with open(mp3_path, "wb") as f:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        f.write(chunk["data"])
                    elif chunk["type"] == "WordBoundary":
                        start_sec = chunk["offset"] / 10_000_000
                        dur_sec = chunk["duration"] / 10_000_000
                        word_boundaries.append({"word": chunk["text"], "start": round(start_sec, 2), "end": round(start_sec + dur_sec, 2)})
            return word_boundaries

        word_bounds = asyncio.run(_run_edge())
        total_duration = word_bounds[-1]["end"] if word_bounds else round(len(clean_text.split()) / 2.3, 1)

        # Generate SRT
        if word_bounds:
            srt_lines = []
            for idx, i in enumerate(range(0, len(word_bounds), 4)):
                sub_chunk = word_bounds[i : i + 4]
                s_t = sub_chunk[0]["start"]
                e_t = sub_chunk[-1]["end"]
                sub_text = " ".join(item["word"] for item in sub_chunk)
                s_m, s_s, s_ms = int(s_t // 60), int(s_t % 60), int((s_t % 1) * 1000)
                e_m, e_s, e_ms = int(e_t // 60), int(e_t % 60), int((e_t % 1) * 1000)
                srt_lines.append(f"{idx+1}\n00:{s_m:02d}:{s_s:02d},{s_ms:03d} --> 00:{e_m:02d}:{e_s:02d},{e_ms:03d}\n{sub_text}\n")
            srt_path.write_text("\n".join(srt_lines), encoding="utf-8")

        return {
            "success": True,
            "mp3_path": str(mp3_path.resolve()),
            "srt_path": str(srt_path.resolve()),
            "duration": total_duration,
            "voice_name": voice_name,
            "word_count": len(clean_text.split()),
            "cached": False,
        }
    except Exception as exc:
        logger.info(f"Edge-TTS not available ({exc}), using Windows SAPI voice synthesizer.")

    # 3. Windows Native SAPI Voice Synthesizer
    try:
        dur = _synthesize_windows_sapi(clean_text, mp3_path, srt_path)
        if mp3_path.exists() and mp3_path.stat().st_size > 1000:
            return {
                "success": True,
                "mp3_path": str(mp3_path.resolve()),
                "srt_path": str(srt_path.resolve()),
                "duration": dur,
                "voice_name": "Windows Neural Voice",
                "word_count": len(clean_text.split()),
                "cached": False,
            }
    except Exception as e:
        logger.error(f"Windows SAPI voice failed: {e}")

    return {"success": False, "error": "Speech synthesis failed"}
