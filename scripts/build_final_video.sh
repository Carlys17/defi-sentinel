#!/bin/bash
# Rebuild final 95s demo video: intro(8s) + main(79s) + outro(8s)
set -e

FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
OUTDIR="/root/defi-sentinel/demo"
TMPDIR="/tmp/defi_sentinel_build"
mkdir -p "$TMPDIR" "$OUTDIR"

echo "[1/4] Creating intro (8s)..."
FF="${FONT}" FFREG="${FONT_REG}" \
ffmpeg -y -f lavfi -i color=c=0x0A0E17:s=1920x1080:d=8 -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p \
  -vf 'drawtext=fontfile="'"$FONT"'":text='"'"'DEFI SENTINEL'"'"':fontsize=80:fontcolor=white:x='\'(w-text_w)'/2:y=h*0.40:enable='"'"'between(t,1.0,7.0)'"'"',drawtext=fontfile="'"$FONT"'":text='"'"'Your DeFi portfolio never sleeps.'"'"':fontsize=36:fontcolor="#4FC3F7":x='\'(w-text_w)'/2:y=h*0.58:enable='"'"'between(t,2.5,7.0)'"'"',drawtext=fontfile="'"$FONT_REG"'":text='"'"'Autonomous · Reliable · Verifiably Onchain'"'"':fontsize=28:fontcolor="#90A4AE":x='\'(w-text_w)'/2:y=h*0.68:enable='"'"'between(t,3.5,7.0)'"'"'' \
  "$TMPDIR/intro.mp4" 2>&1 | tail -1

echo "[2/4] Creating outro (8s)..."
ffmpeg -y -f lavfi -i color=c=0x0A0E17:s=1920x1080:d=8 -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p \
  -vf 'drawtext=fontfile="'"$FONT"'":text='"'"'DEFI SENTINEL'"'"':fontsize=56:fontcolor=white:x='\'(w-text_w)'/2:y=h*0.35:enable='"'"'between(t,0.5,6.0)'"'"',drawtext=fontfile="'"$FONT"'":text='"'"'github.com/Carlys17/defi-sentinel'"'"':fontsize=32:fontcolor="#4FC3F7":x='\'(w-text_w)'/2:y=h*0.52:enable='"'"'between(t,1.5,6.5)'"'"',drawtext=fontfile="'"$FONT_REG"'":text='"'"'Built for DoraHacks Agents Onchain x KeeperHub'"'"':fontsize=24:fontcolor="#78909C":x='\'(w-text_w)'/2:y=h*0.65:enable='"'"'between(t,2.5,6.5)'"'"'' \
  "$TMPDIR/outro.mp4" 2>&1 | tail -1

echo "[3/4] Concatenating intro + main + outro..."
cat > "$TMPDIR/list.txt" <<EOF
file '$TMPDIR/intro.mp4'
file '/tmp/defi_demo_v2_extended.mp4'
file '$TMPDIR/outro.mp4'
EOF

ffmpeg -y -f concat -safe 0 -i "$TMPDIR/list.txt" -c copy "$TMPDIR/concat_raw.mp4" 2>&1 | tail -1

echo "[4/4] Finalizing..."
cp "$TMPDIR/concat_raw.mp4" "$OUTDIR/defi_sentinel_final.mp4"
DURATION=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$TMPDIR/concat_raw.mp4" | tr -d '\r')
echo "Total duration: ${DURATION}s"
ls -lh "$OUTDIR/defi_sentinel_final.mp4"
echo "Done."
