#!/usr/bin/env python3
"""Final ultra-compose: all DashScope AI assets into 95s demo video."""
import json, os, subprocess
from PIL import Image, ImageDraw, ImageFont

ASSETS = "/tmp/defi_sentinel_build/assets"
OUT = "/tmp/defi_sentinel_build"
FINAL = "/root/defi-sentinel/demo/defi_sentinel_ultra.mp4"

with open(f"{ASSETS}/copy.json") as f:
    copy = json.load(f)

FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = ImageFont.truetype(FONT_B, 72)
REG_SM = ImageFont.truetype(FONT_R, 34)
W, H = 1920, 1080

def wrap(text, d, font, max_w):
    words, line, lines = text.split(), "", []
    for w in words:
        t = (line + " " + w).strip()
        if d.textbbox((0,0), t, font=font)[2] > max_w and line:
            lines.append(line); line = w
        else: line = t
    if line: lines.append(line)
    return lines

def make_slide(image_path, title, bullets, outname, duration):
    print(f"  {outname}...")
    bg = Image.open(image_path).convert("RGB").resize((W,H), Image.Resampling.LANCZOS)
    bg = Image.blend(bg, Image.new("RGB", (W,H), (0,0,0)), 0.4)
    img = bg.copy()
    d = ImageDraw.Draw(img)
    d.text((100, 80), title, font=BOLD, fill=(79,195,247))
    y = 220
    for b in bullets:
        for ln in wrap(b, d, REG_SM, W-260):
            d.text((140, y), "\u2022  " + ln, font=REG_SM, fill=(235,235,235))
            y += 52
        y += 18
    one = f"{OUT}/{outname}_one.png"
    img.save(one)
    subprocess.run(
        f"ffmpeg -y -loop 1 -t {duration} -i '{one}' "
        f"-c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -r 30 "
        f"'{OUT}/{outname}.mp4'",
        shell=True, capture_output=True, timeout=60)

make_slide(f"{ASSETS}/problem.png", "THE PROBLEM", copy["problem"], "prob", 4)
make_slide(f"{ASSETS}/arch_max.png", "ARCHITECTURE", copy["arch"], "arch", 6)
make_slide(f"{ASSETS}/safety.png", "SAFETY & OBSERVABILITY", copy["safety"], "safe", 4)

# Build concat list of all 6 parts (normalized to same codec/reso/fps first)
print("normalizing all parts...")
os.makedirs(f"{OUT}/n", exist_ok=True)
parts = [
    ("v1", f"{ASSETS}/intro_clip.mp4"),
    ("v2", f"{OUT}/prob.mp4"),
    ("v3", f"{OUT}/arch.mp4"),
    ("v4", "/tmp/defi_demo_v2_extended.mp4"),
    ("v5", f"{OUT}/safe.mp4"),
    ("v6", f"{ASSETS}/outro_clip.mp4"),
]
norm_paths = []
for tag, src in parts:
    dst = f"{OUT}/n/{tag}.mp4"
    subprocess.run(
        f"ffmpeg -y -i '{src}' -c:v libx264 -preset medium -crf 20 "
        f"-pix_fmt yuv420p -r 30 -an -vf 'scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2' '{dst}'",
        shell=True, capture_output=True, timeout=120)
    norm_paths.append(dst)

with open(f"{OUT}/ultra_cl.txt", "w") as f:
    for p in norm_paths: f.write(f"file '{p}'\n")

print("concatenating...")
subprocess.run(
    f"ffmpeg -y -f concat -safe 0 -i {OUT}/ultra_cl.txt -c:v libx264 -crf 20 "
    f"-pix_fmt yuv420p -r 30 '{OUT}/final_raw.mp4'",
    shell=True, capture_output=True, timeout=120)

dr = subprocess.run(
    f"ffprobe -v error -show_entries format=duration -of csv=p=0 '{OUT}/final_raw.mp4'",
    shell=True, capture_output=True, text=True).stdout.strip()
print(f"total duration: {dr}s")

# ambient music
mex = ("sin(55)*0.15+sin(55.5)*0.1+sin(110)*0.08+sin(111)*0.05+"
       "sin(220)*0.04+sin(221)*0.03+sin(330)*0.02+"
       "((sin(2*PI*0.12*t)+sin(2*PI*0.17*t))*0.12)+"
       "((sin(2*PI*0.23*t)*sin(2*PI*0.07*t))*0.06)")
adur = int(float(dr)) + 5
subprocess.run(
    f'ffmpeg -y -f lavfi -i "aevalsrc=exprs=\'{mex}\':s=44100:d={adur}" '
    f'-ac 2 -af "loudnorm=I=-20:LRA=2:dual_mono=true,afade=t=in:d=3,'
    f'afade=t=out:st={int(float(dr))-3}:d=3,lowpass=f=500,highpass=f=40" '
    f"'{OUT}/amb.wav'",
    shell=True, capture_output=True, timeout=90)

subprocess.run(
    f"ffmpeg -y -i {OUT}/final_raw.mp4 -i {OUT}/amb.wav "
    f"-filter_complex '[1:a]volume=0.35[a1]' "
    f"-map 0:v -map '[a1]' -c:v copy -c:a aac -b:a 192k -shortest "
    f"'{FINAL}'",
    shell=True, capture_output=True, timeout=120)

sz = os.path.getsize(FINAL)
dur_final = subprocess.run(
    f"ffprobe -v error -show_entries format=duration -of csv=p=0 '{FINAL}'",
    shell=True, capture_output=True, text=True).stdout.strip()
print(f"\n[DONE] {FINAL}")
print(f"  size: {sz/1024/1024:.1f} MB")
print(f"  duration: {dur_final}s")
