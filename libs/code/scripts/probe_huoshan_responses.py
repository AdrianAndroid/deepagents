"""Probe huoshan via Responses API to see if it returns the real underlying model."""

from __future__ import annotations

import json
import os

from langchain_openai import ChatOpenAI

import sys

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "https://ark.cn-beijing.volces.com/api/coding/v3"
MODEL = sys.argv[2] if len(sys.argv) > 2 else "ark-code-latest"


def main() -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    assert api_key, "OPENAI_API_KEY must be set"

    print(f"=== base_url = {BASE_URL}")
    print(f"=== model    = {MODEL}")
    print(f"=== use_responses_api = True")

    llm = ChatOpenAI(
        model=MODEL,
        base_url=BASE_URL,
        api_key=api_key,
        use_responses_api=True,
    )
    resp = llm.invoke("say hi")
    print("\ncontent:", repr(resp.content)[:200])
    print("response_metadata:")
    print(json.dumps(resp.response_metadata, indent=2, ensure_ascii=False, default=str))
    print("usage_metadata:", resp.usage_metadata)
    print("additional_kwargs keys:", list(resp.additional_kwargs.keys()))


if __name__ == "__main__":
    main()
