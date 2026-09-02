from evals.evaluate_finance_precheck import evaluate_cases


def test_internal_finance_benchmark_compares_keyword_baseline_and_rule_precheck():
    cases = [{
        "id": "conflict",
        "documents": [
            {"name": "营业执照.txt", "text": "营业执照 企业名称：测试公司 法定代表人：张三 统一社会信用代码：91310000ABCDEFGH12"},
            {"name": "融资申请.txt", "text": "融资申请 申请人：测试公司 法定代表人：李四"},
            {"name": "财务报表.txt", "text": "资产负债表 利润表 现金流量表"},
            {"name": "完税证明.txt", "text": "完税证明"},
            {"name": "银行流水.txt", "text": "银行流水"},
            {"name": "销售合同.txt", "text": "销售合同 合同编号：A1"},
            {"name": "应收账款账龄表.txt", "text": "应收账款 账龄 回款计划"},
        ],
        "expected_major_risks": ["inconsistency:legal_representative"],
    }]

    report = evaluate_cases(cases)

    assert report["summary"]["risklens_rule_precheck"]["recall"] == 1.0
    assert report["summary"]["traditional_keyword_baseline"]["recall"] == 0.0
    assert report["summary"]["evidence_citation_error_rate"] == 0.0
