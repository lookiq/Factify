const path = require('path');
const { uploadShortVideo } = require('./src/youtube_uploader');

async function testUpload() {
  console.log("==================================================");
  console.log("🚀 Testing Live YouTube Upload...");
  console.log("==================================================");

  const videoPath = path.join(__dirname, 'output', 'factition_short_1789804477364.mp4');
  const title = "NASA Recorded What Saturn Sounds Like and It's Terrifying! 🪐🔊 #shorts";
  const description = "Astronomers pointed NASA's Cassini spacecraft directly at Saturn's rings, and what they recorded will give you chills.\n\n#shorts #facts #mystery #science #space #amazingfacts #factition";
  const tags = ["shorts", "facts", "mystery", "science", "space", "mindblowing", "factition"];

  // Upload as private for safe testing
  const result = await uploadShortVideo({
    videoPath,
    title,
    description,
    tags
  });

  console.log("\n==================================================");
  console.log("🎉 LIVE UPLOAD TEST SUCCESSFUL!");
  console.log(`Video ID: ${result.id}`);
  console.log(`Live Link: https://youtube.com/shorts/${result.id}`);
  console.log("==================================================");
}

testUpload().catch(err => {
  console.error("❌ Upload test failed:", err.message);
  if (err.response && err.response.data) {
    console.error("Error details:", JSON.stringify(err.response.data, null, 2));
  }
});
