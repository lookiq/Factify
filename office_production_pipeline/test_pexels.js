const https = require('https');

https.get('https://www.pexels.com/search/videos/cargo%20ship/', {
  headers: {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9'
  }
}, res => {
  let d = '';
  res.on('data', c => d += c);
  res.on('end', () => {
    console.log('Status:', res.statusCode);
    const vimeoMatches = d.match(/https:\/\/player\.vimeo\.com\/external\/[^"'\s]+/g) || [];
    const pexelsMatches = d.match(/https:\/\/(?:images|videos)\.pexels\.com\/video-files\/[^"'\s]+/g) || [];
    console.log('Vimeo matches:', vimeoMatches.length);
    console.log('Pexels matches:', pexelsMatches.length);
    if (pexelsMatches.length > 0) {
      console.log('Sample Pexels video:', pexelsMatches[0]);
    }
  });
}).on('error', console.error);
