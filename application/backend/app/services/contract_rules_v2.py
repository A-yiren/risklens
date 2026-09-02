"""合同审查 V2 的保守型确定性规则。

只对合同原文中能够直接计算的事实作判断。每条结论同时保留合同原文、
字符位置和官方法源；无法确定合同期限、工资基数等前提时不猜测。
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Callable, Dict, List, Optional


LABOR_LAW_URL = (
    "https://www.mohrss.gov.cn/xxgk2020/fdzdgknr/zcfg/fl/"
    "202011/t20201102_394622_wap.html"
)
CIVIL_CODE_LEASE_URL = "https://gongbao.court.gov.cn/Details/74143ea5b6d1d47f82d6759fc6ef17.html"
CIVIL_CODE_DEPOSIT_URL = (
    "https://gongbao.court.gov.cn/Details/dfe439fb9450f0525bd7e7b50a6242.html"
)

NUMBER_TOKEN = r"[零〇一二两三四五六七八九十百\d.]+"
PERCENT_TOKEN = (
    rf"(?:(?P<percent_numeric>{NUMBER_TOKEN})\s*%|"
    rf"百分之\s*(?P<percent_chinese>{NUMBER_TOKEN}))"
)


def _number(value: str) -> Optional[float]:
    """解析规则所需的小范围阿拉伯/中文数字；无法确定时返回 None。"""
    try:
        return float(value)
    except ValueError:
        pass
    digits = {"零": 0, "〇": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4,
              "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
    if value in digits:
        return float(digits[value])
    if "百" in value:
        left, right = value.split("百", 1)
        base = digits.get(left, 1) * 100
        tail = _number(right) if right else 0
        return float(base + tail) if tail is not None else None
    if "十" in value:
        left, right = value.split("十", 1)
        tens = digits.get(left, 1) * 10
        ones = digits.get(right, 0) if right else 0
        return float(tens + ones)
    return None


def _percent(match: re.Match[str]) -> Optional[float]:
    """从百分号或“百分之”表述中取得明确比例。"""
    value = match.group("percent_numeric") or match.group("percent_chinese")
    return _number(value) if value else None


def _money(value: str, unit: str) -> Optional[float]:
    """将明确的元/万元金额折算为元；无法确定时不参与计算。"""
    number = _number(value)
    if number is None:
        return None
    if unit in {"万元", "万"}:
        return number * 10_000
    if unit == "元":
        return number
    return None


def _date_from_parts(year: str, month: str, day: str) -> Optional[date]:
    try:
        return date(int(year), int(month), int(day))
    except ValueError:
        return None


def _date_range(match: re.Match[str]) -> Optional[tuple[date, date]]:
    start = _date_from_parts(match.group(1), match.group(2), match.group(3))
    end = _date_from_parts(match.group(4), match.group(5), match.group(6))
    if not start or not end or end <= start:
        return None
    return start, end


def _calendar_months(start: date, end: date) -> int:
    months = (end.year - start.year) * 12 + end.month - start.month
    return months - 1 if end.day < start.day else months


def _inclusive_calendar_months(start: date, end: date) -> int:
    """按“起至…日止”的通常包含终止日写法计算完整自然月边界。"""
    return _calendar_months(start, end + timedelta(days=1))


def _add_years(value: date, years: int) -> date:
    try:
        return value.replace(year=value.year + years)
    except ValueError:
        # 2 月 29 日到非闰年按 2 月 28 日处理，保持保守边界。
        return value.replace(year=value.year + years, day=28)


class _EvidenceMatch:
    """把多段可直接计算的合同事实保留为一个原文证据区间。"""

    def __init__(self, text: str, start: int, end: int) -> None:
        self._text = text
        self._start = start
        self._end = end

    def group(self, _index: int = 0) -> str:
        return self._text[self._start:self._end]

    def start(self) -> int:
        return self._start

    def end(self) -> int:
        return self._end


@dataclass(frozen=True)
class RuleFinding:
    rule_id: str
    name: str
    level: str
    description: str
    suggestion: str
    contract_quote: str
    start: int
    end: int
    law_name: str
    article_no: str
    law_quote: str
    source_url: str
    confidence: str = "high"

    def as_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "level": self.level,
            "description": self.description,
            "suggestion": self.suggestion,
            "contract_evidence": {
                "quote": self.contract_quote,
                "start": self.start,
                "end": self.end,
            },
            "legal_basis": {
                "law_name": self.law_name,
                "article_no": self.article_no,
                "quote": self.law_quote,
                "source_url": self.source_url,
            },
            "confidence": self.confidence,
            "decision_mode": "deterministic",
        }


def _finding(
    match: re.Match[str],
    *,
    rule_id: str,
    name: str,
    description: str,
    suggestion: str,
    law_name: str,
    article_no: str,
    law_quote: str,
    source_url: str,
    level: str = "high",
) -> RuleFinding:
    return RuleFinding(
        rule_id=rule_id,
        name=name,
        level=level,
        description=description,
        suggestion=suggestion,
        contract_quote=match.group(0).strip(),
        start=match.start(),
        end=match.end(),
        law_name=law_name,
        article_no=article_no,
        law_quote=law_quote,
        source_url=source_url,
    )


def _scan_probation_duration(text: str, contract_type: str) -> List[RuleFinding]:
    if contract_type != "labor":
        return []
    term_match = re.search(
        rf"(?:劳动)?合同期限\s*(?:为|:|：)?\s*({NUMBER_TOKEN})\s*(年|个月|月)",
        text,
    )
    term_months: Optional[float] = None
    term_evidence: Optional[re.Match[str] | _EvidenceMatch] = None
    if term_match:
        term_value = _number(term_match.group(1))
        if term_value is not None:
            term_months = term_value * (12 if term_match.group(2) == "年" else 1)
            term_evidence = term_match
    else:
        date_match = re.search(
            r"(?:劳动)?合同(?:期限)?[^。；\n自]{0,24}自\s*(\d{4})年(\d{1,2})月(\d{1,2})日"
            r"起至\s*(\d{4})年(\d{1,2})月(\d{1,2})日止",
            text,
        )
        if date_match:
            parsed_range = _date_range(date_match)
            if parsed_range:
                term_months = float(_inclusive_calendar_months(*parsed_range))
                term_evidence = date_match
    probation_match = re.search(
        rf"试用期\s*(?:为|:|：)?\s*({NUMBER_TOKEN})\s*(个月|月)", text,
    )
    probation_months: Optional[float] = None
    probation_evidence: Optional[re.Match[str]] = probation_match
    if probation_match:
        probation_months = _number(probation_match.group(1))
    else:
        probation_date_match = re.search(
            r"试用期[^。；\n自]{0,24}自\s*(\d{4})年(\d{1,2})月(\d{1,2})日"
            r"起至\s*(\d{4})年(\d{1,2})月(\d{1,2})日止",
            text,
        )
        if probation_date_match:
            parsed_range = _date_range(probation_date_match)
            if parsed_range:
                probation_months = float(_inclusive_calendar_months(*parsed_range))
                probation_evidence = probation_date_match
    if term_months is None or not term_evidence or not probation_evidence or probation_months is None:
        return []
    maximum: Optional[float]
    if term_months < 3:
        maximum = 0
    elif term_months < 12:
        maximum = 1
    elif term_months < 36:
        maximum = 2
    else:
        maximum = 6
    if probation_months <= maximum:
        return []
    evidence = _EvidenceMatch(
        text,
        min(term_evidence.start(), probation_evidence.start()),
        max(term_evidence.end(), probation_evidence.end()),
    )
    return [_finding(
        evidence,  # type: ignore[arg-type]
        rule_id="labor.probation_duration.exceeds_cap",
        name="试用期超过法定上限",
        description=f"合同期限约 {term_months:g} 个月，试用期约 {probation_months:g} 个月，超过可由文本确定的 {maximum:g} 个月上限。",
        suggestion="将试用期调整到法定上限以内；签署前由专业人士结合实际用工形式复核。",
        law_name="中华人民共和国劳动合同法",
        article_no="第十九条",
        law_quote="劳动合同期限三个月以上不满一年的，试用期不得超过一个月；劳动合同期限一年以上不满三年的，试用期不得超过二个月；三年以上固定期限和无固定期限的劳动合同，试用期不得超过六个月。以完成一定工作任务为期限的劳动合同或者劳动合同期限不满三个月的，不得约定试用期。",
        source_url=LABOR_LAW_URL,
    )]


def _scan_probation_wage_ratio(text: str, contract_type: str) -> List[RuleFinding]:
    if contract_type != "labor":
        return []
    match = re.search(
        rf"试用期[^。；\n]{{0,30}}?(?:工资|薪资)[^。；\n]{{0,12}}?{PERCENT_TOKEN}",
        text,
    )
    ratio = _percent(match) if match else None
    if not match or ratio is None or ratio >= 80:
        return []
    return [_finding(
        match,
        rule_id="labor.probation_wage.below_80_percent",
        name="试用期工资比例低于 80%",
        description=f"合同明确写明试用期工资比例为 {ratio:g}%。",
        suggestion="将约定比例提高至不低于 80%，并另行核对是否低于同岗位最低档工资及当地最低工资标准。",
        law_name="中华人民共和国劳动合同法",
        article_no="第二十条",
        law_quote="劳动者在试用期的工资不得低于本单位相同岗位最低档工资或者劳动合同约定工资的百分之八十，并不得低于用人单位所在地的最低工资标准。",
        source_url=LABOR_LAW_URL,
    )]


def _scan_earnest_money_ratio(text: str, _contract_type: str) -> List[RuleFinding]:
    match = re.search(
        rf"定金[^。；\n]{{0,36}}?(?:为|按|占)?[^。；\n]{{0,12}}?{PERCENT_TOKEN}",
        text,
    )
    ratio = _percent(match) if match else None
    evidence: Optional[re.Match[str] | _EvidenceMatch] = match
    if ratio is None:
        total_matches = list(re.finditer(
            rf"(?:车辆)?(?:总价款|合同总价|主合同标的额|总金额)\s*(?:为|:|：)?\s*({NUMBER_TOKEN})\s*(万元|万|元)",
            text,
        ))
        deposit_matches = list(re.finditer(
            rf"定金(?:金额)?[^。；\n]{{0,24}}?({NUMBER_TOKEN})\s*(万元|万|元)",
            text,
        ))
        for total_match in total_matches:
            total = _money(total_match.group(1), total_match.group(2))
            if not total:
                continue
            for deposit_match in deposit_matches:
                deposit = _money(deposit_match.group(1), deposit_match.group(2))
                if deposit is None:
                    continue
                ratio = deposit / total * 100
                evidence = _EvidenceMatch(
                    text,
                    min(total_match.start(), deposit_match.start()),
                    max(total_match.end(), deposit_match.end()),
                )
                break
            if ratio is not None:
                break
    if not evidence or ratio is None or ratio <= 20:
        return []
    return [_finding(
        evidence,  # type: ignore[arg-type]
        rule_id="general.earnest_money.exceeds_20_percent",
        name="定金比例超过主合同标的额 20%",
        description=f"合同明确写明定金比例为 {ratio:g}%。超过部分不产生定金效力。",
        suggestion="将定金比例调整到主合同标的额的 20% 以内，并确认条款使用的是“定金”而非押金或预付款。",
        law_name="中华人民共和国民法典",
        article_no="第五百八十六条",
        law_quote="定金的数额由当事人约定；但是，不得超过主合同标的额的百分之二十，超过部分不产生定金的效力。",
        source_url=CIVIL_CODE_DEPOSIT_URL,
    )]


def _scan_lease_term(text: str, contract_type: str) -> List[RuleFinding]:
    if contract_type != "lease":
        return []
    match = re.search(rf"租赁期限[^。；\n]{{0,16}}?({NUMBER_TOKEN})\s*年", text)
    years = _number(match.group(1)) if match else None
    evidence: Optional[re.Match[str] | _EvidenceMatch] = match
    date_exceeds_cap = False
    if years is None:
        date_match = re.search(
            r"租赁期(?:限|间)?[^。；\n]{0,24}?自\s*(\d{4})年(\d{1,2})月(\d{1,2})日"
            r"起至\s*(\d{4})年(\d{1,2})月(\d{1,2})日止",
            text,
        )
        if date_match:
            parsed_range = _date_range(date_match)
            if parsed_range and parsed_range[1] > _add_years(parsed_range[0], 20):
                cap_end = _add_years(parsed_range[0], 20)
                years = 20 + (parsed_range[1] - cap_end).days / 365
                evidence = date_match
                date_exceeds_cap = True
    if not evidence or years is None or (not date_exceeds_cap and years <= 20):
        return []
    return [_finding(
        evidence,  # type: ignore[arg-type]
        rule_id="lease.term.exceeds_20_years",
        name="租赁期限超过二十年",
        description=f"合同明确写明租赁期限为 {years:g} 年，超过二十年的部分无效。",
        suggestion="将单次约定的租赁期限调整到二十年以内；续订时重新核对期限。",
        law_name="中华人民共和国民法典",
        article_no="第七百零五条",
        law_quote="租赁期限不得超过二十年。超过二十年的，超过部分无效。",
        source_url=CIVIL_CODE_LEASE_URL,
    )]


RuleScanner = Callable[[str, str], List[RuleFinding]]
SCANNERS: List[RuleScanner] = [
    _scan_probation_duration,
    _scan_probation_wage_ratio,
    _scan_earnest_money_ratio,
    _scan_lease_term,
]


def scan_contract_rules_v2(text: str, contract_type: str = "general") -> List[Dict[str, Any]]:
    """运行所有 V2 规则；规则异常不应静默变成法律结论。"""
    findings: List[RuleFinding] = []
    for scanner in SCANNERS:
        findings.extend(scanner(text, contract_type))
    findings.sort(key=lambda item: (item.start, item.rule_id))
    return [item.as_dict() for item in findings]
