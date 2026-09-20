const { execFile, exec } = require('child_process');
const installer = require('@ffmpeg-installer/ffmpeg');
const path = require('path');
const fs = require('fs');

const ffmpegPath = installer.path;
const tempDir = path.resolve('./temp');
const outDir = path.resolve('./output');

if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });

function runFfmpeg(args) {
  return new Promise((resolve, reject) => {
    console.log(`Executing FFmpeg: ffmpeg ${args.slice(0, 6).join(' ')}...`);
    execFile(ffmpegPath, args, (err, stdout, stderr) => {
      if (err) {
        console.error("FFmpeg error:", stderr);
        return reject(err);
      }
      resolve(stdout);
    });
  });
}

async function buildVideo() {
  console.log("=== BUILDING FACTIFY SHORT #1 ===");

  const scenes = [
    { file: 'scene_1.jpg', duration: 10.0, zoom: "z='min(zoom+0.0015,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'" },
    { file: 'scene_2.jpg', duration: 10.0, zoom: "z='min(zoom+0.0018,1.20)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'" },
    { file: 'scene_3.jpg', duration: 10.0, zoom: "z='max(1.15-0.0015*on,1.0)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'" },
    { file: 'scene_4.jpg', duration: 10.0, zoom: "z='min(zoom+0.0022,1.25)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'" },
    { file: 'scene_5.jpg', duration: 11.5, zoom: "z='min(zoom+0.0012,1.12)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'" }
  ];

  const clipPaths = [];

  for (let i = 0; i < scenes.length; i++) {
    const s = scenes[i];
    const imgPath = path.join(tempDir, s.file);
    const clipOut = path.join(tempDir, `clip_${i + 1}.mp4`);
    clipPaths.push(clipOut);

    const totalFrames = Math.floor(s.duration * 25);
    console.log(`Rendering Scene ${i + 1} (${s.duration}s)...`);

    await runFfmpeg([
      '-y',
      '-loop', '1',
      '-i', imgPath,
      '-t', String(s.duration),
      '-vf', `scale=1080:1920,zoompan=${s.zoom}:d=${totalFrames}:s=1080x1920:fps=25`,
      '-c:v', 'libx264',
      '-preset', 'veryfast',
      '-pix_fmt', 'yuv420p',
      clipOut
    ]);
  }

  // Create concat list
  const listFile = path.join(tempDir, 'concat_list.txt');
  const fileLines = clipPaths.map(p => `file '${p.replace(/\\/g, '/')}'`).join('\n');
  fs.writeFileSync(listFile, fileLines, 'utf-8');

  const stitchedVisual = path.join(tempDir, 'stitched_visual.mp4');
  console.log("Stitching scenes together...");
  await runFfmpeg([
    '-y',
    '-f', 'concat',
    '-safe', '0',
    '-i', listFile,
    '-c', 'copy',
    stitchedVisual
  ]);

  // Final Assembly with Voiceover and Subtitles
  const finalOutput = path.join(outDir, 'Factify_Short_01_Mooring_Snapback.mp4');
  const desktopOutput = 'C:/Users/E-laerning & Earning/Desktop/Factify_Short_01_Mooring_Snapback.mp4';
  const audioPath = path.join(tempDir, 'voice_short_1.mp3');
  const assPath = path.join(tempDir, 'subtitles.ass').replace(/\\/g, '/').replace(':', '\\:');

  console.log("Adding Voiceover, Subtle Tension Drone & Burning Subtitles...");
  await runFfmpeg([
    '-y',
    '-i', stitchedVisual,
    '-i', audioPath,
    '-filter_complex', `[0:v]ass='${assPath}'[v];sine=frequency=60:duration=52[drone];[drone]volume=0.06[drone_low];[1:a][drone_low]amix=inputs=2:duration=first[a]`,
    '-map', '[v]',
    '-map', '[a]',
    '-c:v', 'libx264',
    '-preset', 'fast',
    '-b:v', '6000k',
    '-c:a', 'aac',
    '-b:a', '192k',
    '-shortest',
    finalOutput
  ]);

  // Copy to desktop for user convenience
  fs.copyFileSync(finalOutput, desktopOutput);
  console.log("\n==========================================");
  console.log("SUCCESS! Video generated at:");
  console.log("1. Workspace:", finalOutput);
  console.log("2. Desktop:", desktopOutput);
  console.log("==========================================");
}

buildVideo().catch(console.error);
