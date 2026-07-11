"""Raw HTTP probe: capture response headers + body for both aliases,
   look for any field/header that reveals the real routed model
   even when we asked for 'ark-code-latest'."""

from __future__ import annotations
import json, os, sys
import httpx

BASE = "https://ark.cn-beijing.volces.com/api/coding/v3"
KEY = os.environ["OPENAI_API_KEY"]

def probe(model: str, stream: bool) -> None:
    body = {
        "model": model,
        "messages": [{"role": "user", "content": "hi"}],
        "stream": stream,
    }
    if stream:
        body["stream_options"] = {"include_usage": True}

    print(f"\n===== model={model}  stream={stream} =====")
    with httpx.Client(timeout=60.0) as c:
        r = c.post(
            f"{BASE}/chat/completions",
            headers={"Authorization": f"Bearer {KEY}",
                     "Content-Type": "application/json"},
            json=body,
        )
        print("STATUS:", r.status_code)
        print("HEADERS:")
        for k, v in r.headers.items():
            print(f"  {k}: {v}")
        print("BODY (first 1500 chars):")
        text = r.text
        print(text[:1500])

for m in ("ark-code-latest", "gpt-5.5"):
    probe(m, stream=False)
