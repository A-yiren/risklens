"""
下载 17 段 TTS mp3 到本地
"""
import subprocess, json, os, sys, time, urllib.request

MCODE = r"C:\Users\34464\.minimax\bin\mcode-tools.cmd"
OUT_DIR = r"C:\work space\risklens\RiskLens-法律AI-演示\video_build\tts"
META = os.path.join(OUT_DIR, "narration_meta.json")

with open(META, "r", encoding="utf-8") as f:
    meta = json.load(f)

print(f"待下载 {len(meta)} 段")
for it in meta:
    out = os.path.join(OUT_DIR, f"slide-{it['slide']:02d}.mp3")
    if os.path.exists(out) and os.path.getsize(out) > 1000:
        print(f"  slide {it['slide']:02d} 已存在 ({os.path.getsize(out)} bytes)")
        continue
    # get URL
    r = subprocess.run(
        [MCODE, "get-asset-url", it["node_id"]],
        capture_output=True, text=True, encoding="utf-8", timeout=30
    )
    if r.returncode != 0:
        print(f"  slide {it['slide']:02d} get-asset-url FAILED: {r.stderr[:200]}")
        continue
    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError:
        print(f"  slide {it['slide']:02d} JSON FAILED: {r.stdout[:200]}")
        continue
    url = data.get("url") or data.get("download_url") or data.get("asset_url")
    if not url:
        print(f"  slide {it['slide']:02d} no url in {list(data.keys())}")
        continue
    # download
    try:
        with urllib.request.urlopen(url, timeout=60) as resp:
            with open(out, "wb") as f:
                f.write(resp.read())
        print(f"  slide {it['slide']:02d} -> {os.path.basename(out)} ({os.path.getsize(out)} bytes)")
    except Exception as e:
        print(f"  slide {it['slide']:02d} download FAILED: {e}")
    time.sleep(0.3)
print("完成")
