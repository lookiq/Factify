import os
import sys
import json
from datetime import datetime
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)

METADATA_FILE = 'output/metadata.json'
VIDEO_FILE = 'output/factify_short_latest.mp4'
DATABASE_FILE = 'pipeline/topics_database.json'

def load_local_env():
    if os.path.exists('.env'):
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    if k not in os.environ:
                        os.environ[k.strip()] = v.strip()

def get_authenticated_service():
    load_local_env()
    client_id = os.environ.get('YOUTUBE_CLIENT_ID')
    client_secret = os.environ.get('YOUTUBE_CLIENT_SECRET')
    refresh_token = os.environ.get('YOUTUBE_REFRESH_TOKEN')

    if not (client_id and client_secret and refresh_token):
        print("ERROR: Missing YouTube OAuth credentials in environment variables or .env file.")
        print("Please ensure YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, and YOUTUBE_REFRESH_TOKEN are set.")
        sys.exit(1)

    credentials = Credentials(
        None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret
    )

    if not credentials.valid:
        print("Refreshing YouTube access token...")
        credentials.refresh(Request())

    return build('youtube', 'v3', credentials=credentials)

def mark_topic_used(topic_id):
    if os.path.exists(DATABASE_FILE):
        with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
            topics = json.load(f)
        for t in topics:
            if t['id'] == topic_id:
                t['used'] = True
                break
        with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
            json.dump(topics, f, indent=2)

def upload_video():
    if not os.path.exists(METADATA_FILE) or not os.path.exists(VIDEO_FILE):
        print("ERROR: Video or metadata file not found. Run build_short.py first.")
        sys.exit(1)

    with open(METADATA_FILE, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    privacy_status = os.environ.get('YOUTUBE_PRIVACY_STATUS', 'public')

    youtube = get_authenticated_service()

    body = {
        'snippet': {
            'title': metadata['title'],
            'description': metadata['description'],
            'tags': metadata.get('tags', []),
            'categoryId': metadata.get('category_id', '28')
        },
        'status': {
            'privacyStatus': privacy_status,
            'selfDeclaredMadeForKids': False
        }
    }

    print(f"Uploading '{metadata['title']}' to Factify Shorts channel...")
    media = MediaFileUpload(VIDEO_FILE, mimetype='video/mp4', resumable=True)

    request = youtube.videos().insert(
        part='snippet,status',
        body=body,
        media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploaded {int(status.progress() * 100)}%")

    video_id = response.get('id')
    video_url = f"https://www.youtube.com/shorts/{video_id}"
    print("\n" + "=" * 60)
    print("SUCCESS: Video uploaded successfully to Factify Shorts!")
    print(f"Shorts URL: {video_url}")
    print("=" * 60)

    mark_topic_used(metadata.get('id'))

    log_entry = f"[{datetime.now().isoformat()}] ID: {video_id} | Title: {metadata['title']} | URL: {video_url}\n"
    with open('upload_history.log', 'a', encoding='utf-8') as f:
        f.write(log_entry)

    return video_url

if __name__ == '__main__':
    upload_video()
