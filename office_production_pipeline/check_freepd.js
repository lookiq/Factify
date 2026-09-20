const https = require('https');

function getPage(url) {
  return new Promise(resolve => {
    https.get(url, { headers: { 'User-Agent': 'Mozilla/5.0' } }, res => {
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => resolve(d));
    }).on('error', () => resolve(''));
  });
}

async function run() {
  const html = await getPage('https://freepd.com/epic.php');
  const mp3s = html.match(/https:\/\/[^"']+\.mp3/g) || [];
  console.log('FreePD Epic mp3s count:', mp3s.length);
  if (mp3s.length > 0) console.log('FreePD samples:', mp3s.slice(0, 5));

  // Also check Mixkit adventure track titles
  const mixkitHtml = await getPage('https://mixkit.co/free-stock-music/tag/adventure/');
  const matches = mixkitHtml.match(/<a[^>]*href="\/free-stock-music\/[0-9]+-[^"]+"[^>]*>([^<]+)<\/a>/g) || [];
  console.log('Mixkit adventure links count:', matches.length);
  matches.slice(0, 5).forEach(m => console.log(m));
}

run();
