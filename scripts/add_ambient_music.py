#!/usr/bin/env python3
"""Add ambient synth music to the DeFi Sentinel demo video using ffmpeg aevalsrc."""
import subprocess, os

VIDEO_IN = "/root/defi-sentinel/demo/defi_sentinel_final.mp4"
VIDEO_OUT = "/root/defi-sentinel/demo/defi_sentinel_final_music.mp4"
TMPDIR = "/tmp/defi_sentinel_build"

os.makedirs(TMPDIR, exist_ok=True)

# Get video duration
dur_r = subprocess.run(
    f"ffprobe -v error -show_entries format=duration -of csv=p=0 {VIDEO_IN}",
    shell=True, capture_output=True, text=True
)
duration = round(float(dur_r.stdout.strip()))
print(f"Video duration: {duration}s")

# Generate ambient synth pad using ffmpeg aevalsrc
# Low drone with slow modulation, cyberpunk feel
SYNTH_EXPR = (
    "sin(55)*0.15+sin(55.5)*0.1+"
    "sin(110)*0.08+sin(111)*0.05+"
    "sin(220)*0.04+sin(221)*0.03+"
    "sin(330)*0.02+"
    "((sin(2*PI*0.12*t)+sin(2*PI*0.17*t))*0.12)+"
    "((sin(2*PI*0.23*t)*sin(2*PI*0.07*t))*0.06)"
)

print("[1/2] Generating ambient synth pad...")
r = subprocess.run(
    f'ffmpeg -y -f lavfi -i "aevalsrc=exprs=\'{SYNTH_EXPR}\':s=44100:d={duration}" '
    f'-ac 2 -af "loudnorm=I=-20:LRA=2:dual_mono=true,afade=t=in:d=3,afade=t=out:st={duration-3}:d=3,'
    f'lowpass=f=500,highpass=f=40" '
    f'{TMPDIR}/ambient.wav',
    shell=True, capture_output=True, text=True, timeout=60
)
last_line = [l for l in r.stderr.strip().split('\n') if 'time=' in l.lower()]
if last_line:
    print(f"  synth done: {last_line[-1][-100:]}")

print("[2/2] Mixing ambient into video...")
# Mix: video track from original, audio from synth (lower volume)
r = subprocess.run(
    f'ffmpeg -y -i {VIDEO_IN} -i {TMPDIR}/ambient.wav '
    f'-filter_complex "[1:a]volume=0.35[a1]" '
    f'-map 0:v -map "[a1]" -c:v copy -c:a aac -b:a 192k -shortest '
    f'{VIDEO_OUT}',
    shell=True, capture_output=True, text=True, timeout=120
)
last_line = [l for l in r.stderr.strip().split('\n') if 'time=' in l.lower()]
if last_line:
    print(f"  mix done: {last_line[-1][-100:]}")

print(f"\n[DONE] Saved to {VIDEO_OUT}")
os.system(f"ls -lh {VIDEO_OUT}")