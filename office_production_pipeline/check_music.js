const https = require('https');

function getMp3s(url) {
  return new Promise(resolve => {
    https.get(url, { headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)' } }, res => {
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => {
        const mp3s = Array.from(new Set(d.match(/https:\/\/assets\.mixkit\.co\/music\/[^"']+\.mp3/g) || []));
        resolve({ status: res.statusCode, count: mp3s.length, sample: mp3s.slice(0, 5) });
      });
    }).on('error', e => resolve({ error: e.message }));
  });
}

async function run() {
  const tags = ['cinematic', 'sci-fi', 'space', 'ambient', 'drama'];
  for (const t of tags) {
    const res = await getMp3s(`https://mixkit.co/free-stock-music/tag/${t}/`);
    console.log(`Tag "${t}":`, res);
  }
}

run();
