const https = require('https');

function getMp3s(url) {
  return new Promise(resolve => {
    https.get(url, { headers: { 'User-Agent': 'Mozilla/5.0' } }, res => {
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => {
        const mp3s = Array.from(new Set(d.match(/https:\/\/assets\.mixkit\.co\/music\/[0-9]+\/[0-9]+\.mp3/g) || []));
        resolve({ count: mp3s.length, list: mp3s });
      });
    }).on('error', () => resolve({ count: 0, list: [] }));
  });
}

async function run() {
  const tags = ['adventure', 'epic', 'action', 'trailer'];
  for (const t of tags) {
    const res = await getMp3s(`https://mixkit.co/free-stock-music/tag/${t}/`);
    console.log(`Tag "${t}": ${res.count} tracks`);
    if (res.list.length > 0) {
      console.log(`  Samples:`, res.list.slice(0, 4));
    }
  }
}

run();
