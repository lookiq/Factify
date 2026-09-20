const { EdgeTTS } = require('@andresaya/edge-tts');
const { execSync } = require('child_process');
const ffmpegPath = require('@ffmpeg-installer/ffmpeg').path;
const path = require('path');
const fs = require('fs');

function ticksToAssTime(ticks) {
  const totalSeconds = ticks / 10000000;
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = Math.floor(totalSeconds % 60);
  const centiseconds = Math.floor((totalSeconds % 1) * 100);
  const pad = (num, size = 2) => String(num).padStart(size, '0');
  return `${hours}:${pad(minutes)}:${pad(seconds)}.${pad(centiseconds)}`;
}

function generateAssSubtitles(wordBoundaries) {
  const assHeader = `[Script Info]
Title: Optical Illusion Kinetic Toy Subtitles
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial Black,68,&H00FFFFFF,&H0000FFFF,&H00000000,&H90000000,-1,0,0,0,100,100,1,0,1,6,3,2,60,60,520,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
`;

  const PHRASE_SIZE = 3;
  const events = [];

  for (let i = 0; i < wordBoundaries.length; i += PHRASE_SIZE) {
    const chunk = wordBoundaries.slice(i, i + PHRASE_SIZE);
    if (chunk.length === 0) continue;

    for (let wIndex = 0; wIndex < chunk.length; wIndex++) {
      const activeWord = chunk[wIndex];
      const start = ticksToAssTime(activeWord.offset);
      const end = ticksToAssTime(activeWord.offset + activeWord.duration);

      const lineText = chunk.map((w, idx) => {
        const cleanWord = (w.text || '').toUpperCase();
        if (idx === wIndex) {
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

async function buildKineticShort() {
  console.log("==================================================");
  console.log("🎬 BUILDING FACTIFY OPTICAL ILLUSION TOY SHORT");
  console.log("==================================================");

  const script = "You're probably wondering how this metal ball is floating in mid-air! This is the Luna kinetic toy. When spun, it creates an illusion making the ball seem to defy gravity. In reality, the rotating spiral helix tricks your brain into seeing levitation. Follow Factify for more!";

  const tts = new EdgeTTS({
    voice: 'en-US-ChristopherNeural',
    rate: '+15%',
    pitch: '-1Hz'
  });

  const tempDir = path.resolve('temp');
  const outDir = path.resolve('output');
  if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });

  console.log("1. Synthesizing English Voiceover (Christopher Neural)...");
  await tts.synthesize(script, 'en-US-ChristopherNeural');
  const voicePath = await tts.toFile(path.join(tempDir, 'kinetic_toy_voice_final'));
  const wordBoundaries = tts.getWordBoundaries();

  const assContent = generateAssSubtitles(wordBoundaries);
  const assPath = path.join(tempDir, 'kinetic_toy_subtitles.ass');
  fs.writeFileSync(assPath, assContent, 'utf-8');
  console.log("✅ Synced animated subtitles created:", assPath);

  const safeAssPath = assPath.replace(/\\/g, '/').replace(/:/g, '\\:');

  const videoInput = path.join(tempDir, 'target_short.mp4');
  const bgmInput = path.resolve('assets/bgm/cinematic_mystery_drama_614.mp3');
  const finalOutput = path.join(outDir, 'Factify_Short_Optical_Illusion_Toy.mp4');
  const desktopOutput = 'C:/Users/E-laerning & Earning/Desktop/Factify_Short_Optical_Illusion_Toy.mp4';

  console.log("2. Composing video with Watermark Swap, Subtitles & Audio Ducking...");

  // FFmpeg filter:
  // 1) Remove old watermark FACTITION using delogo
  // 2) Draw user's channel watermark FACTIFY
  // 3) Burn-in word-by-word yellow highlight subtitles
  // 4) Mix English voiceover with ducked BGM and normalize loudness
  const filterComplex = [
    `[0:v]delogo=x=210:y=1705:w=660:h=95,drawtext=text='FACTIFY':font='Arial Black':fontsize=80:fontcolor=white:x=(w-text_w)/2:y=1715:shadowcolor=black@0.7:shadowx=3:shadowy=3,ass='${safeAssPath}'[vout]`,
    `[1:a]volume=1.3[v]`,
    `[2:a]volume=0.14[m]`,
    `[v][m]amix=inputs=2:duration=first:dropout_transition=1,loudnorm=I=-14:TP=-1.5:LRA=9[aout]`
  ].join(';');

  // Offline SEO metadata embedded into MP4 container header
  const title = "This Kinetic Toy Defies Gravity! 🤯🔮 Optical Illusion #shorts";
  const artist = "Factify Shorts";
  const album = "Daily Science & Kinetic Mysteries";
  const comment = "Offline SEO: optical illusion toy, mezmoglobe, kinetic sculpture, floating ball, gravity illusion, satisfying desk toy";
  const description = "How is this metal ball floating in mid-air? This is the Luna kinetic desk toy! Watch how its rotating spiral helix tricks your brain into seeing gravity defiance.";
  const keywords = "shorts,optical illusion,kinetic toy,mezmoglobe,floating ball,gravity,satisfying,physics,facts,science,factify";

  const metaArgs = [
    `-metadata title="${title}"`,
    `-metadata artist="${artist}"`,
    `-metadata album_artist="${artist}"`,
    `-metadata album="${album}"`,
    `-metadata comment="${comment}"`,
    `-metadata description="${description}"`,
    `-metadata keywords="${keywords}"`,
    `-metadata genre="Science & Technology"`
  ].join(' ');

  const cmd = [
    `"${ffmpegPath}" -y`,
    `-i "${videoInput}"`,
    `-i "${voicePath}"`,
    `-stream_loop -1 -i "${bgmInput}"`,
    `-filter_complex "${filterComplex}"`,
    `-map "[vout]"`,
    `-map "[aout]"`,
    `-t 19.48`,
    metaArgs,
    `-c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p -r 60`,
    `-c:a aac -b:a 192k`,
    `"${finalOutput}"`
  ].join(' ');

  console.log("3. Executing FFmpeg render command...");
  execSync(cmd, { stdio: 'inherit' });

  if (fs.existsSync(finalOutput)) {
    const stats = fs.statSync(finalOutput);
    console.log(`\n==================================================`);
    console.log(`🎉 VIDEO CREATED SUCCESSFULLY!`);
    console.log(`Saved in project output folder: ${finalOutput} (${(stats.size / (1024 * 1024)).toFixed(2)} MB)`);
    
    // Copy to Desktop
    fs.copyFileSync(finalOutput, desktopOutput);
    console.log(`Saved copy to Desktop: ${desktopOutput}`);
    console.log(`==================================================`);
    return finalOutput;
  } else {
    throw new Error("Render finished but output file not found.");
  }
}

buildKineticShort().catch(console.error);
