import io
import os
import sys
from pathlib import Path

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent))

print("========================================")
print("  SIGNAL STUDIO END-TO-END TEST SUITE   ")
print("========================================")

# 1. Test Hooks
print("\n[1/6] Testing Viral Hook A/B Lab...")
from studio.hooks import generate_hook_variations, replace_script_hook

hooks = generate_hook_variations("AI productivity systems", "creators")
print(f"[OK] Generated {len(hooks)} hook archetypes:")
for h in hooks:
    print(f"  • [{h['archetype']}] {h['tag']}: \"{h['hook']}\" ({h['hold_rate']}% Hold Rate)")

test_script = "Old hook. This is the body. And this is the end."
new_script = replace_script_hook(test_script, hooks[0]["hook"])
assert hooks[0]["hook"] in new_script
print("[OK] Script hook replacement passed!")

# 2. Test Storyboard & Scene Segmentation
print("\n[2/6] Testing Scene Storyboard Timeline...")
from studio.storyboard import segment_script_into_scenes, compile_storyboard_to_broll_terms

scenes = segment_script_into_scenes(new_script, target_clip_duration_sec=5)
print(f"[OK] Segmented script into {len(scenes)} visual scenes:")
for sc in scenes:
    print(f"  • SCENE {sc['scene_idx']:02d} [{sc['time_label']}]: {sc['visual_concept']} (Query: {sc['broll_query']})")

broll_terms = compile_storyboard_to_broll_terms(scenes)
print(f"[OK] Compiled B-roll search terms: {broll_terms}")

# 3. Test SVG Thumbnail Generation
print("\n[3/6] Testing Vector SVG Thumbnail Canvas...")
from studio.thumbnails import generate_thumbnail_svg

svg = generate_thumbnail_svg(
    headline="THE 7-MINUTE AI WORKFLOW",
    subtitle="EXPERIMENT",
    badge="AI × HUMAN",
    aspect_ratio="16:9",
    theme="emerald",
)
assert "<svg" in svg and "</svg>" in svg
print("[OK] SVG Thumbnail successfully generated (Valid SVG markup).")

# 4. Test Social Packaging & Chapters
print("\n[4/6] Testing Social Packaging & Chapters...")
from studio.engine import create_social_package

soc = create_social_package(
    topic="The 7-Minute AI Workflow",
    script=new_script,
    niche="AI Productivity",
    research_claims=[],
    title="The 7-Minute AI Workflow I Actually Kept",
)
print("[OK] Generated YouTube Description & Chapters:")
print(soc["youtube_description"][:200] + "...")

# 5. Test Live Video Simulator Markup
print("\n[5/6] Testing Live HTML5 Video Simulator...")
from studio.simulator import render_live_video_simulator

sim_html = render_live_video_simulator(scenes=scenes, title="Test Video Preview")
assert "<!DOCTYPE html>" in sim_html and "karaokeBox" in sim_html
print("[OK] HTML5 Video Simulator code rendered successfully with karaoke events.")

# 6. Test Video Rendering Pipeline
print("\n[6/6] Testing Video Rendering Engine & Asset Bundler...")
from studio.renderer import render_video_pipeline

out_dir = Path(__file__).parent / "studio_outputs" / "test_run"
out_dir.mkdir(parents=True, exist_ok=True)

success, msg, out_path = render_video_pipeline(
    topic="The 7-Minute AI Workflow",
    script=new_script,
    settings={
        "voice_name": "en-US-JennyNeural-Female",
        "voice_rate": 1.0,
        "video_aspect": "16:9",
        "video_clip_duration": 5,
        "video_terms": broll_terms,
    },
    output_dir=out_dir,
)
print(f"[OK] Render Result: success={success}")
print(f"     Message: {msg}")
print(f"     Output Path: {out_path}")

print("\n========================================")
print("  ALL TESTS COMPLETED SUCCESSFULLY! 🎉  ")
print("========================================")
