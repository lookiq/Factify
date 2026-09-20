const https = require('https');
const fs = require('fs');
const path = require('path');

function getPage(url) {
  return new Promise(resolve => {
    https.get(url, { headers: { 'User-Agent': 'Mozilla/5.0' } }, res => {
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => resolve(d));
    }).on('error', () => resolve(''));
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

async function run() {
  const bgmDir = path.resolve('./assets/bgm');
  if (!fs.existsSync(bgmDir)) fs.mkdirSync(bgmDir, { recursive: true });

  const html = await getPage('https://mixkit.co/free-stock-music/tag/sci-fi/');
  // Match items with title and audio url
  const regex = /<h2[^>]*class="[^"]*item-grid-music__title[^"]*"[^>]*>([^<]+)<\/h2>[\s\S]*?(https:\/\/assets\.mixkit\.co\/music\/[0-9]+\/[0-9]+\.mp3)/g;
  let match;
  const tracks = [];
  while ((match = regex.exec(html)) !== null) {
    tracks.push({ title: match[1].trim(), url: match[2] });
  }

  console.log(`Found ${tracks.length} tracks with titles on sci-fi page:`);
  console.log(tracks.slice(0, 8));

  // Also check space
  const htmlSpace = await getPage('https://mixkit.co/free-stock-music/tag/space/');
  while ((match = regex.exec(htmlSpace)) !== null) {
    tracks.push({ title: match[1].trim(), url: match[2] });
  }

  console.log(`Total tracks found: ${tracks.length}`);
  
  // Let's download the top 3 cinematic sci-fi tracks
  for (let i = 0; i < Math.min(4, tracks.length); i++) {
    const t = tracks[i];
    const safeTitle = t.title.toLowerCase().replace(/[^a-z0-9]+/g, '_') + '.mp3';
    const dest = path.join(bgmDir, safeTitle);
    console.log(`Downloading track ${i + 1}: ${t.title} -> ${safeTitle}`);
    await downloadFile(t.url, dest);
  }
}

run().catch(console.error);
