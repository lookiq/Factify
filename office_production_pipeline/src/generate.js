const path = require('path');
const fs = require('fs');
const { generateFactitionScript } = require('./script_generator');
const { createVoiceoverAndSubtitles } = require('./tts_subtitles');
const { ensureBackgroundMusic, getBrollVideo } = require('./broll_fetcher');
const { composeShortVideo } = require('./video_composer');

async function main() {
  console.log("==================================================");
  console.log("🚀 YouTube Shorts Automation Engine (Factition Style)");
  console.log("==================================================");

  const customTopic = process.argv[2] || null;

  // Step 1: Script Generation
  console.log("\n[1/5] Generating Factition-Style Script...");
  const scriptData = await generateFactitionScript(customTopic);
  console.log(`📌 Topic: ${scriptData.topic}`);
  console.log(`🎬 Title: ${scriptData.title}`);
  console.log(`📜 Script: "${scriptData.script.slice(0, 120)}..."`);

  // Step 2: Background Music Preparation
  console.log("\n[2/5] Preparing Ambient Mystery Music...");
  const musicPath = ensureBackgroundMusic();

  // Step 3: Voiceover & Word-by-Word Highlight Subtitles
  console.log("\n[3/5] Synthesizing Voiceover (Christopher - Edge Neural Voice)...");
  const timestamp = Date.now();
  const ttsResult = await createVoiceoverAndSubtitles(scriptData.script, `voice_${timestamp}`);
  console.log(`Audio Duration: ${ttsResult.duration.toFixed(1)} seconds`);

  // Step 4: B-Roll Video Fetcher
  console.log("\n[4/5] Preparing 1080x1920 Vertical B-Roll...");
  const videoPath = await getBrollVideo(scriptData.searchQuery, ttsResult.duration);

  // Step 5: Master Video Composition
  console.log("\n[5/5] Assembling Full HD Short Video...");
  const outputDir = path.join(__dirname, '..', 'output');
  if (!fs.existsSync(outputDir)) fs.mkdirSync(outputDir, { recursive: true });

  const finalVideoPath = path.join(outputDir, `factition_short_${timestamp}.mp4`);
  await composeShortVideo({
    videoPath,
    voiceAudioPath: ttsResult.audioPath,
    musicAudioPath: musicPath,
    assSubtitlesPath: ttsResult.assPath,
    outputPath: finalVideoPath,
    duration: ttsResult.duration
  });

  // Save YouTube metadata (Title, Description, Tags)
  const metaPath = path.join(outputDir, `factition_short_${timestamp}.json`);
  const metadata = {
    title: scriptData.title,
    description: `${scriptData.script}\n\n#shorts #facts #mystery #science #space #amazingfacts #factition`,
    tags: ["shorts", "facts", "mystery", "science", "space", "mindblowing", "factition"],
    category: "27", // Education
    duration: ttsResult.duration,
    created_at: new Date().toISOString(),
    video_file: finalVideoPath
  };
  fs.writeFileSync(metaPath, JSON.stringify(metadata, null, 2), 'utf-8');

  console.log("\n==================================================");
  console.log("✅ FACTITION SHORT GENERATION COMPLETED!");
  console.log(`📁 Video Path: ${finalVideoPath}`);
  console.log(`📄 Metadata: ${metaPath}`);
  console.log("==================================================");
}

main().catch(err => {
  console.error("❌ Pipeline failed:", err);
  process.exit(1);
});
