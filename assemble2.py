"""
拼装：视频 + 音频 + 烧录字幕 (短路径版本)
- 复制 SRT/视频到 X:\vbuild\ 短路径,避开空格和中文
- atempo 匹配视频时长
- ffmpeg subtitles filter 烧硬字幕
"""
import subprocess, json, os, sys, shutil

VB_SRC = r"X:\risklens\RiskLens-法律AI-演示\video_build"
VB = r"C:\vbuild"
TTS = os.path.join(VB, "tts")
os.makedirs(VB, exist_ok=True)
os.makedirs(TTS, exist_ok=True)

# 复制源文件到短路径
for fn in ["demo-raw.webm", "demo.srt", "timing.json"]:
    src = os.path.join(VB_SRC, fn)
    dst = os.path.join(VB, fn)
    if os.path.exists(src):
        shutil.copy2(src, dst)
        print(f"copy {fn} -> {dst}")

# 复制 17 段 mp3
for i in range(1, 18):
    n = f"slide-{i:02d}.mp3"
    src = os.path.join(VB_SRC, "tts", n)
    dst = os.path.join(TTS, n)
    if os.path.exists(src):
        shutil.copy2(src, dst)
print("copy 17 mp3 ok")

def run(cmd, **kw):
    cmd_str = " ".join(f'"{x}"' if " " in str(x) else str(x) for x in cmd)
    print(f"$ {cmd_str[:300]}{'...' if len(cmd_str) > 300 else ''}")
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        print("STDERR:", r.stderr[-2000:])
        sys.exit(1)
    return r

# 1) 拼接 17 段 mp3 (中间 0.4s 静音)
SILENCE = os.path.join(TTS, "silence-400ms.mp3")
run([
    "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
    "-t", "0.4", "-q:a", "9", "-acodec", "libmp3lame", SILENCE
])

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
VIDEO = os.path.join(VB, "demo-raw.webm")
SRT = os.path.join(VB, "demo.srt")
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
# 短路径 C:/vbuild/demo.srt (正斜杠避开 ffmpeg \ 转义)
srt_posix = SRT.replace("\\", "/")
print(f"SRT path (posix): {srt_posix}")

# ffmpeg filter 内部用 : 分隔参数, 路径里的 : 必须用 \ 转义
# 但 ffmpeg 会把 \: 解释为 :, 所以最终在命令行要用 \:
# 双重转义: Python 字符串中 \\:  → ffmpeg 看到 \:
srt_for_ffmpeg = srt_posix.replace(":", "\\:")

# 字幕样式: 底部居中 / 白色 + 黑色描边 / 26pt / 微软雅黑
style = (
    "FontName=Microsoft YaHei,"
    "FontSize=26,"
    "PrimaryColour=&H00FFFFFF&,"
    "OutlineColour=&H00000000&,"
    "Outline=2,"
    "Shadow=1,"
    "ShadowColour=&H80000000&,"
    "MarginV=50,"
    "Alignment=2"
)
# 用 file: protocol, ffmpeg 接受 file: 后跟绝对路径
# 但 file: 后路径有 : 仍会被 ffmpeg filter 当分隔符
# 解决方案: 不指定完整路径, 改用 ffmpeg 自动从视频同目录找同名 srt
import os as _os
srt_basename = _os.path.basename(SRT)
video_dir = _os.path.dirname(VIDEO)
srt_in_video_dir = _os.path.join(video_dir, srt_basename)
if not _os.path.exists(srt_in_video_dir):
    import shutil as _sh
    _sh.copy2(SRT, srt_in_video_dir)
print(f"使用 ffmpeg 自动找字幕: {srt_in_video_dir}")

vf = f"subtitles='{srt_basename}':force_style='{style}'"
print(f"vf: {vf[:300]}")

OUT = os.path.join(VB, "demo-final.mp4")
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

# 复制回原路径
final_dst = os.path.join(VB_SRC, "demo-final.mp4")
shutil.copy2(OUT, final_dst)
print(f"已复制到: {final_dst}")

r = subprocess.run(
    ["ffprobe", "-v", "error", "-show_entries", "format=duration",
     "-of", "default=noprint_wrappers=1:nokey=1", OUT],
    capture_output=True, text=True
)
print(f"最终时长: {r.stdout.strip()} sec")
