const https = require('https');

function test(url) {
  return new Promise(resolve => {
    https.get(url, { headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)' } }, res => {
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => {
        const mp4s = d.match(/https:\/\/[^"']+\.mp4/g) || [];
        resolve({ status: res.statusCode, mp4Count: mp4s.length, sample: mp4s.slice(0, 3) });
      });
    }).on('error', e => resolve({ error: e.message }));
  });
}

async function run() {
  const r1 = await test('https://mixkit.co/free-stock-video/ship/');
  console.log('Mixkit ship:', r1);
  const r2 = await test('https://mixkit.co/free-stock-video/ocean/');
  console.log('Mixkit ocean:', r2);
}

run();
