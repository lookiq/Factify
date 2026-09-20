const { EdgeTTS } = require('@andresaya/edge-tts');
const fs = require('fs');
const path = require('path');

const script = [
  "This ordinary looking ship rope is actually one of the deadliest weapons on Earth.",
  "When massive one hundred thousand ton cargo ships dock, they are tied to the harbor using synthetic polymer lines as thick as a human leg.",
  "These ropes are stretched under astronomical tension.",
  "If even a single strand snaps, the entire rope acts like a giant slingshot.",
  "In maritime engineering, this lethal hazard is called the snapback zone.",
  "The severed line whips back at over seven hundred kilometers per hour.",
  "At that speed, the kinetic force is so violent that it can slice through steel railings and literally cut a human body in half in a split second.",
  "That is why sailors are trained to never step into the line of fire.",
  "Which deadly phenomenon should we uncover next? Subscribe to Factify Shorts."
];

const fullText = script.join(" ");

async function generateVoice() {
  console.log("Starting voice generation for Factify Shorts #1...");
  const tts = new EdgeTTS({
    voice: 'en-US-ChristopherNeural',
    rate: '+5%',
    pitch: '-2Hz'
  });

  const outDir = path.join(__dirname, 'output');
  const tempDir = path.join(__dirname, 'temp');
  if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });
  if (!fs.existsSync(tempDir)) fs.mkdirSync(tempDir, { recursive: true });

  const audioBase = path.join(tempDir, 'voice_short_1');
  await tts.synthesize(fullText, 'en-US-ChristopherNeural');
  const savedFile = await tts.toFile(audioBase);
  console.log("Audio successfully saved to:", savedFile);

  const boundaries = tts.getWordBoundaries();
  console.log("Total word boundaries captured:", boundaries ? boundaries.length : 0);

  fs.writeFileSync(path.join(tempDir, 'words.json'), JSON.stringify(boundaries, null, 2));

  // Generate ASS subtitles with Hormozi-style styling
  generateAssSubtitles(boundaries, path.join(tempDir, 'subtitles.ass'));
}

function formatAssTime(offsetNs) {
  const totalMs = Math.floor(offsetNs / 10000); // 100ns units to ms
  const ms = Math.floor((totalMs % 1000) / 10); // centiseconds
  const totalSeconds = Math.floor(totalMs / 1000);
  const s = totalSeconds % 60;
  const m = Math.floor(totalSeconds / 60) % 60;
  const h = Math.floor(totalSeconds / 3600);

  const pad = (n, len = 2) => String(n).padStart(len, '0');
  return `${h}:${pad(m)}:${pad(s)}.${pad(ms)}`;
}

function generateAssSubtitles(boundaries, outputPath) {
  // ASS header for 1080x1920 vertical video
  let ass = `[Script Info]
Title: Factify Shorts Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.601
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial Black,78,&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,8,4,2,40,40,680,1
Style: Highlight,Arial Black,84,&H0000E5FF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,105,105,0,0,1,10,6,2,40,40,680,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
`;

  if (!boundaries || boundaries.length === 0) return;

  // Group words into short 2-3 word chunks for viral fast shorts
  const chunkSize = 3;
  for (let i = 0; i < boundaries.length; i += chunkSize) {
    const chunk = boundaries.slice(i, i + chunkSize);
    const start = formatAssTime(chunk[0].offset);
    const lastWord = chunk[chunk.length - 1];
    const end = formatAssTime(lastWord.offset + lastWord.duration);
    
    // Capitalize and format text
    const text = chunk.map(w => w.text.toUpperCase()).join(" ");
    ass += `Dialogue: 0,${start},${end},Highlight,,0,0,0,,{\\c&H00E5FF&}${text}\n`;
  }

  fs.writeFileSync(outputPath, ass, 'utf-8');
  console.log("ASS Subtitles generated at:", outputPath);
}

generateVoice().catch(console.error);
