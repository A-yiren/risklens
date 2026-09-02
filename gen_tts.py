"""
单条 TTS + 重试（避免 batch 限流） - 从 narration.json 读取
"""
import subprocess, json, os, sys, time

VOICE = "male-qn-qingse"
SPEED = 1.3
EMOTION = "neutral"
OUT_DIR = r"C:\work space\risklens\RiskLens-法律AI-演示\video_build\tts"
META = os.path.join(OUT_DIR, "narration_meta.json")
MCODE = r"C:\Users\34464\.minimax\bin\mcode-tools.cmd"
NARRATION = r"C:\work space\risklens\RiskLens-法律AI-演示\video_build\narration.json"

with open(NARRATION, "r", encoding="utf-8") as f:
    narr = json.load(f)
items = [(it["slide"], it["text"]) for it in narr["items"]]

def call_tts(text, out_file):
    payload = json.dumps({
        "text": text,
        "voice_id": VOICE,
        "speed": SPEED,
        "emotion": EMOTION,
        "output_file": out_file,
    }, ensure_ascii=False)
    for attempt in range(6):
        try:
            r = subprocess.run(
                [MCODE, "connector", "call", "connector__matrix__synthesize_speech", "--args", payload],
                capture_output=True, text=True, encoding="utf-8", timeout=60
            )
        except subprocess.TimeoutExpired:
            time.sleep(3); continue
        if r.returncode != 0:
            time.sleep(3); continue
        try:
            data = json.loads(r.stdout)
        except json.JSONDecodeError:
            time.sleep(3); continue
        if data.get("code") == 0 and data.get("node_id"):
            return data
        # 限流
        time.sleep(4)
    return None

os.makedirs(OUT_DIR, exist_ok=True)
meta = []
for n, t in items:
    out_file = f"slide-{n:02d}.mp3"
    print(f"slide {n:02d} ... ", end="", flush=True)
    res = call_tts(t, out_file)
    if res is None:
        print("FAILED (give up)")
        continue
    print(f"OK ({res.get('file_name')})")
    meta.append({"slide": n, "text": t, "node_id": res["node_id"], "file_name": res["file_name"]})
    time.sleep(2.0)  # 避免限流

with open(META, "w", encoding="utf-8") as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)
print(f"\n成功 {len(meta)}/{len(items)}")
