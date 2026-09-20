const { execFile } = require('child_process');
const installer = require('@ffmpeg-installer/ffmpeg');
const path = require('path');
const fs = require('fs');

const ffmpegPath = installer.path;
const clipsDir = path.resolve('./temp/real_clips');
const tempDir = path.resolve('./temp');
const outDir = path.resolve('./output');

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

async function buildRealVideo() {
  console.log("=== CREATING 100% REAL FOOTAGE FACTIFY SHORT ===");

  // 11 fast-paced cuts mapped to the narration
  const timeline = [
    { file: 'clip_ship_sailing.mp4', start: 0.0, duration: 4.5 },
    { file: 'clip_ship_harbor.mp4', start: 1.0, duration: 4.5 },
    { file: 'clip_cargo_crane.mp4', start: 0.0, duration: 4.5 },
    { file: 'clip_extra_worker.mp4', start: 0.0, duration: 4.5 },
    { file: 'clip_danger_hazard.mp4', start: 2.0, duration: 4.5 },
    { file: 'clip_storm_ocean.mp4', start: 0.5, duration: 4.5 },
    { file: 'clip_extra_waves.mp4', start: 0.0, duration: 4.5 },
    { file: 'clip_extra_metal.mp4', start: 0.0, duration: 4.5 },
    { file: 'clip_danger_hazard.mp4', start: 6.0, duration: 5.0 },
    { file: 'clip_ship_harbor.mp4', start: 4.0, duration: 5.0 },
    { file: 'clip_deep_ocean.mp4', start: 1.0, duration: 5.3 }
  ];

  const processedClips = [];

  for (let i = 0; i < timeline.length; i++) {
    const item = timeline[i];
    const inPath = path.join(clipsDir, item.file);
    const outClip = path.join(tempDir, `real_cut_${i + 1}.mp4`);
    processedClips.push(outClip);

    console.log(`Processing Cut ${i + 1}/${timeline.length}: ${item.file} (${item.duration}s)...`);

    // Scale to vertical 1080x1920 with high-quality center crop and 30fps
    await runFfmpeg([
      '-y',
      '-ss', String(item.start),
      '-i', inPath,
      '-t', String(item.duration),
      '-vf', 'scale=-2:1920,crop=1080:1920:(in_w-1080)/2:0,fps=30',
      '-c:v', 'libx264',
      '-preset', 'fast',
      '-pix_fmt', 'yuv420p',
      '-an',
      outClip
    ]);
  }

  // Concat list
  const listFile = path.join(tempDir, 'real_concat.txt');
  const fileLines = processedClips.map(p => `file '${p.replace(/\\/g, '/')}'`).join('\n');
  fs.writeFileSync(listFile, fileLines, 'utf-8');

  const stitchedPath = path.join(tempDir, 'real_stitched.mp4');
  console.log("Stitching all real video clips seamlessly...");
  await runFfmpeg([
    '-y',
    '-f', 'concat',
    '-safe', '0',
    '-i', listFile,
    '-c', 'copy',
    stitchedPath
  ]);

  // Final Assembly with Voiceover and Styled Subtitles
  const finalOutput = path.join(outDir, 'Factify_Short_01_REAL_FOOTAGE.mp4');
  const desktopOutput = 'C:/Users/E-laerning & Earning/Desktop/Factify_Short_01_REAL_FOOTAGE.mp4';
  const audioPath = path.join(tempDir, 'voice_short_1.mp3');
  const assPath = path.join(tempDir, 'subtitles.ass').replace(/\\/g, '/').replace(':', '\\:');

  console.log("Adding Voiceover, Sub-bass Tension & Burning Hormozi-style Subtitles...");
  await runFfmpeg([
    '-y',
    '-i', stitchedPath,
    '-i', audioPath,
    '-filter_complex', `[0:v]ass='${assPath}'[v];sine=frequency=55:duration=52[drone];[drone]volume=0.05[dlow];[1:a][dlow]amix=inputs=2:duration=first[a]`,
    '-map', '[v]',
    '-map', '[a]',
    '-c:v', 'libx264',
    '-preset', 'medium',
    '-b:v', '7000k',
    '-c:a', 'aac',
    '-b:a', '192k',
    '-shortest',
    finalOutput
  ]);

  // Copy to desktop for user convenience
  fs.copyFileSync(finalOutput, desktopOutput);
  console.log("\n==========================================");
  console.log("SUCCESS! Real Footage Video Generated at:");
  console.log("1. Workspace:", finalOutput);
  console.log("2. Desktop:", desktopOutput);
  console.log("==========================================");
}

buildRealVideo().catch(console.error);
