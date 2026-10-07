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
from pipeline.telegram_service import get_telegram_creds, send_message, send_delivery_package

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

    print("⚠️ All verified topics with local 3D footage have already been posted!")
    return None

def run_cloud_pipeline(topic_id=None):
    print("=" * 70)
    print("🚀 FACTIFY SHORTS — CLOUD BUILD & TELEGRAM DELIVERY")
    print("=" * 70)

    token, chat_id = get_telegram_creds()
    if not token or not chat_id:
        print("❌ CRITICAL: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing from environment / secrets!")
        sys.exit(1)

    # 1. Autonomous Topic Selection (STRICT: only verified 3D footage allowed)
    chosen_topic_id = select_next_autopilot_topic(topic_id)
    if not chosen_topic_id:
        warn_msg = (
            "⚠️ [Factify Alert] All verified 3D medical topics have already been posted! "
            "Autopilot safely paused to prevent uploading videos without real 3D video clips. "
            "Please add new verified topics with 3D footage."
        )
        print(warn_msg)
        send_message(token, chat_id, warn_msg)
        sys.exit(0)

    print(f"\n🎬 Selected Topic for Autonomous Production: {chosen_topic_id}")

    # 2. Render Master Short (suppressing manual preview buttons)
    master_path = run_pipeline(chosen_topic_id, notify_telegram=False)
    seo_path = master_path.replace('.mp4', '_seo.json')

    if not os.path.exists(master_path):
        err_msg = f"❌ Production failed: Master video not found at {master_path}"
        print(err_msg)
        send_message(token, chat_id, err_msg)
        sys.exit(1)

    # 3. Telegram-only delivery (NO YouTube auto-upload — user publishes manually)
    print("\n📱 Delivering finished Short + full metadata package to Telegram...")
    ok = send_delivery_package(master_path, seo_path, topic_id=chosen_topic_id)
    if not ok:
        err_msg = f"❌ Telegram delivery failed for topic '{chosen_topic_id}'"
        print(err_msg)
        send_message(token, chat_id, err_msg)
        sys.exit(1)

    print("\n" + "=" * 70)
    print("🎉 DELIVERY COMPLETE — video + upload package sent to Telegram!")
    print("   No auto-upload: publish manually from the Telegram package.")
    print("=" * 70)

if __name__ == '__main__':
    selected = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else None
    run_cloud_pipeline(selected)

