"""
按音频时长动态停留 + 截图 + 录视频
"""
import subprocess, json, os, sys, time
from playwright.sync_api import sync_playwright

VB = r"C:\work space\risklens\RiskLens-法律AI-演示\video_build"
TTS = os.path.join(VB, "tts")
SHOTS = os.path.join(VB, "shots")
URL = "file:///C:/work%20space/risklens/RiskLens-%E6%B3%95%E5%BE%8BAI-%E6%BC%94%E7%A4%BA/demo.html"
os.makedirs(SHOTS, exist_ok=True)

# 17 段音频时长（实测, 2026-09-02 重做后）
DURS = {
    1: 5.80, 2: 3.60, 3: 5.05, 4: 5.48, 5: 6.00, 6: 5.70,
    7: 8.07, 8: 6.20, 9: 10.50, 10: 5.77, 11: 5.70, 12: 6.88,
    13: 6.43, 14: 6.00, 15: 6.95, 16: 8.39, 17: 9.06
}

# 参数
PRE_MS = 2200              # 开场等
POST_MS = 1500             # 结尾停
TRANS_MS = 950             # 滚动动画时间
GAP_S = 0.5                # 每段末尾多停 0.5s（让画面在音频结束后还能看到）
MIN_STAY_S = 4.0           # 最短停留 4s

# 写每段停留时长表
TIMES = []
for i in range(1, 18):
    stay = max(DURS[i] + GAP_S, MIN_STAY_S)
    TIMES.append(stay)
print("停留时长表 (s):")
for i, t in enumerate(TIMES, 1):
    print(f"  slide {i:02d}: {t:.2f}s (audio {DURS[i]:.2f}s + 0.5s)")

total_dur = PRE_MS/1000 + sum(TIMES) + 16*TRANS_MS/1000 + POST_MS/1000
print(f"预估总时长: {total_dur:.1f} 秒")

# Playwright
with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
    )
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        device_scale_factor=1,
        record_video_dir=VB,
        record_video_size={"width": 1920, "height": 1080},
    )
    page = context.new_page()
    print("\n打开 demo.html ...")
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_timeout(PRE_MS)
    page.screenshot(path=os.path.join(SHOTS, "slide-01.png"), full_page=False)

    for i in range(2, 18):
        page.keyboard.press("PageDown")
        page.wait_for_timeout(TRANS_MS)
        page.screenshot(path=os.path.join(SHOTS, f"slide-{i:02d}.png"), full_page=False)
        stay_ms = int(TIMES[i-1] * 1000 - TRANS_MS)
        page.wait_for_timeout(stay_ms)
        print(f"  slide {i:02d} OK ({TIMES[i-1]:.2f}s)")

    page.wait_for_timeout(POST_MS)
    context.close()
    browser.close()

# 重命名 webm
import glob
webms = glob.glob(os.path.join(VB, "*.webm"))
if webms:
    src = max(webms, key=os.path.getmtime)
    dst = os.path.join(VB, "demo-raw.webm")
    if os.path.exists(dst):
        os.remove(dst)
    os.rename(src, dst)
    print(f"\n录屏完成 -> {dst}")
    print(f"文件大小: {os.path.getsize(dst) / 1024 / 1024:.1f} MB")

# 写 timing.json 给后续拼装用
with open(os.path.join(VB, "timing.json"), "w", encoding="utf-8") as f:
    json.dump({
        "pre_ms": PRE_MS,
        "post_ms": POST_MS,
        "trans_ms": TRANS_MS,
        "gap_s": GAP_S,
        "stays": TIMES,
        "audio_durs": DURS,
    }, f, ensure_ascii=False, indent=2)
print(f"timing.json 写入完成")
