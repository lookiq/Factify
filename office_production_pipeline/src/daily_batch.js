const path = require('path');
const fs = require('fs');
const { generateFactitionScript } = require('./script_generator');
const { createVoiceoverAndSubtitles } = require('./tts_subtitles');
const { ensureBackgroundMusic, getBrollVideo } = require('./broll_fetcher');
const { composeShortVideo } = require('./video_composer');
const { uploadShortVideo } = require('./youtube_uploader');
const { generateSeoMetadata } = require('./seo_engine');

const HISTORY_UPLOAD_FILE = path.join(__dirname, '..', 'data', 'upload_history.json');

/**
 * Calculates the next 3 upcoming US Eastern Time slots in ISO 8601 UTC string:
 * Slot 1: 08:00 AM ET (12:00 UTC)
 * Slot 2: 12:30 PM ET (16:30 UTC)
 * Slot 3: 07:30 PM ET (23:30 UTC)
 */
function getUpcomingUsTimeSlots() {
  const now = new Date();

  // Targets in UTC (EDT is UTC-4):
  // 8:00 AM EDT -> 12:00 UTC
  // 12:30 PM EDT -> 16:30 UTC
  // 7:30 PM EDT -> 23:30 UTC
  const slotHours = [
    { name: "Slot 1 (8:00 AM ET)", hourUTC: 12, minUTC: 0 },
    { name: "Slot 2 (12:30 PM ET)", hourUTC: 16, minUTC: 30 },
    { name: "Slot 3 (7:30 PM ET)", hourUTC: 23, minUTC: 30 }
  ];

  return slotHours.map(slot => {
    let target = new Date();
    target.setUTCHours(slot.hourUTC, slot.minUTC, 0, 0);

    // If this time has already passed today (with a 15-minute buffer), schedule for tomorrow
    if (target.getTime() <= now.getTime() + (15 * 60 * 1000)) {
      target.setUTCDate(target.getUTCDate() + 1);
    }

    return {
      name: slot.name,
      isoString: target.toISOString(),
      formattedLocal: target.toLocaleString()
    };
  });
}

async function runDailyBatch() {
  console.log("===============================================================");
  console.log("🌟 DAILY 3X YOUTUBE SHORTS AUTOMATION & US SCHEDULER ENGINE");
  console.log("   (Full Offline & Online SEO + YouTube API Auto-Upload)");
  console.log("===============================================================\n");

  const slots = getUpcomingUsTimeSlots();
  console.log("🕒 Today's 3 US Prime Time Release Slots:");
  slots.forEach((s, idx) => {
    console.log(`   [${idx + 1}] ${s.name} -> PublishAt (UTC): ${s.isoString}`);
  });
  console.log("\n---------------------------------------------------------------");

  const results = [];
  const musicPath = ensureBackgroundMusic();

  for (let i = 0; i < 3; i++) {
    const slot = slots[i];
    console.log(`\n===============================================================`);
    console.log(`🎬 GENERATING SHORT [${i + 1}/3] FOR ${slot.name}`);
    console.log(`===============================================================`);

    // 1. Script with 30-day anti-repetition memory
    const scriptData = await generateFactitionScript();
    console.log(`📌 Topic: ${scriptData.topic}`);

    // 2. Comprehensive SEO Generation (Online & Offline)
    const seo = generateSeoMetadata(scriptData);
    console.log(`🎬 SEO Title: ${seo.title}`);
    console.log(`🏷️ Tags: ${seo.tags.slice(0, 8).join(', ')}... (+${seo.tags.length - 8} more)`);

    // 3. Realistic Voiceover + Word timestamps
    const timestamp = Date.now();
    const ttsResult = await createVoiceoverAndSubtitles(scriptData.script, `voice_batch_${i + 1}_${timestamp}`);
    console.log(`🔊 Voiceover Duration: ${ttsResult.duration.toFixed(1)}s`);

    // 4. 1080x1920 B-Roll Video
    const videoPath = await getBrollVideo(scriptData.searchQuery, ttsResult.duration);

    // 5. Video Compositing + Offline File Metadata Injection
    const outputDir = path.join(__dirname, '..', 'output');
    if (!fs.existsSync(outputDir)) fs.mkdirSync(outputDir, { recursive: true });

    const finalVideoPath = path.join(outputDir, `batch_short_${i + 1}_${timestamp}.mp4`);
    await composeShortVideo({
      videoPath,
      voiceAudioPath: ttsResult.audioPath,
      musicAudioPath: musicPath,
      assSubtitlesPath: ttsResult.assPath,
      outputPath: finalVideoPath,
      duration: ttsResult.duration,
      offlineMetadata: seo.offlineMetadata
    });

    // 6. Upload & Schedule to YouTube with Full Online SEO
    const uploadResult = await uploadShortVideo({
      videoPath: finalVideoPath,
      title: seo.title,
      description: seo.description,
      tags: seo.tags,
      scheduledPublishTime: slot.isoString
    });

    results.push({
      slot: slot.name,
      publishAtUTC: slot.isoString,
      title: seo.title,
      videoPath: finalVideoPath,
      uploadStatus: uploadResult.status || "uploaded",
      videoId: uploadResult.id || uploadResult.video_id || "LOCAL"
    });
  }

  // Save batch run to history
  let history = [];
  if (fs.existsSync(HISTORY_UPLOAD_FILE)) {
    try { history = JSON.parse(fs.readFileSync(HISTORY_UPLOAD_FILE, 'utf-8')); } catch (e) {}
  }
  history.push({
    batch_date: new Date().toISOString(),
    videos: results
  });
  fs.writeFileSync(HISTORY_UPLOAD_FILE, JSON.stringify(history, null, 2), 'utf-8');

  console.log("\n===============================================================");
  console.log("🎉 ALL 3 DAILY SHORTS GENERATED, SEO-OPTIMIZED & SCHEDULED!");
  console.log("===============================================================");
  results.forEach((r, idx) => {
    console.log(`\n[${idx + 1}] ${r.slot}`);
    console.log(`    Title:     ${r.title}`);
    console.log(`    File:      ${r.videoPath}`);
    console.log(`    Scheduled: ${r.publishAtUTC}`);
    if (r.videoId && r.videoId !== "LOCAL") {
      console.log(`    Live Link: https://youtube.com/shorts/${r.videoId}`);
    }
  });
  console.log("\n===============================================================\n");
}

if (require.main === module) {
  runDailyBatch().catch(err => {
    console.error("❌ Daily batch failed:", err);
    process.exit(1);
  });
}

module.exports = {
  runDailyBatch,
  getUpcomingUsTimeSlots
};
