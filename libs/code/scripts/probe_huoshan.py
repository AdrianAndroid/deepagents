"""Probe Volcengine (huoshan) coding endpoint to see the raw response.

Usage:
    OPENAI_API_KEY=... uv run --project libs/code python libs/code/scripts/probe_huoshan.py
"""

from __future__ import annotations

import json
import os
import sys

from langchain_openai import ChatOpenAI


def main() -> int:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY not set", file=sys.stderr)
        return 1

    base_url = "https://ark.cn-beijing.volces.com/api/coding/v3"
    model = "ark-code-latest"

    print(f"=== base_url = {base_url}")
    print(f"=== model    = {model}")
    print()

    # ---- Non-streaming path -------------------------------------------------
    llm = ChatOpenAI(
        model=model,
        base_url=base_url,
        api_key=api_key,
        streaming=False,
    )
    resp = llm.invoke("say hi in one word")
    print("---- non-streaming ----")
    print("content:", repr(resp.content))
    print("response_metadata:")
    print(json.dumps(resp.response_metadata, indent=2, ensure_ascii=False, default=str))
    print("usage_metadata:", resp.usage_metadata)
    print("additional_kwargs keys:", list(resp.additional_kwargs.keys()))
    print()

    # ---- Streaming path with include_usage ---------------------------------
    llm_stream = ChatOpenAI(
        model=model,
        base_url=base_url,
        api_key=api_key,
        streaming=True,
        stream_usage=True,  # emit usage in the final chunk
    )
    final = None
    print("---- streaming (with stream_usage=True) ----")
    for chunk in llm_stream.stream("say hi in one word"):
        # merge chunks
        final = chunk if final is None else final + chunk
        rm = getattr(chunk, "response_metadata", {}) or {}
        chunk_position = getattr(chunk, "chunk_position", None)
        model_in_chunk = rm.get("model_name") or rm.get("model")
        finish = rm.get("finish_reason")
        print(
            f"  chunk chunk_position={chunk_position!r} "
            f"model={model_in_chunk!r} finish={finish!r} "
            f"usage={getattr(chunk, 'usage_metadata', None)}"
        )
    print()
    print("---- streaming aggregated ----")
    if final is not None:
        print("content:", repr(final.content))
        print("response_metadata:")
        print(
            json.dumps(
                final.response_metadata,
                indent=2,
                ensure_ascii=False,
                default=str,
            )
        )
        print("usage_metadata:", final.usage_metadata)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
