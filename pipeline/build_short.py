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
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 1000000:
        print(f"High-quality footage already exists at: {dest_path}")
        return

    # Auto-upgrade any 720p URL to 1080p master quality
    url_1080 = url.replace('-720.mp4', '-1080.mp4') if url else ''

    candidate_urls = [
        url_1080,
        url,
        "https://images-assets.nasa.gov/video/GSFC_20190925_BlackHole_m13442/GSFC_20190925_BlackHole_m13442~medium.mp4",
        "https://assets.mixkit.co/videos/1195/1195-1080.mp4"
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

def prepare_footage(topic, total_duration, dest_path):
    scenes = topic.get('scenes')
    if not scenes:
        download_footage(topic.get('footage_url'), dest_path)
        return

    print(f"Detected {len(scenes)} topic-specific visual scenes for: {topic['title']}")
    scene_files = []
    
    # Calculate scene durations so they sum up to total_duration
    scene_durations = []
    total_assigned = sum(sc.get('duration', 0) for sc in scenes)
    if total_assigned <= 0:
        each_d = total_duration / len(scenes)
        scene_durations = [each_d] * len(scenes)
    else:
        # Scale proportionally to exact total_duration
        scale_factor = total_duration / total_assigned
        scene_durations = [sc.get('duration', total_duration/len(scenes)) * scale_factor for sc in scenes]

    for idx, sc in enumerate(scenes):
        sc_dur = scene_durations[idx]
        sc_url = sc.get('clip_url')
        sc_type = sc.get('type', 'video')
        sc_raw = f"temp/{topic['id']}_sc_{idx}_raw.mp4" if sc_type == 'video' else f"temp/{topic['id']}_sc_{idx}.jpg"
        sc_norm = f"temp/{topic['id']}_sc_{idx}_norm.mp4"

        print(f"  [Scene {idx+1}/{len(scenes)}] {sc.get('label', 'Visual')} ({sc_dur:.2f}s)...")
        if sc_type == 'video':
            download_footage(sc_url, sc_raw)
            cmd = [
                'ffmpeg', '-y', '-stream_loop', '-1', '-i', sc_raw,
                '-t', f"{sc_dur:.2f}",
                '-vf', 'scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30',
                '-c:v', 'libx264', '-crf', '18', '-an', sc_norm
            ]
            subprocess.run(cmd, check=True)
        else:
            if not os.path.exists(sc_raw) and sc_url:
                try:
                    r = requests.get(sc_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=20)
                    with open(sc_raw, 'wb') as f:
                        f.write(r.content)
                except Exception as e:
                    print(f"Warning: could not download scene visual {sc_url}: {e}")
            frames = max(30, int(30 * sc_dur))
            cmd = [
                'ffmpeg', '-y', '-loop', '1', '-i', sc_raw,
                '-t', f"{sc_dur:.2f}",
                '-vf', f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='min(zoom+0.001,1.15)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920,setsar=1,fps=30",
                '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', '-an', sc_norm
            ]
            subprocess.run(cmd, check=True)

        scene_files.append(sc_norm)

    concat_txt = f"temp/{topic['id']}_concat.txt"
    with open(concat_txt, 'w', encoding='utf-8') as f:
        for sf in scene_files:
            abs_p = os.path.abspath(sf).replace('\\', '/')
            f.write(f"file '{abs_p}'\n")

    concat_cmd = [
        'ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', concat_txt,
        '-c', 'copy', dest_path
    ]
    subprocess.run(concat_cmd, check=True)
    print(f"Multi-scene visual master assembled: {dest_path}")

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

    # Radium & Neon luminescent color map (BGR format: &HAABBGGRR)
    # Radium Green: #39FF14 -> &H0014FF39, Radium Lime: #CCFF00 -> &H0000FFCC
    # Radium Cyan: #00FFFF -> &H00FFFF00, Radium Coral: #FF3366 -> &H006633FF
    style_colors = {
        '#39FF14': '&H0014FF39&', # Pure Radium Electric Green
        '#CCFF00': '&H0000FFCC&', # Radioactive Radium Lime
        '#00FFFF': '&H00FFFF00&', # Luminescent Cyan
        '#FFFF00': '&H0000FFFF&', # Vibrant Neon Yellow
        '#FF3366': '&H006633FF&', # Radium Coral Pink
        '#FF9900': '&H0000A5FF&', # Glowing Amber
        '#00FF66': '&H0014FF39&', # Radium Lime
        '#FFFFFF': '&H00FFFFFF&'  # Crisp White
    }

    watermark_text = topic.get('watermark_text', '@FactifyDailyShorts')
    wm_size = 34 if len(watermark_text) > 10 else 44
    wm_spacing = 2 if len(watermark_text) > 10 else 4

    ass_lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        "PlayResX: 1080",
        "PlayResY: 1920",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: RadiumSub,Arial Black,66,&H0000FF16,&H00000000,&H00003005,&H00000000,-1,0,0,0,100,100,1,0,1,2.8,4.5,2,50,50,620,1",
        f"Style: Watermark,Arial Black,{wm_size},&H80FFFFFF,&H00000000,&H60000000,&H90000000,-1,0,0,0,100,100,{wm_spacing},0,1,1.5,2.0,2,40,40,170,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
        f"Dialogue: 0,0:00:00.00,{format_ass_time(duration)},Watermark,,0,0,0,,{watermark_text}"
    ]

    for sub in topic.get('subtitles', []):
        start_t = sub['start']
        end_t = min(sub['end'], duration)
        if start_t >= duration:
            continue
        
        start_str = format_ass_time(start_t)
        end_str = format_ass_time(end_t)
        
        hex_col = sub.get('color', '#39FF14')
        ass_color = style_colors.get(hex_col, '&H0000FF16&')

        raw_text = sub['text']
        # Format text to 2 lines if longer than 20 chars
        words = raw_text.split()
        if len(words) > 3 and len(raw_text) > 20:
            mid = len(words) // 2
            formatted_text = " ".join(words[:mid]) + r"\N" + " ".join(words[mid:])
        else:
            formatted_text = raw_text

        # Add stylish quotes around text matching user reference
        quoted_text = f'"{formatted_text}"'

        # Radium 3D Drop-Shadow Animation: 2.8 outline + 4.5 solid shadow
        anim_tag = f"{{\\c{ass_color}\\3c&H00002000&\\bord2.8\\shad4.5\\fscx108\\fscy108\\t(0,80,\\fscx100\\fscy100)}}"
        dialogue_line = f"Dialogue: 1,{start_str},{end_str},RadiumSub,,0,0,0,,{anim_tag}{quoted_text}"
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
    
    footage_args = []
    if topic.get('footage_start_sec'):
        footage_args = ['-ss', str(topic['footage_start_sec'])]

    # Filter Complex:
    # 1. Full-screen 9:16 vertical crop with contrast & saturation enhancement
    # 2. Burn in clean modern animated ASS subtitles
    # 3. Balanced audio mix: Voice (1.0) + Subtle BGM (0.12)
    filter_complex = (
        f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,eq=contrast=1.08:saturation=1.15,ass={ass_path}[outv]; "
    )
    
    if has_bgm:
        filter_complex += (
            f"[1:a]volume=1.0[voice]; "
            f"[2:a]volume=0.12[bgm]; "
            f"[voice][bgm]amix=inputs=2:duration=first:dropout_transition=2[outa]"
        )
        ffmpeg_cmd = [
            'ffmpeg', '-y',
            *footage_args,
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
            *footage_args,
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

    top_header = topic.get('top_header', 'MIND-BLOWING FACTS')
    sub_header = topic.get('sub_header', '')

    description = (
        f"{title}\n\n"
        f"🔥 {top_header}: {sub_header}\n"
        f"Discover mind-blowing facts that will completely change how you see the world!\n\n"
        f"🗣️ Video Transcript:\n"
        f"\"{topic['script']}\"\n\n"
        f"🔔 Subscribe to @FactifyDailyShorts for your daily dose of mind-blowing facts, odd mysteries, and science truths!\n"
        f"👍 If you learned something new today, leave a like and share with a friend!\n\n"
        f"🔍 Related Search Queries:\n"
        f"{', '.join(tags)}, mind blowing facts, odd facts, weird facts that sound fake, did you know facts, crazy facts you didnt know, science facts, Factify Shorts, shorts\n\n"
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

    asyncio.run(generate_voice(topic['script'], audio_path))
    duration = get_media_duration(audio_path)
    prepare_footage(topic, duration, footage_path)
    render_short(topic, footage_path, audio_path, output_video_path)
    generate_metadata(topic)

    print("\n" + "=" * 60)
    print("FACTIFY SHORT GENERATED SUCCESSFULLY!")
    print(f"Video Path: {os.path.abspath(output_video_path)}")
    print("=" * 60)

if __name__ == '__main__':
    main()
