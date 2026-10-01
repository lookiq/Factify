import os
import sys
import json
import time
import requests

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)

TOKEN = "***REVOKED***"

print("Waiting for user to click START on @factify_jewel_shorts_bot...")
chat_id = None
start_time = time.time()

while time.time() - start_time < 120:
    try:
        r = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates", timeout=10)
        res = r.json().get('result', [])
        for u in res:
            if 'message' in u:
                chat_id = u['message']['chat']['id']
                user_name = u['message']['chat'].get('first_name', 'User')
                print(f"✅ FOUND USER: {user_name} (Chat ID: {chat_id})")
                break
        if chat_id:
            break
    except Exception as e:
        print(f"Polling error: {e}")
    time.sleep(2)

if chat_id:
    # Save to .env
    with open('.env', 'r', encoding='utf-8') as f:
        env_content = f.read()
    if 'TELEGRAM_CHAT_ID=' in env_content:
        import re
        env_content = re.sub(r'TELEGRAM_CHAT_ID=.*', f'TELEGRAM_CHAT_ID={chat_id}', env_content)
    else:
        env_content += f"\nTELEGRAM_CHAT_ID={chat_id}\n"
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)
    print(f"✅ Saved TELEGRAM_CHAT_ID={chat_id} to .env")

    # Send first preview video!
    from pipeline.telegram_service import send_preview
    v = "output/Factify_what_actually_happens_to_fat_Master.mp4"
    m = "output/Factify_what_actually_happens_to_fat_Master_seo.json"
    print(f"Sending master video to Telegram ({v})...")
    success = send_preview(v, m)
    if success:
        print("MASTER VIDEO SENT TO YOUR TELEGRAM!")
else:
    print("Still waiting for user to click Start...")
