"""融资材料预审的公开评测披露口径。

这里故意把“内部规则基准”与“专家双盲评测”分开，避免把合成样本或产品
规则误称为法规准确率、专家结论或真实授信效果。
"""

from __future__ import annotations

from typing import Any


def public_evaluation_disclosure() -> dict[str, Any]:
    """返回前端可展示的、可复现但不可夸大的评测状态。"""
    return {
        "scenario": {
            "name": "企业流动资金融资材料预审",
            "boundary": "只识别材料完整性、可读性与跨材料字段差异；不输出授信、放款、投资或理赔决定。",
        },
        "benchmark": {
            "name": "融资材料预审内部规则基准",
            "version": "FPC-Benchmark-0.1",
            "cases": 3,
            "data_scope": "去标识化合成材料场景，用于回归测试；不代表真实客群、银行策略或法规全量语料。",
            "reproducible_command": "python -m evals.evaluate_finance_precheck",
        },
        "comparison": [
            {
                "name": "人工专家参照",
                "status": "PENDING_DOUBLE_REVIEW",
                "description": "需由两名独立的信贷/合规专业人员分别标注，再完成分歧裁决后，才能作为公开对照。",
            },
            {
                "name": "传统关键词检索基线",
                "status": "INTERNAL_ONLY",
                "description": "仅按材料关键词判断是否命中；不做跨材料字段一致性核验。",
                "result": "重大提示召回率 85.7%，重大风险漏检率 14.3%（3 个合成场景）。",
            },
            {
                "name": "RiskLens 规则核验",
                "status": "INTERNAL_ONLY",
                "description": "规则集 FPC-1.0 + 原文证据回链 + 跨材料字段一致性检查。",
                "result": "重大提示召回率 100.0%，重大风险漏检率 0.0%，错误引用率 0.0%（3 个合成场景）。",
            },
        ],
        "metrics": [
            {
                "key": "controlled_rule_recall",
                "name": "受控预审规则召回率",
                "value": "100.0%",
                "scope": "FPC-Benchmark-0.1 的 3 个合成场景；不等同法规召回率。",
            },
            {
                "key": "evidence_citation_error_rate",
                "name": "错误引用率",
                "value": "0.0%",
                "scope": "仅检查系统输出的证据摘录是否可在对应输入材料中精确定位。",
            },
            {
                "key": "major_risk_miss_rate",
                "name": "重大风险漏检率",
                "value": "0.0%",
                "scope": "仅统计基准定义的“缺少基础材料、跨材料主体字段冲突”两类重大提示。",
            },
            {
                "key": "regulation_retrieval_recall",
                "name": "法规依据召回率",
                "value": "100.0%",
                "status": "INTERNAL_OFFICIAL_CATALOG",
                "scope": "FRR-0.1：3 条人工核验的官方来源、3 个冻结查询的 Recall@3；不代表法规全量覆盖或真实授信准确率。",
            },
        ],
        "publication_gate": "竞赛或对外材料不得将上述内部结果表述为专家评测或真实授信准确率；法规检索指标仅适用于当前受控目录。需完成双专家独立标注、分歧裁决和扩大官方来源审计后，方可发布正式对照数据。",
    }
