import os
import sys
import subprocess
import yt_dlp

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)

def get_video_dimensions(file_path):
    cmd = [
        'ffprobe', '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height',
        '-of', 'csv=p=0:s=x',
        file_path
    ]
    try:
        out = subprocess.check_output(cmd, text=True).strip()
        w, h = map(int, out.split('x'))
        return w, h
    except Exception:
        return 1920, 1080

def smart_normalize_clip(source_file, dest_path, start_sec=2.0, duration=5.0, custom_crop=None):
    w, h = get_video_dimensions(source_file)
    ratio = w / h if h > 0 else 1.777

    print(f"  [Smart Engine] Source dims: {w}x{h} (Ratio: {ratio:.2f})")

    if ratio <= 0.75:
        # Native vertical 9:16 (Zack D Films / vertical 3D animations)
        print("  [Format] Native Vertical -> 100% Fullscreen Cover")
        cmd = [
            'ffmpeg', '-y', '-ss', str(start_sec), '-i', source_file,
            '-t', str(duration),
            '-vf', 'scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920:(in_w-1080)/2:(in_h-1920)/2,eq=contrast=1.06:saturation=1.12,setsar=1,fps=30',
            '-c:v', 'libx264', '-crf', '17', '-preset', 'fast', '-pix_fmt', 'yuv420p', '-an', dest_path
        ]
    else:
        # Landscape / square 16:9 / 4:3
        # Smart Hybrid: Cinematic ambient blurred backdrop + crystal-clear uncropped center video (watermark-free)
        print("  [Format] Landscape/Standard -> Cinematic Ambient Blurred Backdrop + Center Clear HD")
        
        crop_expr = custom_crop if custom_crop else "crop=in_w:700:0:60"
        filter_complex = (
            f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920:(in_w-1080)/2:(in_h-1920)/2,"
            f"boxblur=25:5,eq=brightness=-0.22:contrast=1.08,setsar=1,fps=30[bg]; "
            f"[0:v]{crop_expr},scale=1080:-2,setsar=1,fps=30,eq=contrast=1.05:saturation=1.08[fg]; "
            f"[bg][fg]overlay=0:(1920-h)/2-80[outv]"
        )
        cmd = [
            'ffmpeg', '-y', '-ss', str(start_sec), '-i', source_file,
            '-t', str(duration),
            '-filter_complex', filter_complex,
            '-map', '[outv]',
            '-c:v', 'libx264', '-crf', '17', '-preset', 'fast', '-pix_fmt', 'yuv420p', '-an', dest_path
        ]

    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return os.path.exists(dest_path)

def fetch_scene_clip(query, dest_path, start_sec=2.0, duration=5.0, source_video=None, custom_crop=None):
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 50000:
        print(f"  [OK] Clip already cached: {dest_path}")
        return True

    os.makedirs(os.path.dirname(dest_path) or 'temp', exist_ok=True)

    # 1. Direct local source file support (checking relative path, assets/footage, and temp)
    resolved_source = None
    if source_video:
        candidates = [
            source_video,
            os.path.join('pipeline', 'assets', 'footage', os.path.basename(source_video)),
            os.path.join('temp', os.path.basename(source_video))
        ]
        for c in candidates:
            if os.path.exists(c) and os.path.getsize(c) > 1000:
                resolved_source = c
                break

    if resolved_source:
        print(f"  [Processing] Found source footage '{resolved_source}' ({start_sec}s - {start_sec + duration}s)...")
        try:
            return smart_normalize_clip(resolved_source, dest_path, start_sec=start_sec, duration=duration, custom_crop=custom_crop)
        except Exception as e:
            print(f"  [Warning] Source processing failed: {e}")

    # 2. Remote download via URL or search query
    target = source_video if (source_video and source_video.startswith('http')) else query
    print(f"  [Fetching] Sourcing '{target}' ({start_sec}s - {start_sec + duration}s)...")

    ydl_opts = {
        'format': 'bestvideo[height<=1080]/best[height<=1080]/best',
        'outtmpl': dest_path.replace('.mp4', '_raw.%(ext)s'),
        'download_ranges': yt_dlp.utils.download_range_func(None, [(start_sec, start_sec + duration + 1.0)]),
        'quiet': True,
        'no_warnings': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([target])
        
        # Check if raw file was downloaded
        raw_candidates = [
            dest_path.replace('.mp4', '_raw.mp4'),
            dest_path.replace('.mp4', '_raw.mkv'),
            dest_path.replace('.mp4', '_raw.webm')
        ]
        raw_file = None
        for cand in raw_candidates:
            if os.path.exists(cand) and os.path.getsize(cand) > 30000:
                raw_file = cand
                break

        if raw_file:
            success = smart_normalize_clip(raw_file, dest_path, start_sec=0.0, duration=duration, custom_crop=custom_crop)
            if os.path.exists(raw_file) and raw_file != dest_path:
                try:
                    os.remove(raw_file)
                except Exception:
                    pass
            if success:
                print(f"  [OK] Successfully transformed and saved: {dest_path}")
                return True
    except Exception as e:
        print(f"  [Warning] Could not fetch '{target}': {e}. Using cinematic dark canvas.")

    # High quality dark cinematic procedural canvas (NEVER TV color bars)
    fallback_cmd = [
        'ffmpeg', '-y', '-f', 'lavfi',
        '-i', f'color=c=#060d1a:s=1080x1920:d={duration},format=yuv420p',
        '-t', str(duration),
        '-c:v', 'libx264', '-crf', '18', '-preset', 'fast', '-an', dest_path
    ]
    subprocess.run(fallback_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return os.path.exists(dest_path)

def prepare_topic_scenes(topic):
    scenes = topic.get('scenes', [])
    print(f"\nPreparing {len(scenes)} distinct visual scenes for '{topic['title']}'...")
    ready_scenes = []

    for idx, sc in enumerate(scenes):
        sc_dest = f"temp/{topic['id']}_sc_{idx}.mp4"
        query = sc.get('query')
        src_vid = sc.get('source_video', None)
        start_sec = sc.get('start_sec', 2.0)
        dur = sc.get('duration', 5.0)
        c_crop = sc.get('custom_crop', None)

        success = fetch_scene_clip(query, sc_dest, start_sec=start_sec, duration=dur, source_video=src_vid, custom_crop=c_crop)
        ready_scenes.append({
            'label': sc.get('label', f'Scene {idx+1}'),
            'duration': dur,
            'local_path': sc_dest,
            'type': 'video'
        })

    topic['scenes'] = ready_scenes
    return topic
