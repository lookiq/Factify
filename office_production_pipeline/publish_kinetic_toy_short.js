const path = require('path');
const fs = require('fs');
const { uploadShortVideo } = require('./src/youtube_uploader');

async function publishKineticShort() {
  console.log("==================================================");
  console.log("🚀 PUBLISHING OPTICAL ILLUSION KINETIC TOY SHORT");
  console.log("==================================================");

  const videoPath = path.resolve('output/Factify_Short_Optical_Illusion_Toy.mp4');

  if (!fs.existsSync(videoPath)) {
    throw new Error(`Video file not found at: ${videoPath}`);
  }

  const title = "How Does This Ball Defy Gravity?! 🤯🔮 Optical Illusion #shorts";

  const description = [
    "🔮 You're probably wondering how this metal ball appears to float in mid-air! Watch till the end to discover the secret of this hypnotic optical illusion!",
    "",
    "📌 In this video:",
    "0:00 - The Floating Ball Mystery",
    "0:05 - Meet the Luna Kinetic Desk Toy",
    "0:10 - How the Rotating Spiral Helix Tricks the Human Brain",
    "0:16 - Real Physics Behind Levitation Illusions",
    "",
    "🔬 Science Explained:",
    "• The Luna kinetic toy uses a precision-machined double helix spiral.",
    "• When rotated at constant velocity, the human eye interprets the moving spiral edges as vertical motion, creating an impossible visual illusion where the centered sphere appears to levitate freely in mid-air!",
    "",
    "Credits: MEZMOGLOBE, physicsfun",
    "",
    "👍 Like & SUBSCRIBE to Factify Shorts for your daily dose of mind-bending science and optical illusions!",
    "",
    "#shorts #opticalillusion #kinetictoy #satisfying #physics #science #mezmoglobe #magic #illusions #viral #trending #didyouknow #factify"
  ].join("\n");

  const tags = [
    "shorts",
    "optical illusion",
    "optical illusions",
    "kinetic toy",
    "kinetic desk toy",
    "mezmoglobe",
    "floating ball",
    "gravity illusion",
    "defying gravity",
    "satisfying video",
    "physics toy",
    "physics toys",
    "science illusion",
    "mind blowing",
    "how it works",
    "oddly satisfying",
    "satisfying",
    "viral shorts",
    "facts",
    "science facts",
    "did you know",
    "cool toys",
    "magic trick",
    "desk toy",
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

publishKineticShort().catch(err => {
  console.error("❌ Upload failed:", err.message);
  if (err.response && err.response.data) {
    console.error("Error details:", JSON.stringify(err.response.data, null, 2));
  }
});
