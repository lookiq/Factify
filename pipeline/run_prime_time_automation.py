import os
import sys
import json
import subprocess
from datetime import datetime, timezone, timedelta

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)

# USA Prime Time Targets in UTC (EDT is UTC-4 in September, delayed by 15 mins):
# 1. US Morning Commute: 08:15 AM EDT -> 12:15 UTC (06:15 PM BST)
# 2. US Lunch Break: 12:45 PM EDT -> 16:45 UTC (10:45 PM BST)
# 3. US Evening Peak: 06:45 PM EDT -> 22:45 UTC (04:45 AM BST next day)
# 4. US Late Night / West Coast: 10:15 PM EDT -> 02:15 UTC (08:15 AM BST next day)
PRIME_SLOTS_UTC = [
    {"name": "US Morning Commute (8:15 AM EDT)", "hour": 12, "minute": 15},
    {"name": "US Lunch Peak (12:45 PM EDT)", "hour": 16, "minute": 45},
    {"name": "US Evening Peak (6:45 PM EDT)", "hour": 22, "minute": 45},
    {"name": "US Night Owl / West Coast (10:15 PM EDT)", "hour": 2, "minute": 15},
]

def get_next_prime_time_slot():
    now_utc = datetime.now(timezone.utc)
    candidates = []

    for day_offset in [0, 1]:
        base_date = now_utc.date() + timedelta(days=day_offset)
        for s in PRIME_SLOTS_UTC:
            target_dt = datetime(
                base_date.year, base_date.month, base_date.day,
                s["hour"], s["minute"], 0, tzinfo=timezone.utc
            )
            # If at least 15 minutes in the future
            if target_dt > now_utc + timedelta(minutes=15):
                candidates.append((target_dt, s["name"]))

    candidates.sort(key=lambda x: x[0])
    return candidates[0] if candidates else None

def run_automation(schedule_mode=True):
    print("=" * 65)
    print("   🚀 FACTIFY SHORTS - USA PRIME TIME AUTOMATION ENGINE")
    print("=" * 65)

    now_utc = datetime.now(timezone.utc)
    now_bst = now_utc + timedelta(hours=6)
    now_edt = now_utc - timedelta(hours=4)
    print(f"Current Time:")
    print(f"  - Local (BST): {now_bst.strftime('%Y-%m-%d %I:%M %p')}")
    print(f"  - USA (EDT):   {now_edt.strftime('%Y-%m-%d %I:%M %p')}")
    print(f"  - UTC:         {now_utc.strftime('%Y-%m-%d %H:%M UTC')}")
    print("-" * 65)

    target_slot = get_next_prime_time_slot()
    if target_slot:
        target_dt, slot_name = target_slot
        target_edt = target_dt - timedelta(hours=4)
        target_bst = target_dt + timedelta(hours=6)
        iso_publish_at = target_dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        print(f"🎯 Target Prime Slot: {slot_name}")
        print(f"   - USA Broadcast:  {target_edt.strftime('%I:%M %p EDT (%b %d)')}")
        print(f"   - Local Watch:    {target_bst.strftime('%I:%M %p BST (%b %d)')}")
        print(f"   - Scheduled ISO:  {iso_publish_at}")
    else:
        iso_publish_at = None
        print("⚡ No upcoming scheduled slot found, will publish live immediately!")

    print("-" * 65)
    print("\n[Step 1/2] Generating Video (Ultra 1080p + Radium Subtitles + Option A Watermark)...")

    # Run build_short.py
    build_cmd = [sys.executable, "pipeline/build_short.py"]
    res = subprocess.run(build_cmd)
    if res.returncode != 0:
        print("\n❌ ERROR: Video generation failed.")
        sys.exit(1)

    # Attach scheduled publish time if in schedule_mode
    metadata_path = "output/metadata.json"
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        
        if schedule_mode and iso_publish_at:
            meta['publish_at'] = iso_publish_at
        else:
            meta.pop('publish_at', None)

        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)

    print("\n[Step 2/2] Uploading to Factify Shorts Channel...")
    upload_cmd = [sys.executable, "pipeline/upload_to_youtube.py"]
    res_upload = subprocess.run(upload_cmd)
    if res_upload.returncode != 0:
        print("\n❌ ERROR: YouTube upload failed.")
        sys.exit(1)

    print("\n" + "=" * 65)
    if schedule_mode and iso_publish_at:
        print(f"🎉 SUCCESS! Short is scheduled for USA Prime Time: {target_edt.strftime('%I:%M %p EDT')}")
    else:
        print("🎉 SUCCESS! Short is LIVE on YouTube!")
    print("=" * 65)

if __name__ == '__main__':
    # Default to schedule mode for prime time
    run_automation(schedule_mode=True)
