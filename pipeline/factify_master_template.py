"""
FACTIFY SHORTS - MASTER EDITING TEMPLATE
Channel: Factify Shorts (@FactifyDailyShorts)
Canvas: 1080 x 1920 (9:16 Vertical)

Layer Architecture:
  Layer 1: Full-Screen Video (100% width & height, object-fit: cover)
  Layer 2: Subtle Cinematic Dark Gradient Overlay
  Layer 3: Top-Left Factify Branding (X=48, Y=55, 64x64 logo, handle)
  Layer 4: Lower-Middle Caption Plate (rgba(0,0,0,0.65), 18px radius, cyan glow)
  Layer 5: Animated Kinetic Subtitles (Montserrat ExtraBold, White + Yellow #FFD400)
  Layer 6: CTA Follow Pill (End 2.0s, Cyan border, YouTube icon, Follow for More)
"""

import os
import sys
import re
import json
import math
import asyncio
import subprocess
import edge_tts
from PIL import Image, ImageDraw, ImageFont, ImageFilter

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)

# Base Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, 'pipeline', 'assets')
BRANDING_DIR = os.path.join(ASSETS_DIR, 'branding')
FONTS_DIR = os.path.join(ASSETS_DIR, 'fonts')
TEMP_DIR = os.path.join(BASE_DIR, 'temp')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')

os.makedirs(BRANDING_DIR, exist_ok=True)
os.makedirs(FONTS_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

FONT_EXTRA_BOLD = os.path.join(FONTS_DIR, 'Montserrat-ExtraBold-Static.ttf')
BGM_DEFAULT = os.path.join(ASSETS_DIR, 'bgm.mp3')

# Color System
COLOR_DARK = (5, 11, 24)       # #050B18
COLOR_WHITE = (255, 255, 255)   # #FFFFFF
COLOR_YELLOW = (255, 212, 0)    # #FFD400 (Important words)
COLOR_CYAN = (32, 217, 255)     # #20D9FF (Brand accent / glow)
COLOR_RED = (255, 48, 64)       # #FF3040 (YouTube icon)

class FactifyShortsTemplate:
    def __init__(self):
        self.canvas_w = 1080
        self.canvas_h = 1920
        self.ensure_branding_assets()

    def ensure_branding_assets(self):
        """Generates static branding overlays: Top-Left brand & CTA follow pill."""
        top_brand_path = os.path.join(BRANDING_DIR, 'top_left_brand.png')
        cta_path = os.path.join(BRANDING_DIR, 'cta_follow_pill.png')
        grad_path = os.path.join(BRANDING_DIR, 'cinematic_gradient_overlay.png')

        # 1. Gradient Overlay (1080x1920)
        if not os.path.exists(grad_path):
            grad = Image.new('RGBA', (self.canvas_w, self.canvas_h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(grad)
            for y in range(220):
                a = int(100 * (1.0 - (y / 220.0)) ** 1.5)
                draw.line([(0, y), (self.canvas_w, y)], fill=(COLOR_DARK[0], COLOR_DARK[1], COLOR_DARK[2], a))
            for y in range(1050, self.canvas_h):
                progress = (y - 1050) / (float(self.canvas_h) - 1050.0)
                a = int(155 * (progress ** 1.8))
                draw.line([(0, y), (self.canvas_w, y)], fill=(COLOR_DARK[0], COLOR_DARK[1], COLOR_DARK[2], a))
            grad.save(grad_path)

        # 2. Top-Left Branding Component (X≈48, Y≈55, Logo 64x64)
        if not os.path.exists(top_brand_path):
            logo_src_path = os.path.join(
                'C:/Users/MD JEWEL RANA/.gemini/antigravity/brain/ae960e2b-dff2-48e8-a557-8238de3a1171/.user_uploaded/media_1790812613768.png'
            )
            if os.path.exists(logo_src_path):
                logo_src = Image.open(logo_src_path).convert('RGBA')
            else:
                logo_src = Image.new('RGBA', (128, 128), (32, 217, 255, 255))

            size = 64
            logo = logo_src.resize((size, size), Image.Resampling.LANCZOS)
            mask = Image.new('L', (size, size), 0)
            draw_m = ImageDraw.Draw(mask)
            draw_m.ellipse((0, 0, size, size), fill=255)
            circle_logo = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            circle_logo.paste(logo, (0, 0), mask)

            border_draw = ImageDraw.Draw(circle_logo)
            border_draw.ellipse((0, 0, size - 1, size - 1), outline=(32, 217, 255, 180), width=2)

            brand_w, brand_h = 420, 80
            brand_img = Image.new('RGBA', (brand_w, brand_h), (0, 0, 0, 0))
            brand_img.paste(circle_logo, (0, 8), circle_logo)

            draw_b = ImageDraw.Draw(brand_img)
            font_name = ImageFont.truetype(FONT_EXTRA_BOLD, 28)
            try:
                font_handle = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 19)
            except:
                font_handle = ImageFont.truetype(FONT_EXTRA_BOLD, 18)

            draw_b.text((80 + 1, 10 + 2), 'Factify Shorts', font=font_name, fill=(0, 0, 0, 200))
            draw_b.text((80, 10), 'Factify Shorts', font=font_name, fill=(255, 255, 255, 255))
            draw_b.text((80 + 1, 46 + 1), '@FactifyDailyShorts', font=font_handle, fill=(0, 0, 0, 180))
            draw_b.text((80, 46), '@FactifyDailyShorts', font=font_handle, fill=(240, 240, 240, 230))
            brand_img.save(top_brand_path)

        # 3. CTA Subscribe Pill (Width 420, Height 76, Cyan border & glow)
        cta_path = os.path.join(BRANDING_DIR, 'cta_subscribe_pill.png')
        if not os.path.exists(cta_path):
            pw, ph = 420, 76
            glow_layer = Image.new('RGBA', (pw + 60, ph + 40), (0, 0, 0, 0))
            draw_g = ImageDraw.Draw(glow_layer)
            draw_g.rounded_rectangle([20, 10, 20 + pw, 10 + ph], radius=ph//2, outline=(32, 217, 255, 220), width=6)
            glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=6))

            pill = Image.new('RGBA', (pw + 60, ph + 40), (0, 0, 0, 0))
            draw_p = ImageDraw.Draw(pill)
            draw_p.rounded_rectangle([20, 10, 20 + pw, 10 + ph], radius=ph//2, fill=(5, 11, 24, 235), outline=(32, 217, 255, 255), width=3)

            icon_x = 32
            icon_y = 10 + (ph - 38) // 2
            draw_p.rounded_rectangle([icon_x, icon_y, icon_x + 54, icon_y + 38], radius=10, fill=(255, 48, 64, 255))
            tri = [(icon_x + 23, icon_y + 11), (icon_x + 23, icon_y + 27), (icon_x + 36, icon_y + 19)]
            draw_p.polygon(tri, fill=(255, 255, 255, 255))

            font_cta = ImageFont.truetype(FONT_EXTRA_BOLD, 24)
            draw_p.text((icon_x + 66, 10 + ph // 2), 'SUBSCRIBE FOR MORE', font=font_cta, fill=(255, 255, 255, 255), anchor='lm')

            arrow_x = 20 + pw + 8
            arrow_y = 10 + ph // 2 - 4
            draw_p.arc([arrow_x, arrow_y, arrow_x + 24, arrow_y + 26], start=180, end=300, fill=(32, 217, 255, 255), width=3)
            draw_p.polygon([(arrow_x + 18, arrow_y), (arrow_x + 26, arrow_y + 6), (arrow_x + 25, arrow_y - 4)], fill=(32, 217, 255, 255))

            cta_final = Image.alpha_composite(glow_layer, pill)
            cta_final.save(cta_path)

        # 4. Sleek Frosted Caption Plate (Width 960, Height 250, masks source subtitles)
        plate_path = os.path.join(BRANDING_DIR, 'caption_plate.png')
        if not os.path.exists(plate_path):
            plate = Image.new('RGBA', (960, 250), (0, 0, 0, 0))
            draw_p = ImageDraw.Draw(plate)
            # High-opacity dark container (#050B18, 90% opacity) with sleek cyan border
            draw_p.rounded_rectangle(
                [0, 0, 960, 250],
                radius=28,
                fill=(5, 11, 24, 230),
                outline=(32, 217, 255, 130),
                width=2
            )
            plate.save(plate_path)

        self.top_brand_path = top_brand_path
        self.cta_path = cta_path
        self.grad_path = grad_path
        self.caption_plate_path = plate_path

    async def synthesize_voice_and_words(self, script_text, voice_path, voice='en-US-ChristopherNeural', rate='+3%'):
        """Generates EdgeTTS voiceover audio and returns word boundary timestamps."""
        print(f"[Factify Engine] Synthesizing voiceover with {voice} ({rate})...")
        communicate = edge_tts.Communicate(script_text, voice, rate=rate, boundary='WordBoundary')
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
        print(f"[Factify Engine] Voice saved: {voice_path} ({len(words)} words)")
        return words

    def group_words_into_caption_cards(self, words, highlight_keywords=None):
        """
        Groups words into readable 1-2 line mobile-optimized cards.
        Font size 76pt: keeps max 2-3 words per line (max 15 chars).
        Detects keywords to highlight in Yellow (#FFD400).
        """
        if not highlight_keywords:
            highlight_keywords = [
                'fat', 'really', 'water', 'slide', 'drill', 'nerve', 'pain', 'tooth',
                'decay', 'crown', 'stent', 'blood', 'heart', 'attack', 'stone',
                'kidney', 'shockwave', 'doctor', 'skin', 'stitches', 'collagen',
                'artery', 'catheter', 'balloon', 'life', 'die', 'fatal', 'huge',
                'secret', 'actually', 'happens', 'inside', 'acid', 'reflux', 'burn',
                'solar', 'storm', 'sun', 'earth', 'kill', 'destroy', 'power', 'flare',
                'deep', 'massive', 'energy', 'space', 'plasma', 'darkness'
            ]
        hl_set = {k.lower() for k in highlight_keywords}

        cleaned = []
        for w in words:
            raw = w['text']
            clean_txt = re.sub(r"[^\w\'-]", "", raw)
            if not clean_txt:
                continue
            is_hl = clean_txt.lower() in hl_set or any(c.isdigit() for c in clean_txt)
            cleaned.append({
                'raw': raw,
                'clean': clean_txt,
                'start': w['start'],
                'end': w['end'],
                'highlight': is_hl
            })

        if not cleaned:
            return []

        # Chunks of 2-4 words (ultra-readable on mobile screens)
        cards = []
        curr = []
        for i, w in enumerate(cleaned):
            curr.append(w)
            ends_punct = any(p in w['raw'] for p in ['.', '!', '?'])
            has_comma = ',' in w['raw']
            gap = 0.0
            if i + 1 < len(cleaned):
                gap = cleaned[i + 1]['start'] - w['end']

            curr_len = sum(len(x['clean']) for x in curr) + len(curr) - 1
            if len(curr) >= 3 or curr_len >= 14 or ends_punct or (len(curr) >= 2 and (has_comma or gap > 0.25)):
                cards.append(curr)
                curr = []
        if curr:
            cards.append(curr)

        formatted_cards = []
        for i, c in enumerate(cards):
            c_st = c[0]['start']
            # Strictly prevent overlap with subsequent card
            if i + 1 < len(cards):
                next_st = cards[i + 1][0]['start']
                c_et = min(c[-1]['end'] + 0.05, max(c_st + 0.1, next_st - 0.02))
            else:
                c_et = c[-1]['end'] + 0.15

            # If card has > 2 words, split into 2 lines
            if len(c) > 2:
                mid = math.ceil(len(c) / 2.0)
                line1_words = c[:mid]
                line2_words = c[mid:]
                lines = [
                    [(w['clean'].upper(), w['highlight']) for w in line1_words],
                    [(w['clean'].upper(), w['highlight']) for w in line2_words]
                ]
            else:
                lines = [[(w['clean'].upper(), w['highlight']) for w in c]]

            formatted_cards.append({
                'start': c_st,
                'end': c_et,
                'lines': lines
            })

        return formatted_cards

    def build_ass_subtitles(self, words, total_duration, ass_path):
        """
        Creates ASS kinetic subtitles with Montserrat ExtraBold:
        - Mobile-optimized LARGE size (Fontsize=76)
        - Lower-middle placement (MarginV=480, safely above CTA pill)
        - Heavy black outline (6.0px) & drop shadow (4.0px) for 100% contrast
        - White base text, Neon Yellow #FFD400 active keyword pop
        """
        ass_lines = [
            "[Script Info]",
            "Title: Factify Shorts Master Subtitles",
            "ScriptType: v4.00+",
            "PlayResX: 1080",
            "PlayResY: 1920",
            "ScaledBorderAndShadow: yes",
            "",
            "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
            # Fontsize=68 with Montserrat ExtraBold, MarginV=415 perfectly centered inside frosted caption plate
            "Style: FactifyCaption,Montserrat ExtraBold,68,&H00FFFFFF,&H00000000,&H00000000,&HA0000000,-1,0,0,0,100,100,0.5,0,1,5.0,2.0,2,40,40,415,1",
            "",
            "[Events]",
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
        ]

        def fmt_time(sec):
            h = int(sec // 3600)
            m = int((sec % 3600) // 60)
            s = sec % 60
            return f"{h}:{m:02d}:{s:05.2f}"

        cards = self.group_words_into_caption_cards(words)
        for card in cards:
            st = fmt_time(card['start'])
            et = fmt_time(min(card['end'], total_duration))
            line_strings = []
            for line in card['lines']:
                line_parts = []
                for word_txt, is_hl in line:
                    if is_hl:
                        # Yellow #FFD400 (&H0000D4FF& in ASS BGR)
                        line_parts.append(r"{\c&H0000D4FF&}" + word_txt + r"{\c&H00FFFFFF&}")
                    else:
                        line_parts.append(word_txt)
                line_strings.append(" ".join(line_parts))

            full_text = r"\N".join(line_strings)
            # Modern pop-in animation: 0ms scale 92 -> 120ms scale 104 -> 220ms scale 100
            anim_text = r"{\fscx92\fscy92\alpha&H60&\t(0,120,\fscx104\fscy104\alpha&H00&)\t(120,220,\fscx100\fscy100)}" + full_text
            ass_lines.append(f"Dialogue: 1,{st},{et},FactifyCaption,,0,0,0,,{anim_text}")

        with open(ass_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(ass_lines))
        print(f"[Factify Engine] ASS Subtitles created: {ass_path}")
        return ass_path

    def render_short(
        self,
        video_source_path,
        script_text,
        output_filename,
        metadata=None,
        highlight_keywords=None,
        voice_rate='+3%',
        bgm_path=None
    ):
        """
        Executes the master 6-layer pipeline:
        1. Full-screen 100% cover video (1080x1920)
        2. Subtle cinematic dark gradient overlay
        3. Top-left branding (X=48, Y=55)
        4. Lower-middle caption plate & kinetic subtitles (Montserrat ExtraBold 76pt Mobile)
        5. Yellow #FFD400 word highlights
        6. CTA Subscribe Pill visible from A to Z (throughout entire video)
        """
        print("=" * 70)
        print(f"🎬 FACTIFY SHORTS MASTER RENDER: {output_filename}")
        print("=" * 70)

        # Step 1: Voiceover & Timings
        voice_path = os.path.join(TEMP_DIR, f"{output_filename}_voice.mp3")
        words = asyncio.run(self.synthesize_voice_and_words(script_text, voice_path, rate=voice_rate))

        cmd_dur = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{voice_path}"'
        total_duration = float(subprocess.check_output(cmd_dur, shell=True, text=True).strip())
        print(f"[Factify Engine] Short Total Duration: {total_duration:.2f}s")

        # Step 2: ASS Kinetic Subtitles (Lower-Middle Montserrat ExtraBold 76pt)
        ass_path = os.path.join(TEMP_DIR, f"{output_filename}_subs.ass")
        self.build_ass_subtitles(words, total_duration, ass_path)
        safe_ass = ass_path.replace('\\', '/').replace(':', '\\:')
        fonts_dir_safe = FONTS_DIR.replace('\\', '/').replace(':', '\\:')

        # Multi-clip stitching if list of scenes is passed
        if isinstance(video_source_path, (list, tuple)):
            print(f"[Factify Engine] Stitching {len(video_source_path)} visual scenes...")
            concat_txt = os.path.join(TEMP_DIR, f"{output_filename}_concat.txt")
            with open(concat_txt, 'w', encoding='utf-8') as f:
                for p in video_source_path:
                    abs_p = os.path.abspath(p).replace('\\', '/')
                    f.write(f"file '{abs_p}'\n")
            stitched_video = os.path.join(TEMP_DIR, f"{output_filename}_stitched.mp4")
            concat_cmd = [
                'ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', concat_txt,
                '-c:v', 'libx264', '-preset', 'fast', '-crf', '18', '-an', stitched_video
            ]
            subprocess.run(concat_cmd, check=True)
            video_source_path = stitched_video

        # Step 3: Video Filter Complex (6 Layers)
        # [0:v] Full-Screen Video 100% cover (scale to 1080x1920 with crop)
        # [1:v] Subtle Cinematic Gradient Overlay (1080x1920)
        # [2:v] Top-Left Branding overlay at x=48, y=55
        # [3:v] CTA SUBSCRIBE Pill overlay at center bottom (x=(1080-w)/2, y=1610) throughout entire video (A to Z)
        # ass subtitle burning
        bgm_file = bgm_path or BGM_DEFAULT

        # Filter string
        filter_complex = (
            # Layer 1: Full-Screen 100% Canvas Cover
            f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920:(in_w-1080)/2:(in_h-1920)/2,"
            f"eq=contrast=1.05:saturation=1.12[layer1_video]; "
            # Subtitle Zone Blur Band: dissolves underlying hardcoded subtitles in y=1325..1595
            f"[layer1_video]split[v_base][v_sub_crop]; "
            f"[v_sub_crop]crop=1000:270:40:1325,boxblur=24:4[v_blur_band]; "
            f"[v_base][v_blur_band]overlay=40:1325[v_cleaned]; "
            # Layer 2: Subtle Cinematic Dark Gradient Overlay
            f"[v_cleaned][1:v]overlay=0:0[layer2_comp]; "
            # Layer 3: Top-Left Factify Branding Overlay
            f"[layer2_comp][2:v]overlay=48:55[layer3_comp]; "
            # Layer 4: Sleek Frosted Caption Plate (masks 100% of underlying subtitles)
            f"[layer3_comp][3:v]overlay=60:1335[layer4_comp]; "
            # Layer 6: CTA SUBSCRIBE Pill Overlay (Continuous presence from A to Z)
            f"[layer4_comp][4:v]overlay=(W-w)/2:1610[layer_branded]; "
            # Layer 5: Subtitles & Keyword Highlights (Mobile-Optimized 70pt, centered in plate)
            f"[layer_branded]ass='{safe_ass}':fontsdir='{fonts_dir_safe}'[outv]; "
            # Audio: Broadcast EQ + Ducked BGM + Loudnorm -14 LUFS
            f"[5:a]equalizer=f=120:width_type=o:width=1.5:g=3.2,equalizer=f=3400:width_type=o:width=1.5:g=2.2,volume=1.08[voice]; "
            f"[6:a]volume=0.07[bgm]; "
            f"[voice][bgm]amix=inputs=2:duration=first:dropout_transition=2,loudnorm=I=-14:TP=-1.5:LRA=11[outa]"
        )

        output_path = os.path.join(OUTPUT_DIR, output_filename)

        # Offline Metadata Tags
        clean = lambda s: (s or '').replace('"', '').replace('\n', ' ')
        meta_args = []
        if metadata:
            for k, v in [
                ('title', metadata.get("title", "")),
                ('artist', "@FactifyDailyShorts"),
                ('album', "Factify Shorts"),
                ('description', metadata.get("description", "")),
                ('comment', "Factify Science & Curiosity Shorts"),
                ('genre', "Education"),
                ('keywords', metadata.get("tags_str", ""))
            ]:
                meta_args.extend(['-metadata', f'{k}={clean(v)}'])

        ffmpeg_cmd = [
            'ffmpeg', '-y',
            '-stream_loop', '-1', '-i', video_source_path,
            '-loop', '1', '-i', self.grad_path,
            '-loop', '1', '-i', self.top_brand_path,
            '-loop', '1', '-i', self.caption_plate_path,
            '-loop', '1', '-i', self.cta_path,
            '-i', voice_path,
            '-stream_loop', '-1', '-i', bgm_file,
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
            '-t', f"{total_duration:.2f}",
            output_path
        ]

        print("[Factify Engine] Executing master FFmpeg render...")
        subprocess.run(ffmpeg_cmd, check=True)
        print(f"🎉 MASTER SHORT RENDERED: {output_path}")

        # Save SEO Metadata Package
        if metadata:
            seo_path = os.path.join(OUTPUT_DIR, output_filename.replace('.mp4', '_seo.json'))
            with open(seo_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            print(f"📄 VidIQ SEO Package saved: {seo_path}")

        return output_path


if __name__ == '__main__':
    template = FactifyShortsTemplate()
    
    solar_meta = {
        "title": "Can a Solar Superflare DESTROY Earth? ☀️ (Astrophysics) #Shorts",
        "description": (
            "What would ACTUALLY happen if a solar superflare hit Earth? ☀️ Here is the cosmic physics mechanism!\n\n"
            "Deep within the Sun, entangled magnetic field lines build up astronomical energy. "
            "When these magnetic ropes snap, a coronal mass ejection erupts, hurling billions of tons of charged plasma at millions of miles per hour!\n"
            "1️⃣ Sunspot magnetic shear triggers a hyper-powerful solar flare\n"
            "2️⃣ Billions of tons of plasma streak across 93 million miles of space\n"
            "3️⃣ Direct collision violently crushes Earth's protective magnetosphere\n"
            "4️⃣ Geomagnetically induced currents overpower electrical transformers\n"
            "5️⃣ Global power grids fail instantly, causing catastrophic worldwide blackout\n\n"
            "Subscribe to @FactifyDailyShorts for mind-blowing science & space mechanisms every day!\n\n"
            "#solarflare #space #astronomy #science #earth #sun #shorts #factify"
        ),
        "tags": [
            "can a solar flare destroy earth", "solar storm 2026", "what is a coronal mass ejection",
            "space facts shorts", "astrophysics animation", "science facts", "solar flare hitting earth",
            "geomagnetic storm", "factify shorts", "how it actually works"
        ]
    }
    solar_meta['tags_str'] = ", ".join(solar_meta['tags'])

    solar_script = (
        "Deep inside the sun, twisted magnetic fields build up unimaginable energy. "
        "Suddenly, a massive solar flare erupts, blasting billions of tons of electrified plasma into deep space! "
        "If aimed directly at Earth, this cosmic storm would violently compress our magnetic field. "
        "Within minutes, electrical grids around the world would catch fire, plunging humanity into total darkness!"
    )

    template.render_short(
        video_source_path='temp/solar_storm_superflare_raw.mp4',
        script_text=solar_script,
        output_filename='Factify_Solar_Superflare_Master.mp4',
        metadata=solar_meta
    )
