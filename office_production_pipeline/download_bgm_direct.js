const https = require('https');
const fs = require('fs');
const path = require('path');

const tracks = [
  { name: 'interstellar_space_ambient_127.mp3', url: 'https://assets.mixkit.co/music/127/127.mp3' },
  { name: 'cinematic_mystery_drama_614.mp3', url: 'https://assets.mixkit.co/music/614/614.mp3' },
  { name: 'scifi_deep_cosmos_139.mp3', url: 'https://assets.mixkit.co/music/139/139.mp3' },
  { name: 'space_atmospheric_arpeggio_292.mp3', url: 'https://assets.mixkit.co/music/292/292.mp3' }
];

const dir = path.resolve('./assets/bgm');
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
        console.log('Downloaded BGM:', path.basename(dest), (fs.statSync(dest).size / 1024 / 1024).toFixed(2), 'MB');
        resolve();
      });
    }).on('error', (err) => {
      fs.unlink(dest, () => {});
      reject(err);
    });
  });
}

async function downloadAll() {
  console.log('Downloading cinematic sci-fi BGM tracks...');
  for (const t of tracks) {
    const dest = path.join(dir, t.name);
    await downloadFile(t.url, dest);
  }
  console.log('All BGM tracks downloaded successfully!');
}

downloadAll().catch(console.error);
