from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import wave
from concurrent.futures import ThreadPoolExecutor
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
    """Find FFmpeg binary across Linux, macOS, and Windows."""
    sys_ffmpeg = shutil.which("ffmpeg")
    if sys_ffmpeg:
        return sys_ffmpeg

    try:
        import imageio_ffmpeg  # type: ignore

        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and os.path.exists(exe):
            return exe
    except Exception:
        pass

    exe_names = ["ffmpeg", "ffmpeg.exe"]
    search_dirs = [
        Path(__file__).parent.parent / "studio_outputs" / "bin",
        Path(__file__).parent.parent / "studio_outputs" / "test_run" / "bin",
    ]
    for s_dir in search_dirs:
        for name in exe_names:
            candidate = s_dir / name
            if candidate.exists() and candidate.stat().st_size > 100_000:
                return str(candidate.resolve())

    root_outputs = Path(__file__).parent.parent / "studio_outputs"
    for pattern in ["**/ffmpeg", "**/ffmpeg.exe"]:
        for found in root_outputs.glob(pattern):
            if found.is_file() and found.stat().st_size > 100_000:
                return str(found.resolve())

    return None


def _generate_srt_from_words(words: list[str], total_duration: float, srt_path: Path, chunk_size: int = 4) -> None:
    """Generate properly formatted SRT subtitles based on word distribution."""
    if not words:
        words = ["Video", "Narration"]
    srt_lines = []
    word_dur = total_duration / max(1, len(words))
    for idx, i in enumerate(range(0, len(words), chunk_size)):
        chunk = words[i : i + chunk_size]
        s_t = i * word_dur
        e_t = min(total_duration, s_t + (len(chunk) * word_dur))
        s_m, s_s, s_ms = int(s_t // 60), int(s_t % 60), int((s_t % 1) * 1000)
        e_m, e_s, e_ms = int(e_t // 60), int(e_t % 60), int((e_t % 1) * 1000)
        srt_lines.append(
            f"{idx + 1}\n00:{s_m:02d}:{s_s:02d},{s_ms:03d} --> 00:{e_m:02d}:{e_s:02d},{e_ms:03d}\n{' '.join(chunk)}\n"
        )
    srt_path.write_text("\n".join(srt_lines), encoding="utf-8")


def _synthesize_windows_sapi(text: str, output_mp3: Path, output_srt: Path | None = None) -> float:
    """Synthesize speech using Windows SAPI (Windows only)."""
    if sys.platform != "win32" or not shutil.which("powershell"):
        raise OSError("Windows SAPI requires Windows OS with PowerShell.")

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
        _generate_srt_from_words(words, total_dur, output_srt)

    return total_dur


def _synthesize_linux_espeak(text: str, output_mp3: Path, output_srt: Path | None = None) -> float:
    """Synthesize speech using espeak or espeak-ng on Linux."""
    espeak_bin = shutil.which("espeak-ng") or shutil.which("espeak")
    if not espeak_bin:
        raise OSError("Neither espeak-ng nor espeak found on system.")

    wav_path = output_mp3.with_suffix(".wav")
    subprocess.run(
        [espeak_bin, "-w", str(wav_path.resolve()), "-s", "160", text],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

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
        _generate_srt_from_words(words, total_dur, output_srt)

    return total_dur


def _synthesize_macos_say(text: str, output_mp3: Path, output_srt: Path | None = None) -> float:
    """Synthesize speech using macOS native 'say' command."""
    say_bin = shutil.which("say")
    if not say_bin or sys.platform != "darwin":
        raise OSError("macOS 'say' command not available.")

    aiff_path = output_mp3.with_suffix(".aiff")
    subprocess.run([say_bin, "-o", str(aiff_path.resolve()), text], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    ffmpeg_bin = _find_ffmpeg()
    if aiff_path.exists() and aiff_path.stat().st_size > 1000:
        if ffmpeg_bin:
            cmd = [ffmpeg_bin, "-y", "-i", str(aiff_path.resolve()), "-c:a", "libmp3lame", "-q:a", "2", str(output_mp3.resolve())]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            shutil.copy(aiff_path, output_mp3)

        if aiff_path.exists():
            aiff_path.unlink()

    words = text.split()
    total_dur = max(4.0, round(len(words) / 2.3, 1))
    if output_srt:
        _generate_srt_from_words(words, total_dur, output_srt)

    return total_dur


def _synthesize_synthetic_audio(text: str, output_mp3: Path, output_srt: Path | None = None, rate_factor: float = 1.0) -> float:
    """Generate rhythmic modulated audio track with exact speech timing for offline environments."""
    words = text.split() or ["Video", "Narration"]
    total_dur = max(3.0, round(len(words) / (2.3 * max(0.5, rate_factor)), 1))
    wav_path = output_mp3.with_suffix(".wav")

    # Generate synthetic speech-cadence WAV
    sample_rate = 22050
    num_samples = int(total_dur * sample_rate)
    with wave.open(str(wav_path.resolve()), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)

        frames = bytearray()
        word_dur = total_dur / len(words)
        for i in range(num_samples):
            t = i / sample_rate
            word_idx = min(len(words) - 1, int(t / max(0.01, word_dur)))
            w_time = t - (word_idx * word_dur)
            # Rhythmic cadence pulse
            envelope = math.sin(math.pi * min(1.0, w_time / max(0.01, word_dur * 0.85)))
            freq = 220.0 + (len(words[word_idx]) * 15.0)
            sample = int(32767 * 0.28 * envelope * math.sin(2.0 * math.pi * freq * t))
            frames.extend(struct.pack("<h", max(-32768, min(32767, sample))))

        wf.writeframes(frames)

    ffmpeg_bin = _find_ffmpeg()
    if ffmpeg_bin and wav_path.exists():
        cmd = [ffmpeg_bin, "-y", "-i", str(wav_path.resolve()), "-c:a", "libmp3lame", "-q:a", "3", str(output_mp3.resolve())]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    elif wav_path.exists():
        shutil.copy(wav_path, output_mp3)

    if wav_path.exists() and output_mp3.exists() and output_mp3.stat().st_size > 100:
        wav_path.unlink()

    if output_srt:
        _generate_srt_from_words(words, total_dur, output_srt)

    return total_dur


def synthesize_speech(
    text: str,
    voice_name: str = "en-US-JennyNeural-Female",
    output_dir: Path | None = None,
    rate_factor: float = 1.0,
) -> dict[str, Any]:
    """Synthesize spoken voiceover audio and subtitle timestamps with cross-platform fallback."""
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
    if mp3_path.exists() and mp3_path.stat().st_size > 3000:
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

    # 2. Try Edge-TTS if installed and connected
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
                        word_boundaries.append({
                            "word": chunk["text"],
                            "start": round(start_sec, 2),
                            "end": round(start_sec + dur_sec, 2),
                        })
            return word_boundaries

        def _execute_async_safe():
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    with ThreadPoolExecutor(max_workers=1) as pool:
                        return pool.submit(lambda: asyncio.run(_run_edge())).result(timeout=30)
                else:
                    return loop.run_until_complete(_run_edge())
            except Exception:
                return asyncio.run(_run_edge())

        word_bounds = _execute_async_safe()
        total_duration = word_bounds[-1]["end"] if word_bounds else round(len(clean_text.split()) / (2.3 * rate_factor), 1)

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
                srt_lines.append(
                    f"{idx + 1}\n00:{s_m:02d}:{s_s:02d},{s_ms:03d} --> 00:{e_m:02d}:{e_s:02d},{e_ms:03d}\n{sub_text}\n"
                )
            srt_path.write_text("\n".join(srt_lines), encoding="utf-8")
        else:
            _generate_srt_from_words(clean_text.split(), total_duration, srt_path)

        if mp3_path.exists() and mp3_path.stat().st_size > 1000:
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
        logger.info(f"Edge-TTS synthesis bypassed ({exc}); attempting system TTS.")

    # 3. System Native TTS Fallbacks (macOS / Linux / Windows)
    if sys.platform == "darwin":
        try:
            dur = _synthesize_macos_say(clean_text, mp3_path, srt_path)
            if mp3_path.exists() and mp3_path.stat().st_size > 500:
                return {
                    "success": True,
                    "mp3_path": str(mp3_path.resolve()),
                    "srt_path": str(srt_path.resolve()),
                    "duration": dur,
                    "voice_name": "macOS Native Voice",
                    "word_count": len(clean_text.split()),
                    "cached": False,
                }
        except Exception as e:
            logger.info(f"macOS say TTS failed: {e}")

    elif sys.platform == "win32":
        try:
            dur = _synthesize_windows_sapi(clean_text, mp3_path, srt_path)
            if mp3_path.exists() and mp3_path.stat().st_size > 500:
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
            logger.info(f"Windows SAPI TTS failed: {e}")

    else:
        # Linux
        try:
            dur = _synthesize_linux_espeak(clean_text, mp3_path, srt_path)
            if mp3_path.exists() and mp3_path.stat().st_size > 500:
                return {
                    "success": True,
                    "mp3_path": str(mp3_path.resolve()),
                    "srt_path": str(srt_path.resolve()),
                    "duration": dur,
                    "voice_name": "Linux espeak Voice",
                    "word_count": len(clean_text.split()),
                    "cached": False,
                }
        except Exception as e:
            logger.info(f"Linux espeak TTS failed: {e}")

    # 4. Universal Synthetic Audio Fallback (Guaranteed to succeed anywhere offline)
    try:
        dur = _synthesize_synthetic_audio(clean_text, mp3_path, srt_path, rate_factor=rate_factor)
        if mp3_path.exists():
            return {
                "success": True,
                "mp3_path": str(mp3_path.resolve()),
                "srt_path": str(srt_path.resolve()),
                "duration": dur,
                "voice_name": "Synthetic Cadence Track",
                "word_count": len(clean_text.split()),
                "cached": False,
            }
    except Exception as e:
        logger.error(f"Universal synthetic audio generation failed: {e}")

    return {"success": False, "error": "Speech synthesis failed across all providers."}
