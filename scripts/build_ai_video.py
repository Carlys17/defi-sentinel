#!/usr/bin/env python3
"""Intro/outro title cards from DashScope AI bg → MP4 via PIL + ffmpeg."""

import os
import shutil
import subprocess

from PIL import Image, ImageDraw, ImageFont

TMPDIR = "/tmp/defi_sentinel_build"
OUTDIR = "/root/defi-sentinel/demo"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

os.makedirs(TMPDIR, exist_ok=True)
os.makedirs(OUTDIR, exist_ok=True)

RESAMPLE = getattr(Image.Resampling, "LANCZOS", getattr(Image, "ANTIALIAS", 1))
FPS, DURATION, TOTAL = 24, 8, 192
BOLD = ImageFont.truetype(FONT_B, 80)
BOLD_SM = ImageFont.truetype(FONT_B, 56)
REG = ImageFont.truetype(FONT_R, 36)
RSM = ImageFont.truetype(FONT_R, 28)
RXS = ImageFont.truetype(FONT_R, 24)
W, H = 1920, 1080


def fade_alpha(i, start):
    """Alpha value for a fade-in starting at frame `start`."""
    progress = min(1.0, (i - start) / 20)
    return int(min(255, progress * 255))


def make_intro():
    bg = Image.open(f"{TMPDIR}/intro_bg.png").convert("RGB").resize((W, H), RESAMPLE)
    prefix = f"{TMPDIR}/intro_f"
    for i in range(TOTAL):
        img = bg.copy()
        d = ImageDraw.Draw(img)

        if i >= 20:
            d.text(
                (750, int(H * 0.42)),
                "DEFI SENTINEL",
                font=BOLD,
                fill=(255, 255, 255, fade_alpha(i, 20)),
            )
        if i >= 40:
            d.text(
                (640, int(H * 0.58)),
                "Your DeFi portfolio never sleeps.",
                font=REG,
                fill=(79, 195, 247, fade_alpha(i, 40)),
            )
        if i >= 60:
            d.text(
                (540, int(H * 0.68)),
                "Autonomous · Reliable · Verifiably Onchain",
                font=RSM,
                fill=(144, 164, 174, fade_alpha(i, 60)),
            )
        if i >= 80:
            d.text(
                (640, int(H * 0.76)),
                "github.com/Carlys17/defi-sentinel",
                font=RXS,
                fill=(0, 170, 204, fade_alpha(i, 80)),
            )
        img.save(f"{prefix}_{i:04d}.png")


def make_outro():
    bg = Image.open(f"{TMPDIR}/outro_bg.png").convert("RGB").resize((W, H), RESAMPLE)
    prefix = f"{TMPDIR}/outro_f"
    for i in range(TOTAL):
        img = bg.copy()
        d = ImageDraw.Draw(img)
        if i >= 20:
            d.text(
                (750, int(H * 0.36)),
                "DEFI SENTINEL",
                font=BOLD_SM,
                fill=(255, 255, 255, fade_alpha(i, 20)),
            )
        if i >= 40:
            d.text(
                (640, int(H * 0.50)),
                "Autonomous · Reliable · Verifiably Onchain",
                font=REG,
                fill=(79, 195, 247, fade_alpha(i, 40)),
            )
        if i >= 60:
            d.text(
                (640, int(H * 0.63)),
                "github.com/Carlys17/defi-sentinel",
                font=RSM,
                fill=(0, 170, 204, fade_alpha(i, 60)),
            )
        if i >= 80:
            progress = min(1.0, (i - 80) / 20)
            d.text(
                (560, int(H * 0.72)),
                "Built for DoraHacks Agents Onchain × KeeperHub",
                font=RSM,
                fill=(120, 144, 156, int(min(200, progress * 200))),
            )
        img.save(f"{prefix}_{i:04d}.png")


def render(name):
    tag = f"{name}_f_%04d.png"
    ff_cmd = (
        f"ffmpeg -y -r 24 -i '{TMPDIR}/{tag}' -c:v libx264 -preset medium "
        f"-crf 18 -pix_fmt yuv420p '{TMPDIR}/{name}.mp4'"
    )
    subprocess.run(ff_cmd, shell=True, capture_output=True, timeout=120)
    dr = subprocess.run(
        f"ffprobe -v error -show_entries format=duration -of csv=p=0 '{TMPDIR}/{name}.mp4'",
        shell=True,
        capture_output=True,
        text=True,
        timeout=60,
    ).stdout.strip()
    print(f"[3] {name}: {dr}s")


def main():
    print("[1] intro frames...")
    make_intro()
    print("  OK")
    print("[2] outro frames...")
    make_outro()
    print("  OK")

    render("intro")
    render("outro")

    # concat list
    cl = f"{TMPDIR}/cl.txt"
    with open(cl, "w") as f:
        f.write(f"file '{TMPDIR}/intro.mp4'\n")
        f.write("file '/tmp/defi_demo_v2_extended.mp4'\n")
        f.write(f"file '{TMPDIR}/outro.mp4'\n")

    print("[4] concat...")
    subprocess.run(
        f"ffmpeg -y -f concat -safe 0 -i {cl} -c copy '{TMPDIR}/final.mp4'",
        shell=True,
        capture_output=True,
        timeout=120,
    )

    dr = subprocess.run(
        f"ffprobe -v error -show_entries format=duration -of csv=p=0 '{TMPDIR}/final.mp4'",
        shell=True,
        capture_output=True,
        text=True,
        timeout=60,
    ).stdout.strip()
    print(f"[5] total duration: {dr}s")

    shutil.copy(f"{TMPDIR}/final.mp4", f"{OUTDIR}/defi_sentinel_ai.mp4")
    print("[6] saved plain: defi_sentinel_ai.mp4")

    # ambient music
    print("[7] ambient synth...")
    mex = (
        "sin(55)*0.15+sin(55.5)*0.1+sin(110)*0.08+sin(111)*0.05+sin(220)*0.04"
        "+sin(221)*0.03+sin(330)*0.02+((sin(2*PI*0.12*t)+sin(2*PI*0.17*t))*0.12)"
        "+((sin(2*PI*0.23*t)*sin(2*PI*0.07*t))*0.06)"
    )
    adur = int(float(dr)) + 5
    subprocess.run(
        "ffmpeg -y -f lavfi -i "
        f"'aevalsrc=exprs='{mex}':s=44100:d={adur}' -ac 2 "
        f'-af "loudnorm=I=-20:LRA=2:dual_mono=true,afade=t=in:d=3,'
        f'afade=t=out:st={int(float(dr)) - 3}:d=3,lowpass=f=500,highpass=f=40" '
        f"'{TMPDIR}/amb.wav'",
        shell=True,
        capture_output=True,
        timeout=60,
    )

    final_music = f"{OUTDIR}/defi_sentinel_music.mp4"
    subprocess.run(
        f"ffmpeg -y -i {OUTDIR}/defi_sentinel_ai.mp4 -i {TMPDIR}/amb.wav "
        "-filter_complex '[1:a]volume=0.35[a1]' -map 0:v -map '[a1]' "
        f"-c:v copy -c:a aac -b:a 192k -shortest '{final_music}'",
        shell=True,
        capture_output=True,
        timeout=120,
    )

    for fn in ["defi_sentinel_ai.mp4", "defi_sentinel_music.mp4"]:
        size = os.path.getsize(f"{OUTDIR}/{fn}")
        print(f"  {fn} ({size / 1024 / 1024:.1f} MB)")
    print("\n[DONE]")


if __name__ == "__main__":
    main()
