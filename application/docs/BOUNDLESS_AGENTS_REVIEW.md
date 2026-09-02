# Boundless Agents 复赛验收与演示指南

## 参赛定位

**场景**：中小企业流动资金融资材料预审。  
**目标用户**：企业融资经办人、银行普惠客户经理、担保/合规复核人员。  
**不做的事**：不输出授信审批、放款、投资、保险理赔或法律结论。

## 可验证的完整任务链路（3 分钟）

1. 使用测试账号登录线上 Demo，进入“融资材料预审”；
2. 在“规则与企业资料库”上传去标识化文本材料：营业执照、融资申请、财务报表、完税证明、银行流水、销售合同、应收账款账龄表；
3. 回到预审页勾选材料，点击“开始材料预审”；
4. 验收 Agent 链路：私有材料范围确认 → 文档解析 → FPC-1.0 材料规则核验 → 字段提取/跨材料一致性检查 → 官方法规依据检索 → 证据回链 → 人工复核交接；
5. 演示异常：缺少一份基础材料，或在融资申请中将法定代表人改为不同值；确认系统展示缺件/差异、原文件摘录与人工复核事项，而不生成审批结论；
6. 打开“评测透明度”，确认内部指标范围、传统检索对照、法规来源与双专家复核门槛。

## 要求—证据映射

| 复赛要求 | 工程证据 | 现场验收点 |
|---|---|---|
| 真实场景与完整任务链路 | `pages/finance-precheck.html`、`services/finance_precheck.py` | 从材料输入到证据交付与异常处理可操作完成 |
| Agent 能力 | 规则计划、文档解析、法规检索、字段一致性工具调用、会话内预审记录 | 输出包含步骤、依据、待人工判断项，不只有一段生成文本 |
| 知识增强 | `finance_regulation_catalog.py` | 每次预审展示官方来源、条目、生效时间与链接 |
| 产品稳定与工程可复现 | `DEPLOY.md`、`backend/requirements.txt`、`docker-compose.yml`、pytest | 服务器运行 `python -m pytest -q` |
| 评测 | `evals/evaluate_finance_precheck.py`、`evaluate_finance_regulation_retrieval.py` | 展示数据集、对照对象、范围、Recall@3、错误引用率、漏检率 |
| 数据与合规 | `DATA_COMPLIANCE_FINANCE.md`、`EXPERT_REVIEW_PROTOCOL.md` | 数据分类、权限、外部模型边界与人工决定边界清楚 |
| 开放/复用 | 本文档、示例评测集、部署与接口说明 | 未设定 LICENSE 前，明确“仅评审可验证、未授权公开复用” |

## 评测口径

- FPC-Benchmark-0.1：3 个去标识化合成材料场景，比较传统关键词检索与 RiskLens 规则预审；指标为受控规则召回、错误引用率、重大风险漏检率。
- FRR-0.1：3 条官方来源、3 个冻结查询，比较传统标题检索与受控法规检索；指标为官方来源 Recall@3。
- 两套数据均为内部回归基准，不代表真实授信准确率或全量法规覆盖。正式专家对照需按 `EXPERT_REVIEW_PROTOCOL.md` 由两名独立从业者完成。

## 提交前检查

```bash
cd backend
python -m pytest -q
python -m evals.evaluate_finance_precheck
python -m evals.evaluate_finance_regulation_retrieval
```

提交包应包含本文件、代码仓库、`DEPLOY.md`、合规说明、评测输出、可访问 Demo 链接及一段按上述脚本录制的演示视频。
