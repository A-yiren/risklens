# Contract Review V2 安全发布说明

## 当前边界

- V1 默认服务用户，`CONTRACT_REVIEW_V2_ENABLED=false`。
- V2 首版只判断合同原文中可以直接计算的四类风险：试用期期限、试用期工资比例、定金比例、租赁期限。
- V2 不生成自由文本法律分析，不推断合同未写明的事实。
- 测试集是人工构造的最小文本，不是真实合同，也不代表线上准确率。

## 三个开关

| 开关 | 默认值 | 作用 |
|---|---:|---|
| `CONTRACT_REVIEW_V2_ENABLED` | `false` | 主接口切换到 V2；只有验收通过后才打开。 |
| `CONTRACT_REVIEW_V2_SHADOW_ENABLED` | `false` | 同一请求运行 V1/V2，但只把 V1 返回给用户；会增加延迟。 |
| `CONTRACT_REVIEW_V2_PREVIEW_ENABLED` | `false` | 开放管理员专用的 `/api/contract/review-v2-preview`。 |

主开关优先级最高。不要同时把主开关和影子开关设为 `true`。

## 离线比较

在 backend 目录、项目 Python 环境中执行：

```powershell
python evals/evaluate_contract_review_v2.py --compare-v1 --output ../outputs/contract-review-v1-v2-baseline.json
```

报告分别给出误报、漏报、精确率、召回率、F1 和证据完整性失败数。当前 10 条合成基线只能证明规则实现与标签一致；下一阶段必须加入经过双人复核、去标识化的真实合同片段，单独报告各合同类型指标。

## 建议切换门槛

在扩充且冻结评测集后再设门槛，至少要求：

1. 高风险项零漏报，或每个漏报都有书面接受理由。
2. 引用 URL、法条号、法条摘录和合同原文位置完整率 100%。
3. V2 的误报率和漏报率均不高于 V1。
4. 全量自动化测试通过，且人工抽检没有发现错误法源。

## 回退

运行时回退只需把 `CONTRACT_REVIEW_V2_ENABLED=false` 并重启服务。代码级检查点为 Git 标签 `backup/pre-contract-review-v2-20260827`；不要用破坏性命令覆盖当前工作区。
