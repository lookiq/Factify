const path = require('path');
const fs = require('fs');
const { uploadShortVideo } = require('./src/youtube_uploader');

async function publishAdventureShort() {
  console.log("==================================================");
  console.log("🚀 PUBLISHING FACTIFY SHORT 01 (ADVENTURE EDITION)");
  console.log("==================================================");

  const videoPath = path.resolve('output/Factify_Short_01_ADVENTURE_EDITION.mp4');

  if (!fs.existsSync(videoPath)) {
    throw new Error(`Video file not found at: ${videoPath}`);
  }

  const title = "One Snap Can Cut a Ship in Half! 💀⛴️ Mooring Danger #shorts";

  const description = [
    "💀 This ordinary looking ship rope is actually one of the deadliest weapons on water! Watch what happens when a massive ship mooring line snaps under pressure!",
    "",
    "📌 In this video:",
    "0:00 - The Deadliest Weapon on Water",
    "0:10 - How Massive Cargo Ships Anchor at Docks",
    "0:25 - The Shocking Physics of Mooring Snapback",
    "0:40 - 700 KM/H Kinetic Whip Danger",
    "",
    "🔬 Maritime Science Explained:",
    "• Large cargo ships use ultra-high molecular weight synthetic mooring lines under hundreds of tons of tension.",
    "• When a line snaps, the stored elastic energy is released instantly, creating a supersonic snapback zone where the rope whips back at speeds exceeding 700 km/h (435 mph)—capable of slicing through steel railings in milliseconds.",
    "",
    "👍 Like & SUBSCRIBE to Factify Shorts for daily mind-blowing facts, maritime science, and engineering mysteries!",
    "",
    "#shorts #ship #ocean #danger #physics #engineering #maritime #facts #mindblowing #cargoship #science #viral #trending #factify"
  ].join("\n");

  const tags = [
    "shorts",
    "ship",
    "ships",
    "mooring line",
    "mooring snapback",
    "ship snapback",
    "dangerous jobs",
    "cargo ship",
    "ocean",
    "maritime",
    "deadliest weapon",
    "physics",
    "engineering",
    "extreme tension",
    "snapback zone",
    "facts",
    "amazing facts",
    "mind blowing",
    "did you know",
    "scary facts",
    "ship facts",
    "ocean danger",
    "educational shorts",
    "viral shorts",
    "factify"
  ];

  console.log(`Video File: ${videoPath}`);
  console.log(`Title: ${title}`);
  console.log(`Tags count: ${tags.length}`);
  console.log("Starting upload to YouTube channel...\n");

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

publishAdventureShort().catch(err => {
  console.error("❌ Upload failed:", err.message);
  if (err.response && err.response.data) {
    console.error("Error details:", JSON.stringify(err.response.data, null, 2));
  }
});
