"""受控的官方金融法规小型检索库，服务于流动资金材料预审。

只收录人工核验过来源与生效信息的条目；结果是参考依据，不构成审批规则。
"""
from __future__ import annotations

from typing import Any


REGULATIONS: tuple[dict[str, Any], ...] = (
    {
        "id": "NFRA-WC-2024",
        "title": "流动资金贷款管理办法",
        "issuer": "国家金融监督管理总局",
        "effective_date": "2024-07-01",
        "source_url": "https://www.nfra.gov.cn/cn/view/pages/ItemDetail.html?docId=1151066&generaltype=0&itemId=925",
        "articles": ["第十四条（申请条件）", "第十五条（申请材料真实、完整、有效）"],
        "summary": "贷款申请需满足法定登记、用途明确合法等条件；贷款人提出申请材料要求，借款人承诺材料真实、完整、有效。",
        "keywords": ("流动资金", "经营周转", "融资申请", "借款申请", "申请材料", "材料真实", "贷款用途", "企业登记"),
    },
    {
        "id": "CBIRC-PBC-CLASS-2023",
        "title": "商业银行金融资产风险分类办法",
        "issuer": "原中国银保监会、中国人民银行",
        "effective_date": "2023-07-01",
        "source_url": "https://www.nfra.gov.cn/cn/view/pages/rulesDetail.html?docId=1095372",
        "articles": ["第五条（真实性、及时性、审慎性、独立性）", "第三十条（初分、认定、审批）"],
        "summary": "风险分类应真实、及时、审慎、独立；商业银行应建立初分、认定、审批的流程和制衡机制。",
        "keywords": ("风险分类", "初分", "认定", "审批", "独立性", "及时性", "审慎性", "金融资产风险"),
    },
    {
        "id": "PBC-CREDIT-2021",
        "title": "征信业务管理办法",
        "issuer": "中国人民银行",
        "effective_date": "2022-01-01",
        "source_url": "https://www.pbc.gov.cn/zhengwugongkai/attachDir/2025/11/2025111914572495786.pdf",
        "articles": ["第十五条（企业信用信息合法目的、商业秘密）", "第十六至十七条（客观性、准确性、信息质量）"],
        "summary": "采集企业信用信息应有合法目的且不得侵犯商业秘密；整理、保存和加工应保持客观性并保障准确性与信息质量。",
        "keywords": ("企业信用", "征信", "商业秘密", "信用信息", "数据准确", "信息质量", "客观性", "数据采集"),
    },
)


def search_regulations(query: str, limit: int = 3) -> list[dict[str, Any]]:
    """可解释的检索：关键词覆盖度排序，返回官方来源与命中依据。"""
    text = query.lower()
    hits = []
    for item in REGULATIONS:
        matched = [word for word in item["keywords"] if word.lower() in text]
        if matched:
            hits.append({**item, "match_terms": matched, "score": len(matched)})
    return sorted(hits, key=lambda item: (-item["score"], item["id"]))[:limit]


def product_regulation_references() -> list[dict[str, Any]]:
    """材料预审固定展示的法规边界，不据此推导授信结论。"""
    return [{**item, "match_terms": ["流动资金材料预审场景"], "score": 1} for item in REGULATIONS]
