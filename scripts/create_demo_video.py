#!/usr/bin/env python3
"""Create a proper demo video for DeFi Sentinel hackathon submission."""

import subprocess
from pathlib import Path

def create_demo_video():
    """Create a complete demo video."""
    
    scenes = [
        # Scene 1: Title
        {
            "text": "DeFi Sentinel - Autonomous AI Agent",
            "duration": 5.0,
            "color": "black",
            "font_color": "green",
            "font_size": 48
        },
        # Scene 2: GitHub
        {
            "text": "GitHub: github.com/Carlys17/defi-sentinel",
            "duration": 5.0,
            "color": "black",
            "font_color": "white",
            "font_size": 36
        },
        # Scene 3: Demo Results
        {
            "text": "DEMO RESULTS: All 8 Steps PASSED",
            "duration": 5.0,
            "color": "black",
            "font_color": "green",
            "font_size": 36
        },
        # Scene 4: Transactions
        {
            "text": "2 Verified Transactions on Base Sepolia",
            "duration": 5.0,
            "color": "black",
            "font_color": "green",
            "font_size": 36
        },
        # Scene 5: Strategies
        {
            "text": "3 Agent Strategies via KeeperHub MCP",
            "duration": 5.0,
            "color": "black",
            "font_color": "white",
            "font_size": 36
        },
        # Scene 6: KeeperHub Features
        {
            "text": "KeeperHub: MCP | Wallet | Simulation | Audit",
            "duration": 5.0,
            "color": "black",
            "font_color": "green",
            "font_size": 36
        },
        # Scene 7: Submit
        {
            "text": "Submit to DoraHacks - Good Luck!",
            "duration": 5.0,
            "color": "black",
            "font_color": "yellow",
            "font_size": 36
        },
    ]
    
    # Create video segments
    segments = []
    for i, scene in enumerate(scenes):
        segment_file = f"logs/segment_{i}.mp4"
        
        # Create ffmpeg command for this scene
        cmd = [
            "ffmpeg",
            "-f", "lavfi",
            "-i", f"color=c={scene['color']}:s=1280x720:d={scene['duration']}",
            "-vf", f"drawtext=text='{scene['text']}':fontsize={scene['font_size']}:fontcolor={scene['font_color']}:x=(w-text_w)/2:y=(h-text_h)/2",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "22",
            "-pix_fmt", "yuv420p",
            segment_file,
            "-y"
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        segments.append(segment_file)
        print(f"Created segment {i}: {segment_file}")
    
    # Concatenate all segments
    concat_file = "logs/concat_list.txt"
    with open(concat_file, 'w') as f:
        for segment in segments:
            f.write(f"file '{segment}'\n")
    
    # Create final video
    final_cmd = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_file,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "22",
        "-pix_fmt", "yuv420p",
        "logs/demo_video.mp4",
        "-y"
    ]
    
    subprocess.run(final_cmd, check=True, capture_output=True)
    print(f"Final video saved to logs/demo_video.mp4")
    
    # Get video info
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", "logs/demo_video.mp4"],
        capture_output=True, text=True
    )
    duration = result.stdout.strip()
    print(f"Video duration: {duration}s")

if __name__ == "__main__":
    create_demo_video()