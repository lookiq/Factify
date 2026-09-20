const https = require('https');
const fs = require('fs');
const path = require('path');

function getMp4s(url) {
  return new Promise(resolve => {
    https.get(url, { headers: { 'User-Agent': 'Mozilla/5.0' } }, res => {
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => {
        const mp4s = Array.from(new Set(d.match(/https:\/\/assets\.mixkit\.co\/videos\/[0-9]+\/[0-9]+-720\.mp4/g) || []));
        resolve(mp4s);
      });
    }).on('error', () => resolve([]));
  });
}

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

async function fetchMore() {
  const dir = path.resolve('./temp/real_clips');
  const queries = ['waves', 'water', 'metal', 'dock', 'worker'];
  let count = 0;
  for (const q of queries) {
    const urls = await getMp4s(`https://mixkit.co/free-stock-video/${q}/`);
    if (urls.length > 0) {
      const dest = path.join(dir, `clip_extra_${q}.mp4`);
      console.log(`Downloading extra clip for "${q}":`, urls[0]);
      await downloadFile(urls[0], dest);
      count++;
    }
  }
  console.log(`Added ${count} more real video clips!`);
}

fetchMore().catch(console.error);
