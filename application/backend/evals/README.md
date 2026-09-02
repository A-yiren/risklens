# RiskLens 可复现第三方评测

这个目录用于验证 RiskLens，而不是展示宣传性分数。评测数据与生产知识库隔离，
法院公开材料是事实标准，裁判模型只负责对照标准答案评价语义，不负责创造标准答案。

## 信任链

1. 数据集中的每个案例都有法院官方 HTTPS 来源、访问日期和证据条目。
2. 输入只保留案情，禁止出现当事人、案号等容易直接搜索到答案的标识。
3. 每次运行记录数据集 SHA-256、目标系统健康信息、原始响应哈希和延迟。
4. 案号、法条、金额等适合程序核验的字段优先做确定性核验。
5. 语义评分至少需要两名不同 `provider/model` 身份的裁判模型。
6. 所有案例没有全部成功、任一哈希不匹配或裁判缺失时，报告固定为 `INCOMPLETE`，综合分为空。
7. 裁判分差超过 0.20 的案例进入争议清单，不能只隐藏在平均分中。

## 当前试点集

`official_cases_pilot_v1.jsonl` 包含 7 个最高人民法院或最高人民法院公报公开案例。
它用于验证流程，不足以支撑比赛中的最终泛化结论。正式报告建议扩展到至少 100 个案例，
并保留从未用于提示词、检索参数或模型选择的密封测试集。

## 运行

从仓库根目录执行：

```powershell
python -m backend.evals.eval_cli validate
```

在线记录法院来源状态和网页响应哈希：

```powershell
python -m backend.evals.eval_cli verify-sources `
  --output backend/evals/runs/source-verification.json
```

只读检索测试：

```powershell
$env:RISK_EVAL_USERNAME = "demo_risklens"
$env:RISK_EVAL_PASSWORD = "<demo-password>"
python -m backend.evals.eval_cli run `
  --mode retrieval `
  --output backend/evals/runs/pilot-retrieval.json
```

完整案件分析使用 `--mode both`。账号密码只从环境变量读取，不写入结果文件。

## 独立裁判

裁判接口采用 OpenAI-compatible API。至少配置两组不同的提供方或模型身份：

```powershell
$env:JUDGE_A_BASE_URL = "https://provider-a.example/v1"
$env:JUDGE_A_API_KEY = "<secret>"
$env:JUDGE_A_MODEL = "<model-a>"

$env:JUDGE_B_BASE_URL = "https://provider-b.example/v1"
$env:JUDGE_B_API_KEY = "<secret>"
$env:JUDGE_B_MODEL = "<model-b>"

python -m backend.evals.eval_cli judge `
  --run backend/evals/runs/pilot-analysis.json `
  --prefix JUDGE_A --name "Independent Judge A" `
  --output backend/evals/runs/judge-a.json

python -m backend.evals.eval_cli judge `
  --run backend/evals/runs/pilot-analysis.json `
  --prefix JUDGE_B --name "Independent Judge B" `
  --output backend/evals/runs/judge-b.json
```

生成严格汇总报告：

```powershell
python -m backend.evals.eval_cli report `
  --run backend/evals/runs/pilot-analysis.json `
  --source-verification backend/evals/runs/source-verification.json `
  --judge backend/evals/runs/judge-a.json `
  --judge backend/evals/runs/judge-b.json `
  --output backend/evals/runs/report.json
```

## 比赛报告必须披露

- 测试集规模、领域和年份分布；
- 官方来源清单及数据集哈希；
- RiskLens、裁判模型的精确版本；
- 完成率、失败率、延迟和成本；
- Recall@K、MRR、各法律评分维度；
- 裁判一致性与争议案例；
- 所有失败案例，而不仅是成功案例；
- 测试集是否曾用于调参；
- MiniMax 或裁判服务不可用时，明确标记未执行。

## 局限

AI 裁判不是司法鉴定机构，也不能替代法院或法律专家。可信度来自公开权威标准答案、
多裁判交叉验证、确定性指标、完整审计轨迹和失败披露，而不是把某个模型包装成“权威机构”。
