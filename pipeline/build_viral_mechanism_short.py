import os
import sys
import json
import asyncio
import subprocess
import textwrap
import edge_tts
from PIL import Image, ImageDraw, ImageFont
import re

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)

TEMP_DIR = 'temp'
OUTPUT_DIR = 'output'
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

BGM_FILE = 'pipeline/assets/bgm.mp3'

def render_channel_footer(question_text, out_path):
    footer = Image.open('temp/pure_channel_footer.png').convert('RGBA')
    draw = ImageDraw.Draw(footer)

    card_x0, card_y0 = 175, 45
    card_w, card_h = 730, 480

    # Clean rounded card matching channel aesthetic
    draw.rounded_rectangle(
        [card_x0, card_y0, card_x0 + card_w, card_y0 + card_h],
        radius=50, fill=(225, 245, 252, 255), outline=(255, 255, 255, 255), width=3
    )

    # Top question mark badge
    badge_r = 42
    bx = card_x0 + card_w // 2
    by = card_y0
    draw.ellipse(
        [bx - badge_r, by - badge_r + 4, bx + badge_r, by + badge_r + 4],
        fill=(210, 238, 248, 255), outline=(225, 245, 252, 255), width=4
    )
    try:
        font_q = ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf', 44)
    except:
        font_q = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 44)
    draw.text((bx, by + 4), '?', font=font_q, fill=(16, 40, 90, 255), anchor='mm')

    # Question text
    lines = textwrap.wrap(question_text, width=22)
    try:
        font_txt = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 42)
    except:
        font_txt = ImageFont.load_default()

    line_h = 52
    tot_h = len(lines) * line_h
    sy = card_y0 + 90 + (190 - tot_h) // 2
    for i, l in enumerate(lines):
        draw.text((bx, sy + i * line_h), l, font=font_txt, fill=(12, 38, 88, 255), anchor='mm')

    # Bottom Answer button
    pw, ph = 520, 68
    px = card_x0 + (card_w - pw) // 2
    py = card_y0 + card_h - ph - 30
    draw.rounded_rectangle([px, py, px + pw, py + ph], radius=34, fill=(185, 238, 248, 255))
    try:
        font_ans = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 32)
    except:
        font_ans = ImageFont.load_default()
    draw.text((bx, py + ph // 2), 'Answer', font=font_ans, fill=(12, 38, 88, 255), anchor='mm')

    footer.save(out_path)
    print(f"Branded channel footer generated: {out_path}")
    return out_path

def format_ass_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"

async def generate_voice_and_words(text, voice_path, voice='en-US-ChristopherNeural', rate='+3%'):
    print(f"Synthesizing voiceover with {voice}...")
    communicate = edge_tts.Communicate(text, voice, rate=rate, boundary='WordBoundary')
    words = []
    with open(voice_path, 'wb') as f:
        async for chunk in communicate.stream():
            if chunk['type'] == 'audio':
                f.write(chunk['data'])
            elif chunk['type'] == 'WordBoundary':
                st = chunk['offset'] / 10000000.0
                dur = chunk['duration'] / 10000000.0
                words.append({
                    'text': chunk['text'],
                    'start': st,
                    'end': st + dur
                })
    print(f"Voice saved to: {voice_path} ({len(words)} words tracked)")
    return words

def create_karaoke_ass_subtitles(words, duration, ass_path, margin_v=740, watermark_text='@FactifyDailyShorts'):
    # PlayResX=1080, PlayResY=1920
    # margin_v=740 places subtitle right above the bottom branded card at y=1140-1180
    ass_lines = [
        "[Script Info]",
        "Title: Factify Kinetic Karaoke Subtitles",
        "ScriptType: v4.00+",
        "PlayResX: 1080",
        "PlayResY: 1920",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: KaraokeSub,Arial Black,68,&H00FFFFFF,&H00000000,&H00000000,&HA0000000,-1,0,0,0,100,100,1.0,0,1,6.0,4.0,2,40,40,{margin_v},1",
        "Style: ChannelWatermark,Arial,28,&H60FFFFFF,&H00000000,&H80000000,&HA0000000,-1,0,0,0,100,100,2.0,0,1,1.8,1.8,8,60,60,60,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
        f"Dialogue: 0,{format_ass_time(0.0)},{format_ass_time(duration)},ChannelWatermark,,0,0,0,,{watermark_text}"
    ]

    cleaned = []
    for w in (words or []):
        txt = re.sub(r"[^\w\'-]", "", w["text"]).upper()
        if txt:
            cleaned.append({
                "raw": w["text"],
                "text": txt,
                "start": max(0.0, float(w["start"])),
                "end": max(0.0, float(w["end"]))
            })

    if cleaned:
        chunks = []
        current_chunk = []

        for i, w in enumerate(cleaned):
            current_chunk.append(w)
            ends_sentence = any(p in w["raw"] for p in [".", "!", "?"])
            has_comma = "," in w["raw"]

            gap = 0.0
            if i + 1 < len(cleaned):
                gap = cleaned[i + 1]["start"] - w["end"]

            chunk_chars = sum(len(x["text"]) for x in current_chunk) + len(current_chunk) - 1

            if len(current_chunk) >= 2 or chunk_chars >= 12 or ends_sentence or has_comma or gap > 0.30:
                chunks.append(current_chunk)
                current_chunk = []

        if current_chunk:
            chunks.append(current_chunk)

        prev_end = 0.0
        for chunk_idx, chunk in enumerate(chunks):
            c_start = max(prev_end, chunk[0]["start"])
            if chunk_idx + 1 < len(chunks):
                next_start = chunks[chunk_idx + 1][0]["start"]
                if next_start - chunk[-1]["end"] <= 0.25:
                    c_end = max(chunk[-1]["end"], next_start)
                else:
                    c_end = chunk[-1]["end"] + 0.10
            else:
                c_end = chunk[-1]["end"] + 0.15

            for active_idx, target_word in enumerate(chunk):
                if active_idx == 0:
                    w_st = c_start
                else:
                    w_st = max(c_start, target_word["start"])

                if active_idx + 1 < len(chunk):
                    w_et = max(w_st + 0.05, chunk[active_idx + 1]["start"])
                else:
                    w_et = max(w_st + 0.05, c_end)

                line_parts = []
                for j, w in enumerate(chunk):
                    if j == active_idx:
                        # Neon Yellow #FFE600 with 110% elastic pop
                        line_parts.append(r"{\c&H0000E6FF&\fscx110\fscy110}" + w["text"] + r"{\fscx100\fscy100}")
                    else:
                        line_parts.append(r"{\c&H00FFFFFF&}" + w["text"])

                dialogue_text = " ".join(line_parts)
                start_str = format_ass_time(w_st)
                end_str = format_ass_time(min(w_et, duration))
                ass_lines.append(f"Dialogue: 1,{start_str},{end_str},KaraokeSub,,0,0,0,,{dialogue_text}")

            prev_end = c_end

    with open(ass_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(ass_lines))
    print(f"Generated ASS subtitles: {ass_path} ({len(cleaned)} words)")

def build_branded_channel_short(
    video_source_path,
    question_text,
    script_text,
    output_filename,
    metadata
):
    print("=" * 60)
    print(f"BUILDING OFFICIAL BRANDED SHORT: {metadata['title']}")
    print("=" * 60)

    # 1. Generate Voiceover & Word Timings
    voice_path = os.path.join(TEMP_DIR, 'branded_voice.mp3')
    words = asyncio.run(generate_voice_and_words(script_text, voice_path))
    
    cmd_dur = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{voice_path}"'
    voice_duration = float(subprocess.check_output(cmd_dur, shell=True, text=True).strip())
    print(f"Voiceover duration: {voice_duration:.2f}s")

    # 2. Render Official Channel Branded Footer
    footer_path = os.path.join(TEMP_DIR, 'branded_footer.png')
    render_channel_footer(question_text, footer_path)

    # 3. Generate Word-by-Word Kinetic Karaoke Subtitles (Safe above footer)
    ass_path = os.path.join(TEMP_DIR, 'branded_subtitles.ass')
    create_karaoke_ass_subtitles(words, voice_duration, ass_path, margin_v=740)

    safe_ass = ass_path.replace('\\', '/').replace(':', '\\:')

    # 4. Filter Complex:
    # [0:v] 3D animation scaled to 1080x1250 with studio color grading
    # [1:v] Channel Footer overlay at y=1250
    # ass subtitles burned in above footer
    # Voice radio broadcast EQ + ducked subtle BGM + Loudnorm -14 LUFS
    filter_complex = (
        f"[0:v]scale=1080:1250:force_original_aspect_ratio=increase,crop=1080:1250:0:0,"
        f"eq=contrast=1.06:saturation=1.14[topv]; "
        f"[topv]pad=1080:1920:0:0:color=black[padded]; "
        f"[padded][1:v]overlay=0:1250[vcomp]; "
        f"[vcomp]ass='{safe_ass}'[outv]; "
        f"[2:a]equalizer=f=120:width_type=o:width=1.5:g=3.0,equalizer=f=3400:width_type=o:width=1.5:g=2.2,volume=1.08[voice]; "
        f"[3:a]volume=0.08[bgm]; "
        f"[voice][bgm]amix=inputs=2:duration=first:dropout_transition=2,loudnorm=I=-14:TP=-1.5:LRA=11[outa]"
    )

    output_path = os.path.join(OUTPUT_DIR, output_filename)

    clean = lambda s: (s or '').replace('"', '').replace('\n', ' ')
    meta_args = []
    for k, v in [
        ('title', metadata.get("title", "")),
        ('artist', "@FactifyDailyShorts"),
        ('description', metadata.get("description", "")),
        ('comment', "Factify Health & Science Mechanisms"),
        ('genre', "Education"),
        ('keywords', metadata.get("tags_str", ""))
    ]:
        meta_args.extend(['-metadata', f'{k}={clean(v)}'])

    ffmpeg_cmd = [
        'ffmpeg', '-y',
        '-stream_loop', '-1', '-i', video_source_path,
        '-i', footer_path,
        '-i', voice_path,
        '-stream_loop', '-1', '-i', BGM_FILE,
        '-filter_complex', filter_complex,
        '-map', '[outv]',
        '-map', '[outa]',
        *meta_args,
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '17',
        '-pix_fmt', 'yuv420p',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-t', f"{voice_duration:.2f}",
        output_path
    ]

    print("Executing FFmpeg render command...")
    subprocess.run(ffmpeg_cmd, check=True)
    print(f"Video rendered successfully: {output_path}")

    seo_file = os.path.join(OUTPUT_DIR, output_filename.replace('.mp4', '_seo.json'))
    with open(seo_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    print(f"VidIQ SEO Metadata saved: {seo_file}")

    return output_path

if __name__ == '__main__':
    meta = {
        "title": "How a Heart Stent ACTUALLY Saves Your Life! ❤️ (3D Animation) #Shorts",
        "question": "Q: How does a heart stent actually save your life?",
        "script": (
            "When bad cholesterol clogs your coronary artery, blood flow to the heart stops. "
            "To prevent a massive heart attack, doctors perform an emergency angioplasty. "
            "A flexible catheter is guided through your artery to the blockage. "
            "A tiny balloon inflates, expanding a metal mesh stent to lock the passage wide open. "
            "Blood rushes back instantly, saving your heart muscle from dying!"
        ),
        "description": (
            "Ever wondered how doctors clear blocked arteries during a heart attack? ❤️ Here is the step-by-step 3D medical animation!\n\n"
            "When cholesterol and plaque accumulate inside coronary arteries, oxygen cannot reach the heart muscle. "
            "To prevent fatal tissue death, cardiologists deploy an expanding metallic stent:\n"
            "1️⃣ Guiding a micro-catheter directly to the arterial blockage\n"
            "2️⃣ Positioning the balloon-expandable cobalt chromium stent\n"
            "3️⃣ Inflating the balloon to compress plaque against arterial walls\n"
            "4️⃣ Locking the scaffold permanently to restore full blood circulation\n"
            "5️⃣ Withdrawing the balloon, keeping the coronary vessel open for life\n\n"
            "Subscribe to @FactifyDailyShorts for mind-blowing science & body mechanisms every day!\n\n"
            "#heartstent #heartattack #cardiology #3danimation #science #anatomy #health #medical #shorts"
        ),
        "tags": [
            "how a heart stent works", "coronary angioplasty 3d", "heart stent procedure",
            "blocked artery treatment", "heart attack prevention", "cardiovascular health",
            "heart anatomy 3d", "cardiology animation", "body mechanisms",
            "medical facts", "how it actually works", "factify shorts",
            "science shorts", "health facts"
        ]
    }
    meta['tags_str'] = ", ".join(meta['tags'])

    build_branded_channel_short(
        video_source_path='temp/source_heart_stent.mp4',
        question_text=meta['question'],
        script_text=meta['script'],
        output_filename='Factify_Heart_Stent_Channel_Branded.mp4',
        metadata=meta
    )
