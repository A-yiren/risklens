"""Legacy MiniMax configuration helper.

The API key must be supplied through the process environment. This script never
contains or prints the key. Production RiskLens uses systemd encrypted
credentials instead of this helper.
"""

import os
from pathlib import Path


ENV_PATH = Path(os.environ.get("RISK_ENV_PATH", "/opt/legal-lens/.env"))
API_KEY = os.environ.get("LLM_API_KEY", "").strip()
BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.minimaxi.com/v1").strip()
MODEL = os.environ.get("LLM_MODEL", "MiniMax-M3").strip()


def main() -> None:
    if not API_KEY:
        raise SystemExit("LLM_API_KEY is required in the process environment")
    if not ENV_PATH.is_file():
        raise SystemExit(f"Environment file does not exist: {ENV_PATH}")

    updates = {
        "LLM_API_KEY": API_KEY,
        "LLM_BASE_URL": BASE_URL,
        "LLM_MODEL": MODEL,
    }
    output: list[str] = []
    seen: set[str] = set()

    for line in ENV_PATH.read_text(encoding="utf-8").splitlines(keepends=True):
        key = line.split("=", 1)[0].strip() if "=" in line else ""
        if key in updates:
            output.append(f"{key}={updates[key]}\n")
            seen.add(key)
        else:
            output.append(line)

    for key, value in updates.items():
        if key not in seen:
            output.append(f"{key}={value}\n")

    ENV_PATH.write_text("".join(output), encoding="utf-8")
    print(f"Updated {ENV_PATH} without printing credential values")
    print("Restart the intended service through its deployment procedure.")


if __name__ == "__main__":
    main()
