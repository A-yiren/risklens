"""
重写 SRT: 让字幕严格跟 audio 同步 (不跟 video 滚动位置)
- 段 i 起始 = 之前音频累计 + 段间静音 (在最终 mp4 audio 流中)
- 段 i 结束 = 起始 + audio 段时长
- 静音实际 0.46s (ffmpeg lavfi anullsrc -t 0.4 实际输出 0.46s 编码 padding)
- 总: 109.08 + 16*0.46 = 116.44s (mp4 audio 实际 116.49s 接近)
"""
import json, os

VB = r"C:\work space\risklens\RiskLens-法律AI-演示\video_build"
NARRATION = os.path.join(VB, "narration.json")
META = os.path.join(VB, "tts", "narration_meta.json")
SRT = os.path.join(VB, "demo.srt")

with open(NARRATION, encoding="utf-8") as f:
    narr = json.load(f)
with open(META, encoding="utf-8") as f:
    meta = json.load(f)

items = narr["items"]

# 每段 mp3 实际时长
DURS = [5.80, 3.60, 5.05, 5.48, 6.00, 5.70, 8.07, 6.20, 10.50, 5.77, 5.70, 6.88, 6.43, 6.00, 6.95, 8.39, 9.06]
# 16 段静音 (实测 0.46s 不是 0.4s)
SILENCE = 0.46

# 算每段在最终 mp4 audio 流中的位置
cur = 0.0
intervals = []
for i, dur in enumerate(DURS):
    if i > 0:
        cur += SILENCE
    start = cur
    end = cur + dur
    intervals.append((start, end, i+1))
    cur = end

# 微调: 实际总长 116.49s, 算出来 116.44s, 差 0.05s 均匀分到每段间隔
diff = 116.49 - cur
if abs(diff) > 0.001:
    intervals = [(s + diff*i/17, e + diff*(i+1)/17, n) for i, (s, e, n) in enumerate(intervals)]

def fmt(t):
    if t < 0: t = 0
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")

print(f"总时长: {intervals[-1][1]:.2f}s (目标 mp4 audio 116.49s)\n")
print(f"每段字幕区间 (跟 audio 严格同步):")
for s, e, n in intervals:
    text = next((it["text"] for it in items if it["slide"] == n), "")
    print(f"  slide {n:02d}: {fmt(s)} --> {fmt(e)}  ({e-s:.2f}s)  {text[:30]}")

with open(SRT, "w", encoding="utf-8") as f:
    for i, (start, end, n) in enumerate(intervals, 1):
        text = next((it["text"] for it in items if it["slide"] == n), "")
        f.write(f"{i}\n")
        f.write(f"{fmt(start)} --> {fmt(end)}\n")
        f.write(f"{text}\n\n")

print(f"\nSRT 写入 {SRT}")
