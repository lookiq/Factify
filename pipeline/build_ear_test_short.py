import os
import sys
import math
import wave
import struct
import asyncio
import subprocess
import edge_tts

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)

TEMP_DIR = 'temp'
OUTPUT_DIR = 'output'
BGM_FILE = 'pipeline/assets/bgm.mp3'
VOICE = 'en-US-ChristopherNeural'

# Timeline breakdown:
# 0.00s - 7.50s: Intro Voice
# 7.50s - 37.50s: Interactive Frequency Test (30 seconds)
# 37.50s - 44.50s: Outro Voice & Call to Action
TEST_START = 7.50
TEST_DURATION = 30.00
TOTAL_DURATION = 44.50

AGE_STEPS = [
    (7.50, 10.50, 90, 4000, "4,000 Hz"),
    (10.50, 13.50, 80, 6500, "6,500 Hz"),
    (13.50, 16.50, 70, 8500, "8,500 Hz"),
    (16.50, 19.50, 60, 10500, "10,500 Hz"),
    (19.50, 22.50, 50, 12000, "12,000 Hz"),
    (22.50, 25.50, 40, 13500, "13,500 Hz"),
    (25.50, 28.50, 30, 15000, "15,000 Hz"),
    (28.50, 31.50, 24, 16200, "16,200 Hz"),
    (31.50, 34.50, 20, 17200, "17,200 Hz"),
    (34.50, 37.50, 18, 18500, "18,500 Hz"),
]

def format_ass_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"

def generate_tone_wav(output_wav_path, sample_rate=44100):
    """Generates the audio track with exact silence + rising frequency tones."""
    print("Generating precision sine-wave tone audio...")
    total_samples = int(TOTAL_DURATION * sample_rate)
    test_start_sample = int(TEST_START * sample_rate)
    test_end_sample = int((TEST_START + TEST_DURATION) * sample_rate)

    raw_data = bytearray()
    
    # We will compute sample by sample
    current_phase = 0.0
    
    for i in range(total_samples):
        t = i / sample_rate
        if test_start_sample <= i < test_end_sample:
            # Find current frequency
            curr_freq = 4000.0
            for start, end, age, freq, label in AGE_STEPS:
                if start <= t < end:
                    curr_freq = float(freq)
                    break
            
            # Smoothly advance phase
            current_phase += 2.0 * math.pi * curr_freq / sample_rate
            if current_phase > 2.0 * math.pi:
                current_phase -= 2.0 * math.pi
            
            # Amplitude envelope (avoid clicking at start/end of test)
            amp = 0.28 # comfortable listening level
            if i - test_start_sample < 2000:
                amp *= (i - test_start_sample) / 2000.0
            elif test_end_sample - i < 2000:
                amp *= (test_end_sample - i) / 2000.0
                
            sample_val = int(amp * 32767.0 * math.sin(current_phase))
        else:
            sample_val = 0

        raw_data.extend(struct.pack('<h', sample_val))

    with wave.open(output_wav_path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(raw_data)
    print(f"Generated tone WAV: {output_wav_path}")

async def generate_speech_tracks():
    print("Generating speech audio tracks...")
    intro_text = "Scientists created a sound that can determine the exact age of your ears. Put on headphones and listen closely. The number where you stop hearing the sound is your true ear age!"
    outro_text = "What number did you stop hearing it at? Comment your ear age below! And subscribe to Factify for more daily mind-bending tests!"

    intro_path = os.path.join(TEMP_DIR, 'ear_intro.mp3')
    outro_path = os.path.join(TEMP_DIR, 'ear_outro.mp3')

    c1 = edge_tts.Communicate(intro_text, VOICE, rate='+2%')
    await c1.save(intro_path)
    c2 = edge_tts.Communicate(outro_text, VOICE, rate='+2%')
    await c2.save(outro_path)
    print("Speech tracks generated.")
    return intro_path, outro_path

def build_ass_subtitles(ass_path):
    print("Building advanced interactive ASS subtitles...")
    ass_lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        "PlayResX: 1080",
        "PlayResY: 1920",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: RadiumSub,Arial Black,64,&H0000FF16,&H00000000,&H00003005,&H00000000,-1,0,0,0,100,100,1,0,1,2.8,4.5,2,50,50,620,1",
        "Style: Watermark,Arial Black,34,&H80FFFFFF,&H00000000,&H60000000,&H90000000,-1,0,0,0,100,100,2,0,1,1.5,2.0,2,40,40,170,1",
        "Style: CardBox,Arial Black,38,&H00FFFFFF,&H00000000,&H00000000,&HB0000000,-1,0,0,0,100,100,1,0,3,10,0,5,40,40,0,1",
        "Style: CardTitle,Arial Black,48,&H0000FFFF,&H00000000,&H00000000,&H00000000,-1,0,0,0,100,100,2,0,1,2.0,3.0,2,40,40,1260,1",
        "Style: BigAge,Arial Black,150,&H0000FF16,&H00000000,&H00002000,&H90000000,-1,0,0,0,100,100,1,0,1,3.5,6.0,2,40,40,940,1",
        "Style: FreqLabel,Arial Black,40,&H00FFFFFF,&H00000000,&H00000000,&H90000000,-1,0,0,0,100,100,2,0,1,2.0,3.0,2,40,40,840,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
        # Watermark persistent across entire video
        f"Dialogue: 0,0:00:00.00,{format_ass_time(TOTAL_DURATION)},Watermark,,0,0,0,,@FactifyDailyShorts"
    ]

    # Intro dialogue lines (0 to 7.5s)
    intro_subs = [
        (0.0, 3.8, '"HOW OLD ARE YOUR EARS?"', '&H0000FFFF&'),
        (3.8, 5.8, '"PUT ON HEADPHONES NOW!"', '&H0000FF16&'),
        (5.8, 7.5, '"LISTEN VERY CLOSELY..."', '&H00FFFFFF&'),
    ]
    for s, e, txt, col in intro_subs:
        tag = f"{{\\c{col}\\3c&H00002000&\\bord2.8\\shad4.5\\fscx108\\fscy108\\t(0,80,\\fscx100\\fscy100)}}"
        ass_lines.append(f"Dialogue: 1,{format_ass_time(s)},{format_ass_time(e)},RadiumSub,,0,0,0,,{tag}{txt}")

    # Interactive Card (7.5s to 37.5s)
    t_start = format_ass_time(TEST_START)
    t_end = format_ass_time(TEST_START + TEST_DURATION)

    # Card Title
    ass_lines.append(f"Dialogue: 1,{t_start},{t_end},CardTitle,,0,0,0,,{{\\c&H0000FFFF&\\3c&H00000000&\\bord2.5\\shad3.0}}TESTING YOUR EAR AGE...")

    # Age Steps with bounce animation
    for start, end, age, freq, label in AGE_STEPS:
        s_str = format_ass_time(start)
        e_str = format_ass_time(end)
        
        # Color coding: Green for elder/easy, Yellow for middle, Red/Pink for youth/extreme
        if age >= 60:
            age_col = '&H0000FF16&' # Radium Green
        elif age >= 30:
            age_col = '&H0000FFFF&' # Bright Yellow
        elif age >= 20:
            age_col = '&H0000A5FF&' # Neon Orange
        else:
            age_col = '&H003333FF&' # Radiant Red / Teenager
            
        anim = f"{{\\c{age_col}\\3c&H00002000&\\bord3.5\\shad6.0\\fscx115\\fscy115\\t(0,100,\\fscx100\\fscy100)}}"
        ass_lines.append(f"Dialogue: 2,{s_str},{e_str},BigAge,,0,0,0,,{anim}{age}")
        ass_lines.append(f"Dialogue: 2,{s_str},{e_str},FreqLabel,,0,0,0,,{{\\c&H00FFFFFF&\\3c&H00000000&\\bord2.0\\shad3.0}}FREQUENCY: {label}")

    # Outro dialogue lines (37.5s to 44.5s)
    outro_subs = [
        (37.5, 41.0, '"WHAT NUMBER DID YOU HEAR?"', '&H0000FFFF&'),
        (41.0, 43.0, '"COMMENT YOUR EAR AGE BELOW!"', '&H0000FF16&'),
        (43.0, 44.5, '"SUBSCRIBE TO FACTIFY!"', '&H0000FFCC&')
    ]
    for s, e, txt, col in outro_subs:
        tag = f"{{\\c{col}\\3c&H00002000&\\bord2.8\\shad4.5\\fscx108\\fscy108\\t(0,80,\\fscx100\\fscy100)}}"
        ass_lines.append(f"Dialogue: 1,{format_ass_time(s)},{format_ass_time(e)},RadiumSub,,0,0,0,,{tag}{txt}")

    with open(ass_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(ass_lines))
    print(f"Generated interactive ASS subtitles: {ass_path}")

def render_ear_test_short(footage_path, output_path):
    intro_path, outro_path = asyncio.run(generate_speech_tracks())
    tone_wav_path = os.path.join(TEMP_DIR, 'ear_tones.wav')
    generate_tone_wav(tone_wav_path)

    ass_path = 'temp/ear_test_subtitles.ass'
    build_ass_subtitles(ass_path)
    safe_ass = ass_path.replace('\\', '/')

    # Audio mixing complex:
    # Inputs:
    # 0: video footage
    # 1: ear_tones.wav (precision frequency sweep)
    # 2: ear_intro.mp3 (voiceover)
    # 3: ear_outro.mp3 (voiceover)
    # 4: bgm.mp3 (ambient music)
    
    # Filter complex logic:
    # 1. Video: scale/crop to 1080x1920, boost contrast & saturation, burn in ASS subtitles
    # 2. Audio:
    #    - intro voice at t=0
    #    - outro voice at t=37.5s (adelay)
    #    - tones at 100% volume from 7.5s to 37.5s
    #    - subtle bgm ducked during intro & outro, muted during tone test
    filter_complex = (
        f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,eq=contrast=1.10:saturation=1.20,ass={safe_ass}[outv]; "
        f"[2:a]volume=1.25[intro_v]; "
        f"[3:a]adelay=37500|37500,volume=1.25[outro_v]; "
        f"[1:a]volume=1.0[tones]; "
        f"[4:a]volume=0.15[bgm_raw]; "
        f"[intro_v][outro_v][tones][bgm_raw]amix=inputs=4:duration=first:dropout_transition=1[outa]"
    )

    cmd = [
        'ffmpeg', '-y',
        '-stream_loop', '-1', '-i', footage_path,
        '-i', tone_wav_path,
        '-i', intro_path,
        '-i', outro_path,
        '-stream_loop', '-1', '-i', BGM_FILE,
        '-filter_complex', filter_complex,
        '-map', '[outv]',
        '-map', '[outa]',
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '17',
        '-c:a', 'aac',
        '-b:a', '256k',
        '-t', str(TOTAL_DURATION),
        output_path
    ]

    print("Rendering final Ear Age Test Short via FFmpeg...")
    subprocess.run(cmd, check=True)
    print(f"Short generated successfully: {output_path}")

def generate_ear_metadata():
    title = "How Old Are Your Ears? (Take The Audio Test!) 👂🔊 #Shorts"
    description = (
        "How Old Are Your Ears? (Take The Audio Test!) 👂🔊 #Shorts\n\n"
        "🎧 Put on your headphones and take the viral ear age challenge!\n"
        "Can you hear the high frequencies? As we age, our ears naturally lose the ability to hear high pitch sounds.\n\n"
        "📊 Hearing Scale:\n"
        "• 4,000 Hz = 90 Years Old\n"
        "• 8,500 Hz = 70 Years Old\n"
        "• 12,000 Hz = 50 Years Old\n"
        "• 15,000 Hz = 30 Years Old\n"
        "• 17,200 Hz = 20 Years Old\n"
        "• 18,500 Hz = Under 18 (Teenager Hearing!)\n\n"
        "💬 Comment your ear age below! At what number did the sound disappear for you?\n\n"
        "🔔 Subscribe to @FactifyDailyShorts for more daily viral science challenges, mind-blowing facts, and illusions!\n\n"
        "#earage #hearingtest #audiotest #science #facts #factify #shorts #soundtest #earagetest\n\n"
        "Notice: Educational hearing frequency challenge for curiosity purposes."
    )
    tags = [
        "ear age test",
        "hearing test",
        "how old are your ears",
        "sound test",
        "frequency test",
        "audio test",
        "ear test",
        "can you hear this",
        "Factify",
        "shorts",
        "science"
    ]
    meta = {
        'id': 'ear_age_frequency_test',
        'title': title,
        'description': description,
        'tags': tags,
        'category_id': '27'
    }
    with open(os.path.join(OUTPUT_DIR, 'metadata.json'), 'w', encoding='utf-8') as f:
        import json
        json.dump(meta, f, indent=2)
    print("Metadata saved to output/metadata.json")

if __name__ == '__main__':
    footage = 'temp/galaxy_bg.mp4'
    output = os.path.join(OUTPUT_DIR, 'factify_short_latest.mp4')
    render_ear_test_short(footage, output)
    generate_ear_metadata()
