const { execSync } = require('child_process');
const installer = require('@ffmpeg-installer/ffmpeg');
const ffmpeg = installer.path;
const fs = require('fs');
const path = require('path');

const tracks = [
  './assets/bgm/adventure/adventure_676.mp3',
  './assets/bgm/adventure/adventure_677.mp3',
  './assets/bgm/adventure/adventure_680.mp3',
  './assets/bgm/adventure/adventure_871.mp3',
  './assets/bgm/adventure/adventure_706.mp3',
  './assets/bgm/space_atmospheric_arpeggio_292.mp3'
];

tracks.forEach(t => {
  try {
    const full = path.resolve(t);
    execSync(`"${ffmpeg}" -i "${full}"`);
  } catch(e) {
    const out = (e.stderr || e.stdout || '').toString();
    const dur = out.match(/Duration: ([0-9:.]+)/);
    const bit = out.match(/bitrate: ([0-9]+ kb\/s)/);
    console.log(path.basename(t), '->', dur ? dur[1] : '', bit ? bit[1] : '');
  }
});
