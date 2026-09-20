const { execFile } = require('child_process');
const installer = require('@ffmpeg-installer/ffmpeg');
const path = require('path');
const fs = require('fs');

const ffmpegPath = installer.path;
const clipsDir = path.resolve('./temp/real_clips');
const tempDir = path.resolve('./temp');
const outDir = path.resolve('./output');
const bgmPath = path.resolve('./assets/bgm/interstellar_space_ambient_127.mp3');

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

async function buildCinematicPro() {
  console.log("=== BUILDING CINEMATIC PRO SHORT WITH INTERSTELLAR BGM ===");

  const stitchedPath = path.join(tempDir, 'real_stitched.mp4');
  const finalOutput = path.join(outDir, 'Factify_Short_01_CINEMATIC_PRO.mp4');
  const desktopOutput = 'C:/Users/E-laerning & Earning/Desktop/Factify_Short_01_CINEMATIC_PRO.mp4';
  const audioPath = path.join(tempDir, 'voice_short_1.mp3');
  const assPath = path.join(tempDir, 'subtitles.ass').replace(/\\/g, '/').replace(':', '\\:');

  console.log("Using BGM:", bgmPath);
  console.log("Mixing voiceover with low-volume Interstellar Sci-Fi BGM & burning subtitles...");

  await runFfmpeg([
    '-y',
    '-i', stitchedPath,
    '-i', audioPath,
    '-i', bgmPath,
    '-filter_complex', `[0:v]ass='${assPath}'[v];[2:a]volume=0.13,afade=t=out:st=49:d=2[bgm];[1:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[a]`,
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
  console.log("SUCCESS! Pro Cinematic Video Generated at:");
  console.log("Desktop:", desktopOutput);
  console.log("==========================================");
}

buildCinematicPro().catch(console.error);
