const https = require('https');

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

async function findMore() {
  const terms = ['sea', 'crane', 'industrial', 'danger', 'boat'];
  for (const t of terms) {
    const urls = await getMp4s(`https://mixkit.co/free-stock-video/${t}/`);
    console.log(`Term "${t}": found ${urls.length} 720p MP4 clips`);
    if (urls.length > 0) {
      console.log(`  Samples:`, urls.slice(0, 3));
    }
  }
}

findMore();
