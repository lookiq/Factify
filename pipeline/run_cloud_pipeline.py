import os
import sys
import json
import time
import requests
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
from pipeline.telegram_service import get_telegram_creds, send_message, answer_callback
from pipeline.upload_to_youtube import upload_video

def run_cloud_pipeline(topic_id=None, wait_minutes=45):
    print("=" * 70)
    print("🚀 FACTIFY SHORTS — GITHUB ACTIONS CLOUD AUTOMATION ENGINE")
    print("=" * 70)

    token, chat_id = get_telegram_creds()
    if not token or not chat_id:
        print("❌ CRITICAL: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing from environment / secrets!")
        sys.exit(1)

    # 1. Select or pick next topic
    if not topic_id:
        from pipeline.health_mechanism_database import HEALTH_MECHANISM_TOPICS
        # Look for unused topics
        used_topics = []
        if os.path.exists("upload_history.log"):
            with open("upload_history.log", "r", encoding="utf-8") as f:
                used_topics = f.read()

        chosen = None
        for k, v in HEALTH_MECHANISM_TOPICS.items():
            if k not in used_topics and v.get('ready_for_production', False):
                chosen = k
                break
        topic_id = chosen or "what_actually_happens_to_fat"

    print(f"🎬 Running production for topic: {topic_id}")
    master_path = run_pipeline(topic_id)
    seo_path = master_path.replace('.mp4', '_seo.json')

    # Read metadata for scheduling info
    with open(seo_path, 'r', encoding='utf-8') as f:
        meta = json.load(f)

    slot_info = meta.get('slot_name', 'Next Prime Slot')
    print(f"\n📱 Preview has been dispatched to Telegram.")
    print(f"⏳ Waiting up to {wait_minutes} minutes for mobile approval from Telegram...")

    send_message(
        token,
        chat_id,
        f"🔔 *Action Required on Mobile:*\n\n"
        f"Cloud Runner is online! Please watch the preview above and tap *Approve* within {wait_minutes} minutes to schedule for `{slot_info}`."
    )

    # Wait / listen for callback query
    start_time = time.time()
    max_seconds = wait_minutes * 60
    offset = 0

    try:
        init_res = requests.get(f"https://api.telegram.org/bot{token}/getUpdates?offset=-1", timeout=10).json()
        updates = init_res.get('result', [])
        if updates:
            offset = updates[-1]['update_id'] + 1
    except Exception:
        pass

    approved = False
    rejected = False

    while (time.time() - start_time) < max_seconds:
        try:
            url = f"https://api.telegram.org/bot{token}/getUpdates?offset={offset}&timeout=15"
            res = requests.get(url, timeout=20)
            if res.status_code != 200:
                time.sleep(3)
                continue

            updates = res.json().get('result', [])
            for update in updates:
                offset = update['update_id'] + 1

                if 'callback_query' in update:
                    cb = update['callback_query']
                    cb_id = cb['id']
                    data = cb.get('data', '')

                    if data.startswith('appr:'):
                        approved = True
                        answer_callback(token, cb_id, "🚀 Approved! Uploading Scheduled Short to YouTube...")
                        send_message(token, chat_id, f"⏳ Uploading Master Short to YouTube Channel as SCHEDULED...\nPlease wait a few seconds!")

                        video_url = upload_video(master_path, seo_path)
                        send_message(
                            token,
                            chat_id,
                            f"🎉 UPLOAD SUCCESSFUL!\n\n"
                            f"🕒 Status: SCHEDULED for {slot_info}\n"
                            f"📺 Video URL: {video_url}\n\n"
                            f"✨ YouTube will publish it automatically at prime time!"
                        )
                        break

                    elif data.startswith('rej:'):
                        rejected = True
                        answer_callback(token, cb_id, "❌ Video Rejected.")
                        send_message(token, chat_id, f"❌ Video '{topic_id}' was rejected. Exiting without publishing.")
                        break

            if approved or rejected:
                break

            time.sleep(2)
        except Exception as e:
            print(f"Listener error: {e}")
            time.sleep(3)

    if not approved and not rejected:
        print(f"⏰ Timeout reached ({wait_minutes} mins). No decision received.")
        send_message(
            token,
            chat_id,
            f"⏰ *Approval Window Expired:*\n"
            f"No response was received within {wait_minutes} minutes. The video has NOT been uploaded."
        )

    print("🏁 Cloud Pipeline Complete.")

if __name__ == '__main__':
    selected = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else None
    run_cloud_pipeline(selected)
