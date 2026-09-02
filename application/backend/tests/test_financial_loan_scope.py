from types import SimpleNamespace

from app.services.agents import _filter_inapplicable_financial_lending_materials


def _hit(law_name: str, text: str = ""):
    return SimpleNamespace(law_name=law_name, text=text)


def test_financial_institution_loan_excludes_private_lending_materials():
    results = [
        _hit("民法典-合同编"),
        _hit("最高人民法院关于审理民间借贷案件适用法律若干问题的规定"),
    ]

    filtered = _filter_inapplicable_financial_lending_materials(
        results, "张某与某银行签订个人住房按揭贷款合同，后发生逾期还款纠纷。"
    )

    assert [item.law_name for item in filtered] == ["民法典-合同编"]


def test_private_lending_case_keeps_private_lending_materials():
    results = [_hit("最高人民法院关于审理民间借贷案件适用法律若干问题的规定")]

    filtered = _filter_inapplicable_financial_lending_materials(
        results, "张某向李某借款 20 万元，约定年利率。"
    )

    assert filtered == results
