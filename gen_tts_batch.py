"""
批量 TTS (17 段分 2 批: 10 + 7) - 从 narration.json 读取
"""
import subprocess, json, os, sys, time

VB = r"C:\work space\risklens\RiskLens-法律AI-演示\video_build"
OUT_DIR = os.path.join(VB, "tts")
META = os.path.join(OUT_DIR, "narration_meta.json")
MCODE = r"C:\Users\34464\.minimax\bin\mcode-tools.cmd"
NARRATION = os.path.join(VB, "narration.json")

with open(NARRATION, "r", encoding="utf-8") as f:
    narr = json.load(f)
items = narr["items"]
VOICE = narr.get("voice_id", "male-qn-qingse")
SPEED = narr.get("speed", 1.3)
EMOTION = narr.get("emotion", "neutral")

os.makedirs(OUT_DIR, exist_ok=True)

def call_batch(requests):
    payload = json.dumps({"requests": requests}, ensure_ascii=False)
    for attempt in range(5):
        try:
            r = subprocess.run(
                [MCODE, "connector", "call", "connector__matrix__batch_text_to_audio", "--args", payload],
                capture_output=True, text=True, encoding="utf-8", timeout=120
            )
        except subprocess.TimeoutExpired:
            time.sleep(5); continue
        if r.returncode != 0:
            print(f"  rc={r.returncode}, stderr: {r.stderr[:300]}"); time.sleep(5); continue
        try:
            data = json.loads(r.stdout)
        except json.JSONDecodeError:
            time.sleep(5); continue
        if data.get("code") == 0:
            return data
        print(f"  code={data.get('code')}, msg: {data.get('message','')[:200]}")
        time.sleep(5)
    return None

meta = []
# 分批: 10 + 7
batches = [items[0:10], items[10:17]]
for bi, batch in enumerate(batches, 1):
    print(f"\n=== 批次 {bi}: {len(batch)} 段 ===")
    requests = []
    for it in batch:
        requests.append({
            "text": it["text"],
            "voice_id": VOICE,
            "speed": SPEED,
            "emotion": EMOTION,
            "output_file": f"slide-{it['slide']:02d}.mp3",
        })
    res = call_batch(requests)
    if res is None:
        print(f"批次 {bi} FAILED")
        continue
    success = res.get("success_items", [])
    failed = res.get("failed_items", [])
    print(f"  成功 {len(success)} 段, 失败 {len(failed)} 段")
    for s in success:
        slide_no = int(s["file_name"].replace("slide-", "").replace(".mp3", ""))
        text = next((it["text"] for it in items if it["slide"] == slide_no), "")
        meta.append({"slide": slide_no, "text": text, "node_id": s["node_id"], "file_name": s["file_name"]})
        print(f"  slide {slide_no:02d} -> {s['file_name']} OK")
    for f in failed:
        print(f"  slide ?? FAILED: {f.get('error_msg','')[:200]}")
    if bi < len(batches):
        time.sleep(3.0)

with open(META, "w", encoding="utf-8") as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)
print(f"\n成功 {len(meta)}/{len(items)}")
print(f"narration_meta.json 写入完成")
