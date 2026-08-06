#!/usr/bin/env python3
"""Generate all AI media assets for the DeFi Sentinel demo using every
media-capable DashScope model. Logs to stdout. Run once, saves to
/tmp/defi_sentinel_build/assets/."""
import json, re, time, sys, os, urllib.request, urllib.error

BASE = "https://dashscope-intl.aliyuncs.com"
OUT = "/tmp/defi_sentinel_build/assets"
os.makedirs(OUT, exist_ok=True)

def key():
    with open("/root/image.env") as f:
        m = re.search(r'API KEY:\s*(sk-[^\s]+)', f.read())
    if not m:
        print("FATAL: no key"); sys.exit(1)
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
        return None, f"HTTP {e.code}: {e.read().decode()[:300]}"
    except Exception as e:
        return None, str(e)

def get(path, timeout=60):
    req = urllib.request.Request(BASE + path, headers={"Authorization": f"Bearer {key()}"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read()), None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}: {e.read().decode()[:300]}"
    except Exception as e:
        return None, str(e)

def download(url, path):
    import subprocess
    subprocess.run(["curl", "-s", "-L", "-o", path, url], timeout=300)
    return os.path.exists(path) and os.path.getsize(path) > 10000

# ---------- 1. qwen3.7-flash: write slide copy ----------
def gen_copy():
    print("=== [qwen3.7-flash] generating slide copy ===")
    prompt = ("Write concise English text for 4 slides of a hackathon demo video "
              "for 'DeFi Sentinel', an autonomous AI agent for DeFi portfolio "
              "management and liquidation protection, built on KeeperHub as its "
              "execution layer, deployed on Base Sepolia. "
              "Slide 1 'THE PROBLEM': 3 short bullet pain points (liquidations, "
              "failed transactions/MEV, manual monitoring). "
              "Slide 2 'ARCHITECTURE': 5 one-line layers (LLM Engine, Strategy "
              "Engine, KeeperHub MCP 30+ tools, Execution chains, Observability). "
              "Slide 3 'ONCHAIN PROOF': one line about 2 real Base Sepolia "
              "transactions verifiable on-chain. "
              "Slide 4 'SAFETY': 3 bullets (simulation-first, idempotency keys, "
              "audit trail). Output STRICT JSON: "
              '{"problem":["..."],"arch":["..."],"proof":"...","safety":["..."]}')
    d, err = post("/compatible-mode/v1/chat/completions",
                  {"model": "qwen3.7-flash", "temperature": 0.3,
                   "messages": [{"role": "user", "content": prompt}]})
    if err: print("ERR:", err); return None
    txt = d["choices"][0]["message"]["content"]
    # extract JSON
    m = re.search(r'\{.*\}', txt, re.S)
    if not m: print("no json in response:", txt[:200]); return None
    copy = json.loads(m.group(0))
    with open(f"{OUT}/copy.json", "w") as f: json.dump(copy, f, indent=1)
    print("copy saved:", list(copy.keys()))
    return copy

# ---------- 2. qwen-image family (sync, multimodal-generation) ----------
def qwen_image(model, prompt, outname, size="1664*928"):
    print(f"=== [{model}] generating {outname} ===")
    payload = {"model": model,
               "input": {"messages": [{"role": "user",
                                        "content": [{"text": prompt}]}]},
               "parameters": {"prompt_extend": True, "size": size}}
    d, err = post("/api/v1/services/aigc/multimodal-generation/generation", payload)
    if err: print("ERR:", err); return None
    try:
        url = d["output"]["choices"][0]["message"]["content"][0]["image"]
    except Exception:
        print("unexpected:", json.dumps(d)[:300]); return None
    path = f"{OUT}/{outname}.png"
    ok = download(url, path)
    print(f"  saved {path} ({os.path.getsize(path)} bytes)" if ok else "  download FAILED")
    return path if ok else None

# ---------- 3. wan/z async text2image ----------
def submit_t2i(model, prompt, size="1664*928"):
    print(f"=== [{model}] submitting t2i task ===")
    payload = {"model": model, "input": {"prompt": prompt},
               "parameters": {"size": size, "n": 1}}
    d, err = post("/api/v1/services/aigc/text2image/image-synthesis", payload,
                  headers={"X-DashScope-Async": "enable"})
    if err: print("ERR:", err); return None
    tid = d.get("output", {}).get("task_id")
    print(f"  task_id={tid}")
    return tid

# ---------- 4. wan2.7-t2v async video ----------
def submit_t2v(prompt, size="1280*720"):
    print(f"=== [wan2.7-t2v] submitting video task ({size}) ===")
    payload = {"model": "wan2.7-t2v", "input": {"prompt": prompt},
               "parameters": {"size": size}}
    d, err = post("/api/v1/services/aigc/video-generation/video-synthesis", payload,
                  headers={"X-DashScope-Async": "enable"})
    if err: print("ERR:", err); return None
    tid = d.get("output", {}).get("task_id")
    print(f"  task_id={tid}")
    return tid

def poll_task(tid, kind, outname, timeout_s=600, interval=18):
    start = time.time()
    while time.time() - start < timeout_s:
        d, err = get(f"/api/v1/tasks/{tid}")
        if err: print(f"  poll err: {err}"); time.sleep(interval); continue
        st = d.get("output", {}).get("task_status")
        print(f"  [{kind}:{outname}] {st} ({int(time.time()-start)}s)")
        if st == "SUCCEEDED":
            out = d.get("output", {})
            url = out.get("video_url")
            if not url:
                res = out.get("results") or []
                url = res[0].get("url") if res else None
            if not url: print("  no url:", json.dumps(out)[:300]); return None
            path = f"{OUT}/{outname}"
            ok = download(url, path)
            print(f"  saved {path}" if ok else "  download FAILED")
            return path if ok else None
        if st in ("FAILED", "CANCELED", "UNKNOWN"):
            print("  task failed:", json.dumps(d)[:300]); return None
        time.sleep(interval)
    print("  TIMEOUT polling", kind, outname)
    return None

# ---------- prompts ----------
NO_TEXT = " no text, no letters, no watermark, no words."
P_INTRO_V = ("Cinematic slow camera push-in on a glowing translucent cyan digital "
             "shield hologram floating above a dark futuristic city of financial "
             "data streams, teal and blue neon light trails flowing around it like "
             "protected transactions, dark navy atmosphere, particles, depth of "
             "field, ultra smooth motion, 16:9." + NO_TEXT)
P_OUTRO_V = ("Slow cinematic pull-back revealing a constellation of glowing teal "
             "network nodes connecting into a shield emblem, dark navy space, "
             "gentle particle drift, calm and triumphant mood, soft light bloom, "
             "16:9." + NO_TEXT)
P_PROBLEM = ("Dark dramatic fintech scene: a crumbling red candlestick chart "
             "falling apart into fragments, warning glow, dark navy background "
             "#0a0e14, red accent lighting, sense of danger and urgency, "
             "cinematic, 16:9." + NO_TEXT)
P_ARCH = ("Clean isometric dark tech diagram scene: five glowing translucent "
          "platform layers stacked and connected by teal light beams, abstract "
          "neural core at top, circuit patterns, near-black navy background "
          "#0a0e14, professional, 16:9." + NO_TEXT)
P_PROOF = ("Macro cinematic shot of a glowing teal blockchain ledger: rows of "
           "luminous blocks chaining together, one block highlighted with a "
           "checkmark-like glow, dark navy background, shallow depth of field, "
           "16:9." + NO_TEXT)
P_SAFETY = ("Serene dark cyberpunk scene: a protective translucent energy dome "
            "covering a small glowing city grid, calm teal ambient light, audit "
            "scan lines sweeping gently, near-black navy background, 16:9." + NO_TEXT)

# ---------- main flow ----------
if __name__ == "__main__":
    t0 = time.time()
    gen_copy()  # fast

    # submit async tasks first (they run while we do sync gens)
    tasks = {}
    tid = submit_t2v(P_INTRO_V);   tasks[tid and ("v", "intro_clip.mp4", tid)] = True
    tid = submit_t2v(P_OUTRO_V);   tasks[tid and ("v", "outro_clip.mp4", tid)] = True
    tid = submit_t2i("wan2.7-image-pro", P_ARCH); tasks[tid and ("i", "arch.png", tid)] = True
    tid = submit_t2i("z-image-turbo", P_PROOF);   tasks[tid and ("i", "proof.png", tid)] = True
    tid = submit_t2i("wan2.6-t2i", P_SAFETY);     tasks[tid and ("i", "safety_wan26.png", tid)] = True

    # sync qwen-image gens (1 RPM models: serialize with 62s gaps)
    last = 0
    def sync_gap(needed=62):
        global last
        wait = needed - (time.time() - last)
        if wait > 0:
            print(f"... rate-limit wait {int(wait)}s ..."); time.sleep(wait)
        last = time.time()

    sync_gap(0)
    qwen_image("qwen-image-3.0", P_PROBLEM, "problem")
    sync_gap(62)
    qwen_image("qwen-image-2.0-pro", P_SAFETY, "safety")
    sync_gap(32)  # 2 RPM
    qwen_image("qwen-image-max", P_ARCH, "arch_max")
    sync_gap(32)
    qwen_image("qwen-image-3.0-pro", P_SAFETY, "safety_pro")  # extra variant

    # now poll all async tasks
    for k in tasks:
        if not k: continue
        kind, name, tid = k
        poll_task(tid, kind, name, timeout_s=600)

    print(f"\n=== ALL DONE in {int(time.time()-t0)}s ===")
    for f in sorted(os.listdir(OUT)):
        print(f"  {f:24s} {os.path.getsize(os.path.join(OUT,f))/1024:.0f} KB")
