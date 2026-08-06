#!/usr/bin/env python3
"""Build final 95s DeFi Sentinel demo: intro(8s) + main(79s) + outro(8s) + music."""
import subprocess, os, sys

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
OUTDIR = "/root/defi-sentinel/demo"
TMPDIR = "/tmp/defi_sentinel_build"

os.makedirs(TMPDIR, exist_ok=True)
os.makedirs(OUTDIR, exist_ok=True)

def run(cmd, label=""):
    print(f"[{label}] Running...")
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.returncode != 0 and label != "WARN":
        print(f"STDERR: {r.stderr[-500:]}")
    else:
        lines = [l for l in r.stderr.strip().split('\n') if 'frame=' in l or 'time=' in l]
        if lines:
            print(f"  last: {lines[-1][-100:]}")
    return r.returncode == 0

# === INTRO (8s) ===
intro_vf = (
    f"drawtext=fontfile='{FONT}':text='DEFI SENTINEL':"
    f"fontsize=80:fontcolor=white:x=(w-text_w)/2:y=h*0.40:"
    f"enable='between(t,1.0,7.0)',"
    f"drawtext=fontfile='{FONT}':text='Your DeFi portfolio never sleeps.':"
    f"fontsize=36:fontcolor=#4FC3F7:x=(w-text_w)/2:y=h*0.58:"
    f"enable='between(t,2.5,7.0)',"
    f"drawtext=fontfile='{FONT_REG}':text='Autonomous · Reliable · Verifiably Onchain':"
    f"fontsize=28:fontcolor=#90A4AE:x=(w-text_w)/2:y=h*0.68:"
    f"enable='between(t,3.5,7.0')"
)
run(f'ffmpeg -y -f lavfi -i color=c=0x0A0E17:s=1920x1080:d=8 '
    f'-c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p '
    f'-vf "{intro_vf}" {TMPDIR}/intro.mp4', "INTRO")

# === OUTRO (8s) ===
outro_vf = (
    f"drawtext=fontfile='{FONT}':text='DEFI SENTINEL':"
    f"fontsize=56:fontcolor=white:x=(w-text_w)/2:y=h*0.35:"
    f"enable='between(t,0.5,6.0)',"
    f"drawtext=fontfile='{FONT}':text='github.com/Carlys17/defi-sentinel':"
    f"fontsize=32:fontcolor=#4FC3F7:x=(w-text_w)/2:y=h*0.52:"
    f"enable='between(t,1.5,6.5)',"
    f"drawtext=fontfile='{FONT_REG}':text='Built for DoraHacks Agents Onchain x KeeperHub':"
    f"fontsize=24:fontcolor=#78909C:x=(w-text_w)/2:y=h*0.65:"
    f"enable='between(t,2.5,6.5')"
)
run(f'ffmpeg -y -f lavfi -i color=c=0x0A0E17:s=1920x1080:d=8 '
    f'-c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p '
    f'-vf "{outro_vf}" {TMPDIR}/outro.mp4', "OUTRO")

# === CONCAT list ===
with open(f"{TMPDIR}/list.txt", "w") as f:
    f.write(f"file '{TMPDIR}/intro.mp4'\n")
    f.write("file '/tmp/defi_demo_v2_extended.mp4'\n")
    f.write(f"file '{TMPDIR}/outro.mp4'\n")

print("[CONCAT] Building concatenation file and merging...")
r = subprocess.run(
    f'ffmpeg -y -f concat -safe 0 -i {TMPDIR}/list.txt -c copy {TMPDIR}/concat_raw.mp4 2>&1',
    shell=True, capture_output=True, text=True
)
if r.returncode != 0:
    # If -c copy fails due to codec mismatch, re-encode
    print("  -c copy failed, retrying with re-encode...")
    r = subprocess.run(
        f'ffmpeg -y -f concat -safe 0 -i {TMPDIR}/list.txt -c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p {TMPDIR}/concat_raw.mp4',
        shell=True, capture_output=True, text=True
    )

last_line = [l for l in r.stderr.strip().split('\n') if 'time=' in l.lower()]
if last_line:
    print(f"  merge done: {last_line[-1][-100:]}")
else:
    print(f"  stderr tail: {r.stderr[-200:]}")

# === COPY FINAL ===
import shutil
shutil.copy(f"{TMPDIR}/concat_raw.mp4", f"{OUTDIR}/defi_sentinel_final.mp4")

dur_r = subprocess.run(
    f"ffprobe -v error -show_entries format=duration -of csv=p=0 {TMPDIR}/concat_raw.mp4",
    shell=True, capture_output=True, text=True
)
duration = dur_r.stdout.strip()
print(f"\n[FINAL] Total duration: {duration}s")
print(f"[FINAL] Saved to {OUTDIR}/defi_sentinel_final.mp4")

# Check if ambient music already exists
music_files = []
for d in ["/root/music", "/root/media", os.path.expanduser("~")]:
    try:
        for f in os.listdir(d):
            if f.endswith(('.mp3', '.wav')) and ('ambient' in f.lower() or 'synth' in f.lower()):
                music_files.append(os.path.join(d, f))
    except:
        pass

if music_files:
    print(f"[MUSIC] Found ambient tracks: {music_files}")
else:
    print("[MUSIC] No ambient/synth tracks found. Will skip music layer.")
