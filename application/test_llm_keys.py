"""Test explicitly supplied MiniMax API keys without hard-coding credentials."""

import os

import httpx


def configured_keys() -> list[tuple[str, str]]:
    candidates = (
        ("primary", os.environ.get("LLM_API_KEY", "")),
        ("secondary", os.environ.get("LLM_API_KEY_SECONDARY", "")),
    )
    return [(name, value.strip()) for name, value in candidates if value.strip()]


def main() -> None:
    keys = configured_keys()
    if not keys:
        raise SystemExit("Set LLM_API_KEY before running this diagnostic")

    base_urls = (
        "https://api.minimax.chat/v1",
        "https://api.minimaxi.com/v1",
    )
    model = os.environ.get("LLM_MODEL", "MiniMax-M3")

    for name, key in keys:
        for base_url in base_urls:
            print(f"Testing {name} credential at {base_url}")
            try:
                with httpx.Client(timeout=15) as client:
                    response = client.post(
                        f"{base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": model,
                            "messages": [{"role": "user", "content": "ping"}],
                            "max_tokens": 5,
                        },
                    )
                print(f"status={response.status_code}")
            except httpx.HTTPError as exc:
                print(f"request failed: {type(exc).__name__}")


if __name__ == "__main__":
    main()
