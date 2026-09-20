const { execFile } = require('child_process');
const installer = require('@ffmpeg-installer/ffmpeg');
const path = require('path');
const fs = require('fs');

const ffmpegPath = installer.path;
const tempDir = path.resolve('./temp');
const outDir = path.resolve('./output');
const bgmPath = path.resolve('./assets/bgm/adventure/adventure_871.mp3');

function runFfmpeg(args) {
  return new Promise((resolve, reject) => {
    execFile(ffmpegPath, args, (err, stdout, stderr) => {
      if (err) {
        console.error("FFmpeg error:", stderr);
        return reject(err);
      }
      resolve(stdout);
    });
  });
}

async function buildAdventureEdition() {
  console.log("=== BUILDING ADVENTURE EDITION SHORT ===");

  const stitchedPath = path.join(tempDir, 'real_stitched.mp4');
  const finalOutput = path.join(outDir, 'Factify_Short_01_ADVENTURE_EDITION.mp4');
  const desktopOutput = 'C:/Users/E-laerning & Earning/Desktop/Factify_Short_01_ADVENTURE_EDITION.mp4';
  const audioPath = path.join(tempDir, 'voice_short_1.mp3');
  const assPath = path.join(tempDir, 'subtitles.ass').replace(/\\/g, '/').replace(':', '\\:');

  console.log("Using Adventure Track:", bgmPath);
  console.log("Mixing with fast-paced cinematic adventure BGM...");

  await runFfmpeg([
    '-y',
    '-i', stitchedPath,
    '-i', audioPath,
    '-i', bgmPath,
    '-filter_complex', `[0:v]ass='${assPath}'[v];[2:a]volume=0.16,afade=t=out:st=49:d=2[bgm];[1:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[a]`,
    '-map', '[v]',
    '-map', '[a]',
    '-c:v', 'libx264',
    '-preset', 'fast',
    '-b:v', '7500k',
    '-c:a', 'aac',
    '-b:a', '192k',
    '-shortest',
    finalOutput
  ]);

  fs.copyFileSync(finalOutput, desktopOutput);
  console.log("\n==========================================");
  console.log("SUCCESS! Adventure Edition Generated at:");
  console.log("Desktop:", desktopOutput);
  console.log("==========================================");
}

buildAdventureEdition().catch(console.error);
