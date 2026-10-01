"""
Factify Shorts Automation Pipeline Runner
Topic: What Actually Happens to Fat When You Lose Weight?
"""

import os
import sys
import json
import subprocess

# Ensure UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from pipeline.health_mechanism_database import HEALTH_MECHANISM_TOPICS
from pipeline.fetch_viral_clips import fetch_scene_clip
from pipeline.factify_master_template import FactifyShortsTemplate

def run_pipeline(topic_id="what_actually_happens_to_fat"):
    print("=" * 70)
    print("🚀 FACTIFY SHORTS AUTOMATION PIPELINE")
    print(f"📌 Target Topic: {topic_id}")
    print("=" * 70)

    # 1. Locate topic in database
    topic = next((t for t in HEALTH_MECHANISM_TOPICS if t['id'] == topic_id), None)
    if not topic:
        print(f"❌ Topic '{topic_id}' not found in database!")
        sys.exit(1)

    print(f"📖 Title: {topic['title']}")
    print(f"🎙️ Narration Script ({len(topic['script'].split())} words):")
    print(f"   \"{topic['script']}\"")
    print("-" * 70)

    # 2. Fetch & Prepare Visual Scenes (3D Medical Animations & Real Footage)
    print("\n🎬 [Phase 1/3] Sourcing & Normalizing Visual Scenes (Hybrid CC & Fair Use)...")
    scene_video_paths = []
    for idx, sc in enumerate(topic['scenes']):
        sc_dest = f"temp/{topic['id']}_sc_{idx}.mp4"
        query = sc.get('query', '')
        src_vid = sc.get('source_video', None)
        start_sec = sc.get('start_sec', 2.0)
        dur = sc.get('duration', 5.0)

        # Clear old cached scene if needed
        if os.path.exists(sc_dest):
            try:
                os.remove(sc_dest)
            except Exception:
                pass

        c_crop = sc.get('custom_crop', None)
        print(f"  ▶️ [{idx+1}/{len(topic['scenes'])}] {sc['label']}")
        success = fetch_scene_clip(query, sc_dest, start_sec=start_sec, duration=dur, source_video=src_vid, custom_crop=c_crop)
        if success and os.path.exists(sc_dest):
            scene_video_paths.append(sc_dest)
        else:
            print(f"  ⚠️ Warning: Fallback applied for scene {idx+1}")

    if not scene_video_paths:
        print("❌ Error: No scenes were successfully fetched.")
        sys.exit(1)

    # 3. Assemble VidIQ SEO Package
    seo_data = topic.get('vidiq_seo', {})
    tags_list = seo_data.get('tags', [
        "science facts", "human body mechanism", "did you know", "medical animation 3d", "Factify Shorts"
    ])
    
    desc = topic.get('description')
    if not desc:
        desc = (
            f"{topic['title']}\n\n"
            f"Here is what ACTUALLY happens inside your body!\n\n"
            f"📖 The Mechanism:\n"
            f"{topic['script']}\n\n"
            f"Subscribe to @FactifyDailyShorts for mind-blowing science & body mechanisms every day!\n\n"
            f"#science #humanbody #health #3danimation #factify #shorts"
        )

    from pipeline.run_prime_time_automation import get_next_prime_time_slot
    target_slot = get_next_prime_time_slot()
    publish_at = None
    slot_label = None
    if target_slot:
        target_dt, slot_name = target_slot
        publish_at = target_dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        slot_label = slot_name
        print(f"🕒 Next Scheduled Prime Time Slot: {slot_name} ({publish_at})")

    metadata = {
        "title": topic['title'],
        "description": desc,
        "tags": tags_list,
        "tags_str": ", ".join(tags_list),
        "primary_keyword": seo_data.get('primary_keyword', topic['title']),
        "search_volume": seo_data.get('search_volume', 'Very High'),
        "competition": seo_data.get('competition', 'Low'),
        "publish_at": publish_at,
        "slot_name": slot_label
    }

    # 4. Master Template Render
    print("\n🎨 [Phase 2/3] Rendering Master Factify Short (6-Layer Architecture)...")
    template = FactifyShortsTemplate()
    output_filename = f"Factify_{topic_id}_Master.mp4"

    master_path = template.render_short(
        video_source_path=scene_video_paths,
        script_text=topic['script'],
        output_filename=output_filename,
        metadata=metadata,
        voice_rate='+3%'
    )

    print("\n✅ [Phase 3/3] Master Production Complete!")
    print(f"   📁 Master Video: {master_path}")
    print(f"   📄 VidIQ SEO:    {master_path.replace('.mp4', '_seo.json')}")
    print("=" * 70)

    # Launch Preview on Windows Desktop
    try:
        abs_master = os.path.abspath(master_path)
        print(f"🎬 Opening local preview: {abs_master}")
        subprocess.Popen(['powershell', '-Command', f'Start-Process "{abs_master}"'])
    except Exception as e:
        print(f"Note: Could not auto-launch player: {e}")

    # Dispatch to Telegram for Mobile Review & Approval
    try:
        from pipeline.telegram_service import send_preview
        seo_path = master_path.replace('.mp4', '_seo.json')
        print(f"📱 Dispatching preview to Telegram bot...")
        send_preview(master_path, seo_path, topic_id=topic_id)
    except Exception as e:
        print(f"Note: Telegram dispatch error: {e}")

    return master_path

if __name__ == '__main__':
    selected_id = sys.argv[1] if len(sys.argv) > 1 else "what_actually_happens_to_fat"
    run_pipeline(selected_id)

