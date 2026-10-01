import os
import sys
import json
import time
import subprocess
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

def load_env():
    env_file = os.path.join(PROJECT_ROOT, '.env')
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    if k not in os.environ:
                        os.environ[k.strip()] = v.strip()

def get_telegram_creds():
    load_env()
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    return token, chat_id

def make_fast_mobile_preview(video_path):
    """Compresses video to ~4-5MB 720p for instant Telegram delivery"""
    preview_path = os.path.join(PROJECT_ROOT, 'temp', 'telegram_preview.mp4')
    os.makedirs(os.path.dirname(preview_path), exist_ok=True)

    cmd = [
        'ffmpeg', '-y', '-i', video_path,
        '-c:v', 'libx264', '-crf', '28', '-preset', 'faster',
        '-vf', 'scale=720:1280',
        '-c:a', 'aac', '-b:a', '96k',
        preview_path
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        if os.path.exists(preview_path) and os.path.getsize(preview_path) > 1000:
            return preview_path
    except Exception as e:
        print(f"Note: Could not compress fast preview ({e}), using original.")
    return video_path

def send_preview(video_path, metadata_path, topic_id=None):
    token, chat_id = get_telegram_creds()
    if not token or not chat_id:
        print("❌ ERROR: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in .env")
        return False

    if not os.path.exists(video_path):
        print(f"❌ ERROR: Video file not found: {video_path}")
        return False

    metadata = {}
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

    title = metadata.get('title', Path(video_path).stem)
    tags = metadata.get('tags', [])
    tags_preview = ", ".join(tags[:5]) + "..." if len(tags) > 5 else ", ".join(tags)
    sched_info = f"🕒 Scheduled For: {metadata.get('slot_name')}\n" if metadata.get('slot_name') else ""

    caption = (
        f"🎬 Factify Shorts — New Video Preview\n\n"
        f"📌 Title: {title}\n"
        f"{sched_info}\n"
        f"🏷️ Tags: {tags_preview}\n\n"
        f"📱 ভিডিওটি দেখে নিচের বাটনে ট্যাপ করুন:"
    )

    if not topic_id:
        # derive short key
        filename = Path(video_path).stem
        if "what_actually_happens_to_fat" in filename:
            topic_id = "fat"
        elif "root_canal" in filename:
            topic_id = "root_canal"
        elif "heart_stent" in filename:
            topic_id = "heart_stent"
        else:
            topic_id = filename[:20]

    # Max 64 bytes callback_data
    cb_appr = f"appr:{topic_id}"
    cb_rej = f"rej:{topic_id}"

    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "🚀 Approve & Upload to YouTube", "callback_data": cb_appr}
            ],
            [
                {"text": "❌ Reject / Next Topic", "callback_data": cb_rej}
            ]
        ]
    }

    # Generate lightweight preview for lightning-fast Telegram upload
    print("⚡ Generating fast mobile preview for Telegram...")
    upload_target = make_fast_mobile_preview(video_path)

    url = f"https://api.telegram.org/bot{token}/sendVideo"
    print(f"📤 Uploading preview to Telegram chat {chat_id} ({os.path.getsize(upload_target)/(1024*1024):.1f} MB)...")

    with open(upload_target, 'rb') as vf:
        files = {'video': vf}
        data = {
            'chat_id': chat_id,
            'caption': caption,
            'reply_markup': json.dumps(reply_markup),
            'supports_streaming': True
        }
        res = requests.post(url, data=data, files=files, timeout=60)

    try:
        resp_json = res.json()
        if resp_json.get('ok'):
            print("✅ Successfully sent video preview with interactive buttons to Telegram!")
            return True
        else:
            print(f"❌ Telegram API Error: {resp_json}")
            return False
    except Exception as e:
        print(f"❌ Failed to parse response: {e}")
        return False

def answer_callback(token, callback_query_id, text=None):
    url = f"https://api.telegram.org/bot{token}/answerCallbackQuery"
    payload = {"callback_query_id": callback_query_id}
    if text:
        payload["text"] = text
        payload["show_alert"] = True
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception:
        pass

def send_message(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception:
        pass

def resolve_master_paths(topic_key):
    """Map short topic key to actual full master video and metadata files"""
    output_dir = os.path.join(PROJECT_ROOT, 'output')
    candidates = os.listdir(output_dir) if os.path.exists(output_dir) else []

    if topic_key == "fat":
        search = "what_actually_happens_to_fat"
    elif topic_key == "root_canal":
        search = "root_canal"
    elif topic_key == "heart_stent":
        search = "heart_stent"
    else:
        search = topic_key

    v_file = None
    m_file = None
    for f in candidates:
        if search in f and f.endswith('_Master.mp4'):
            v_file = os.path.join(output_dir, f)
        if search in f and f.endswith('_Master_seo.json'):
            m_file = os.path.join(output_dir, f)

    if not v_file or not m_file:
        # Fallback to latest
        masters = [os.path.join(output_dir, f) for f in candidates if f.endswith('_Master.mp4')]
        if masters:
            v_file = sorted(masters, key=os.path.getmtime)[-1]
            m_file = v_file.replace('.mp4', '_seo.json')

    return v_file, m_file

def run_listener():
    token, chat_id = get_telegram_creds()
    if not token or not chat_id:
        print("❌ Cannot run listener: Missing credentials in .env")
        return

    print("🤖 Telegram Decision Listener ACTIVE. Polling for actions...")
    from pipeline.upload_to_youtube import upload_video

    offset = 0
    # Clean previous pending updates
    try:
        init_res = requests.get(f"https://api.telegram.org/bot{token}/getUpdates?offset=-1", timeout=10).json()
        updates = init_res.get('result', [])
        if updates:
            offset = updates[-1]['update_id'] + 1
    except Exception:
        pass

    while True:
        try:
            url = f"https://api.telegram.org/bot{token}/getUpdates?offset={offset}&timeout=20"
            res = requests.get(url, timeout=30)
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
                        topic_key = data.split(':', 1)[1]
                        v_path, m_path = resolve_master_paths(topic_key)

                        answer_callback(token, cb_id, "🚀 Approved! Uploading Master 1080p Short to YouTube...")
                        send_message(token, chat_id, f"⏳ Uploading Master Short to YouTube Channel...\nPlease wait a few seconds!")

                        try:
                            # Check if scheduled
                            sched_str = "LIVE"
                            if os.path.exists(m_path):
                                with open(m_path, 'r', encoding='utf-8') as mf:
                                    m_data = json.load(mf)
                                    if m_data.get('slot_name'):
                                        sched_str = f"SCHEDULED for {m_data['slot_name']}"

                            video_url = upload_video(v_path, m_path)
                            send_message(
                                token,
                                chat_id,
                                f"🎉 UPLOAD SUCCESSFUL!\n\n"
                                f"🕒 Status: {sched_str}\n"
                                f"📺 Video URL: {video_url}\n\n"
                                f"✨ YouTube will publish it automatically at the prime time slot!"
                            )
                        except Exception as e:
                            send_message(token, chat_id, f"❌ Upload Failed: {e}")

                    elif data.startswith('rej:'):
                        topic_key = data.split(':', 1)[1]
                        answer_callback(token, cb_id, "❌ Video Rejected. Moving to next topic.")
                        send_message(token, chat_id, f"❌ Video '{topic_key}' rejected. Standing by for next generation.")

            time.sleep(1)
        except Exception as e:
            print(f"Listener loop error: {e}")
            time.sleep(3)

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'listen':
        run_listener()
    elif len(sys.argv) > 2:
        send_preview(sys.argv[1], sys.argv[2])
    else:
        v = os.path.join(PROJECT_ROOT, "output", "Factify_what_actually_happens_to_fat_Master.mp4")
        m = os.path.join(PROJECT_ROOT, "output", "Factify_what_actually_happens_to_fat_Master_seo.json")
        send_preview(v, m)
