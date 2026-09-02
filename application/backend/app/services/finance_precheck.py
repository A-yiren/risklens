"""企业融资材料预审。

本模块只做材料完整性、可读性和跨材料事实一致性提示，不输出授信、投资、
理赔或其他专业机构应作出的结论。规则优先，便于测试和复核。
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from app.models import DocumentInfo
from app.parsers import get_parser
from app.services.finance_regulation_catalog import product_regulation_references


@dataclass(frozen=True)
class MaterialRule:
    rule_id: str
    key: str
    name: str
    description: str
    keywords: tuple[str, ...]
    required: bool = True


MATERIAL_RULES: tuple[MaterialRule, ...] = (
    MaterialRule("FPC-001", "business_license", "营业执照", "核验企业主体与统一社会信用代码。", ("营业执照", "统一社会信用代码")),
    MaterialRule("FPC-002", "loan_application", "融资/借款申请材料", "说明融资用途、金额、期限及申请主体。", ("借款申请", "融资申请", "授信申请", "贷款申请")),
    MaterialRule("FPC-003", "financial_statements", "近期财务报表", "至少应可识别资产负债表、利润表或现金流量表。", ("资产负债表", "利润表", "现金流量表", "财务报表")),
    MaterialRule("FPC-004", "tax_material", "纳税材料", "用于人工核验纳税申报或完税情况。", ("纳税证明", "完税证明", "纳税申报", "税务")),
    MaterialRule("FPC-005", "bank_statement", "银行流水/账户明细", "用于人工核验经营性收支与账户明细。", ("银行流水", "交易明细", "账户对账单", "账户流水")),
    MaterialRule("FPC-006", "major_contract", "主要交易合同", "用于观察交易背景、履约与回款安排。", ("采购合同", "销售合同", "服务合同", "合同编号")),
    MaterialRule("FPC-007", "receivables_schedule", "应收账款明细或账龄表", "用于人工核验应收账款构成与账龄。", ("应收账款", "账龄", "客户名称", "回款计划")),
    MaterialRule("FPC-008", "shareholder_resolution", "内部授权文件（如适用）", "企业章程、融资产品或授权规则要求时，再补充股东会/董事会决议。", ("股东会决议", "董事会决议", "融资授权"), required=False),
    MaterialRule("FPC-009", "guarantee_material", "担保/抵押材料（如适用）", "存在担保、抵押、质押或保证安排时，再补充对应资料。", ("抵押", "质押", "保证合同", "担保"), required=False),
)

FIELD_PATTERNS: dict[str, tuple[str, ...]] = {
    "enterprise_name": (r"(?:企业名称|公司名称|单位名称|申请人|借款人)[：:\s]*([^\n；;，,]{2,80})",),
    "legal_representative": (r"(?:法定代表人|法人代表)[：:\s]*([^\n；;，,]{2,40})",),
    "credit_code": (r"\b([0-9A-Z]{18})\b",),
    "reporting_period": (r"\b(20\d{2}年(?:度|[1-4]季度|[1-2]月))",),
    "financing_amount": (r"(?:申请金额|融资金额|借款金额)[：:\s]*([^\n；;]{1,60})",),
}


class FinancePrecheckService:
    """在用户已授权的私有材料范围内执行预审。"""

    def review(self, documents: Iterable[DocumentInfo], product_type: str = "working_capital") -> dict[str, Any]:
        parsed_documents = [self._parse_document(doc) for doc in documents]
        classifications: dict[str, list[dict[str, Any]]] = defaultdict(list)
        facts: dict[str, list[dict[str, Any]]] = defaultdict(list)
        format_issues: list[dict[str, Any]] = []

        for item in parsed_documents:
            if item["parse_error"]:
                format_issues.append({
                    "severity": "high",
                    "title": "材料无法解析",
                    "detail": "系统无法读取该文件内容，请确认文件未损坏、未加密，或提供可检索文本版本。",
                    "evidence": self._evidence(item, "解析失败", item["parse_error"]),
                })
                continue
            if not item["text"].strip():
                format_issues.append({
                    "severity": "medium",
                    "title": "材料缺少可检索文本",
                    "detail": "该材料未提取到文本；扫描件请补充清晰的可识别版本，供人工复核。",
                    "evidence": self._evidence(item, "文本提取", "未提取到可检索文本"),
                })
                continue

            for rule in MATERIAL_RULES:
                if self._matches(rule, item):
                    classifications[rule.key].append(item)
            for field, values in self._extract_facts(item).items():
                facts[field].extend(values)

        checklist = []
        for rule in MATERIAL_RULES:
            matches = classifications.get(rule.key, [])
            if matches:
                checklist.append({
                    "rule_id": rule.rule_id,
                    "key": rule.key,
                    "name": rule.name,
                    "required": rule.required,
                    "status": "present",
                    "description": rule.description,
                    "evidence": [
                        self._evidence(item, "材料匹配", self._match_keyword(rule, item) or rule.name)
                        for item in matches[:3]
                    ],
                })
            else:
                checklist.append({
                    "rule_id": rule.rule_id,
                    "key": rule.key,
                    "name": rule.name,
                    "required": rule.required,
                    "status": "missing" if rule.required else "not_applicable_or_missing",
                    "description": rule.description,
                    "evidence": [],
                })

        conflicts = self._find_conflicts(facts)
        missing_required = [item for item in checklist if item["required"] and item["status"] == "missing"]
        risk_flags = [
            {
                "severity": "high",
                "type": "material_missing",
                "title": f"缺少{item['name']}",
                "detail": item["description"],
                "evidence": [],
            }
            for item in missing_required
        ]
        risk_flags.extend(format_issues)
        risk_flags.extend(conflicts)

        follow_up = [f"请补充：{item['name']}。{item['description']}" for item in missing_required]
        for conflict in conflicts:
            follow_up.append(f"请人工核实：{conflict['title']}。以原件和最新有效材料为准。")
        if not follow_up:
            follow_up.append("基础材料已识别，请由业务人员结合融资产品规则核对时效、原件与授权要求。")

        required_total = len([rule for rule in MATERIAL_RULES if rule.required])
        required_present = required_total - len(missing_required)
        reasoning_trace = self._build_reasoning_trace(
            parsed_documents, checklist, facts, conflicts, format_issues, missing_required
        )
        return {
            "product_type": product_type,
            "status": "needs_human_review",
            "decision_boundary": "本结果仅为融资材料预审与风险提示，不构成授信审批、授信准入、放款承诺、投资建议或其他专业机构决定。",
            "scope_notice": "系统只对本次选中的私有材料执行规则核验；“已识别”表示命中材料关键词或字段，不表示文件真实、有效、完整或满足某金融机构的具体要求。",
            "rulebook": {
                "name": "企业流动资金材料预审规则集",
                "version": "FPC-1.0",
                "source_type": "产品受控核验规则",
                "notice": "该规则集不是法规数据库，也不能替代银行、担保机构或合规人员的业务规则。",
            },
            "official_regulation_references": product_regulation_references(),
            "summary": {
                "documents_received": len(parsed_documents),
                "required_materials_present": required_present,
                "required_materials_total": required_total,
                "missing_required_count": len(missing_required),
                "format_issue_count": len(format_issues),
                "inconsistency_count": len(conflicts),
                "manual_review_required": True,
            },
            "material_checklist": checklist,
            "extracted_facts": self._public_facts(facts),
            "risk_flags": risk_flags,
            "reasoning_trace": reasoning_trace,
            "follow_up_questions": follow_up,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def _matches(rule: MaterialRule, item: dict[str, Any]) -> bool:
        return FinancePrecheckService._match_keyword(rule, item) is not None

    @staticmethod
    def _match_keyword(rule: MaterialRule, item: dict[str, Any]) -> str | None:
        haystack = f"{item['name']}\n{item['text'][:8000]}".lower()
        return next((keyword for keyword in rule.keywords if keyword.lower() in haystack), None)

    def _parse_document(self, doc: DocumentInfo) -> dict[str, Any]:
        item = {"id": doc.id, "name": doc.name, "text": "", "pages": 0, "parse_error": ""}
        path = Path(doc.file_path or "")
        if not path.is_file():
            item["parse_error"] = "原始文件不可用"
            return item
        try:
            parsed = get_parser(path).parse(path)
            item["text"] = parsed.full_text or ""
            item["pages"] = parsed.total_pages or 0
        except Exception as exc:  # 将解析错误转为可复核提示，避免整个任务失败。
            item["parse_error"] = str(exc)[:200]
        return item

    def _extract_facts(self, item: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
        extracted: dict[str, list[dict[str, Any]]] = defaultdict(list)
        text = item["text"]
        for field, patterns in FIELD_PATTERNS.items():
            for pattern in patterns:
                for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                    value = self._normalise_value(match.group(1))
                    if value and len(value) >= 2:
                        extracted[field].append({
                            "value": value,
                            "evidence": self._evidence(item, self._field_label(field), match.group(0).strip()),
                        })
        return extracted

    def _find_conflicts(self, facts: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
        flags = []
        for field in ("enterprise_name", "legal_representative", "credit_code"):
            by_value: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for fact in facts.get(field, []):
                by_value[self._normalise_value(fact["value"])].append(fact)
            if len(by_value) > 1:
                flags.append({
                    "severity": "high",
                    "type": "cross_document_inconsistency",
                    "title": f"跨材料{self._field_label(field)}不一致",
                    "detail": "不同材料出现多个值，系统不判断哪一个正确；请以最新有效原件和人工核验结果为准。",
                    "evidence": [fact["evidence"] for values in by_value.values() for fact in values[:1]],
                })
        return flags

    def _build_reasoning_trace(
        self,
        parsed_documents: list[dict[str, Any]],
        checklist: list[dict[str, Any]],
        facts: dict[str, list[dict[str, Any]]],
        conflicts: list[dict[str, Any]],
        format_issues: list[dict[str, Any]],
        missing_required: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """输出可审计的规则执行摘要，而不是模型的隐藏推理过程。"""
        matched = [item for item in checklist if item["status"] == "present"]
        fact_evidence = [fact["evidence"] for values in facts.values() for fact in values]
        return [
            {
                "step": 1,
                "title": "范围确认",
                "method": "仅处理本次用户选择且已入库的私有文件",
                "outcome": f"已接收 {len(parsed_documents)} 份材料；不访问共享法规库或其他用户文件。",
                "evidence": [
                    self._evidence(item, "输入材料", item["name"])
                    for item in parsed_documents[:20]
                ],
            },
            {
                "step": 2,
                "title": "材料清单比对",
                "method": "以规则集 FPC-1.0 的材料名称和关键词进行文本匹配",
                "outcome": f"识别到 {len(matched)} 类材料；{len(missing_required)} 类基础材料未识别。",
                "evidence": [evidence for item in matched for evidence in item["evidence"]],
            },
            {
                "step": 3,
                "title": "字段与一致性核验",
                "method": "从可检索文本提取企业名称、法定代表人、统一社会信用代码等字段，并比较跨材料值",
                "outcome": f"提取 {len(fact_evidence)} 条字段证据；发现 {len(conflicts)} 项跨材料差异。",
                "evidence": fact_evidence[:30],
            },
            {
                "step": 4,
                "title": "人工复核交接",
                "method": "汇总缺件、解析问题与字段差异；系统不判断材料真伪、授信准入或放款结果",
                "outcome": f"待补充 {len(missing_required)} 项，解析问题 {len(format_issues)} 项，所有结果均需人工复核。",
                "evidence": [evidence for flag in [*format_issues, *conflicts] for evidence in flag.get("evidence", [])],
            },
        ]

    @staticmethod
    def _normalise_value(value: str) -> str:
        return re.sub(r"\s+", "", value).strip("：:；;，,。. ")

    @staticmethod
    def _field_label(field: str) -> str:
        return {
            "enterprise_name": "企业名称",
            "legal_representative": "法定代表人",
            "credit_code": "统一社会信用代码",
            "reporting_period": "报告期间",
            "financing_amount": "融资金额",
        }[field]

    @staticmethod
    def _evidence(item: dict[str, Any], label: str, excerpt: str) -> dict[str, Any]:
        return {
            "document_id": item["id"],
            "document_name": item["name"],
            "location": f"第1-{item['pages']}页" if item["pages"] else "文档文本",
            "label": label,
            "excerpt": excerpt[:220],
        }

    @staticmethod
    def _public_facts(facts: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
        items = []
        for field, values in facts.items():
            seen = set()
            for fact in values:
                key = (field, fact["value"], fact["evidence"]["document_id"])
                if key in seen:
                    continue
                seen.add(key)
                items.append({"field": field, "label": FinancePrecheckService._field_label(field), **fact})
        return items


finance_precheck_service = FinancePrecheckService()
