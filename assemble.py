"""
拼装：视频 + 音频 + 烧录字幕
- 17 段 mp3 中间 0.4s 静音
- atempo 匹配视频时长
- ffmpeg subtitles filter 烧硬字幕
"""
import subprocess, json, os, sys

VB = r"X:\risklens\RiskLens-法律AI-演示\video_build"
TTS = os.path.join(VB, "tts")
TIMING = os.path.join(VB, "timing.json")
VIDEO = os.path.join(VB, "demo-raw.webm")
SRT = os.path.join(VB, "demo.srt")
OUT = os.path.join(VB, "demo-final.mp4")

def run(cmd, **kw):
    cmd_str = " ".join(f'"{x}"' if " " in str(x) else str(x) for x in cmd)
    print(f"$ {cmd_str[:300]}{'...' if len(cmd_str) > 300 else ''}")
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        print("STDERR:", r.stderr[-2000:])
        sys.exit(1)
    return r

# 1) 拼接 17 段 mp3（中间 0.4s 静音）
SILENCE = os.path.join(TTS, "silence-400ms.mp3")
run([
    "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
    "-t", "0.4", "-q:a", "9", "-acodec", "libmp3lame", SILENCE
])
print("silence 0.4s ok")

LIST = os.path.join(TTS, "concat-list.txt")
with open(LIST, "w", encoding="utf-8") as f:
    for i in range(1, 18):
        f.write(f"file 'slide-{i:02d}.mp3'\n")
        f.write(f"file 'silence-400ms.mp3'\n")

CONCAT = os.path.join(TTS, "concat.mp3")
run([
    "ffmpeg", "-y", "-f", "concat", "-safe", "0",
    "-i", LIST, "-c", "copy", CONCAT
])

r = subprocess.run(
    ["ffprobe", "-v", "error", "-show_entries", "format=duration",
     "-of", "default=noprint_wrappers=1:nokey=1", CONCAT],
    capture_output=True, text=True
)
audio_dur = float(r.stdout.strip())
print(f"concat audio: {audio_dur:.2f} sec")

# 2) 视频时长
r = subprocess.run(
    ["ffprobe", "-v", "error", "-show_entries", "format=duration",
     "-of", "default=noprint_wrappers=1:nokey=1", VIDEO],
    capture_output=True, text=True
)
video_dur = float(r.stdout.strip())
print(f"video: {video_dur:.2f} sec")

# 3) atempo 匹配
ratio = audio_dur / video_dur
print(f"atempo: {ratio:.3f}")
chain = []
r = ratio
while r > 2.0:
    chain.append(2.0); r /= 2.0
while r < 0.5:
    chain.append(0.5); r /= 0.5
chain.append(r)
filter_a = ",".join([f"atempo={x:.3f}" for x in chain])
print(f"atempo chain: {filter_a}")

SPEEDED = os.path.join(TTS, "concat-speeded.mp3")
run([
    "ffmpeg", "-y", "-i", CONCAT,
    "-filter:a", filter_a,
    "-vn", "-c:a", "libmp3lame", "-b:a", "128k", SPEEDED
])
print("audio speeded ok")

# 4) 视频 + 音频 + 烧字幕
# 字幕样式：底部居中 / 白色 + 黑色描边 / 28pt / 中文字体
# 查找 Windows 中文字体
import glob
font_candidates = [
    r"C:\Windows\Fonts\msyh.ttc",       # 微软雅黑
    r"C:\Windows\Fonts\msyh.ttf",
    r"C:\Windows\Fonts\simhei.ttf",     # 黑体
    r"C:\Windows\Fonts\simsun.ttc",    # 宋体
]
font = next((f for f in font_candidates if os.path.exists(f)), None)
if font:
    print(f"使用字体: {font}")
    style = (
        f"FontName=Microsoft YaHei,"
        f"FontSize=26,"
        f"PrimaryColour=&H00FFFFFF&,"
        f"OutlineColour=&H00000000&,"
        f"Outline=2,"
        f"Shadow=1,"
        f"ShadowColour=&H80000000&,"
        f"MarginV=50,"
        f"Alignment=2"
    )
    # escape 冒号防止 ffmpeg filter 解析为 key=
    srt_escaped = SRT.replace(":", "\\:")
    vf = f"subtitles='{srt_escaped}':force_style='{style}'"
else:
    print("未找到中文字体，使用默认")
    srt_escaped = SRT.replace(":", "\\:")
    vf = f"subtitles='{srt_escaped}'"

# 转 webm (vp8/vp9) → mp4 (h264)
# 注：原视频是 webm，可能 vp8/vp9，强制转 h264
run([
    "ffmpeg", "-y",
    "-i", VIDEO, "-i", SPEEDED,
    "-map", "0:v:0", "-map", "1:a:0",
    "-vf", vf,
    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast", "-crf", "23",
    "-c:a", "aac", "-b:a", "128k",
    "-shortest",
    OUT
])

print(f"\n最终输出: {OUT}")
print(f"文件大小: {os.path.getsize(OUT) / 1024 / 1024:.2f} MB")

r = subprocess.run(
    ["ffprobe", "-v", "error", "-show_entries", "format=duration",
     "-of", "default=noprint_wrappers=1:nokey=1", OUT],
    capture_output=True, text=True
)
print(f"最终时长: {r.stdout.strip()} sec")
