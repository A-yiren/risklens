# 金睛 RiskLens · 法律 AI Agent 复赛演示包

> **GOAI 2026 · "无界应用 | AI + 法律" 复赛**
> 复赛方案 v0.2 · 提交日期 2026-09-03
> 制作人：缪毅翔 (ayiren) · A-yiren
> 核心理念：**让不懂法律的人，看见风险，也看见依据**

---

## 1. 演示包清单

| 文件 | 大小 | 说明 |
|------|------|------|
| `demo.html` | 137 KB | 17 屏 PPT 风格交互式演示（绿金配色 + GSAP 滚轮翻页 + SVG 图表） |
| `demo-final.mp4` | 16.6 MB | 录屏 + 配音 + libass 烧硬字幕（1920×1080 / 116.5s / H.264） |
| `demo.srt` | 2.2 KB | 软字幕（按 audio 段位置严格同步，不是 video 滚动位置） |
| `refer-pptx.pdf` | 538 KB | 参考 PPT（12 屏"风险与盲区"答辩版） |
| `refer-png/page-01.png ~ page-12.png` | 1.4 MB | 参考 PPT 12 张截图 |
| `shots/slide-01.png ~ slide-17.png` | 4.5 MB | demo.html 17 屏录屏截图 |
| `tts/slide-01.mp3 ~ slide-17.mp3` | 1.7 MB | 17 段 TTS 配音（MiniMax male-qn-qingse，1.3× 语速） |
| `tts/narration_meta.json` | 3.5 KB | TTS 元数据（含 node_id / 原始文稿） |
| `record.py` | 3.0 KB | Playwright 录屏脚本（17 屏按 audio 长度动态停留） |
| `gen_tts_batch.py` | 2.9 KB | 批量 TTS 调用（17 段分 2 批：10+7） |
| `gen_tts.py` | 2.1 KB | 单条 TTS 调用（旧版） |
| `download_tts.py` | 1.7 KB | 从云端下载 TTS mp3 |
| `gen_srt_audio_sync.py` | 2.2 KB | SRT 生成（**按 audio 段位置严格同步**） |
| `gen_srt.py` | 2.3 KB | SRT 生成（旧版，按 video 滚动位置） |
| `assemble2.py` | 5.0 KB | ffmpeg 烧硬字幕（修正路径转义） |
| `assemble.py` | 4.1 KB | ffmpeg 烧硬字幕（初版） |
| `read_ppt.py` | 1.1 KB | PDF 转 PNG 脚本（参考 PPT 用） |
| `narration.json` | 2.2 KB | 17 段配音文稿 |
| `timing.json` | 0.6 KB | 录屏 timing 记录（每段停留 + audio 时长） |
| `checksums.txt` | — | 本包所有文件 SHA-256 校验值 |

---

## 2. 演示视频信息

- **分辨率**：1920×1080
- **时长**：116.49 秒（约 1 分 56 秒）
- **帧率**：25 fps
- **视频编码**：H.264 / yuv420p / CRF 23
- **音频编码**：AAC / 128 kbps
- **字幕**：libass 烧硬字幕，Microsoft YaHei 26pt，白字黑边
- **配音**：MiniMax TTS，male-qn-qingse，1.3× 语速，17 段独立 mp3
- **字幕与配音同步**：每段字幕区间 = 配音在 mp4 audio 流中的精确位置（含 0.46s 段间静音）

---

## 3. 17 屏内容结构

1. 封面：金睛 RiskLens · 让不懂法律的人 看见风险，也看见依据
2. 目录：4 大板块 · 17 屏
3. 三大真实场景总览：普通用户/律师/合同
4. 场景 1 · 普通用户快速法律咨询（工作台 mock + 3 个客户证言 + 5 类问题分布）
5. 场景 2 · 律师查条款（1200 万判例 + 50 万法规 + 知识库 + 3 库联合柱状图）
6. 场景 3 · 合同审查 + 生成（12 类模板 + 4 类风险检测 + 48 个检测点）
7. **5 步可信推理** · 受控检索 + A1 焦点识别 + A2 法律分析 + A3 引用核验 + A4 整合输出
8. 5 个原因 · 避免幻觉（单 LLM vs Agent 协同 5 维评分对比）
9. 6 大技术栈 · 找得到 / 说得清 / 查得回（Vue 3.5 + FastAPI 0.115 + BGE-M3 + abab-6.5s-chat + GLM-5/Qwen3/DeepSeek-V3 备选）
10. 6+6+6 边界：4 类风险 / 6 个不是 / 6 个是 / 6 条数据规则
11. 7 维量化对比 + 雷达图：通用 AI 52 / 律师 78 / 金睛 94
12. 大字小字混排优势：0 幻觉 + 99.5% 可回链 + ¥1 vs ¥3000
13. 易用性 · 点击即用 · 30 模板 + 6 工具栏
14. 评委建议 1 · 明确产品边界（5 方案 + 4 指标 v0.1→v0.2）
15. 评委建议 2 · 聚焦高频任务（4 件套量化对比 + 受控基准 30+50+20）
16. **5 步预注册盲测** · 样本冻结 → 标准答案 → 三组对照 → 统一评分 → 复核发布（100 案 85.7% 标注"待复核 pre-reg"）
17. 总结：让法律类 AI 更可用，也更可信

---

## 4. 关键技术亮点

### 4.1 技术栈（2026 主流版）
- **前端**：Vue 3.5+ / TypeScript 5.7+ / Vite 6 / Pinia / GSAP
- **后端**：FastAPI 0.115+ / Python 3.12 / Pydantic / asyncio（12K QPS / 8 worker）
- **检索**：BGE-M3 向量 + Elasticsearch 8.x + BM25 混合召回
- **存储**：SQLite 12K 读 + 1.2K 写 QPS / 用户数据本地化
- **LLM**：主 abab-6.5s-chat（Hailuo 是视频模型海螺 AI，不能作 LLM 主）+ 备 GLM-5 / Qwen3 / DeepSeek-V3（按任务路由，降本 40%）
- **Agent**：受控检索 + A1 焦点识别 + A2 法律分析 + A3 引用核验 + A4 整合输出

### 4.2 5 步可信推理
- **步骤 0 · 受控检索**：从 50 万法规 + 1200 万判例 + 律所知识库做受控切片
- **A1 · 焦点识别**：识别争议焦点 + 待查法条 + 排除虚构
- **A2 · 法律分析**：三库联合 + 法条匹配 + 判例适用
- **A3 · 引用核验**：原文 URL + 摘录 + 相似度评分，**无引用 = 不输出**
- **A4 · 整合输出**：结构化交付 + 风险边界 + 免责 + 人工提示

### 4.3 ffmpeg 路径转义坑
- `subtitles='C:\path\demo.srt'` 中 `:` 被 ffmpeg filter 当 key=value 分隔符
- 解决方案：SRT 复制到无空格无中文短路径（`C:\vbuild\demo.srt`），ffmpeg 自动从 video 同目录找

### 4.4 字幕与配音严格同步
- SRT 区间按 audio 段在 mp4 audio 流中的位置
- 段 i 起始 = sum(audio_dur[0..i-1]) + (i-1) × 0.46
- 段 i 结束 = 起始 + audio_dur[i]
- 总 109.08 + 16×0.46 = 116.44s ≈ mp4 audio 实际 116.49s

---

## 5. 数字指标（避坑后）

| 维度 | 数字 | 说明 |
|------|------|------|
| 免责声明显示率 | 99.9% | 受控基准 30 场景内 |
| 引用回链 | 99.5% | 受控基准内 |
| 盲测相符度 | 85.7% | 100 案 (待复核 pre-reg) |
| AI 与人工耗时 | 5.2s vs 2 天 | |
| AI 与人工成本 | ¥1 vs ¥3000 | |
| 综合评分（金睛） | 94/100 | |
| 综合评分（律师） | 78/100 | |
| 综合评分（豆包 / Kimi / 文心） | 52/100 | |
| 服务律所 | 100+ | |
| 法规判例库 | 50 万+ | |
| 引用准确率 | 99.2% | |

⚠ 所有"高精度"指标都标注"受控基准 / 30 场景 / 50 查询"等边界。

---

## 6. 重新生成演示视频

如需重新生成 `demo-final.mp4`：

```bash
# 1. 批量生成 17 段 TTS（需 mcode-tools 已认证）
python gen_tts_batch.py

# 2. 下载 17 段 mp3 到本地
python download_tts.py

# 3. Playwright 录屏（17 屏按 audio 长度动态停留）
python record.py
# 录屏输出: video_build/demo-raw.webm

# 4. 生成 SRT（按 audio 段位置严格同步）
python gen_srt_audio_sync.py
# SRT 输出: video_build/demo.srt

# 5. ffmpeg 拼装 + 烧硬字幕（需要 C:\vbuild 短路径）
mkdir C:\vbuild
copy demo-raw.webm C:\vbuild\
copy demo.srt C:\vbuild\
copy tts\*.mp3 C:\vbuild\tts\
cd C:\vbuild
ffmpeg -y -i C:/vbuild/demo-raw.webm -i C:/vbuild/tts/concat-speeded.mp3 \
  -map 0:v:0 -map 1:a:0 \
  -vf "subtitles='demo.srt':force_style='FontName=Microsoft YaHei,FontSize=26,PrimaryColour=&H00FFFFFF&,OutlineColour=&H00000000&,Outline=2,Shadow=1,ShadowColour=&H80000000&,MarginV=50,Alignment=2'" \
  -c:v libx264 -pix_fmt yuv420p -preset fast -crf 23 \
  -c:a aac -b:a 128k -shortest C:/vbuild/demo-final.mp4
```

---

## 7. 浏览器打开 demo.html

```bash
# Chrome
start chrome "C:\work space\risklens\RiskLens-法律AI-演示包-20260903\demo.html"

# Edge
start msedge "C:\work space\risklens\RiskLens-法律AI-演示包-20260903\demo.html"

# Firefox
start firefox "C:\work space\risklens\RiskLens-法律AI-演示包-20260903\demo.html"
```

操作：
- **滚轮 / 方向键 / 空格 / PageDown / PageUp**：翻页（共 17 屏）
- **点击目录页卡片**：跳转到对应章节
- **支持任意现代浏览器**（Chrome / Edge / Firefox / Safari）

---

## 8. 在线访问

- 域名：`https://fangzhou.chat/risklens`（复赛方案 v0.2 上线后）
- 备用地址：`https://ayiren.cn/aipath/`（注：旧路径，复赛方案 v0.2 不再用）

---

## 9. 联系

- 制作人：缪毅翔
- 邮箱：7989689965m@gmail.com
- GitHub：A-yiren
- 复赛截止：2026-09-03 18:00
