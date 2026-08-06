#!/usr/bin/env python3
"""Convert demo text output to MP4 video using ffmpeg."""

import subprocess
import tempfile
import os
from pathlib import Path

def text_to_video(text_file: str, output_file: str, fps: int = 2):
    """Convert text file to video by rendering each line as a frame."""
    
    # Read text file
    with open(text_file, 'r') as f:
        lines = f.readlines()
    
    # Create frames directory
    frames_dir = Path("logs/frames")
    frames_dir.mkdir(exist_ok=True)
    
    # Generate image frames from text using chafa or ffmpeg
    for i, line in enumerate(lines):
        # Clean ANSI codes
        clean_line = line.replace('\x1b[0m', '').replace('\x1b[1m', '').replace('\x1b[92m', '').replace('\x1b[94m', '').replace('\x1b[93m', '').replace('\x1b[96m', '')
        
        # Create text file for this frame
        frame_file = frames_dir / f"frame_{i:04d}.txt"
        frame_file.write_text(clean_line.strip())
    
    # Use ffmpeg to create video from text images
    # First, create a simple video with black background and white text
    cmd = [
        "ffmpeg",
        "-f", "lavfi",
        "-i", f"color=c=black:s=1280x720:d=30",
        "-vf", f"drawtext=textfile='logs/demo_text.txt':fontsize=24:fontcolor=white:x=10:y=10",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "22",
        "-pix_fmt", "yuv420p",
        "-t", "30",
        output_file,
        "-y"
    ]
    
    subprocess.run(cmd, check=True)
    print(f"Video saved to {output_file}")

if __name__ == "__main__":
    text_to_video("logs/demo_text.txt", "logs/demo_video.mp4")