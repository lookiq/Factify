import os
import sys
import json
import time
from pathlib import Path

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Setup UTF-8 encoding
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)

from pipeline.run_automation import run_pipeline
from pipeline.telegram_service import get_telegram_creds, send_message, send_autopilot_notification
from pipeline.upload_to_youtube import upload_video

def is_topic_footage_available(topic):
    """Check if all required local footage for this topic exists in assets or temp"""
    for sc in topic.get('scenes', []):
        src = sc.get('source_video')
        if not src:
            return False
        candidates = [
            src,
            os.path.join('pipeline', 'assets', 'footage', os.path.basename(src)),
            os.path.join('temp', os.path.basename(src))
        ]
        if not any(os.path.exists(c) and os.path.getsize(c) > 50000 for c in candidates):
            return False
    return True

def select_next_autopilot_topic(forced_id=None):
    from pipeline.health_mechanism_database import HEALTH_MECHANISM_TOPICS

    if forced_id:
        match = next((t for t in HEALTH_MECHANISM_TOPICS if t['id'] == forced_id), None)
        if match:
            return match['id']

    used_content = ""
    if os.path.exists("upload_history.log"):
        with open("upload_history.log", "r", encoding="utf-8") as f:
            used_content = f.read()

    # Prioritize topics with verified 1080p 3D footage
    verified_topics = [t for t in HEALTH_MECHANISM_TOPICS if is_topic_footage_available(t)]

    print(f"🔍 Found {len(verified_topics)} verified 3D medical topics with local footage:")
    for vt in verified_topics:
        status = "ALREADY POSTED" if (vt['id'] in used_content or vt['title'] in used_content) else "READY FOR POST"
        print(f"   • {vt['id']} — {vt['title']} [{status}]")

    # Pick first unposted verified topic
    for t in verified_topics:
        if t['id'] not in used_content and t['title'] not in used_content:
            return t['id']

    # Fallback to any unposted topic
    for t in HEALTH_MECHANISM_TOPICS:
        if t['id'] not in used_content and t['title'] not in used_content:
            return t['id']

    # If all posted, cycle through verified topics
    return verified_topics[0]['id'] if verified_topics else "heart_stent_procedure"

def run_cloud_pipeline(topic_id=None):
    print("=" * 70)
    print("🚀 FACTIFY SHORTS — 100% AUTONOMOUS ZERO-TOUCH CLOUD ENGINE")
    print("=" * 70)

    token, chat_id = get_telegram_creds()
    if not token or not chat_id:
        print("❌ CRITICAL: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing from environment / secrets!")
        sys.exit(1)

    # 1. Autonomous Topic Selection
    chosen_topic_id = select_next_autopilot_topic(topic_id)
    print(f"\n🎬 Selected Topic for Autonomous Production: {chosen_topic_id}")

    # 2. Render Master Short (suppressing manual preview buttons)
    master_path = run_pipeline(chosen_topic_id, notify_telegram=False)
    seo_path = master_path.replace('.mp4', '_seo.json')

    if not os.path.exists(master_path):
        err_msg = f"❌ Production failed: Master video not found at {master_path}"
        print(err_msg)
        send_message(token, chat_id, err_msg)
        sys.exit(1)

    # 3. Direct Scheduled Upload to YouTube Channel
    print("\n📤 Uploading and Scheduling Short to YouTube Channel (USA Prime Time)...")
    try:
        video_url = upload_video(master_path, seo_path)
    except Exception as e:
        err_msg = f"❌ YouTube Upload Error for topic '{chosen_topic_id}': {e}"
        print(err_msg)
        send_message(token, chat_id, err_msg)
        sys.exit(1)

    # 4. Notify User via Telegram with Finished Video & YouTube Link (Zero Clicks Required)
    print("\n📱 Sending celebratory completion report with video to Telegram...")
    send_autopilot_notification(master_path, seo_path, video_url)

    print("\n" + "=" * 70)
    print(f"🎉 100% AUTONOMOUS CYCLE COMPLETE!")
    print(f"   Video URL: {video_url}")
    print("=" * 70)

if __name__ == '__main__':
    selected = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else None
    run_cloud_pipeline(selected)
