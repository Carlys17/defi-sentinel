#!/usr/bin/env python3
"""DashScope image gen helper for DeFi Sentinel title cards."""
import json, subprocess, sys, time, re

def load_api_key():
    with open("/root/image.env") as f:
        content = f.read()
    m = re.search(r'API KEY:\s*(sk-[^\s]+)', content)
    if not m:
        print("ERR: no API KEY found"); sys.exit(1)
    return m.group(1).strip()

BASE = "https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"

def gen(prompt, out_path, size="1664*928"):
    payload = {
        "model": "qwen-image-3.0-pro",
        "input": {"messages": [{"role": "user", "content": [{"text": prompt}]}]},
        "parameters": {"prompt_extend": True, "size": size}
    }
    import urllib.request
    req = urllib.request.Request(
        BASE,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {load_api_key()}"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        body = ""
        if hasattr(e, "read"):
            try: body = e.read().decode()[:500]
            except: pass
        print(f"ERR: {e}\n{body}"); return False

    try:
        url = data["output"]["choices"][0]["message"]["content"][0]["image"]
    except Exception:
        print("ERR: unexpected response:", json.dumps(data)[:400]); return False

    subprocess.run(["curl", "-s", "-L", "-o", out_path, url], timeout=120)
    import os
    print(f"OK: {out_path} ({os.path.getsize(out_path)} bytes)")
    return True

if __name__ == "__main__":
    kind = sys.argv[1]
    if kind == "intro":
        prompt = ("Cinematic dark cyberpunk title card background for a DeFi security product, "
                  "near-black deep navy background #0a0e14, a glowing teal-cyan digital shield "
                  "emblem floating center-frame with circuit-board traces and subtle hexagonal mesh, "
                  "soft volumetric light rays, faint holographic data streams and candlestick chart "
                  "lines in the background, depth of field, clean composition with empty dark space "
                  "in the center for text overlay, ultra sharp, no text, no letters, no watermark, "
                  "professional fintech branding aesthetic, 16:9")
        gen(prompt, "/tmp/defi_sentinel_build/intro_bg.png")
    elif kind == "outro":
        prompt = ("Cinematic dark cyberpunk outro background, near-black deep navy #0a0e14, "
                  "abstract glowing teal-cyan network nodes and connection lines forming a subtle "
                  "constellation, a faint shield silhouette top center, clean minimal composition "
                  "with large empty dark space in the middle for text overlay, soft glow, depth of "
                  "field, no text, no letters, no watermark, professional fintech branding, 16:9")
        gen(prompt, "/tmp/defi_sentinel_build/outro_bg.png")
    elif kind == "test":
        gen("A single glowing cyan cube on near-black background, minimal, no text", "/tmp/ds_test.png")
