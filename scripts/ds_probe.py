#!/usr/bin/env python3
"""Probe DashScope base URL, key, and list available models."""

import json
import re
import urllib.error
import urllib.request


def key():
    with open("/root/image.env") as f:
        m = re.search(r"API KEY:\s*(sk-[^\s]+)", f.read())
    return m.group(1).strip() if m else None


BASE = "https://dashscope-intl.aliyuncs.com"
print("key loaded:", bool(key()))

# 1. list models (OpenAI-compat)
print("\n=== GET /compatible-mode/v1/models ===")
req = urllib.request.Request(
    BASE + "/compatible-mode/v1/models", headers={"Authorization": f"Bearer {key()}"}
)
try:
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read())
    ids = [m.get("id") for m in data.get("data", [])]
    print(f"total models listed: {len(ids)}")
    # filter media-capable
    media = [i for i in ids if any(s in i for s in ["image", "wan", "t2i", "video", "t2v"])]
    print("media-capable:", json.dumps(sorted(set(media)), indent=1))
except urllib.error.HTTPError as e:
    print("HTTP", e.code, e.read().decode()[:300])
except Exception as e:
    print("ERR", e)

# 2. quick text-model probe (confirm key + base work for chat)
print("\n=== probe qwen3.7-flash via chat ===")
payload = {
    "model": "qwen3.7-flash",
    "messages": [{"role": "user", "content": "reply with the single word OK"}],
    "max_tokens": 8,
}
req = urllib.request.Request(
    BASE + "/compatible-mode/v1/chat/completions",
    data=json.dumps(payload).encode(),
    headers={"Authorization": f"Bearer {key()}", "Content-Type": "application/json"},
    method="POST",
)
try:
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.loads(r.read())
    print("chat resp:", d["choices"][0]["message"]["content"][:40])
except urllib.error.HTTPError as e:
    print("HTTP", e.code, e.read().decode()[:300])
except Exception as e:
    print("ERR", e)
