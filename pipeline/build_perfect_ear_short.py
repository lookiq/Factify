import os
import sys
import math
import struct
import wave
import asyncio
import subprocess
import edge_tts
from PIL import Image, ImageDraw, ImageFont
import numpy as np

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)

TEMP_DIR = 'temp'
OUTPUT_DIR = 'output'
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

W, H = 1080, 1920
FPS = 30
TOTAL_DURATION = 46.0
TOTAL_FRAMES = int(TOTAL_DURATION * FPS)

TEST_START = 11.5
TEST_DURATION = 26.5
TEST_END = TEST_START + TEST_DURATION # 38.0

# Calibrated points matching competitor (time_offset, age, freq)
CALIB_T = [0.0, 2.0, 4.5, 6.5, 8.5, 10.5, 12.5, 14.5, 16.5, 18.5, 20.5, 22.5, 24.5, 26.0, 26.5]
CALIB_A = [99,  98,  94,  90,  84,  78,   71,   64,   57,   48,   35,   26,   18,   18,   18]
CALIB_F = [874, 1800, 3654, 5100, 6550, 7900, 9213, 10580, 11940, 13420, 15057, 16400, 17800, 18500, 18500]

def get_age_and_freq(t):
    if t < TEST_START:
        return 99, 874
    if t >= TEST_END:
        return 18, 18500
    rel_t = t - TEST_START
    age = int(round(float(np.interp(rel_t, CALIB_T, CALIB_A))))
    freq = int(round(float(np.interp(rel_t, CALIB_T, CALIB_F))))
    return age, freq

async def generate_speech():
    print("Generating speech voiceovers...")
    intro_text = "Scientists have probably created a sound that you can listen to to determine the age of your ears. I will play a sound now, and the number at which you stop hearing the sound will be your ear age."
    outro_text = "Tell me in the comments how old you are! Stay connected with Factify for more mind-blowing science tests."
    
    comm = edge_tts.Communicate(intro_text, 'en-US-ChristopherNeural')
    await comm.save(os.path.join(TEMP_DIR, 'perfect_intro.mp3'))
    
    comm = edge_tts.Communicate(outro_text, 'en-US-ChristopherNeural')
    await comm.save(os.path.join(TEMP_DIR, 'perfect_outro.mp3'))
    print("Speech generated.")

def generate_tone_wav():
    print("Generating tone audio...")
    sample_rate = 44100
    total_samples = int(TOTAL_DURATION * sample_rate)
    start_sample = int(TEST_START * sample_rate)
    end_sample = int(TEST_END * sample_rate)
    ramp_samples = int(0.3 * sample_rate)

    raw_bytes = bytearray()
    phase = 0.0

    for i in range(total_samples):
        t = i / sample_rate
        if start_sample <= i < end_sample:
            rel_t = t - TEST_START
            freq = float(np.interp(rel_t, CALIB_T, CALIB_F))
            phase += 2.0 * math.pi * freq / sample_rate
            if phase > 2.0 * math.pi:
                phase -= 2.0 * math.pi

            amp = 0.30
            if i - start_sample < ramp_samples:
                amp *= (i - start_sample) / ramp_samples
            elif end_sample - i < ramp_samples:
                amp *= (end_sample - i) / ramp_samples

            val = int(amp * 32767.0 * math.sin(phase))
        else:
            val = 0
        raw_bytes.extend(struct.pack('<h', val))

    tone_path = os.path.join(TEMP_DIR, 'perfect_tone.wav')
    with wave.open(tone_path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(raw_bytes)
    print("Tone audio generated.")
    return tone_path

def mix_master_audio():
    print("Mixing master audio track...")
    audio_out = os.path.join(TEMP_DIR, 'master_audio.m4a')
    cmd = [
        'ffmpeg', '-y',
        '-i', os.path.join(TEMP_DIR, 'perfect_intro.mp3'),
        '-i', os.path.join(TEMP_DIR, 'perfect_tone.wav'),
        '-i', os.path.join(TEMP_DIR, 'perfect_outro.mp3'),
        '-filter_complex',
        '[0:a]aresample=44100[a0]; [1:a]aresample=44100[a1]; [2:a]aresample=44100,adelay=38000|38000[a2]; [a0][a1][a2]amix=inputs=3:duration=longest:dropout_transition=0[aout]',
        '-map', '[aout]',
        '-c:a', 'aac', '-b:a', '192k',
        '-t', str(TOTAL_DURATION),
        audio_out
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("Master audio ready:", audio_out)
    return audio_out

def build_video():
    print("Building full video composite...")
    audio_path = os.path.join(TEMP_DIR, 'master_audio.m4a')
    if not os.path.exists(audio_path):
        asyncio.run(generate_speech())
        generate_tone_wav()
        mix_master_audio()

    bg_video_path = os.path.join(TEMP_DIR, 'clean_bg_full.mp4')
    if not os.path.exists(bg_video_path):
        raise FileNotFoundError(f"Missing background video: {bg_video_path}")

    # Load assets
    ear_raw = Image.open('temp/ear_icon_clean.png').convert('RGBA')
    ear_h = 390
    ear_w = int(ear_raw.width * (ear_h / ear_raw.height))
    ear_left = ear_raw.resize((ear_w, ear_h), Image.Resampling.LANCZOS)
    ear_right = ear_left.transpose(Image.FLIP_LEFT_RIGHT)

    # Fonts
    font_impact_title = ImageFont.truetype('C:/Windows/Fonts/impact.ttf', 74)
    font_age = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 240)
    font_freq = ImageFont.truetype('C:/Windows/Fonts/ARIALNB.TTF', 34)
    font_wm = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 28)
    font_hook_title = ImageFont.truetype('C:/Windows/Fonts/impact.ttf', 68)
    font_hook_sub = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 38)
    font_outro_title = ImageFont.truetype('C:/Windows/Fonts/impact.ttf', 72)
    font_outro_sub = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 36)

    card_w, card_h = 1040, 608
    card_x = (W - card_w) // 2
    card_y = (H - card_h) // 2 # 656

    box_w, box_h = 380, 440
    box_x = (card_w - box_w) // 2
    box_y = 140

    wm_text = '@FactifyDailyShorts'
    wm_y = H - 170

    # Start ffmpeg background reader process
    read_cmd = [
        'ffmpeg',
        '-i', bg_video_path,
        '-f', 'image2pipe',
        '-pix_fmt', 'rgb24',
        '-vcodec', 'rawvideo',
        '-r', str(FPS),
        '-'
    ]
    read_proc = subprocess.Popen(read_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=10**8)

    # Output video file
    output_video = os.path.join(OUTPUT_DIR, 'factify_short_latest.mp4')
    write_cmd = [
        'ffmpeg', '-y',
        '-f', 'rawvideo',
        '-pix_fmt', 'rgb24',
        '-s', f'{W}x{H}',
        '-r', str(FPS),
        '-i', '-',
        '-i', audio_path,
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '17',
        '-pix_fmt', 'yuv420p',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-shortest',
        output_video
    ]
    write_proc = subprocess.Popen(write_cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

    frame_bytes = W * H * 3
    print(f"Rendering {TOTAL_FRAMES} frames ({TOTAL_DURATION}s @ {FPS}fps)...")

    # Pre-generate visualizer base seeds
    np.random.seed(42)
    bars_x = list(range(20, card_w - 20, 3))
    num_bars = len(bars_x)
    base_phases = np.random.uniform(0, 2*np.pi, num_bars)
    base_speeds = np.random.uniform(0.15, 0.45, num_bars)

    for f_idx in range(TOTAL_FRAMES):
        raw_bg = read_proc.stdout.read(frame_bytes)
        if len(raw_bg) < frame_bytes:
            break
        
        t = f_idx / FPS
        frame_pil = Image.frombytes('RGB', (W, H), raw_bg)

        # 1. INTRO SECTION (0.0s <= t < 11.5s)
        if t < TEST_START:
            idraw = ImageDraw.Draw(frame_pil)
            # Glowing dark backdrop plate in center
            intro_plate_w, intro_plate_h = 920, 380
            ix = (W - intro_plate_w) // 2
            iy = (H - intro_plate_h) // 2
            
            # Subtle dark glass plate
            idraw.rectangle([ix, iy, ix + intro_plate_w, iy + intro_plate_h], fill=(0, 0, 0, 220), outline=(255, 255, 255, 240), width=6)
            
            # Hook texts
            t1 = "HOW OLD ARE YOUR EARS?"
            bb1 = idraw.textbbox((0, 0), t1, font=font_hook_title)
            w1 = bb1[2] - bb1[0]
            idraw.text(((W - w1) // 2, iy + 45), t1, fill=(255, 230, 0), font=font_hook_title)

            t2 = "PUT ON HEADPHONES"
            bb2 = idraw.textbbox((0, 0), t2, font=font_hook_sub)
            w2 = bb2[2] - bb2[0]
            idraw.text(((W - w2) // 2, iy + 145), t2, fill=(0, 235, 255), font=font_hook_sub)

            t3 = "The number where you stop hearing is your age!"
            bb3 = idraw.textbbox((0, 0), t3, font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 30))
            w3 = bb3[2] - bb3[0]
            idraw.text(((W - w3) // 2, iy + 225), t3, fill=(240, 240, 240), font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 30))

            t4 = "TEST STARTS IN 3... 2... 1..."
            if t > 8.0:
                bb4 = idraw.textbbox((0, 0), t4, font=ImageFont.truetype('C:/Windows/Fonts/impact.ttf', 44))
                w4 = bb4[2] - bb4[0]
                idraw.text(((W - w4) // 2, iy + 295), t4, fill=(57, 255, 20), font=ImageFont.truetype('C:/Windows/Fonts/impact.ttf', 44))

        # 2. TEST SECTION (11.5s <= t < 38.0s)
        elif TEST_START <= t < TEST_END:
            age, freq = get_age_and_freq(t)
            
            card = Image.new('RGBA', (card_w, card_h), (0, 0, 0, 255))
            cdraw = ImageDraw.Draw(card)

            # Outer white border (12px)
            cdraw.rectangle([6, 6, card_w - 7, card_h - 7], outline=(255, 255, 255, 255), width=12)

            # Dynamic Animated Audio Visualizer Spectrum
            center_y = 350
            # Frequency dependent energy:
            # as frequency increases, bars jitter faster
            for b_i, bx in enumerate(bars_x):
                # multi-sine harmonic height
                osc = math.sin(f_idx * base_speeds[b_i] + base_phases[b_i]) * math.cos(f_idx * 0.2 + b_i * 0.1)
                bar_h = int(35 + 130 * abs(osc))
                
                # Colors: cyan to bright white-blue
                r = int(20 + 80 * abs(osc))
                g = int(200 + 55 * abs(osc))
                b = 255
                cdraw.line([(bx, center_y - bar_h), (bx, center_y + bar_h)], fill=(r, g, b, 210), width=1)

            # Center horizontal glow line
            for dy in range(-5, 6):
                alpha = int(255 * (1 - abs(dy) / 6))
                cdraw.line([(20, center_y + dy), (card_w - 20, center_y + dy)], fill=(130, 235, 255, alpha), width=1)

            # Center Grey Box
            cdraw.rectangle([box_x, box_y, box_x + box_w, box_y + box_h], fill=(110, 110, 110, 255))

            # Ear Icons on Left and Right
            card.paste(ear_left, (35, 155), ear_left)
            card.paste(ear_right, (card_w - 35 - ear_w, 155), ear_right)

            # Title: HOW OLD ARE YOUR EARS
            title_text = 'HOW OLD ARE YOUR EARS'
            bbox = cdraw.textbbox((0, 0), title_text, font=font_impact_title)
            tw = bbox[2] - bbox[0]
            cdraw.text(((card_w - tw) // 2, 22), title_text, fill=(255, 255, 255, 255), font=font_impact_title)

            # Age Number (Arial Regular, 240)
            age_text = str(age)
            bbox = cdraw.textbbox((0, 0), age_text, font=font_age)
            aw = bbox[2] - bbox[0]
            cdraw.text((box_x + (box_w - aw) // 2, box_y + 40), age_text, fill=(255, 255, 255, 255), font=font_age)

            # Frequency Text (Arial Narrow Bold, 34)
            freq_str = f"{freq:,}"
            freq_text = f"FREQUENCY ( HZ ): {freq_str}"
            bbox = cdraw.textbbox((0, 0), freq_text, font=font_freq)
            fw = bbox[2] - bbox[0]
            cdraw.text((box_x + (box_w - fw) // 2, box_y + box_h - 48), freq_text, fill=(255, 255, 255, 255), font=font_freq)

            # Composite card onto background
            frame_pil.paste(card, (card_x, card_y), card)

        # 3. OUTRO SECTION (38.0s <= t <= 46.0s)
        else:
            odraw = ImageDraw.Draw(frame_pil)
            out_plate_w, out_plate_h = 920, 420
            ox = (W - out_plate_w) // 2
            oy = (H - out_plate_h) // 2
            
            odraw.rectangle([ox, oy, ox + out_plate_w, oy + out_plate_h], fill=(0, 0, 0, 220), outline=(255, 255, 255, 240), width=6)
            
            ot1 = "COMMENT YOUR EAR AGE!"
            obb1 = odraw.textbbox((0, 0), ot1, font=font_outro_title)
            ow1 = obb1[2] - obb1[0]
            odraw.text(((W - ow1) // 2, oy + 45), ot1, fill=(255, 230, 0), font=font_outro_title)

            ot2 = "WHAT NUMBER DID YOU HEAR?"
            obb2 = odraw.textbbox((0, 0), ot2, font=font_outro_sub)
            ow2 = obb2[2] - obb2[0]
            odraw.text(((W - ow2) // 2, oy + 145), ot2, fill=(0, 235, 255), font=font_outro_sub)

            ot3 = "Don't forget to like and subscribe for more tests!"
            obb3 = odraw.textbbox((0, 0), ot3, font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 32))
            ow3 = obb3[2] - obb3[0]
            odraw.text(((W - ow3) // 2, oy + 235), ot3, fill=(240, 240, 240), font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 32))

            ot4 = "FACTIFY DAILY SHORTS"
            obb4 = odraw.textbbox((0, 0), ot4, font=ImageFont.truetype('C:/Windows/Fonts/impact.ttf', 46))
            ow4 = obb4[2] - obb4[0]
            odraw.text(((W - ow4) // 2, oy + 310), ot4, fill=(57, 255, 20), font=ImageFont.truetype('C:/Windows/Fonts/impact.ttf', 46))

        # Factify Watermark: @FactifyDailyShorts at bottom center
        wdraw = ImageDraw.Draw(frame_pil)
        bbox = wdraw.textbbox((0, 0), wm_text, font=font_wm)
        wm_w = bbox[2] - bbox[0]
        # Shadow
        wdraw.text(((W - wm_w) // 2 + 2, wm_y + 2), wm_text, fill=(0, 0, 0, 180), font=font_wm)
        # Text
        wdraw.text(((W - wm_w) // 2, wm_y), wm_text, fill=(255, 255, 255, 175), font=font_wm)

        # Write to ffmpeg pipe
        write_proc.stdin.write(frame_pil.tobytes())

        if f_idx % 150 == 0:
            print(f"Render progress: frame {f_idx}/{TOTAL_FRAMES} ({int(f_idx/TOTAL_FRAMES*100)}%)")

    read_proc.stdout.close()
    read_proc.terminate()
    write_proc.stdin.close()
    write_proc.wait()

    print("Video render complete:", output_video)
    
    # Generate metadata.json
    metadata = {
        "title": "How Old Are Your Ears? 👂🔊 Take The Audio Test! #Shorts",
        "description": "Scientists created a sound frequency that can determine the exact age of your ears! Put on your headphones and listen closely. The number at which you stop hearing the sound is your ear age.\n\n👇 Comment your ear age below!\n\nSubscribe to Factify Daily Shorts for more mind-blowing science quizzes and facts!\n\n#Shorts #HearingTest #EarAge #Science #Factify",
        "tags": [
            "how old are your ears",
            "ear age test",
            "hearing test",
            "frequency test",
            "audio test",
            "ear test",
            "science experiment",
            "factify",
            "factify shorts",
            "shorts"
        ],
        "categoryId": "28", # Science & Technology
        "topic_id": "ear_age_hearing_test_animated"
    }
    with open(os.path.join(OUTPUT_DIR, 'metadata.json'), 'w', encoding='utf-8') as f:
        import json
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print("Metadata generated.")

if __name__ == '__main__':
    build_video()
