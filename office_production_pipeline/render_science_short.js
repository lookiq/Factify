const { execSync } = require('child_process');
const ffmpegPath = require('@ffmpeg-installer/ffmpeg').path;
const path = require('path');
const fs = require('fs');

async function renderScienceShort() {
  console.log("==================================================");
  console.log("🎬 RENDERING FACTITION SCIENCE EXPERIMENTS SHORT");
  console.log("==================================================");

  const videoInput = path.resolve('temp/reference_short.mp4');
  const voiceInput = path.resolve('temp/combined_voice.mp3');
  const musicInput = path.resolve('temp/sample_audio.mp3');
  const assInput = path.resolve('temp/experiment_subtitles.ass');
  
  const outDir = path.resolve('output');
  if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });
  
  const finalOutput = path.join(outDir, 'Science_Experiments_Factition_Magic.mp4');
  const desktopOutput = 'C:/Users/E-laerning & Earning/Desktop/Science_Experiments_Factition_Magic.mp4';

  const safeAss = assInput.replace(/\\/g, '/').replace(/:/g, '\\:');

  // Filter complex:
  // Scale video to 1080x1920, burn-in ASS subtitles
  // Duck background music to volume 0.16, voice volume 1.3
  // Mix and normalize to -14 LUFS standard
  const filterComplex = [
    `[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,ass='${safeAss}'[vout]`,
    `[1:a]volume=1.3[v]`,
    `[2:a]volume=0.16[m]`,
    `[v][m]amix=inputs=2:duration=first:dropout_transition=1,loudnorm=I=-14:TP=-1.5:LRA=9[aout]`
  ].join(';');

  // Complete Offline SEO metadata embedded in MP4 container header
  const title = "3 Science Experiments That Look Like Magic! 🤯⚡ #shorts";
  const artist = "Factify Daily Shorts";
  const album = "Daily Science Mysteries & Experiments";
  const comment = "Offline SEO: science experiments, physics tricks, chemistry magic, hydrogen electrolysis, flame jump, steel wool fire";
  const description = "Watch these 3 mind-blowing science experiments that defy intuition! Burning steel wool sparks, pencil electrolysis, and candle smoke flame jumping.";
  const keywords = "shorts,science,experiments,magic,satisfying,physics,chemistry,viral,factition,facts,diy";

  const metaArgs = [
    `-metadata title="${title}"`,
    `-metadata artist="${artist}"`,
    `-metadata album_artist="${artist}"`,
    `-metadata album="${album}"`,
    `-metadata comment="${comment}"`,
    `-metadata description="${description}"`,
    `-metadata keywords="${keywords}"`,
    `-metadata genre="Science & Education"`
  ].join(' ');

  const cmd = [
    `"${ffmpegPath}" -y`,
    `-i "${videoInput}"`,
    `-i "${voiceInput}"`,
    `-i "${musicInput}"`,
    `-filter_complex "${filterComplex}"`,
    `-map "[vout]"`,
    `-map "[aout]"`,
    `-t 14.65`,
    metaArgs,
    `-c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p -r 30`,
    `-c:a aac -b:a 192k`,
    `"${finalOutput}"`
  ].join(' ');

  console.log("Running FFmpeg compositor...");
  execSync(cmd, { stdio: 'inherit' });

  if (fs.existsSync(finalOutput)) {
    const stats = fs.statSync(finalOutput);
    console.log(`\n✅ Render completed successfully!`);
    console.log(`Output: ${finalOutput} (${(stats.size / (1024 * 1024)).toFixed(2)} MB)`);

    // Copy to Desktop for direct user viewing
    fs.copyFileSync(finalOutput, desktopOutput);
    console.log(`✅ Saved copy directly to Desktop: ${desktopOutput}`);
    return finalOutput;
  } else {
    throw new Error("Render finished but output file missing.");
  }
}

renderScienceShort().catch(console.error);
