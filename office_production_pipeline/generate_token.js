const fs = require('fs');
const path = require('path');
const http = require('http');
const { google } = require('googleapis');
const { exec } = require('child_process');

const CLIENT_SECRET_FILE = path.join(__dirname, 'client_secret.json');
const TOKEN_FILE = path.join(__dirname, 'data', 'token.json');
const SCOPES = [
  'https://www.googleapis.com/auth/youtube.upload',
  'https://www.googleapis.com/auth/youtube.readonly'
];

async function main() {
  if (!fs.existsSync(CLIENT_SECRET_FILE)) {
    console.error("ERROR: client_secret.json not found in " + __dirname);
    process.exit(1);
  }

  const content = JSON.parse(fs.readFileSync(CLIENT_SECRET_FILE, 'utf-8'));
  const credentials = content.installed || content.web;
  const { client_secret, client_id } = credentials;

  const redirectUri = 'http://localhost:3000';
  const oauth2Client = new google.auth.OAuth2(client_id, client_secret, redirectUri);

  const authUrl = oauth2Client.generateAuthUrl({
    access_type: 'offline',
    scope: SCOPES,
    prompt: 'consent'
  });

  console.log("==================================================================");
  console.log("🔑 YOUTUBE 1-TIME AUTHORIZATION FOR FACTIFY SHORTS");
  console.log("==================================================================");
  console.log("\nOpening your default browser to authorize your YouTube channel...");
  console.log("Auth URL:\n" + authUrl + "\n");

  const server = http.createServer(async (req, res) => {
    try {
      if (req.url.startsWith('/?code=') || req.url.includes('code=')) {
        const urlObj = new URL(req.url, 'http://localhost:3000');
        const code = urlObj.searchParams.get('code');

        if (code) {
          res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
          res.end(`
            <div style="font-family: Arial, sans-serif; text-align: center; padding: 60px;">
              <h1 style="color: #16a34a; font-size: 28px;">✅ YouTube Channel Connected Successfully!</h1>
              <p style="font-size: 18px; color: #374151;">Your channel is authorized for Factify Shorts automation.</p>
              <p style="color: #6b7280;">You can now close this browser tab.</p>
            </div>
          `);
          server.close();

          console.log("Authorization code received! Exchanging for tokens...");
          const { tokens } = await oauth2Client.getToken(code);

          const tokenDir = path.dirname(TOKEN_FILE);
          if (!fs.existsSync(tokenDir)) fs.mkdirSync(tokenDir, { recursive: true });
          fs.writeFileSync(TOKEN_FILE, JSON.stringify(tokens, null, 2), 'utf-8');

          console.log("\n" + "=".repeat(66));
          console.log("🎉 SUCCESS! Token successfully generated and saved to:");
          console.log(TOKEN_FILE);
          console.log("=".repeat(66));
          process.exit(0);
        }
      }
    } catch (err) {
      server.close();
      console.error("Authentication error:", err.message);
      process.exit(1);
    }
  }).listen(3000, () => {
    console.log("Local listener started on http://localhost:3000");
    // Open in Windows
    exec(`start "" "${authUrl.replace(/&/g, '^&')}"`);
  });
}

main().catch(err => {
  console.error("Fatal error:", err);
  process.exit(1);
});
