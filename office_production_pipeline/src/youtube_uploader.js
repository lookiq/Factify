const fs = require('fs');
const path = require('path');
const http = require('http');
const { google } = require('googleapis');
const readline = require('readline');

const CLIENT_SECRET_FILE = path.join(__dirname, '..', 'client_secret.json');
const TOKEN_FILE = path.join(__dirname, '..', 'data', 'token.json');
const SCOPES = [
  'https://www.googleapis.com/auth/youtube.upload',
  'https://www.googleapis.com/auth/youtube.readonly'
];

/**
 * Loads OAuth2 Client from client_secret.json
 */
function getOAuth2Client() {
  if (!fs.existsSync(CLIENT_SECRET_FILE)) {
    return null;
  }

  const content = JSON.parse(fs.readFileSync(CLIENT_SECRET_FILE, 'utf-8'));
  const credentials = content.installed || content.web;
  if (!credentials) {
    throw new Error("Invalid client_secret.json format. Expected 'installed' or 'web' keys.");
  }

  const { client_secret, client_id } = credentials;
  // For Desktop Apps, Google permits any localhost port
  const redirectUri = 'http://localhost:3000';
  return new google.auth.OAuth2(client_id, client_secret, redirectUri);
}

/**
 * Authenticates user and saves token.json
 */
async function authenticate(oauth2Client) {
  if (fs.existsSync(TOKEN_FILE)) {
    try {
      const token = JSON.parse(fs.readFileSync(TOKEN_FILE, 'utf-8'));
      oauth2Client.setCredentials(token);
      return oauth2Client;
    } catch (e) {
      console.warn("Corrupted token.json, re-authorizing...");
    }
  }

  return new Promise((resolve, reject) => {
    const authUrl = oauth2Client.generateAuthUrl({
      access_type: 'offline',
      scope: SCOPES,
      prompt: 'consent'
    });

    console.log('\n======================================================');
    console.log('🔑 YOUTUBE CHANNEL 1-TIME AUTHORIZATION REQUIRED');
    console.log('Opening your browser for 1-click Google authorization...');
    console.log('Auth URL: ' + authUrl);
    console.log('======================================================\n');

    // Automatically open browser on Windows
    const { exec } = require('child_process');
    exec(`start "" "${authUrl.replace(/&/g, '^&')}"`);

    // Temporary local web server to catch callback code automatically
    const server = http.createServer(async (req, res) => {
      try {
        if (req.url.startsWith('/?code=') || req.url.startsWith('/oauth2callback') || req.url.includes('code=')) {
          const urlObj = new URL(req.url, 'http://localhost:3000');
          const code = urlObj.searchParams.get('code');

          if (code) {
            res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
            res.end(`
              <div style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                <h1 style="color: #22c55e;">✅ YouTube Channel Connected Successfully!</h1>
                <p style="font-size: 18px;">You can now close this browser tab. Your automation engine is authorized.</p>
              </div>
            `);
            server.close();

            const { tokens } = await oauth2Client.getToken(code);
            oauth2Client.setCredentials(tokens);

            const tokenDir = path.dirname(TOKEN_FILE);
            if (!fs.existsSync(tokenDir)) fs.mkdirSync(tokenDir, { recursive: true });
            fs.writeFileSync(TOKEN_FILE, JSON.stringify(tokens, null, 2), 'utf-8');
            console.log('\n✅ Channel Token successfully saved to data/token.json!');

            resolve(oauth2Client);
          }
        }
      } catch (err) {
        server.close();
        reject(err);
      }
    }).listen(3000, () => {
      console.log('Listening on http://localhost:3000 for authorization...');
    });
  });
}

/**
 * Uploads a short video with scheduled publish time
 */
async function uploadShortVideo({ videoPath, title, description, tags, scheduledPublishTime }) {
  const oauth2Client = getOAuth2Client();

  if (!oauth2Client) {
    console.warn("\n⚠️ client_secret.json not found. Video saved locally in 'output/' folder.");
    return {
      status: "mock_saved",
      video_id: "LOCAL_ONLY",
      scheduledPublishTime
    };
  }

  const authenticatedClient = await authenticate(oauth2Client);
  const youtube = google.youtube({ version: 'v3', auth: authenticatedClient });

  console.log(`\n🚀 Uploading to YouTube: "${title}"...`);
  if (scheduledPublishTime) {
    console.log(`🕒 Scheduled Publish Time (UTC): ${scheduledPublishTime}`);
  }

  const requestBody = {
    snippet: {
      title: title.slice(0, 100),
      description: description || '',
      tags: tags || ['shorts', 'facts'],
      categoryId: '27', // Education
      defaultLanguage: 'en',
      defaultAudioLanguage: 'en'
    },
    status: {
      privacyStatus: scheduledPublishTime ? 'private' : 'public',
      selfDeclaredMadeForKids: false
    }
  };

  if (scheduledPublishTime) {
    requestBody.status.publishAt = scheduledPublishTime;
  }

  const fileSize = fs.statSync(videoPath).size;
  const res = await youtube.videos.insert(
    {
      part: ['snippet', 'status'],
      requestBody,
      media: {
        body: fs.createReadStream(videoPath)
      }
    },
    {
      onUploadProgress: evt => {
        const progress = (evt.bytesRead / fileSize) * 100;
        process.stdout.write(`Upload progress: ${Math.round(progress)}%\r`);
      }
    }
  );

  console.log(`\n✅ Upload Complete! Video ID: ${res.data.id}`);
  console.log(`🔗 Link: https://youtube.com/shorts/${res.data.id}`);
  return res.data;
}

// CLI test mode
if (require.main === module) {
  const client = getOAuth2Client();
  if (!client) {
    console.error("❌ client_secret.json not found!");
    process.exit(1);
  }
  console.log("Checking YouTube authorization...");
  authenticate(client).then(() => {
    console.log("✅ YouTube Channel is connected and ready for automated uploads!");
    process.exit(0);
  }).catch(err => {
    console.error("❌ Authentication error:", err);
    process.exit(1);
  });
}

module.exports = {
  uploadShortVideo,
  getOAuth2Client,
  authenticate
};
