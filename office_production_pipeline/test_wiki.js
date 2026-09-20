const https = require('https');

const query = 'cargo ship';
const url = `https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=search&gsrsearch=${encodeURIComponent(query + ' filetype:video')}&gsrlimit=5&prop=imageinfo&iiprop=url|mime|size`;

https.get(url, { headers: { 'User-Agent': 'FactifyBot/1.0 (contact@factify.com)' } }, res => {
  let d = '';
  res.on('data', c => d += c);
  res.on('end', () => {
    try {
      const data = JSON.parse(d);
      const pages = data.query?.pages;
      if (pages) {
        Object.values(pages).forEach(p => {
          console.log(p.title, p.imageinfo?.[0]?.url);
        });
      } else {
        console.log('No pages found');
      }
    } catch(e) {
      console.log('Parse error:', e.message);
    }
  });
}).on('error', console.error);
