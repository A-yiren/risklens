"""Contract Review V2：默认关闭、证据优先的并行实现。"""
from __future__ import annotations

import time
from typing import Any, Dict, Optional

from app.services.contract_review import contract_reviewer
from app.services.contract_rules_v2 import scan_contract_rules_v2
from app.utils.logging import log


class ContractReviewV2Service:
    """首版 V2 只新增可复现的确定性判断，不让模型补全未知事实。"""

    async def review(
        self,
        contract_text: str,
        contract_type: str = "general",
        user_role: str = "中立",
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        started = time.perf_counter()
        findings = scan_contract_rules_v2(contract_text, contract_type)

        # 缺失条款和 RAG 检索沿用已验证的数据边界；不调用 V1 的自由文本 LLM，
        # 避免把未经逐项验证的模型叙述包装成 V2 结论。
        missing = contract_reviewer._check_required_clauses(contract_text, contract_type)
        citations = await contract_reviewer._retrieve_legal_basis(
            contract_text, contract_type, user_id
        )
        high_count = sum(item["level"] == "high" for item in findings)
        risk_level = "high" if high_count else ("medium" if missing else "low")
        log.info(
            "[合同审查V2] 类型={} 规则命中={} 缺失条款={} 耗时={:.3f}s",
            contract_type,
            len(findings),
            len(missing),
            time.perf_counter() - started,
        )
        return {
            "review_engine": "contract-review-v2",
            "contract_type": contract_type,
            "user_role": user_role,
            "risk_level": risk_level,
            "risks": findings,
            "missing_clauses": missing,
            "legal_citations": citations,
            "llm_analysis": {},
            "analysis_policy": {
                "mode": "evidence_first",
                "llm_free_text_enabled": False,
                "unknown_facts_are_inferred": False,
            },
            "summary": f"V2 可复现规则命中 {len(findings)} 项；缺失条款提示 {len(missing)} 项。",
        }


contract_reviewer_v2 = ContractReviewV2Service()
