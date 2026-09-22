import os
import sys
import json
import asyncio
import subprocess
import requests
import edge_tts

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)

DATABASE_FILE = 'pipeline/topics_database.json'
OUTPUT_DIR = 'output'
VOICE = 'en-US-ChristopherNeural'
BGM_FILE = 'pipeline/assets/bgm.mp3'

def format_ass_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"

def get_next_topic():
    with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
        topics = json.load(f)
    for topic in topics:
        if not topic.get('used', False):
            return topic
    # If all used, reset
    for topic in topics:
        topic['used'] = False
    with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
        json.dump(topics, f, indent=2)
    return topics[0]

def download_footage(url, dest_path):
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 100000:
        print(f"Footage already exists at: {dest_path}")
        return

    candidate_urls = [
        url,
        "https://assets.mixkit.co/videos/15209/15209-720.mp4",
        "https://images-assets.nasa.gov/video/GSFC_20190925_BlackHole_m13442/GSFC_20190925_BlackHole_m13442~medium.mp4"
    ]

    for c_url in candidate_urls:
        if not c_url:
            continue
        try:
            print(f'Attempting download footage from: {c_url}')
            res = requests.get(c_url, stream=True, timeout=40, headers={'User-Agent': 'Mozilla/5.0'})
            res.raise_for_status()
            with open(dest_path, 'wb') as f:
                for chunk in res.iter_content(chunk_size=1024*1024):
                    if chunk:
                        f.write(chunk)
            if os.path.exists(dest_path) and os.path.getsize(dest_path) > 50000:
                print(f'Footage saved successfully to: {dest_path}')
                return
        except Exception as e:
            print(f"Warning: Could not fetch {c_url} ({e}), trying next fallback...")
            continue

    print("Generating fallback high-res cinematic background via FFmpeg...")
    fallback_cmd = (
        f'ffmpeg -y -f lavfi -i "mandelbrot=size=1080x1920:rate=30" '
        f'-t 60 -c:v libx264 -pix_fmt yuv420p "{dest_path}"'
    )
    subprocess.run(fallback_cmd, shell=True, check=True)
    print(f"Procedural fallback footage created at {dest_path}")

async def generate_voice(text, dest_path):
    print('Generating natural neural voiceover...')
    communicate = edge_tts.Communicate(text, VOICE, rate='+3%')
    await communicate.save(dest_path)
    print(f'Voice saved to: {dest_path}')

def get_media_duration(file_path):
    cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{file_path}"'
    out = subprocess.check_output(cmd, shell=True, text=True).strip()
    return float(out)

def create_ass_subtitles(topic, duration, ass_path):
    top_header = topic.get('top_header', 'MIND-BLOWING ODD FACTS')
    sub_header = topic.get('sub_header', 'SOUND FAKE BUT 100% REAL!')

    # Color map for ASS (BGR format: &HAABBGGRR)
    # Yellow: &H0000FFFF, Cyan: &H00FFFF00, Coral/Pink: &H005040FF, Orange: &H0000A5FF, Green: &H0033FF33, White: &H00FFFFFF
    style_colors = {
        '#FFFF00': '&H0000FFFF&', # Vibrant Yellow
        '#00FFFF': '&H00FFFF00&', # Electric Cyan
        '#FF3366': '&H005040FF&', # Coral Red
        '#FF9900': '&H0000A5FF&', # Warm Amber
        '#00FF66': '&H0033FF33&', # Lime Green
        '#FFFFFF': '&H00FFFFFF&'  # Pure White
    }

    ass_lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        "PlayResX: 1080",
        "PlayResY: 1920",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: Badge,Arial Black,42,&H0000FFFF,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,2,0,1,5,3,8,40,40,160,1",
        "Style: Title,Arial Black,50,&H00FFFFFF,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,1,0,1,6,4,8,40,40,230,1",
        "Style: SubDefault,Arial Black,74,&H0000FFFF,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,1,0,1,7,4,2,40,40,420,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
        f"Dialogue: 0,0:00:00.00,{format_ass_time(duration)},Badge,,0,0,0,,★ FACTIFY SHORTS ★",
        f"Dialogue: 0,0:00:00.00,{format_ass_time(duration)},Title,,0,0,0,,{top_header}"
    ]

    for sub in topic.get('subtitles', []):
        start_t = sub['start']
        end_t = min(sub['end'], duration)
        if start_t >= duration:
            continue
        
        start_str = format_ass_time(start_t)
        end_str = format_ass_time(end_t)
        
        hex_col = sub.get('color', '#FFFFFF')
        ass_color = style_colors.get(hex_col, '&H00FFFFFF&')

        raw_text = sub['text']
        # Format text to 2 lines if longer than 20 chars
        words = raw_text.split()
        if len(words) > 3 and len(raw_text) > 20:
            mid = len(words) // 2
            formatted_text = " ".join(words[:mid]) + "\\N" + " ".join(words[mid:])
        else:
            formatted_text = raw_text

        # Bouncy pop-in animation: begins at 122% scale, snaps smoothly to 100% in 110ms
        anim_tag = f"{{\\c{ass_color}\\3c&H00000000&\\bord7\\shad4\\fscx122\\fscy122\\t(0,110,\\fscx100\\fscy100)}}"
        dialogue_line = f"Dialogue: 1,{start_str},{end_str},SubDefault,,0,0,0,,{anim_tag}{formatted_text}"
        ass_lines.append(dialogue_line)

    with open(ass_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(ass_lines))
    print(f"Generated animated ASS subtitles: {ass_path}")

def render_short(topic, footage_path, audio_path, output_path):
    duration = get_media_duration(audio_path)
    print(f'Voice duration: {duration:.2f}s')

    ass_path = 'temp/subtitles_animated.ass'
    create_ass_subtitles(topic, duration, ass_path)

    has_bgm = os.path.exists(BGM_FILE)
    
    # Filter Complex:
    # 1. Full-screen 9:16 vertical crop with slight contrast & saturation boost
    # 2. Burn in animated ASS subtitles
    # 3. Audio mix: Voice (1.0) + Subtle BGM (0.12)
    
    filter_complex = (
        f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,eq=contrast=1.05:saturation=1.15,ass={ass_path}[outv]; "
    )
    
    if has_bgm:
        filter_complex += (
            f"[1:a]volume=1.0[voice]; "
            f"[2:a]volume=0.12[bgm]; "
            f"[voice][bgm]amix=inputs=2:duration=first:dropout_transition=2[outa]"
        )
        ffmpeg_cmd = [
            'ffmpeg', '-y',
            '-stream_loop', '-1', '-i', footage_path,
            '-i', audio_path,
            '-stream_loop', '-1', '-i', BGM_FILE,
            '-filter_complex', filter_complex,
            '-map', '[outv]',
            '-map', '[outa]',
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '17',
            '-c:a', 'aac',
            '-b:a', '256k',
            '-t', f"{duration:.2f}",
            output_path
        ]
    else:
        filter_complex += "[1:a]volume=1.0[outa]"
        ffmpeg_cmd = [
            'ffmpeg', '-y',
            '-stream_loop', '-1', '-i', footage_path,
            '-i', audio_path,
            '-filter_complex', filter_complex,
            '-map', '[outv]',
            '-map', '[outa]',
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '17',
            '-c:a', 'aac',
            '-b:a', '256k',
            '-t', f"{duration:.2f}",
            output_path
        ]

    print(f'Rendering studio-quality vertical 9:16 Short (exact duration: {duration:.2f}s)...')
    subprocess.run(ffmpeg_cmd, check=True, timeout=300)
    print(f'Short rendered successfully: {output_path}')

def generate_metadata(topic):
    title = topic['title']
    tags = topic.get('tags', [])
    tags_str = ' '.join(['#' + t.replace(' ', '') for t in tags[:8]])

    description = (
        f"{title}\n\n"
        f"Discover 3 mind-blowing odd facts that sound 100% fake, but are completely real! "
        f"From the unbelievable weight of clouds to prehistoric sharks and immortal honey, "
        f"these bizarre truths from nature and science will leave you amazed.\n\n"
        f"📌 Facts in this Short:\n"
        f"• Fact 1: How much does a single fluffy cloud weigh? (100 elephants floating!)\n"
        f"• Fact 2: Why sharks are older than trees on planet Earth (400M vs 350M years)\n"
        f"• Fact 3: Why 3,000-year-old honey in Egyptian tombs never ever spoils\n\n"
        f"🗣️ Video Transcript:\n"
        f"\"{topic['script']}\"\n\n"
        f"🔔 Subscribe to @FactifyDailyShorts for your daily dose of mind-blowing facts, odd mysteries, and psychology truths!\n"
        f"👍 If you learned something new today, leave a like and share with a friend!\n\n"
        f"🔍 Related Search Queries:\n"
        f"mind blowing facts, odd facts, weird facts that sound fake, did you know facts, crazy facts you didnt know, "
        f"facts about the world, science facts, random facts, interesting facts, Factify Shorts, shorts\n\n"
        f"{tags_str}\n\n"
        f"Notice: This educational video is made for learning, informational, and curiosity purposes under fair use."
    )

    metadata = {
        'id': topic['id'],
        'title': title,
        'description': description,
        'tags': tags,
        'category_id': topic.get('category_id', '27')
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    meta_path = os.path.join(OUTPUT_DIR, 'metadata.json')
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    print(f'Metadata saved to: {meta_path}')
    return metadata

def main():
    os.makedirs('temp', exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    topic = get_next_topic()
    print(f"Selected Topic: {topic['title']} (ID: {topic['id']})")

    footage_path = f"temp/{topic['id']}_raw.mp4"
    audio_path = f"temp/{topic['id']}_voice.mp3"
    output_video_path = f"{OUTPUT_DIR}/factify_short_latest.mp4"

    download_footage(topic['footage_url'], footage_path)
    asyncio.run(generate_voice(topic['script'], audio_path))
    render_short(topic, footage_path, audio_path, output_video_path)
    generate_metadata(topic)

    print("\n" + "=" * 60)
    print("FACTIFY SHORT GENERATED SUCCESSFULLY!")
    print(f"Video Path: {os.path.abspath(output_video_path)}")
    print("=" * 60)

if __name__ == '__main__':
    main()
