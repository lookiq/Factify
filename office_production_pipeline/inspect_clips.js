const { execSync } = require('child_process');
const installer = require('@ffmpeg-installer/ffmpeg');
const ffmpeg = installer.path;
const fs = require('fs');
const path = require('path');
const dir = path.resolve('./temp/real_clips');

fs.readdirSync(dir).forEach(f => {
  const p = path.join(dir, f);
  try {
    const out = execSync(`"${ffmpeg}" -i "${p}" 2>&1`).toString();
    const durationMatch = out.match(/Duration: ([0-9:.]+)/);
    const resMatch = out.match(/(\d{3,4}x\d{3,4})/);
    console.log(f, '-> Duration:', durationMatch ? durationMatch[1] : 'unknown', 'Resolution:', resMatch ? resMatch[1] : 'unknown');
  } catch(e) {}
});
