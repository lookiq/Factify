const path = require('path');
const fs = require('fs');
const { uploadShortVideo } = require('./src/youtube_uploader');

async function publishShort() {
  console.log("==================================================");
  console.log("🚀 PUBLISHING SCIENCE EXPERIMENTS SHORT TO YOUTUBE");
  console.log("==================================================");

  const videoPath = path.resolve('output/Science_Experiments_Factition_Magic.mp4');

  if (!fs.existsSync(videoPath)) {
    throw new Error(`Video file not found at: ${videoPath}`);
  }

  const title = "3 Science Experiments That Look Like Magic! 🤯⚡ #shorts";

  const description = [
    "🤯 Can you believe these 3 science experiments actually work?! Watch till the end to see fire literally jump through the air!",
    "",
    "📌 In this video:",
    "0:00 - Spinning Steel Wool Golden Fire Vortex",
    "0:04 - Splitting Water into Hydrogen with a 9V Battery & Pencils",
    "0:09 - Relighting a Candle through its Smoke Trail",
    "",
    "🔬 Science Explained:",
    "• Rapid iron oxidation creates flying sparks when spinning burning steel wool.",
    "• Water electrolysis uses graphite electrodes to split H2O into pure hydrogen and oxygen gas.",
    "• Vaporized paraffin wax in candle smoke allows the flame to travel back down to the wick!",
    "",
    "Credits: 5-MINUTE MAGIC, YouLab",
    "",
    "👍 Like and SUBSCRIBE to Factify Daily Shorts for more mind-blowing science facts and experiments every day!",
    "",
    "#shorts #science #experiment #magic #satisfying #physics #chemistry #scienceexperiment #facts #viral #trending #didyouknow #factition"
  ].join("\n");

  const tags = [
    "shorts",
    "science",
    "science experiments",
    "experiments",
    "magic tricks",
    "physics",
    "chemistry",
    "satisfying",
    "viral",
    "facts",
    "did you know",
    "mind blowing",
    "hydrogen",
    "electrolysis",
    "fire vortex",
    "candle smoke trick",
    "diy science",
    "factition",
    "educational shorts",
    "trending shorts",
    "crazy experiments",
    "easy science experiments",
    "amazing facts",
    "cool science"
  ];

  console.log(`Video: ${videoPath}`);
  console.log(`Title: ${title}`);
  console.log(`Tags count: ${tags.length}`);
  console.log("Starting upload directly to connected channel...\n");

  const result = await uploadShortVideo({
    videoPath,
    title,
    description,
    tags
    // scheduledPublishTime omitted so privacyStatus is immediately 'public'
  });

  console.log("\n==================================================");
  console.log("🎉 VIDEO SUCCESSFULLY PUBLISHED TO YOUTUBE!");
  console.log(`Video ID: ${result.id}`);
  console.log(`Live Short URL: https://youtube.com/shorts/${result.id}`);
  console.log("==================================================");

  return result;
}

publishShort().catch(err => {
  console.error("❌ Upload failed:", err.message);
  if (err.response && err.response.data) {
    console.error("Error details:", JSON.stringify(err.response.data, null, 2));
  }
});
