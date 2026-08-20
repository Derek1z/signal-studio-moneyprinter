import io
import os
import sys
from pathlib import Path

# Fix console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent))

print("========================================")
print("  SIGNAL STUDIO END-TO-END TEST SUITE   ")
print("========================================")

# 1. Test AI Providers
print("\n[1/8] Testing LLM Providers & Council Architecture...")
from studio.ai_providers import DemoLLMProvider, OpenAILLMProvider, get_llm_provider

demo_llm = DemoLLMProvider()
topics = demo_llm.generate_topics("Productivity", "Creators", "High Reach")
assert len(topics) >= 3
print(f"[OK] Demo LLM generated {len(topics)} topics.")

proposals, win_idx, reasoning = demo_llm.run_council("Automated Video Systems", "AI", "Engineers")
assert len(proposals) == 3
print(f"[OK] Editorial Council generated {len(proposals)} advisor proposals. Winner: #{win_idx} ({reasoning})")

# 2. Test Hooks
print("\n[2/8] Testing Viral Hook A/B Lab...")
from studio.hooks import generate_hook_variations, replace_script_hook

hooks = generate_hook_variations("AI productivity systems", "creators", llm_provider=demo_llm)
assert len(hooks) == 5
print(f"[OK] Generated {len(hooks)} hook archetypes:")
for h in hooks:
    print(f"  • [{h['archetype']}] {h['tag']}: \"{h['hook']}\" ({h['hold_rate']}% Hold Rate)")

test_script = "Old hook. This is the body with 3.5x leverage and Dr. Smith's study. And this is the end."
new_script = replace_script_hook(test_script, hooks[0]["hook"])
assert hooks[0]["hook"] in new_script
print("[OK] Script hook replacement passed!")

# 3. Test Sentence Splitting & Retention Science
print("\n[3/8] Testing Retention Pacing & Sentence Segmentation...")
from studio.retention import analyze_retention, split_into_sentences

sample_text = "I tested 3.5 tools vs. Dr. Watson's approach. It worked! The result was 10x faster."
sentences = split_into_sentences(sample_text)
assert len(sentences) == 3, f"Expected 3 sentences, got {len(sentences)}: {sentences}"
print(f"[OK] Protected sentence splitter handled decimals & abbreviations correctly: {sentences}")

ret_audit = analyze_retention(new_script)
assert "score" in ret_audit and "pacing_verdict" in ret_audit
print(f"[OK] Retention audit completed: Score={ret_audit['score']}/100, Grade={ret_audit['grade']}")

# 4. Test Storyboard & Scene Segmentation
print("\n[4/8] Testing Scene Storyboard Timeline...")
from studio.storyboard import compile_storyboard_to_broll_terms, segment_script_into_scenes

scenes = segment_script_into_scenes(new_script, target_clip_duration_sec=5)
assert len(scenes) >= 1
print(f"[OK] Segmented script into {len(scenes)} visual scenes:")
for sc in scenes:
    print(f"  • SCENE {sc['scene_idx']:02d} [{sc['time_label']}]: {sc['visual_concept']} (Query: {sc['broll_query']})")

broll_terms = compile_storyboard_to_broll_terms(scenes)
assert len(broll_terms) > 0
print(f"[OK] Compiled B-roll search terms: {broll_terms}")

# 5. Test SVG Thumbnail Generation
print("\n[5/8] Testing Vector SVG Thumbnail Canvas & AI Prompt Generator...")
from studio.thumbnails import generate_ai_image_prompt, generate_thumbnail_svg

svg = generate_thumbnail_svg(
    headline="THE 7-MINUTE AI WORKFLOW",
    subtitle="EXPERIMENT",
    badge="AI × HUMAN",
    aspect_ratio="16:9",
    theme="emerald",
)
assert "<svg" in svg and "</svg>" in svg
print("[OK] SVG Thumbnail successfully generated (Valid SVG markup).")

prompt_ai = generate_ai_image_prompt("The 7-Minute AI Workflow", "THE 7-MINUTE AI WORKFLOW")
assert "YouTube thumbnail background" in prompt_ai
print("[OK] AI Image Prompt generated successfully.")

# 6. Test Social Packaging & Chapters
print("\n[6/8] Testing Social Packaging, Chapters & MoneyPrinter Export...")
from studio.social import export_moneyprinter_payload, generate_social_package

soc = generate_social_package(
    topic="The 7-Minute AI Workflow",
    script=new_script,
    niche="AI Productivity",
    research_claims=[],
    title="The 7-Minute AI Workflow I Actually Kept",
)
assert "youtube_description" in soc and "chapters" in soc
print(f"[OK] Generated YouTube Description & {len(soc['chapters'])} Chapters.")

mp_payload = export_moneyprinter_payload("The 7-Minute AI Workflow", new_script)
assert "video_subject" in mp_payload and "video_script" in mp_payload
print("[OK] Validated MoneyPrinterTurbo VideoParams payload exported successfully.")

# 7. Test Live Video Simulator Markup
print("\n[7/8] Testing Live HTML5 Video Simulator...")
from studio.simulator import render_live_video_simulator

sim_html = render_live_video_simulator(scenes=scenes, title="Test Video Preview")
assert "<!DOCTYPE html>" in sim_html and "karaokeBox" in sim_html
print("[OK] HTML5 Video Simulator code rendered successfully with karaoke events.")

# 8. Test Video Rendering Pipeline
print("\n[8/8] Testing Video Rendering Engine & Asset Bundler...")
from studio.renderer import render_video_pipeline

out_dir = Path(__file__).parent / "studio_outputs" / "test_run"
out_dir.mkdir(parents=True, exist_ok=True)

success, msg, out_path = render_video_pipeline(
    topic="The 7-Minute AI Workflow",
    script=new_script,
    settings={
        "voice_name": "en-US-JennyNeural-Female",
        "voice_rate": 1.0,
        "video_aspect": "9:16",
        "video_clip_duration": 4,
        "visual_theme": "cyber_matrix",
        "video_terms": broll_terms,
    },
    output_dir=out_dir,
)
assert success is True
assert out_path is not None and Path(out_path).exists()
print(f"[OK] Render Result: success={success}")
print(f"     Message: {msg}")
print(f"     Output Path: {out_path}")
print(f"     File Size: {Path(out_path).stat().st_size:,} bytes")

print("\n========================================")
print("  ALL 8/8 TESTS COMPLETED SUCCESSFULLY! 🎉  ")
print("========================================")
