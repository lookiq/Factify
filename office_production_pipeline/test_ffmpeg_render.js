const { execFile } = require('child_process');
const installer = require('@ffmpeg-installer/ffmpeg');
const path = require('path');

const ffmpegPath = installer.path;
console.log("Using FFmpeg:", ffmpegPath);

const args = [
  '-y',
  '-loop', '1',
  '-i', path.resolve('./temp/scene_1.jpg'),
  '-t', '3',
  '-vf', "scale=1080:1920,zoompan=z='min(zoom+0.001,1.1)':d=75:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=25",
  '-c:v', 'libx264',
  '-pix_fmt', 'yuv420p',
  path.resolve('./temp/test_clip.mp4')
];

console.log("Running ffmpeg...");
execFile(ffmpegPath, args, (err, stdout, stderr) => {
  if (err) {
    console.error("FFmpeg error:", err.message);
    console.error("Stderr:", stderr);
  } else {
    console.log("Success! Rendered test_clip.mp4");
  }
});
