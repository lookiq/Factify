import os
import sys
import json
import subprocess
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)

SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.readonly'
]

auth_code = None

class OAuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if 'code' in params:
            auth_code = params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            html = """
            <!DOCTYPE html>
            <html>
            <head><title>Factify Shorts Connected</title></head>
            <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; text-align: center; padding: 60px; background: #0f172a; color: #f8fafc;">
                <div style="max-width: 500px; margin: auto; background: #1e293b; padding: 40px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.5);">
                    <h1 style="color: #22c55e; margin-bottom: 12px;">✅ Channel Connected!</h1>
                    <p style="font-size: 16px; color: #94a3b8; line-height: 1.5;">Your Factify Shorts YouTube channel has been authorized successfully.</p>
                    <p style="color: #64748b; font-size: 14px; margin-top: 24px;">You can now close this browser tab and return to the assistant.</p>
                </div>
            </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Missing authorization code in redirect.")

    def log_message(self, format, *args):
        return

def main():
    print("=" * 65, flush=True)
    print("Factify Shorts - YouTube OAuth Setup Helper", flush=True)
    print("=" * 65, flush=True)
    print("This script generates your YouTube Refresh Token so the pipeline", flush=True)
    print("can upload videos automatically to @FactifyDailyShorts.\n", flush=True)

    if not os.path.exists("client_secret.json"):
        print("ERROR: client_secret.json not found.", flush=True)
        sys.exit(1)

    flow = InstalledAppFlow.from_client_secrets_file(
        "client_secret.json",
        SCOPES,
        redirect_uri='http://localhost:8088/'
    )

    with open("client_secret.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        client_info = data.get("installed") or data.get("web", {})
        client_id = client_info.get("client_id", "")
        client_secret = client_info.get("client_secret", "")

    auth_url, state = flow.authorization_url(prompt='consent', access_type='offline')

    # Save link to file
    with open("AUTH_URL.txt", "w", encoding="utf-8") as f:
        f.write(auth_url)

    print("\n" + "=" * 65, flush=True)
    print("🔑 PLEASE AUTHORIZE YOUR YOUTUBE CHANNEL:", flush=True)
    print(auth_url, flush=True)
    print("=" * 65 + "\n", flush=True)

    # Automatically open browser
    try:
        subprocess.Popen(f'start "" "{auth_url}"', shell=True)
        print("Opening default browser...", flush=True)
    except Exception as e:
        print(f"Note: Could not auto-open browser ({e}). Please click the link above.", flush=True)

    print("Waiting for channel authorization in browser on http://localhost:8088/ ...", flush=True)

    httpd = HTTPServer(('127.0.0.1', 8088), OAuthHandler)
    while auth_code is None:
        httpd.handle_request()

    httpd.server_close()

    print("\nAuthorization code received! Exchanging for tokens...", flush=True)
    flow.fetch_token(code=auth_code)
    credentials = flow.credentials
    refresh_token = credentials.refresh_token

    if not refresh_token:
        print("WARNING: No refresh token returned. Ensure you select prompt='consent'.", flush=True)
    else:
        print("\n" + "=" * 65, flush=True)
        print("SUCCESS! Authorization Completed.", flush=True)
        print("=" * 65, flush=True)

        # Check connected channel name & handle
        try:
            youtube = build('youtube', 'v3', credentials=credentials)
            res = youtube.channels().list(part='snippet', mine=True).execute()
            if res.get('items'):
                item = res['items'][0]
                ch_title = item['snippet'].get('title', 'Unknown')
                ch_handle = item['snippet'].get('customUrl', 'N/A')
                ch_id = item.get('id', 'N/A')
                print(f"✅ Connected Channel Name : {ch_title}", flush=True)
                print(f"✅ Connected Handle       : {ch_handle}", flush=True)
                print(f"✅ Channel ID             : {ch_id}", flush=True)
                print("=" * 65, flush=True)
        except Exception as e:
            print(f"Could not fetch channel details: {e}", flush=True)

        # Save to local .env file preserving existing keys
        env_vars = {}
        if os.path.exists(".env"):
            with open(".env", "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        k, v = line.split('=', 1)
                        env_vars[k.strip()] = v.strip()

        env_vars["YOUTUBE_CLIENT_ID"] = client_id
        env_vars["YOUTUBE_CLIENT_SECRET"] = client_secret
        env_vars["YOUTUBE_REFRESH_TOKEN"] = refresh_token
        env_vars["YOUTUBE_PRIVACY_STATUS"] = "public"

        with open(".env", "w", encoding="utf-8") as f:
            for k, v in env_vars.items():
                f.write(f"{k}={v}\n")
        print("[OK] Saved credentials to local '.env' file!", flush=True)

        # Sync for office pipeline
        try:
            office_data_dir = os.path.join("office_production_pipeline", "data")
            if os.path.exists(office_data_dir):
                token_data = {
                    "access_token": credentials.token,
                    "refresh_token": credentials.refresh_token,
                    "scope": " ".join(credentials.scopes) if credentials.scopes else "",
                    "token_type": "Bearer",
                    "expiry_date": int(credentials.expiry.timestamp() * 1000) if credentials.expiry else None
                }
                with open(os.path.join(office_data_dir, "token.json"), "w", encoding="utf-8") as tf:
                    json.dump(token_data, tf, indent=2)
                print("[OK] Synced token with office_production_pipeline/data/token.json!", flush=True)
        except Exception as e:
            print(f"Note on office pipeline token: {e}", flush=True)

        print("\n🎉 Setup is 100% complete! You can now upload shorts automatically.", flush=True)

if __name__ == "__main__":
    main()
