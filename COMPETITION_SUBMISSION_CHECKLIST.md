# GOAI 复赛提交材料核对表

本清单对应“无界应用 Boundless Agents”复赛的四项工程材料要求，供评委快速核验。

## 1. 更新版项目方案（PPT / PDF）

- 目标场景与用户流程：[融资材料预审设计](application/docs/FINANCE_PRECHECK_DESIGN.md)
- Agent 架构与工具调用：[评审映射](application/docs/BOUNDLESS_AGENTS_REVIEW.md)；[架构图](application/docs/diagrams/)
- 数据来源、风险边界和落地计划：[数据与合规说明](application/docs/DATA_COMPLIANCE_FINANCE.md)
- 评测指标与方法：[可信与评测说明](application/docs/FINANCE_PRECHECK_TRUST_AND_EVALUATION.md)、[评测目录](application/backend/evals/)
- 演示版方案文件：`application/docs/` 及 `application/docs/答辩演示材料-20260901/` 中保留 PDF、PPTX、DOCX 和网页演示材料。

## 2. 可运行 Demo 或 Demo 视频

- 在线体验：<https://fangzhou.chat/risklens/>
- 录屏视频：[demo-final.mp4](demo-final.mp4)
- 演示截图：`shots/`
- 字幕与讲解：`demo.srt`、`narration.json`

完整任务链路涵盖：用户输入/材料选择、Agent 处理、规则和知识库调用、带来源的结果交付、缺失项/异常提示与 `needs_human_review` 人工交接。

## 3. 代码仓库或等价工程材料

- 运行入口与项目说明：[application/README.md](application/README.md)
- 部署说明：[application/DEPLOY.md](application/DEPLOY.md)
- 环境配置示例：[application/.env.example](application/.env.example)
- 示例数据：`application/seed_data/`、`application/seed_data_cases/`
- 自动化测试：`application/backend/tests/`
- 评测与运行报告：`application/backend/evals/`
- 线上源码快照记录：[SERVER_SNAPSHOT_20260903.md](SERVER_SNAPSHOT_20260903.md)

## 4. 数据来源与合规说明

- 数据类型、来源、授权与处理方式：[DATA_COMPLIANCE_FINANCE.md](application/docs/DATA_COMPLIANCE_FINANCE.md)
- 人工专家比对的范围与流程：[EXPERT_REVIEW_PROTOCOL.md](application/docs/EXPERT_REVIEW_PROTOCOL.md)
- 法规检索、指标口径和可追溯机制：[FINANCE_PRECHECK_TRUST_AND_EVALUATION.md](application/docs/FINANCE_PRECHECK_TRUST_AND_EVALUATION.md)
- 工程安全测试：`test_api_security.py`、`test_prompt_boundaries.py`、`test_tenant_isolation.py`、`test_retrieval_privacy.py`

## 提交边界

RiskLens 是材料预审与金融合规参考工具。系统不得替代金融机构、专业人员或主管部门进行确定性审批、授信、放款、投资、保险赔付或法律结论；涉及异常、证据不足或高风险事项时，应由有权人员复核。
