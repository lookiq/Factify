import os
import subprocess
import sys

def main():
    print("=" * 65)
    print("      FACTIFY SHORTS - LOCAL 1-CLICK VIDEO GENERATOR")
    print("=" * 65)

    print("\n[Step 1/2] Generating Video (NASA Footage + Neural Voice + Subtitles)...")
    res = subprocess.run([sys.executable, "pipeline/build_short.py"])
    if res.returncode != 0:
        print("\n[ERROR] Video generation failed. Check errors above.")
        return

    output_video = os.path.abspath("output/factify_short_latest.mp4")
    print("\n" + "=" * 65)
    print(f"[Step 2/2] SUCCESS! Your Factify Short is Ready:")
    print(f"Path: {output_video}")
    print("=" * 65)

    if sys.platform == "win32" and os.path.exists(output_video):
        subprocess.run(f'explorer /select,"{output_video}"', shell=True)

if __name__ == "__main__":
    main()
