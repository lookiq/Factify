const https = require('https');
const fs = require('fs');
const path = require('path');

const list = [
  { id: '676', url: 'https://assets.mixkit.co/music/676/676.mp3' },
  { id: '680', url: 'https://assets.mixkit.co/music/680/680.mp3' },
  { id: '677', url: 'https://assets.mixkit.co/music/677/677.mp3' },
  { id: '871', url: 'https://assets.mixkit.co/music/871/871.mp3' },
  { id: '706', url: 'https://assets.mixkit.co/music/706/706.mp3' }
];

const dir = path.resolve('./assets/bgm/adventure');
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
  for (const item of list) {
    const dest = path.join(dir, `adventure_${item.id}.mp3`);
    await downloadFile(item.url, dest);
  }
  console.log('Downloaded all adventure tracks!');
}

downloadAll().catch(console.error);
