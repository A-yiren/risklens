"""合同文本与已登记示范文本结构的保守匹配。

它不是合同类型的法律认定器，也不复制或声称输出官方示范文本。只有合同
正文出现了足够多的交易主体、标的和核心条款信号时，才标示为“精确结构匹配”。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class SignalGroup:
    label: str
    keywords: tuple[str, ...]


@dataclass(frozen=True)
class TemplateProfile:
    template_id: str
    title: str
    publisher: str
    version: str
    source_url: str
    review_contract_type: str
    purpose: str
    signals: tuple[SignalGroup, ...]


RESIDENTIAL_LEASE = TemplateProfile(
    template_id="samr-gf-2025-2614",
    title="城镇房屋租赁合同（示范文本）",
    publisher="国家市场监督管理总局",
    version="GF—2025—2614（2025）",
    source_url="https://htsfwb.samr.gov.cn/View?id=2340996b-882d-47a4-b74d-c30784628737",
    review_contract_type="lease",
    purpose="供城镇房屋出租给承租人居住时参照使用",
    signals=(
        SignalGroup("出租人与承租人", ("出租人", "承租人", "甲方", "乙方")),
        SignalGroup("房屋基本状况", ("房屋", "坐落", "不动产权", "建筑面积")),
        SignalGroup("租赁期限", ("租赁期限", "租赁期", "起至", "起租")),
        SignalGroup("租金与支付", ("租金", "支付", "月租", "付款")),
        SignalGroup("押金或保证金", ("押金", "保证金")),
        SignalGroup("费用或维修", ("物业", "水电", "维修", "修缮")),
        SignalGroup("交付返还或转租", ("交付", "返还", "验收", "转租")),
        SignalGroup("解除或违约", ("解除", "违约", "终止")),
    ),
)

LABOR = TemplateProfile(
    template_id="mohrss-labor-contract-required-terms",
    title="劳动合同必备条款结构",
    publisher="人力资源和社会保障部",
    version="劳动合同法第十七条",
    source_url="https://www.mohrss.gov.cn/xxgk2020/fdzdgknr/zcfg/fl/202011/t20201102_394622.html",
    review_contract_type="labor",
    purpose="用人单位与劳动者订立劳动合同时的法定必备条款结构",
    signals=(
        SignalGroup("用人单位与劳动者", ("用人单位", "劳动者", "甲方", "乙方")),
        SignalGroup("劳动合同期限", ("劳动合同", "合同期限", "无固定期限")),
        SignalGroup("工作内容与地点", ("工作内容", "工作地点", "岗位", "职务")),
        SignalGroup("工时与休假", ("工作时间", "工时", "休息休假")),
        SignalGroup("劳动报酬", ("工资", "薪酬", "劳动报酬", "月薪")),
        SignalGroup("社会保险", ("社会保险", "社保", "公积金")),
        SignalGroup("劳动保护", ("劳动保护", "劳动条件", "职业危害")),
        SignalGroup("试用期或解除", ("试用期", "解除", "终止")),
    ),
)

AUTOMOBILE_SALE = TemplateProfile(
    template_id="samr-xinjiang-auto-sale",
    title="新疆维吾尔自治区汽车买卖合同（示范文本）",
    publisher="国家市场监督管理总局合同示范文本库",
    version="2012",
    source_url="https://htsfwb.samr.gov.cn/View?id=9d126a55-0626-4d94-ae93-28773b45d9dc",
    review_contract_type="sale",
    purpose="汽车销售企业出售新车时参照使用",
    signals=(
        SignalGroup("出卖人与买受人", ("出卖人", "买受人", "卖方", "买方")),
        SignalGroup("车辆标识", ("汽车", "车辆", "车架号", "发动机号", "车型")),
        SignalGroup("价款", ("价款", "总价", "车价", "定金")),
        SignalGroup("交付验收", ("交付", "验收", "交接", "随车文件")),
        SignalGroup("质量或保修", ("质量", "保修", "合格证", "三包")),
        SignalGroup("违约或争议", ("违约", "争议", "仲裁", "诉讼")),
    ),
)

REAL_ESTATE_SALE = TemplateProfile(
    template_id="mohurd-samr-gf-2014-0172",
    title="商品房买卖合同（现售）（示范文本）",
    publisher="住房城乡建设部、国家工商行政管理总局",
    version="GF—2014—0172",
    source_url="https://htsfwb.samr.gov.cn/View?id=18d1427e-11a9-4873-9072-30f1e0804a4a",
    review_contract_type="sale",
    purpose="房地产开发企业出售已竣工验收合格商品房时参照使用",
    signals=(
        SignalGroup("出卖人与买受人", ("出卖人", "买受人", "卖方", "买方")),
        SignalGroup("商品房基本状况", ("商品房", "房屋", "不动产权", "建筑面积")),
        SignalGroup("房屋价款", ("房价款", "商品房价款", "总价", "首付款")),
        SignalGroup("交付手续", ("交付", "交房", "验收", "交付条件")),
        SignalGroup("质量保修", ("质量", "保修", "质量保证")),
        SignalGroup("登记或物业", ("登记", "不动产", "物业")),
        SignalGroup("违约或争议", ("违约", "争议", "仲裁", "诉讼")),
    ),
)

PROFILES = (RESIDENTIAL_LEASE, LABOR, AUTOMOBILE_SALE, REAL_ESTATE_SALE)


def _matches(text: str, group: SignalGroup) -> bool:
    return any(keyword in text for keyword in group.keywords)


def _profile_result(text: str, profile: TemplateProfile) -> dict[str, Any]:
    matched = [group.label for group in profile.signals if _matches(text, group)]
    missing = [group.label for group in profile.signals if group.label not in matched]
    score = round(len(matched) / len(profile.signals) * 100)
    # 交易对象与至少两个核心结构信号均出现，才称“精确结构匹配”。
    precise = len(matched) >= 4 and score >= 60
    partial = len(matched) >= 2 and score >= 35
    return {
        "profile": profile,
        "score": score,
        "matched": matched,
        "missing": missing,
        "precise": precise,
        "partial": partial,
    }


def _as_public(result: dict[str, Any]) -> dict[str, Any]:
    profile: TemplateProfile = result["profile"]
    return {
        "template_id": profile.template_id,
        "template_title": profile.title,
        "publisher": profile.publisher,
        "version": profile.version,
        "source_url": profile.source_url,
        "purpose": profile.purpose,
        "review_contract_type": profile.review_contract_type,
        "score": result["score"],
        "matched_sections": result["matched"],
        "missing_sections": result["missing"],
    }


def match_contract_template(text: str, selected_contract_type: str) -> dict[str, Any]:
    """返回可审计的结构匹配结果；不把低分候选称为模板匹配。"""
    candidates = sorted(
        (_profile_result(text, profile) for profile in PROFILES),
        key=lambda item: item["score"],
        reverse=True,
    )
    best = candidates[0]
    best_public = _as_public(best)
    selected_profiles = [
        item for item in candidates
        if item["profile"].review_contract_type == selected_contract_type
    ]
    selected_best = selected_profiles[0] if selected_profiles else None

    if best["precise"] and best["profile"].review_contract_type != selected_contract_type:
        return {
            "status": "mismatch",
            "review_action": "block",
            "selected_contract_type": selected_contract_type,
            "recommended_contract_type": best["profile"].review_contract_type,
            "message": (
                f"文本更符合“{best['profile'].title}”的结构，"
                "与当前选择的合同类型不一致。请切换类型后再审查，避免错套模板。"
            ),
            "best_candidate": best_public,
            "alternatives": [_as_public(item) for item in candidates[1:]],
        }

    if selected_best and selected_best["precise"]:
        return {
            "status": "precise_structure_match",
            "review_action": "allow",
            "selected_contract_type": selected_contract_type,
            "recommended_contract_type": selected_contract_type,
            "message": "已匹配到已登记示范文本的核心结构；仍需逐条检查填空、选择项与地区性要求。",
            "best_candidate": _as_public(selected_best),
            "alternatives": [_as_public(item) for item in candidates if item is not selected_best],
        }

    if selected_best and selected_best["partial"]:
        return {
            "status": "partial_structure_match",
            "review_action": "allow_with_warning",
            "selected_contract_type": selected_contract_type,
            "recommended_contract_type": selected_contract_type,
            "message": "文本与所选示范文本只有部分结构吻合；将按所选类型审查，但不会声称模板精准匹配。",
            "best_candidate": _as_public(selected_best),
            "alternatives": [_as_public(item) for item in candidates if item is not selected_best],
        }

    return {
        "status": "no_precise_template_match",
        "review_action": "allow_with_warning",
        "selected_contract_type": selected_contract_type,
        "recommended_contract_type": selected_contract_type,
        "message": (
            "未发现足以确认的已登记示范文本结构。系统仅按所选类型进行通用审查，"
            "不会把该文本标示为官方模板或模板匹配稿。"
        ),
        "best_candidate": best_public if best["partial"] else None,
        "alternatives": [_as_public(item) for item in candidates if item["partial"]],
    }


def residential_lease_draft_reference() -> dict[str, str]:
    """固定草稿的可追溯结构来源；明确不是官方表单的逐字副本。"""
    return {
        "reference_type": "structure_reference_not_official_form",
        "template_id": RESIDENTIAL_LEASE.template_id,
        "template_title": RESIDENTIAL_LEASE.title,
        "publisher": RESIDENTIAL_LEASE.publisher,
        "version": RESIDENTIAL_LEASE.version,
        "source_url": RESIDENTIAL_LEASE.source_url,
        "notice": "草稿参考该示范文本的房屋、期限、租金、押金、费用、维修、交付和违约等结构，不是官方表单的逐字副本。",
    }
