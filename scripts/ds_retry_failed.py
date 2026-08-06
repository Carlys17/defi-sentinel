#!/usr/bin/env python3
"""Retry the 3 failed models with multimodal-generation endpoint format."""
import json, re, os, subprocess, urllib.request, urllib.error

BASE = "https://dashscope-intl.aliyuncs.com"
OUT = "/tmp/defi_sentinel_build/assets"
os.makedirs(OUT, exist_ok=True)

def key():
    with open("/root/image.env") as f:
        m = re.search(r'API KEY:\s*(sk-[^\s]+)', f.read())
    return m.group(1).strip()

def post(path, payload, headers=None, timeout=180):
    h = {"Authorization": f"Bearer {key()}", "Content-Type": "application/json"}
    if headers: h.update(headers)
    req = urllib.request.Request(BASE + path, data=json.dumps(payload).encode(),
                                 headers=h, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read()), None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}: {e.read().decode()[:250]}"
    except Exception as e:
        return None, str(e)

def dl(url, path):
    subprocess.run(["curl", "-s", "-L", "-o", path, url], timeout=300)
    return os.path.exists(path) and os.path.getsize(path) > 10000

def try_model(model, prompt, outname):
    print(f"=== [{model}] ===")
    # attempt 1: multimodal-generation messages format
    payload = {"model": model,
               "input": {"messages": [{"role": "user", "content": [{"text": prompt}]}]},
               "parameters": {"prompt_extend": True, "size": "1664*928"}}
    d, err = post("/api/v1/services/aigc/multimodal-generation/generation", payload)
    if not err:
        try:
            url = d["output"]["choices"][0]["message"]["content"][0]["image"]
            path = f"{OUT}/{outname}"
            if dl(url, path):
                print(f"  OK via multimodal-gen: {path} ({os.path.getsize(path)} bytes)")
                return True
        except Exception:
            print("  unexpected resp:", json.dumps(d)[:200])
    else:
        print(f"  mm-gen failed: {err}")

    # attempt 2: text2image sync (no async header)
    payload2 = {"model": model, "input": {"prompt": prompt},
                "parameters": {"size": "1664*928", "n": 1}}
    d, err = post("/api/v1/services/aigc/text2image/image-synthesis", payload2)
    if not err:
        try:
            res = d["output"]["results"]
            url = res[0].get("url") or res[0].get("b64_image")
            if url and url.startswith("http"):
                path = f"{OUT}/{outname}"
                if dl(url, path):
                    print(f"  OK via text2image-sync: {path}")
                    return True
        except Exception:
            print("  unexpected resp:", json.dumps(d)[:200])
    else:
        print(f"  t2i-sync failed: {err}")

    # attempt 3: OpenAI-compat images endpoint
    payload3 = {"model": model, "prompt": prompt, "size": "1664*928", "n": 1}
    d, err = post("/compatible-mode/v1/images/generations", payload3)
    if not err:
        try:
            url = d["data"][0]["url"] or d["data"][0].get("b64_json")
            if url and url.startswith("http"):
                path = f"{OUT}/{outname}"
                if dl(url, path):
                    print(f"  OK via compat images: {path}")
                    return True
        except Exception:
            print("  unexpected resp:", json.dumps(d)[:200])
    else:
        print(f"  compat-images failed: {err}")

    print(f"  FAILED all 3 endpoints for {model}")
    return False

NO_TEXT = " no text, no letters, no watermark, no words."

P_ARCH_WAN = ("Clean isometric dark tech diagram scene: five glowing translucent "
              "platform layers stacked and connected by teal light beams, "
              "abstract neural core at top, circuit patterns, near-black navy "
              "background, professional fintech style, 16:9." + NO_TEXT)
P_PROOF_Z = ("Macro cinematic shot of a glowing teal blockchain ledger: rows of "
             "luminous blocks chaining together, one block highlighted, dark "
             "navy background, shallow depth of field, 16:9." + NO_TEXT)
P_SAFETY_26 = ("Serene dark cyberpunk scene: a protective translucent energy dome "
               "covering a small glowing city grid, calm teal ambient light, "
               "audit scan lines, near-black navy background, 16:9." + NO_TEXT)

r1 = try_model("wan2.7-image-pro", P_ARCH_WAN, "arch_wan.png")
r2 = try_model("z-image-turbo", P_PROOF_Z, "proof_z.png")
r3 = try_model("wan2.6-t2i", P_SAFETY_26, "safety_wan26.png")
print(f"\nresults: wan2.7-image-pro={r1}, z-image-turbo={r2}, wan2.6-t2i={r3}")
