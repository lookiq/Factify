const https = require('https');
const fs = require('fs');
const path = require('path');

const clips = [
  { name: 'clip_ship_harbor.mp4', url: 'https://assets.mixkit.co/videos/20179/20179-720.mp4' },
  { name: 'clip_ship_sailing.mp4', url: 'https://assets.mixkit.co/videos/11937/11937-720.mp4' },
  { name: 'clip_cargo_crane.mp4', url: 'https://assets.mixkit.co/videos/30979/30979-720.mp4' },
  { name: 'clip_storm_ocean.mp4', url: 'https://assets.mixkit.co/videos/47948/47948-720.mp4' },
  { name: 'clip_danger_hazard.mp4', url: 'https://assets.mixkit.co/videos/48076/48076-720.mp4' },
  { name: 'clip_deep_ocean.mp4', url: 'https://assets.mixkit.co/videos/15209/15209-720.mp4' }
];

const dir = path.resolve('./temp/real_clips');
if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });

function downloadFile(url, dest) {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(dest);
    https.get(url, (res) => {
      if (res.statusCode === 302 || res.statusCode === 301) {
        return downloadFile(res.headers.location, dest).then(resolve).catch(reject);
      }
      res.pipe(file);
      file.on('finish', () => {
        file.close();
        console.log('Downloaded:', path.basename(dest), (fs.statSync(dest).size / 1024 / 1024).toFixed(2), 'MB');
        resolve();
      });
    }).on('error', (err) => {
      fs.unlink(dest, () => {});
      reject(err);
    });
  });
}

async function downloadAll() {
  console.log('Downloading real stock video clips...');
  for (const c of clips) {
    const dest = path.join(dir, c.name);
    await downloadFile(c.url, dest);
  }
  console.log('All real video clips downloaded successfully!');
}

downloadAll().catch(console.error);
