const https = require('https');

function fetchUrl(url) {
  return new Promise((resolve, reject) => {
    https.get(url, { headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)' } }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve(data));
    }).on('error', reject);
  });
}

async function checkVideo() {
  const html = await fetchUrl('https://www.youtube.com/watch?v=7GlsxNI4LVI');
  const match = html.match(/ytInitialPlayerResponse\s*=\s*({.+?});/);
  if (match) {
    const data = JSON.parse(match[1]);
    console.log('Title:', data.videoDetails?.title);
    console.log('Author:', data.videoDetails?.author);
    console.log('Length:', data.videoDetails?.lengthSeconds);
    console.log('Description:', (data.videoDetails?.shortDescription || '').slice(0, 300));
  } else {
    console.log('Match failed');
  }
}

checkVideo().catch(console.error);
