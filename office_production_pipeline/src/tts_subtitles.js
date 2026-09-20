const { EdgeTTS } = require('@andresaya/edge-tts');
const fs = require('fs');
const path = require('path');

// Helper to convert ticks (100-nanosecond units) to ASS timestamp format: H:MM:SS.cs
function ticksToAssTime(ticks) {
  const totalSeconds = ticks / 10000000;
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = Math.floor(totalSeconds % 60);
  const centiseconds = Math.floor((totalSeconds % 1) * 100);

  const pad = (num, size = 2) => String(num).padStart(size, '0');
  return `${hours}:${pad(minutes)}:${pad(seconds)}.${pad(centiseconds)}`;
}

/**
 * Generate .ASS subtitle content with word-by-word active highlight (Factition / Hormozi style)
 * Group words into short 3-4 word phrases with active word highlighted in bright yellow!
 */
function generateAssSubtitles(wordBoundaries) {
  if (!wordBoundaries || wordBoundaries.length === 0) return '';

  const assHeader = `[Script Info]
Title: Factition YouTube Shorts Word Highlights
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial Black,72,&H00FFFFFF,&H0000FFFF,&H00000000,&H90000000,-1,0,0,0,100,100,1,0,1,6,3,2,60,60,520,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
`;

  // Group words into phrases of 3 to 4 words
  const PHRASE_SIZE = 3;
  let events = [];

  for (let i = 0; i < wordBoundaries.length; i += PHRASE_SIZE) {
    const chunk = wordBoundaries.slice(i, i + PHRASE_SIZE);
    if (chunk.length === 0) continue;

    // For each word in the chunk, generate an event where that word is highlighted
    for (let wIndex = 0; wIndex < chunk.length; wIndex++) {
      const activeWord = chunk[wIndex];
      const start = ticksToAssTime(activeWord.offset);
      const end = ticksToAssTime(activeWord.offset + activeWord.duration);

      // Build the line: inactive words in white (&H00FFFFFF), active word in yellow (&H0000FFFF) with slight pop
      const lineText = chunk.map((w, idx) => {
        const cleanWord = (w.text || '').toUpperCase();
        if (idx === wIndex) {
          // Yellow highlight with punch
          return `{\\c&H0020FFFF&\\b1\\fscx108\\fscy108}${cleanWord}{\\r}`;
        } else {
          return `{\\c&H00FFFFFF&\\b1}${cleanWord}{\\r}`;
        }
      }).join(' ');

      events.push(`Dialogue: 0,${start},${end},Default,,0,0,0,,${lineText}`);
    }
  }

  return assHeader + events.join('\n') + '\n';
}

/**
 * Synthesize voiceover and generate .ass subtitles
 */
async function createVoiceoverAndSubtitles(scriptText, outputBaseName = 'voiceover') {
  const tts = new EdgeTTS({
    voice: 'en-US-ChristopherNeural', // Confident, energetic, clear documentary narrator
    rate: '+5%',
    pitch: '-2Hz'
  });

  const tempDir = path.join(__dirname, '..', 'temp');
  if (!fs.existsSync(tempDir)) fs.mkdirSync(tempDir, { recursive: true });

  const audioPrefix = path.join(tempDir, outputBaseName);
  console.log("Synthesizing voiceover with Edge TTS (Christopher)...");
  await tts.synthesize(scriptText, 'en-US-ChristopherNeural');
  
  const audioFilePath = await tts.toFile(audioPrefix);
  console.log("Audio saved to:", audioFilePath);

  const wordBoundaries = tts.getWordBoundaries();
  console.log(`Generated ${wordBoundaries.length} word timestamps.`);

  const assContent = generateAssSubtitles(wordBoundaries);
  const assFilePath = path.join(tempDir, `${outputBaseName}.ass`);
  fs.writeFileSync(assFilePath, assContent, 'utf-8');
  console.log("Subtitles saved to:", assFilePath);

  // Return estimated audio duration in seconds
  const totalTicks = wordBoundaries.length > 0 
    ? (wordBoundaries[wordBoundaries.length - 1].offset + wordBoundaries[wordBoundaries.length - 1].duration)
    : 0;
  const durationSeconds = totalTicks / 10000000;

  return {
    audioPath: audioFilePath,
    assPath: assFilePath,
    duration: durationSeconds,
    wordBoundaries
  };
}

module.exports = {
  createVoiceoverAndSubtitles
};
