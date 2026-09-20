const fs = require('fs');
const path = require('path');
const axios = require('axios');
const { execSync } = require('child_process');
const ffmpegPath = require('@ffmpeg-installer/ffmpeg').path;
require('dotenv').config();

const VIDEOS_DIR = path.join(__dirname, '..', 'assets', 'videos');
const MUSIC_DIR = path.join(__dirname, '..', 'assets', 'music');

/**
 * Ensures background ambient mystery music exists in assets/music/
 */
function ensureBackgroundMusic() {
  const musicPath = path.join(MUSIC_DIR, 'mystery_ambient.mp3');
  if (fs.existsSync(musicPath) && fs.statSync(musicPath).size > 1000) {
    return musicPath;
  }

  console.log("Generating subtle cinematic ambient mystery track with FFmpeg...");
  const cmd = `"${ffmpegPath}" -y -f lavfi -i "aevalsrc=sin(55*2*PI*t)*0.15 + sin(110*2*PI*t)*0.08 + sin(220*2*PI*t + sin(0.2*2*PI*t)*2)*0.04:s=44100:d=70" -af "lowpass=f=350,afade=t=in:ss=0:d=3,afade=t=out:st=65:d=5" -c:a libmp3lame -b:a 192k "${musicPath}"`;
  
  execSync(cmd, { stdio: 'ignore' });
  console.log("Ambient track created:", musicPath);
  return musicPath;
}

/**
 * Fetch or generate B-roll background video matching the topic (1080x1920 60FPS)
 */
async function getBrollVideo(searchQuery, durationSeconds = 45) {
  const targetPath = path.join(VIDEOS_DIR, 'bg_video.mp4');
  const targetDuration = Math.ceil(durationSeconds) + 2;

  // 1. Check if Pexels API Key is provided in .env
  const pexelsKey = process.env.PEXELS_API_KEY;
  if (pexelsKey) {
    try {
      console.log(`Searching Pexels for vertical stock clips: "${searchQuery}"...`);
      const response = await axios.get('https://api.pexels.com/videos/search', {
        headers: { Authorization: pexelsKey },
        params: {
          query: searchQuery || 'space galaxy stars mystery',
          orientation: 'portrait',
          per_page: 3
        },
        timeout: 10000
      });

      if (response.data && response.data.videos && response.data.videos.length > 0) {
        const video = response.data.videos[0];
        const videoFile = video.video_files.find(f => f.width && f.height && f.height > f.width) || video.video_files[0];
        if (videoFile && videoFile.link) {
          console.log("Downloading HD vertical stock video from Pexels...");
          const writer = fs.createWriteStream(targetPath);
          const downloadStream = await axios({
            url: videoFile.link,
            method: 'GET',
            responseType: 'stream'
          });
          downloadStream.data.pipe(writer);
          await new Promise((resolve, reject) => {
            writer.on('finish', resolve);
            writer.on('error', reject);
          });
          console.log("Downloaded Pexels B-roll clip successfully!");
          return targetPath;
        }
      }
    } catch (err) {
      console.warn("Pexels fetch notice:", err.message);
    }
  }

  // 2. High-speed cinematic documentary image zoompan engine
  // Uses our curated 4K cosmic images (cosmic_bg, planet_bg, galaxy_bg)
  console.log("Rendering high-speed 1080x1920 60FPS cinematic documentary visuals...");
  const images = ['planet_bg.jpg', 'cosmic_bg.jpg', 'galaxy_bg.jpg']
    .map(name => path.join(VIDEOS_DIR, name))
    .filter(p => fs.existsSync(p));

  const chosenImage = images[0] || path.join(VIDEOS_DIR, 'cosmic_bg.jpg');

  // Fast Ken Burns zoompan: 1080x1920 60FPS
  // Total frames = targetDuration * 60
  const totalFrames = targetDuration * 60;
  const filter = `scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='min(zoom+0.0004,1.35)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=${totalFrames}:s=1080x1920:fps=60`;
  
  const cmd = `"${ffmpegPath}" -y -loop 1 -i "${chosenImage}" -vf "${filter}" -t ${targetDuration} -c:v libx264 -preset veryfast -pix_fmt yuv420p -r 60 "${targetPath}"`;
  execSync(cmd, { stdio: 'ignore' });

  console.log("Cinematic vertical background video ready:", targetPath);
  return targetPath;
}

module.exports = {
  ensureBackgroundMusic,
  getBrollVideo
};
