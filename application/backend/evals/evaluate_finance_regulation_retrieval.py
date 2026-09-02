"""冻结的官方法规检索基准：传统标题检索 vs 受控法规检索。"""
from __future__ import annotations
import json
from app.services.finance_regulation_catalog import REGULATIONS, search_regulations

CASES = (
    ("申请企业日常经营周转借款时，如何核验申请条件和材料真实性？", "NFRA-WC-2024"),
    ("怎样保证信用风险识别的独立性，以及初分认定审批的流程？", "CBIRC-PBC-CLASS-2023"),
    ("采集和加工企业信用数据时，如何保护商业秘密并保证信息质量？", "PBC-CREDIT-2021"),
)

def title_baseline(query: str) -> list[str]:
    return [item["id"] for item in REGULATIONS if item["title"] in query]

def evaluate() -> dict:
    rows = []
    baseline = rag = 0
    for query, expected in CASES:
        b = title_baseline(query)
        r = [item["id"] for item in search_regulations(query)]
        baseline += expected in b
        rag += expected in r
        rows.append({"query": query, "expected_source_id": expected, "traditional_title_retrieval": b, "risklens_regulation_retrieval": r})
    total = len(CASES)
    return {"dataset": "FRR-0.1", "cases": total, "official_source_recall_at_3": round(rag / total, 4), "traditional_title_recall_at_3": round(baseline / total, 4), "rows": rows, "scope": "3 条官方来源、3 个冻结查询；仅代表本受控法规目录的检索覆盖。"}

if __name__ == "__main__":
    print(json.dumps(evaluate(), ensure_ascii=False, indent=2))
