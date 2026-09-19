import os
import sys
import json
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

def main():
    print("=" * 65)
    print("Factify Shorts - YouTube OAuth Setup Helper")
    print("=" * 65)
    print("This script generates your YouTube Refresh Token so the pipeline")
    print("can upload videos automatically to @FactifyDailyShorts.\n")

    client_id = ""
    client_secret = ""

    # Check if client_secret.json exists
    if os.path.exists("client_secret.json"):
        print("Found 'client_secret.json' in current directory!")
        flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
        with open("client_secret.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            client_info = data.get("installed") or data.get("web", {})
            client_id = client_info.get("client_id", "")
            client_secret = client_info.get("client_secret", "")
    else:
        print("Enter your Google Cloud OAuth credentials:")
        client_id = input("Enter Client ID: ").strip()
        client_secret = input("Enter Client Secret: ").strip()

        if not client_id or not client_secret:
            print("ERROR: Client ID and Client Secret cannot be empty.")
            sys.exit(1)

        client_config = {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost"]
            }
        }
        flow = InstalledAppFlow.from_client_config(client_config, SCOPES)

    print("\nOpening your browser for 1-time channel authorization...")
    credentials = flow.run_local_server(port=8088, prompt='consent', access_type='offline')

    refresh_token = credentials.refresh_token
    if not refresh_token:
        print("WARNING: No refresh token returned. Ensure you select prompt='consent'.")
    else:
        print("\n" + "=" * 65)
        print("SUCCESS! Your Credentials Have Been Generated:")
        print("=" * 65)
        print(f"YOUTUBE_CLIENT_ID     : {client_id}")
        print(f"YOUTUBE_CLIENT_SECRET : {client_secret}")
        print(f"YOUTUBE_REFRESH_TOKEN : {refresh_token}")
        print("=" * 65)

        # Save to local .env file (safely ignored by .gitignore)
        with open(".env", "w", encoding="utf-8") as f:
            f.write(f"YOUTUBE_CLIENT_ID={client_id}\n")
            f.write(f"YOUTUBE_CLIENT_SECRET={client_secret}\n")
            f.write(f"YOUTUBE_REFRESH_TOKEN={refresh_token}\n")
            f.write("YOUTUBE_PRIVACY_STATUS=public\n")
        print("\n[OK] Automatically saved credentials to local '.env' file!")
        print("If using GitHub Actions cloud, add these 3 values to:")
        print("GitHub Repo -> Settings -> Secrets and variables -> Actions")

if __name__ == "__main__":
    main()
