const { execFile } = require('child_process');
const installer = require('@ffmpeg-installer/ffmpeg');
const path = require('path');

const ffmpegPath = installer.path;
// In FFmpeg on Windows, forward slashes with escaped colon works best:
// e.g. C\\:/Users/...
const assPath = path.resolve('./temp/subtitles.ass').replace(/\\/g, '/').replace(':', '\\:');

const args = [
  '-y',
  '-i', path.resolve('./temp/test_clip.mp4'),
  '-vf', `ass='${assPath}'`,
  '-c:v', 'libx264',
  '-c:a', 'copy',
  path.resolve('./temp/test_sub.mp4')
];

console.log("Testing ASS filter with args:", args.join(" "));
execFile(ffmpegPath, args, (err, stdout, stderr) => {
  if (err) {
    console.error("ASS Error:", err.message);
    console.error("Stderr:", stderr);
  } else {
    console.log("Success! Subtitles burned into test_sub.mp4");
  }
});
