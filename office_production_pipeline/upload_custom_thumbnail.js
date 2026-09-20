const { google } = require('googleapis');
const { getOAuth2Client, authenticate } = require('./src/youtube_uploader');
const fs = require('fs');
const path = require('path');

async function setThumbnail(videoId, imagePath) {
  console.log("==================================================");
  console.log("🖼️ UPLOADING CUSTOM THUMBNAIL TO YOUTUBE");
  console.log("==================================================");

  const client = await authenticate(getOAuth2Client());
  const youtube = google.youtube({ version: 'v3', auth: client });

  console.log(`Video ID: ${videoId}`);
  console.log(`Thumbnail Path: ${imagePath}`);

  if (!fs.existsSync(imagePath)) {
    throw new Error(`Thumbnail image file not found: ${imagePath}`);
  }

  const res = await youtube.thumbnails.set({
    videoId: videoId,
    media: {
      mimeType: 'image/jpeg',
      body: fs.createReadStream(imagePath)
    }
  });

  console.log("\n==================================================");
  console.log("🎉 THUMBNAIL SET SUCCESSFULLY!");
  console.log("Result:", JSON.stringify(res.data, null, 2));
  console.log("==================================================");
  return res.data;
}

const videoId = 'DG_IZ09jKf0';
const imagePath = path.resolve('temp/custom_thumbnail.jpg');

setThumbnail(videoId, imagePath).catch(err => {
  console.error("❌ Failed to set thumbnail:", err.message);
  if (err.response && err.response.data) {
    console.error("Error details:", JSON.stringify(err.response.data, null, 2));
  }
});
