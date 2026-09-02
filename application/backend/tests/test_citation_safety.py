from app.models import Citation
from app.services.agents import MultiAgentOrchestrator


def _citation(cid: int, article: str, text: str, score: float = 0.8) -> Citation:
    return Citation(
        id=cid,
        law_name="测试法",
        article_no=article,
        article_text=text,
        source_chunk_id=f"chunk-{cid}",
        similarity=score,
    )


def test_composite_claim_is_dropped_if_any_citation_fails():
    orchestrator = MultiAgentOrchestrator.__new__(MultiAgentOrchestrator)
    result = orchestrator._integrate(
        a1_result={"case_focus": [{"focus": "争点"}]},
        a2_result={"legal_analysis": [{
            "focus_index": 1,
            "point": "复合结论 [1][2]",
            "citations": [1, 2],
        }]},
        a3_result={"validation": [
            {"point_index": 1, "citation_id": 1, "valid": True},
            {"point_index": 1, "citation_id": 2, "valid": False},
        ]},
        a4_result={},
        citations=[_citation(1, "第一条", "甲"), _citation(2, "第二条", "乙")],
    )

    assert result["legal_analysis"] == []
    assert result["citations"] == []
    assert result["quality_score"] == 0.0


def test_valid_citations_are_renumbered_without_losing_old_ids():
    orchestrator = MultiAgentOrchestrator.__new__(MultiAgentOrchestrator)
    result = orchestrator._integrate(
        a1_result={"case_focus": [{"focus": "争点"}]},
        a2_result={"legal_analysis": [{
            "focus_index": 1,
            "point": "有依据的结论 [2]",
            "citations": [2],
        }]},
        a3_result={"validation": [
            {"point_index": 1, "citation_id": 2, "valid": True},
        ]},
        a4_result={},
        citations=[_citation(1, "第一条", "甲"), _citation(2, "第二条", "乙")],
    )

    assert result["legal_analysis"] == [{"point": "有依据的结论 [1]", "citations": [1]}]
    assert result["citations"][0]["article_no"] == "第二条"
    assert 0.0 < result["quality_score"] <= 1.0
    assert "confidence" not in result


def test_missing_validation_fails_closed():
    orchestrator = MultiAgentOrchestrator.__new__(MultiAgentOrchestrator)
    result = orchestrator._integrate(
        a1_result={"case_focus": [{"focus": "争点"}]},
        a2_result={"legal_analysis": [{"point": "结论 [1]", "citations": [1]}]},
        a3_result={"validation": []},
        a4_result={},
        citations=[_citation(1, "第一条", "甲")],
    )
    assert result["legal_analysis"] == []
    assert result["quality_score"] == 0.0

