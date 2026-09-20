const { EdgeTTS } = require('@andresaya/edge-tts');
const fs = require('fs');
const path = require('path');

async function test() {
  const tts = new EdgeTTS({
    voice: 'en-US-ChristopherNeural', // Deep, energetic, professional documentary narrator
    rate: '+5%',
    pitch: '-2Hz'
  });

  const text = "Did you know that there is a planet where it literally rains glass sideways?";
  console.log("Synthesizing audio for:", text);

  const outDir = path.join(__dirname, 'temp');
  if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });

  const audioPath = path.join(outDir, 'test_voice');
  await tts.synthesize(text, 'en-US-ChristopherNeural');
  const saved = await tts.toFile(audioPath);
  console.log("Audio saved successfully to:", saved);

  const boundaries = tts.getWordBoundaries();
  console.log("Word boundaries count:", boundaries ? boundaries.length : 0);
  if (boundaries && boundaries.length > 0) {
    console.log("Sample first 3 words:", JSON.stringify(boundaries.slice(0, 3), null, 2));
  }
}

test().catch(console.error);
