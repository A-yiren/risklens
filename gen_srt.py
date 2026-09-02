"""
生成 SRT 字幕文件
- 字幕开始 = 视频到达该屏时 (含滚动过渡)
- 字幕结束 = 视频停留结束前
"""
import json, os

VB = r"C:\work space\risklens\RiskLens-法律AI-演示\video_build"
TIMING = os.path.join(VB, "timing.json")
META = os.path.join(VB, "tts", "narration_meta.json")
SRT = os.path.join(VB, "demo.srt")

with open(TIMING, encoding="utf-8") as f:
    timing = json.load(f)
with open(META, encoding="utf-8") as f:
    meta = json.load(f)

stays = timing["stays"]
pre_s = timing["pre_ms"] / 1000
trans_s = timing["trans_ms"] / 1000
gap_s = timing["gap_s"]

# 视频时间轴
# slide 1 起始: pre_s
# slide 1 结束: pre_s + stays[0] - trans_s   (因为停在停留中段开始前滚动)
# 滚动 + 停留连续：滚到 slide N 后立即开始 N 段的停留

# 简化：slide i 起始 = pre_s + sum(stays[0..i-2]) + (i-1) * trans_s
# slide i 字幕结束 = slide i 起始 + stays[i-1] - trans_s/2
#     (字幕在画面停留中段后结束)

# 但用户听到音频在画面停留中段开始 → 让字幕从到达时开始，到音频结束+0.3s 结束
# audio_durs[i-1] 是该段 mp3 时长

# 时间轴：
# slide 1 显示区间 = [pre_s, pre_s + stays[0]]
# slide 1 字幕在 audio 时长内显示
# slide N (N>=2) 显示区间 = [slide_(N-1) 结束 + trans_s, + stays[N-1]]

cur = pre_s
intervals = []
audio_durs = timing["audio_durs"]
for i in range(17):
    slide_no = i + 1
    start = cur
    # 字幕显示 = 整段停留
    end = cur + stays[i]
    intervals.append((start, end, slide_no))
    # 滚动到下一屏
    cur = end + trans_s

# 写 SRT
def fmt(t):
    """t -> HH:MM:SS,mmm"""
    if t < 0: t = 0
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")

with open(SRT, "w", encoding="utf-8") as f:
    for i, (start, end, slide_no) in enumerate(intervals, 1):
        text = next((m["text"] for m in meta if m["slide"] == slide_no), "")
        f.write(f"{i}\n")
        f.write(f"{fmt(start)} --> {fmt(end)}\n")
        f.write(f"{text}\n\n")

print(f"SRT 写入 {SRT}")
print(f"字幕区间:")
for s, e, n in intervals:
    print(f"  slide {n:02d}: {fmt(s)} -> {fmt(e)}  ({e-s:.2f}s)")
print(f"\n总时长: {intervals[-1][1]:.2f} 秒")
