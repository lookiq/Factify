const https = require('https');

https.get('https://mixkit.co/free-stock-music/tag/adventure/', { headers: { 'User-Agent': 'Mozilla/5.0' } }, res => {
  let d = '';
  res.on('data', c => d += c);
  res.on('end', () => {
    // Find titles and mp3s
    const blocks = d.split('item-grid-music');
    console.log('Blocks found:', blocks.length);
    for (let i = 1; i < blocks.length; i++) {
      const b = blocks[i];
      const titleMatch = b.match(/<span[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)<\/span>/i) || b.match(/data-title="([^"]+)"/i) || b.match(/<h2>([^<]+)<\/h2>/i);
      const mp3Match = b.match(/https:\/\/assets\.mixkit\.co\/music\/[0-9]+\/[0-9]+\.mp3/);
      console.log(`Track ${i}:`, titleMatch ? titleMatch[1] : 'No title', mp3Match ? mp3Match[0] : 'No mp3');
    }
  });
});
