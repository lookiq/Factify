import os
import sys
import json
import asyncio
import subprocess
import wave
import requests
import edge_tts
import numpy as np

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)

DATABASE_FILE = 'pipeline/topics_database.json'
OUTPUT_DIR = 'output'
VOICE = 'en-US-ChristopherNeural'
BGM_FILE = 'pipeline/assets/bgm.mp3'
SFX_DIR = 'pipeline/assets/sfx'
WHOOSH_FILE = os.path.join(SFX_DIR, 'whoosh.wav')
IMPACT_FILE = os.path.join(SFX_DIR, 'impact.wav')

def ensure_sfx_assets():
    os.makedirs(SFX_DIR, exist_ok=True)
    sr = 44100
    
    if not os.path.exists(WHOOSH_FILE):
        print("Synthesizing studio cinematic whoosh SFX...")
        dur = 0.65
        n_samples = int(sr * dur)
        t = np.linspace(0, dur, n_samples, endpoint=False)
        white = np.random.uniform(-1, 1, n_samples)
        pink = np.convolve(white, [0.3, 0.4, 0.3], mode='same')
        env = np.exp(-((t - 0.38) ** 2) / (2 * (0.11 ** 2)))
        sweep_freq = 250 + 1800 * (t / dur) ** 2.2
        phase = 2 * np.pi * np.cumsum(sweep_freq) / sr
        whistle = np.sin(phase) * 0.4
        sig = (pink * 0.8 + whistle) * env
        sig = sig / (np.max(np.abs(sig)) + 1e-6) * 0.88
        with wave.open(WHOOSH_FILE, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes((sig * 32767).astype(np.int16).tobytes())

    if not os.path.exists(IMPACT_FILE):
        print("Synthesizing studio cinematic impact SFX...")
        dur = 1.6
        n_samples = int(sr * dur)
        t = np.linspace(0, dur, n_samples, endpoint=False)
        freq = 140 * np.exp(-t * 4.0) + 32
        phase = 2 * np.pi * np.cumsum(freq) / sr
        env = np.exp(-t * 2.8)
        sub = np.sin(phase) * env
        grit = np.tanh(sub * 2.2) * 0.45
        snap_env = np.exp(-t / 0.012)
        snap = np.sin(2 * np.pi * 320 * t) * snap_env * 0.6
        mix = (sub * 0.7 + grit + snap)
        mix = mix / (np.max(np.abs(mix)) + 1e-6) * 0.95
        with wave.open(IMPACT_FILE, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes((mix * 32767).astype(np.int16).tobytes())

def generate_sfx_track(scene_cuts, total_duration, output_path):
    ensure_sfx_assets()
    sr = 44100
    total_samples = int(sr * (total_duration + 1.0))
    master_sfx = np.zeros(total_samples, dtype=np.float32)

    def load_wav(path):
        with wave.open(path, 'rb') as wf:
            data = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
            return data.astype(np.float32) / 32768.0

    whoosh = load_wav(WHOOSH_FILE)
    impact = load_wav(IMPACT_FILE)

    # 1. Opening hook impact at 0.0s
    n_imp = min(len(impact), total_samples)
    master_sfx[0:n_imp] += impact[:n_imp] * 0.45

    # Transition whooshes on image change removed per user instruction.
    # The audio track maintains clean voiceover and atmospheric background music without cut sound distractions.
    master_sfx = np.clip(master_sfx, -1.0, 1.0)
    i16 = (master_sfx * 32767).astype(np.int16)
    with wave.open(output_path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(i16.tobytes())
    print(f"Clean audio track prepared without transition sounds -> {output_path}")

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

    print("Generating fallback procedural background via FFmpeg...")
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
        return dest_path, [0.0]

    print(f"Detected {len(scenes)} topic-specific visual scenes for: {topic['title']}")
    scene_files = []
    
    # Calculate scene durations so they sum up to total_duration
    total_assigned = sum(sc.get('duration', 0) for sc in scenes)
    if total_assigned <= 0:
        each_d = total_duration / len(scenes)
        scene_durations = [each_d] * len(scenes)
    else:
        scale_factor = total_duration / total_assigned
        scene_durations = [sc.get('duration', total_duration/len(scenes)) * scale_factor for sc in scenes]

    scene_cut_times = []
    running_t = 0.0

    for idx, sc in enumerate(scenes):
        sc_dur = scene_durations[idx]
        scene_cut_times.append(running_t)
        running_t += sc_dur

        sc_type = sc.get('type', 'video')
        sc_url = sc.get('clip_url')
        sc_local = sc.get('local_path')
        if sc_local and os.path.exists(sc_local):
            sc_raw = sc_local
        else:
            sc_raw = f"temp/{topic['id']}_sc_{idx}_raw.mp4" if sc_type == 'video' else f"temp/{topic['id']}_sc_{idx}.jpg"
        sc_norm = f"temp/{topic['id']}_sc_{idx}_norm.mp4"

        print(f"  [Scene {idx+1}/{len(scenes)}] {sc.get('label', 'Visual')} ({sc_dur:.2f}s, start: {scene_cut_times[-1]:.2f}s)...")
        
        # Subtle white flash on scene transition (100ms)
        flash_filter = "fade=t=in:st=0:d=0.08:color=white" if idx > 0 else "null"

        if sc_type == 'video':
            download_footage(sc_url, sc_raw)
            cmd = [
                'ffmpeg', '-y', '-stream_loop', '-1', '-i', sc_raw,
                '-t', f"{sc_dur:.2f}",
                '-vf', f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,{flash_filter},vignette=PI/5,eq=contrast=1.08:saturation=1.18,setsar=1,fps=30",
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
            
            # CapCut Smooth Transition: Buttery smooth 0.15s cinematic dip on transition
            transition_filter = "fade=t=in:st=0:d=0.15:color=black" if idx > 0 else "null"

            cmd = [
                'ffmpeg', '-y', '-loop', '1', '-i', sc_raw,
                '-t', f"{sc_dur:.2f}",
                '-vf', f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,{transition_filter},vignette=PI/5,eq=contrast=1.06:saturation=1.15,setsar=1,fps=30",
                '-c:v', 'libx264', '-crf', '17', '-pix_fmt', 'yuv420p', '-an', sc_norm
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
    return dest_path, scene_cut_times

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
    top_header = topic.get('top_header', 'MIND-BLOWING FACTS')
    sub_header = topic.get('sub_header', '')

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

    ass_lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        "PlayResX: 1080",
        "PlayResY: 1920",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: RadiumSub,Arial Black,70,&H0000FF16,&H00000000,&H00000000,&H00000000,-1,0,0,0,100,100,1,0,1,3.8,5.0,2,60,60,630,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
    ]

    # Split subtitles into snappy 2-3 word power beats
    raw_subtitles = topic.get('subtitles', [])
    snappy_beats = []

    for sub in raw_subtitles:
        st = sub['start']
        et = min(sub['end'], duration)
        if st >= duration:
            continue
        text = sub['text'].strip()
        words = text.split()
        dur = et - st

        if len(words) >= 4 and dur >= 1.6:
            mid = len(words) // 2
            half_dur = dur / 2
            snappy_beats.append({
                'start': st,
                'end': st + half_dur,
                'text': ' '.join(words[:mid]),
                'color': sub.get('color', '#39FF14')
            })
            snappy_beats.append({
                'start': st + half_dur,
                'end': et,
                'text': ' '.join(words[mid:]),
                'color': sub.get('color', '#39FF14')
            })
        else:
            snappy_beats.append({
                'start': st,
                'end': et,
                'text': text,
                'color': sub.get('color', '#39FF14')
            })

    for beat in snappy_beats:
        start_str = format_ass_time(beat['start'])
        end_str = format_ass_time(beat['end'])
        hex_col = beat.get('color', '#39FF14')
        ass_color = style_colors.get(hex_col, '&H0000FF16&')
        raw_text = beat['text'].upper()

        # Dynamic MrBeast/Zach D style elastic punch animation on beat hit
        anim_tag = f"{{\\c{ass_color}\\3c&H00000000&\\bord4.0\\shad5.2\\fscx112\\fscy112\\t(0,75,\\fscx100\\fscy100)}}"
        dialogue_line = f"Dialogue: 1,{start_str},{end_str},RadiumSub,,0,0,0,,{anim_tag}{raw_text}"
        ass_lines.append(dialogue_line)

    with open(ass_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(ass_lines))
    print(f"Generated snappy animated ASS subtitles: {ass_path}")

def render_short(topic, footage_path, audio_path, sfx_path, output_path):
    duration = get_media_duration(audio_path)
    print(f'Voice duration: {duration:.2f}s')

    ass_path = 'temp/subtitles_animated.ass'
    create_ass_subtitles(topic, duration, ass_path)

    has_bgm = os.path.exists(BGM_FILE)
    has_sfx = False  # Image cut sounds and transition SFX removed per user instruction for pure audio clarity
    
    footage_args = []
    if topic.get('footage_start_sec'):
        footage_args = ['-ss', str(topic['footage_start_sec'])]

    # Filter Complex:
    # 1. 9:16 vertical crop with burn-in ASS subtitles
    # 2. Studio radio broadcast voice EQ (punchy low end, crisp presence)
    # 3. Ducked subtle BGM + studio time-synced SFX
    filter_complex = (
        f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,ass={ass_path}[outv]; "
        f"[1:a]equalizer=f=120:width_type=o:width=1.5:g=3.2,equalizer=f=3400:width_type=o:width=1.5:g=2.2,volume=1.06[voice]; "
    )

    if has_bgm and has_sfx:
        filter_complex += (
            f"[2:a]volume=0.08[bgm]; "
            f"[3:a]volume=0.55[sfx]; "
            f"[voice][bgm][sfx]amix=inputs=3:duration=first:dropout_transition=2[outa]"
        )
        ffmpeg_cmd = [
            'ffmpeg', '-y',
            *footage_args,
            '-stream_loop', '-1', '-i', footage_path,
            '-i', audio_path,
            '-stream_loop', '-1', '-i', BGM_FILE,
            '-i', sfx_path,
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
    elif has_bgm:
        filter_complex += (
            f"[2:a]volume=0.08[bgm]; "
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
        filter_complex += "[voice]volume=1.0[outa]"
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

    print(f'Rendering studio-mastered vertical 9:16 Short (exact duration: {duration:.2f}s)...')
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
    sfx_path = f"temp/{topic['id']}_sfx.wav"
    output_video_path = f"{OUTPUT_DIR}/factify_short_latest.mp4"

    asyncio.run(generate_voice(topic['script'], audio_path))
    duration = get_media_duration(audio_path)
    
    footage_path, scene_cuts = prepare_footage(topic, duration, footage_path)
    generate_sfx_track(scene_cuts, duration, sfx_path)
    render_short(topic, footage_path, audio_path, sfx_path, output_video_path)
    generate_metadata(topic)

    print("\n" + "=" * 60)
    print("FACTIFY STUDIO SHORT GENERATED SUCCESSFULLY!")
    print(f"Video Path: {os.path.abspath(output_video_path)}")
    print("=" * 60)

if __name__ == '__main__':
    main()
