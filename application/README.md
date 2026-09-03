# 金睛 RiskLens

> 企业流动资金融资材料预审与金融合规参考助手｜从“找材料、拼结论”转向“看差异、作判断”｜Boundless Agents · AI+金融

[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com/)
[![Demo](https://img.shields.io/badge/demo-fangzhou.chat/risklens-gold)](https://fangzhou.chat/risklens/)

> **让每一次材料核验都有来源、边界和人工交接；让业务人员把时间用在核对差异与作出判断上。**

金睛 RiskLens 的主场景是中小企业流动资金融资材料预审：选择私有材料后，系统完成解析、规则核验、字段一致性检查、官方法规参考检索与证据回链，并将最终决定交给有权人员。它并不输出授信、放款、投资或理赔结论，而是将缺件、差异、证据与待核实事项组织为可交接的预审底稿。金融合规问答保留 A1 焦点识别、A2 参考分析、A3 引用核验链路。

> 复赛快速验收、演示步骤与要求映射见 [`docs/BOUNDLESS_AGENTS_REVIEW.md`](docs/BOUNDLESS_AGENTS_REVIEW.md)；数据来源与高风险边界见 [`docs/DATA_COMPLIANCE_FINANCE.md`](docs/DATA_COMPLIANCE_FINANCE.md)。

> 📌 **参赛信息**：GOAI 2026 Boundless Agents（无界应用）· AI+金融 赛道 · 初赛截止 2026-08-16

---

## ✨ 核心能力

### 🔍 1. 3 Agent 引用校验链路
- **A1 焦点识别 Agent** — 独立从案情抽取焦点
- **A2 法律分析 Agent** — 基于焦点 + 检索法条生成观点
- **A3 引用核验 Agent ⭐** — 逐字核对每条 [n] 引用真实性，自动过滤幻觉
- **A4 风险评估 Agent** — 暂停，待风险建议也具备逐条证据后再启用

> A3 采用失败关闭：引用缺失、格式异常、校验缺失或复合观点中任一引用失败时，整条观点不进入结果。当前没有足以支持“幻觉率 <5%”的标注评测集，因此不作该承诺。

### 📚 2. 双 RAG 隔离检索
- **法律库 collection** — 仓库含 41 个法规种子文件；现行有效性和来源 URL 需逐项核验，chunk 数以实际入库为准
- **案例库 collection** — 60 个种子案例文件；其来源 URL 尚不完整，不能据此宣称全部为真实判例
- 检索时按 collection 物理隔离，payload 携带 `category` 字段，前端可分类展示

### 💼 3. 主场景：流动资金融资材料预审
- **材料核验** — 营业执照、融资申请、财务报表等基础材料的规则化识别
- **事实一致性** — 对企业名称、法定代表人、统一社会信用代码等字段进行跨材料核验
- **法规与人工交接** — 展示官方参考依据、原材料证据和需由专业人员处理的事项

### 📝 4. 合同审查
- 规则引擎（10+ 高风险模式：违约金过高、单方解除不对等...）
- 必备条款检查（5 类合同模板）
- RAG 5-query 并行检索 → 去重取前 5
- LLM 综合分析（高/中/低风险等级 + 5 大模块完整报告）

### ✅ 5. 引用溯源
- 每条观点带 `[n]` 引用编号
- 点开 `[n]` 跳转到原文片段
- `quality_score` 是引用通过、焦点覆盖、校验完整度和检索相关度的组合质量指标，不是正确率、置信概率或胜诉概率

---

## 🛠️ 技术栈（开源可商用）

| 层级 | 技术 |
|------|------|
| **后端** | Python 3.12 + FastAPI 0.115 + SQLite + Pydantic v2 |
| **向量库** | Qdrant（显式 local 或 server 模式） |
| **Embedding** | BAAI/bge-small-zh-v1.5（512 维，100MB，本地推理） |
| **LLM** | OpenAI 兼容接口（供应商与模型由环境变量配置） |
| **前端** | 原生 HTML + Tailwind CDN + Font Awesome（零构建步骤） |
| **认证** | JWT HS256，72h 有效期；默认本地账号，可显式切换 aipath 共享账号 |
| **部署** | Nginx 反向代理 + systemd，单进程 |

---

## 🚀 快速开始

### 1. 准备环境

```bash
# Python 3.10+ （推荐 3.12）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r backend/requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入:
#   LLM_API_KEY=your-minimax-key
#   LLM_BASE_URL=https://api.minimaxi.com/v1
#   JWT_SECRET=your-random-32-char
```

### 3. 初始化知识库

```bash
cd backend
python scripts/local_full_ingest.py
# 预计 1-2 分钟：解析 41 部法规 + 60 判例 → 写入 Qdrant
```

### 4. 启动服务

```bash
cd backend
export HF_ENDPOINT=https://hf-mirror.com  # 国内加速
export HF_HUB_OFFLINE=1                    # 用本地模型
python -m uvicorn app.main:app --host 0.0.0.0 --port 8765
```

### 5. 访问

打开浏览器 → `http://localhost:8765/`

---

## 📁 项目结构

```
legal-lens/
├── backend/
│   ├── app/
│   │   ├── api/           # FastAPI 路由
│   │   │   ├── analyze.py       # 案件分析（3 Agent）
│   │   │   ├── cases.py         # 案件库 CRUD
│   │   │   ├── knowledge.py     # 知识库 CRUD + 搜索
│   │   │   ├── auth.py          # 用户认证（委托 aipath）
│   │   │   └── health.py        # 健康检查
│   │   ├── services/       # 业务逻辑
│   │   │   ├── agents.py        # 3 Agent 引用校验引擎 ⭐
│   │   │   ├── retrieval.py     # 法律库 RAG
│   │   │   ├── case_retrieval.py # 案例库 RAG
│   │   │   ├── embedding.py     # BGE 模型加载
│   │   │   ├── llm.py          # LLM 客户端
│   │   │   ├── contract_review.py # 合同审查
│   │   │   └── ingestion.py     # 文档入库
│   │   ├── storage/        # 数据层
│   │   │   ├── qdrant_client.py # Qdrant 封装
│   │   │   └── sqlite.py        # SQLite 封装
│   │   ├── models/         # Pydantic 模型
│   │   ├── config.py       # 全局配置
│   │   └── main.py         # FastAPI 入口
│   └── scripts/            # 运维脚本
│       └── local_full_ingest.py
├── frontend/               # 静态前端
│   ├── index.html          # 工作台
│   ├── auth.js             # 全局认证
│   └── pages/
│       ├── case-analysis.html    # 案件分析（3 Agent）
│       ├── case-search.html      # 类案检索
│       ├── case-list.html        # 案件库
│       ├── contract-review.html  # 合同审查
│       ├── knowledge-base.html   # 知识库（3 tab）
│       ├── obsidian.html         # Obsidian 集成
│       └── login.html            # 登录/注册
├── seed_data/              # 41 部法规 + 60 判例种子
│   ├── 中华人民共和国商业银行法.md
│   ├── 中华人民共和国证券法.md
│   ├── ... (共 41 部)
│   ├── case-001-信用卡盗刷纠纷案.case
│   └── ... (共 60 判例)
├── docs/
│   ├── 金睛-RiskLens-产品介绍.pdf  # ⭐ GOAI 比赛方案 PPT
│   ├── 作品简介-GOAI-AI金融.md      # ⭐ GOAI 比赛作品简介
│   ├── 作品简介-GOAI-AI金融.docx    # ⭐ 提交格式
│   ├── 作品简介-GOAI-AI金融.pdf     # ⭐ 提交格式
│   ├── ARCHITECTURE.md              # 详细架构说明
│   ├── diagrams/                    # 4 张架构图（mermaid + PNG）
│   ├── screenshots_v2/              # 5 张产品截图
│   └── ppt_preview_v2/              # 18 张 PPT 预览
├── nginx_legallens.conf    # Nginx 反代配置
└── restart.sh              # 启停脚本
```

---

## 🧪 端到端测试

当前 pytest 覆盖认证边界、租户隔离、Embedding/Qdrant 失败关闭、引用全量校验、合同精确摘录和提示注入边界。运行：`cd backend && pytest -q`。测试通过不等于法律结论正确率，端到端 LLM 质量仍需带标注数据集评测。

---

## 📊 核心数据资产

| 资产 | 数量 | 详情 |
|------|------|------|
| **法规** | 41 部 | 26 通用 + 15 金融 |
| **案例种子文件** | 60 个 | 30 通用 + 30 金融；来源真实性待逐项补证 |
| **法律 chunks** | 运行时统计 | 由实际解析、切块与入库结果决定 |
| **案例 chunks** | 运行时统计 | 由实际解析、切块与入库结果决定 |
| **总向量** | 运行时统计 | 查看 `/api/health` 的 `vector_count` |
| **幻觉率** | 尚未测定 | 需要有金标准答案与来源标注的独立评测集 |

### 41 部法规清单

- **通用（26 部）**：民法典-合同编、刑法、民诉、刑诉、公司法、劳动法、劳动合同法、知识产权-专利法、商标法、著作权法、消费者权益保护法、产品质量法、网络安全法、数据安全法、个人信息保护法、律师法、仲裁法、行政处罚法、行政强制法、行政许可法、行政诉讼法、道路交通安全法、反不正当竞争法、反垄断法、保险法...
- **金融（15 部）**：商业银行法、证券法、个人金融信息保护试行办法、征信业管理条例、商业银行理财业务监督管理办法、期货和衍生品法、证券投资基金法、信托法、反洗钱法、票据法、外汇管理条例、银行业监督管理法、存款保险条例、银行卡业务管理办法、民间借贷司法解释

### 60 个案例种子文件

- **法律（30 个）**：消费者维权、劳动纠纷、婚姻家庭、公司治理、知识产权、刑事案件、交通事故、其他民事
- **金融（30 个）**：金融借款合同纠纷、信用卡盗刷、内幕交易、保险代位、期货强行平仓、票据追索、融资租赁、征信、私募基金、信托、理财、担保

---

## 🛡️ 安全、合规与行业边界

### 数据合规
- ⚠️ Qdrant、SQLite 和 Embedding 可本地运行；案情会发送给所配置的外部 LLM API，不能宣称默认不出内网
- ✅ 默认本地账号；也可显式切换 aipath 共享账号
- ✅ 案件库 CRUD 强制带 `user_id` 过滤（多租户隔离）
- ✅ 日志审计可追溯

### 行业应用边界
- ⚠️ 不替代律师/合规官/法官的最终决策
- ⚠️ 输出含「建议咨询专业人士」提示
- ⚠️ 金融风险研判**仅作为辅助参考**
- ⚠️ 是否用于供应商训练、保留多久及跨境情况取决于所选 LLM 服务条款，部署方必须自行审查并配置

### 开放复用
- ⚠️ 当前仓库没有 LICENSE 文件，不能据此主张 MIT 或直接商用
- ⚠️ 种子数据可见不等于已获复用授权，需逐项核验来源与许可
- ✅ 部署文档完整，5 分钟起服务
- ✅ 二次开发友好：所有数据 schema 公开，API 文档自动生成

---

## 🌐 公共 Demo

- **URL**：https://fangzhou.chat/risklens/
- **状态**：以线上工作台和融资材料预审页为准；部署后须按 `docs/BOUNDLESS_AGENTS_REVIEW.md` 完成验收
- **数据**：公网实例的数据与向量数量需以该实例健康检查和审计记录为准

### 测试账号
- 用户名：`demo_risklens`
- 密码：`Demo123456`
- 也可自行注册新账号

---

## 📦 部署

### 单机部署
```bash
# 1. 拉代码
git clone https://github.com/A-yiren/legal-lens.git
cd legal-lens

# 2. 装依赖 + 初始化
pip install -r backend/requirements.txt
cd backend && python scripts/local_full_ingest.py && cd ..

# 3. 启服务
cd backend
export HF_ENDPOINT=https://hf-mirror.com HF_HUB_OFFLINE=1
python -m uvicorn app.main:app --host 0.0.0.0 --port 8765
```

### Nginx 反代
参考 `nginx_legallens.conf`，示例：
```nginx
location /legallens/ {
    alias /opt/legal-lens/frontend/;
    try_files $uri $uri/ /legallens/index.html;
}
location /legallens/api/ {
    proxy_pass http://127.0.0.1:8765/api/;
}
```

---

## 📜 许可

当前仓库未包含 `LICENSE` 文件。发布或复用前应由权利人补充明确的软件与数据许可。

---

## 🏆 GOAI 2026 参赛

本项目正在参加 **GOAI 2026 Boundless Agents（无界应用）· AI+金融** 比赛，提交材料：

- ✅ 作品简介：`docs/作品简介-GOAI-AI金融.md` / `.docx` / `.pdf`
- ✅ 方案 PPT：`docs/金睛-RiskLens-产品介绍.pptx` / `.pdf` (18 页)
- ✅ 可访问 Demo：https://fangzhou.chat/risklens/
- ✅ 源码仓库：本仓库

---

## 👤 参赛者

- **ayiren** (个人开发者)
- 联系：7989689965m@gmail.com
- 主页：https://ayiren.cn
