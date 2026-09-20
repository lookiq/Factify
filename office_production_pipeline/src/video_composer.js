const { execSync } = require('child_process');
const ffmpegPath = require('@ffmpeg-installer/ffmpeg').path;
const path = require('path');
const fs = require('fs');

/**
 * Assembles video, voiceover, ducked background music, word-by-word highlighted subtitles,
 * and permanently bakes OFFLINE SEO metadata into the MP4 container header.
 */
async function composeShortVideo({
  videoPath,
  voiceAudioPath,
  musicAudioPath,
  assSubtitlesPath,
  outputPath,
  duration,
  offlineMetadata
}) {
  console.log("Composing final YouTube Short with FFmpeg...");
  console.log(`Target Duration: ~${duration.toFixed(1)}s`);
  console.log(`Subtitles File: ${assSubtitlesPath}`);

  // Windows-safe path escaping for FFmpeg filters
  const safeAssPath = assSubtitlesPath.replace(/\\/g, '/').replace(/:/g, '\\:');

  // Combined video & audio filter complex:
  // [0:v] -> scale & crop to 1080x1920 -> burn-in .ass subtitles -> [vout]
  // [1:a] -> voice boosted -> [v]
  // [2:a] -> ambient music ducked (-18dB) -> [m]
  // [v][m] -> mix -> normalize loudness (-14 LUFS) -> [aout]
  const filterComplex = [
    `[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,ass='${safeAssPath}'[vout]`,
    `[1:a]volume=1.3[v]`,
    `[2:a]volume=0.12[m]`,
    `[v][m]amix=inputs=2:duration=first:dropout_transition=2,loudnorm=I=-14:TP=-1.5:LRA=11[aout]`
  ].join(';');

  const renderDuration = Math.ceil(duration) + 0.5;

  // Offline SEO metadata embedded directly into the MP4 file header
  let metaArgs = '';
  if (offlineMetadata) {
    const clean = str => (str || '').replace(/["\r\n]/g, ' ');
    metaArgs = [
      `-metadata title="${clean(offlineMetadata.title)}"`,
      `-metadata artist="${clean(offlineMetadata.artist)}"`,
      `-metadata comment="${clean(offlineMetadata.comment)}"`,
      `-metadata description="${clean(offlineMetadata.description)}"`,
      `-metadata genre="${clean(offlineMetadata.genre)}"`,
      `-metadata keywords="${clean(offlineMetadata.keywords)}"`
    ].join(' ');
    console.log("Injecting Offline SEO metadata tags into MP4 container header...");
  }

  const cmd = [
    `"${ffmpegPath}" -y`,
    `-stream_loop -1 -i "${videoPath}"`,     // [0:v] looped video
    `-i "${voiceAudioPath}"`,                 // [1:a] voiceover
    `-stream_loop -1 -i "${musicAudioPath}"`, // [2:a] ambient music
    `-filter_complex "${filterComplex}"`,
    `-map "[vout]"`,
    `-map "[aout]"`,
    `-t ${renderDuration}`,
    metaArgs,                                 // Offline SEO metadata
    `-c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p -r 60`,
    `-c:a aac -b:a 192k`,
    `"${outputPath}"`
  ].filter(Boolean).join(' ');

  console.log("Executing FFmpeg render command...");
  execSync(cmd, { stdio: 'inherit' });

  if (fs.existsSync(outputPath)) {
    const stats = fs.statSync(outputPath);
    console.log(`Video rendered successfully with Offline SEO embedded!`);
    console.log(`File: ${outputPath} (${(stats.size / (1024 * 1024)).toFixed(2)} MB)`);
    return outputPath;
  } else {
    throw new Error("Render completed but output file not found.");
  }
}

module.exports = {
  composeShortVideo
};
