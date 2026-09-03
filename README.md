# 金睛 RiskLens · GOAI 复赛工程材料

> 企业流动资金融资材料预审与金融合规参考助手：从“找材料、拼结论”转向“看差异、作判断”  
> Boundless Agents · AI+金融

RiskLens 面向中小企业融资材料预审这一高频、可验证的任务：系统对用户授权提供的材料进行解析、规则核验、跨材料事实一致性检查、法规参考检索和证据回链。它把重复的材料整理与差异发现前置，交付一份可回看、可复核、可交接的预审清单；授信、放款、投资和其他专业判断仍明确交给有权人员完成。

**线上 Demo：** <https://fangzhou.chat/risklens/>  
**仓库用途：** 复赛可验证工程材料、运行说明、评测基准、数据与合规说明。

## 评委快速入口

| 复赛要求 | 可验证材料 |
| --- | --- |
| 更新版项目方案 | [产品与评审映射](application/docs/BOUNDLESS_AGENTS_REVIEW.md)、[融资预审设计](application/docs/FINANCE_PRECHECK_DESIGN.md)、[架构图](application/docs/diagrams/) |
| 可运行 Demo / 视频 | [线上 Demo](https://fangzhou.chat/risklens/)、[既有演示录屏](demo-final.mp4)、[演示脚本与字幕](narration.json) |
| 代码与工程材料 | [当前服务器源码快照](application/)、[部署说明](application/DEPLOY.md)、[环境变量示例](application/.env.example)、[测试](application/backend/tests/) |
| 数据与合规说明 | [数据与合规说明](application/docs/DATA_COMPLIANCE_FINANCE.md)、[专家复核协议](application/docs/EXPERT_REVIEW_PROTOCOL.md)、[评测说明](application/backend/evals/README.md) |

完整清单见 [COMPETITION_SUBMISSION_CHECKLIST.md](COMPETITION_SUBMISSION_CHECKLIST.md)。

## 核心任务链路

```text
材料选择/上传
  → 文档解析与字段抽取
  → FPC 规则核验 + 跨材料事实一致性检查
  → 官方法规参考检索 + 引用校验
  → 风险清单、缺失项、证据片段与来源链接
  → needs_human_review：由有权人员作最终判断
```

系统提供的是**材料预审与合规参考**，不作授信审批、放款、投资、保险赔付或其他专业机构的最终决定。

## 工程目录

```text
application/               当前线上运行版本的脱敏源码快照
  backend/                 FastAPI 服务、Agent、评测与测试
  frontend/                静态 Web 前端
  seed_data*/              示例知识与评测数据
  docs/                    架构、评测、数据与合规材料
  compliance/              合规交接材料
demo.html / demo-final.mp4 既有演示素材与录屏归档
```

## 本地复现

进入 [application/README.md](application/README.md)，按以下顺序执行：

1. 复制 `.env.example` 为 `.env`，仅在本地填入自己的服务凭据；请勿提交 `.env`。
2. 安装 `application/backend/requirements.txt` 中的依赖。
3. 运行 `application/backend/scripts/local_full_ingest.py` 写入示例知识库。
4. 按 [部署说明](application/DEPLOY.md) 启动服务，或运行 `pytest -q` 执行测试。

## 源码快照说明

本次 `application/` 来自 2026-09-03 从线上运行发布目录取得的脱敏快照。已排除 `.env`、私钥、运行数据库、用户上传文件、运行输出、缓存和模型权重；归档 SHA-256 与服务器导出值一致。详见 [SERVER_SNAPSHOT_20260903.md](SERVER_SNAPSHOT_20260903.md)。

## 安全与数据边界

- 仅处理用户授权材料；示例数据用于演示、测试和评测。
- 通过租户隔离、上传校验、提示注入边界、引用校验与失败关闭机制降低风险。
- 输出包含来源、证据片段与人工复核标记；质量指标不等同于授信、法律或投资结论。
- 第三方模型、法规、示例数据的来源、处理方式与适用限制见数据合规文档。

## 许可证与依赖

本仓库用于竞赛评审与复现。第三方依赖及其许可证以各依赖项目为准；提交、部署和二次使用前应自行核验适用许可证与数据授权。
