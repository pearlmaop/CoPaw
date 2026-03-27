import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from copaw_tool.application.workflows.nodes.ingest_node import ingest_node
from copaw_tool.application.workflows.nodes.normalize_node import normalize_node
from copaw_tool.application.workflows.nodes.ir_build_node import ir_build_node
from copaw_tool.application.workflows.nodes.pseudocode_node import pseudocode_node
from copaw_tool.application.workflows.nodes.check_node import check_node
from copaw_tool.application.workflows.nodes.report_node import report_node


def test_ingest_node_valid_file(tmp_path):
    fake_file = tmp_path / "test.txt"
    fake_file.write_text("content")
    state = {"file_paths": [str(fake_file)], "errors": []}
    result = ingest_node(state)
    assert str(fake_file) in result["file_paths"]
    assert result["errors"] == []


def test_ingest_node_missing_file():
    state = {"file_paths": ["/nonexistent/file.pdf"], "errors": []}
    result = ingest_node(state)
    assert "/nonexistent/file.pdf" not in result["file_paths"]
    assert len(result["errors"]) > 0


def test_normalize_node_combines_text():
    state = {
        "extracted_segments": [
            {"text": "如果 充电状态==充电中", "source": "file1"},
            {"text": "那么 充电指示灯==亮起", "source": "file1"},
        ],
        "errors": [],
    }
    result = normalize_node(state)
    assert "如果" in result["normalized_text"] or "充电" in result["normalized_text"]


def test_ir_build_node_without_llm():
    state = {
        "normalized_text": "如果 充电状态==充电中;\n那么 充电指示灯==亮起;",
        "llm_client": None,
        "errors": [],
    }
    result = ir_build_node(state)
    assert "strategy_ir" in result
    assert result["strategy_ir"] is not None


def test_ir_build_node_with_llm():
    mock_client = MagicMock()
    mock_client.extract_strategy_ir.return_value = {
        "strategy_id": "STRAT_001",
        "rules": [
            {
                "rule_id": "R001",
                "op": "all",
                "conditions": [{"lhs": "A", "cmp": "==", "rhs": "B"}],
                "actions": [{"lhs": "C", "op": "==", "rhs": "D"}],
            }
        ],
    }
    state = {
        "normalized_text": "如果 A==B;\n那么 C==D;",
        "llm_client": mock_client,
        "errors": [],
    }
    result = ir_build_node(state)
    assert result["strategy_ir"]["strategy_id"] == "STRAT_001"


def test_pseudocode_node():
    state = {
        "strategy_ir": {
            "strategy_id": "STRAT_001",
            "rules": [
                {
                    "rule_id": "R001",
                    "op": "all",
                    "conditions": [{"lhs": "A", "cmp": "==", "rhs": "B"}],
                    "actions": [{"lhs": "C", "op": "==", "rhs": "D"}],
                }
            ],
        },
        "errors": [],
    }
    result = pseudocode_node(state)
    assert "pseudocode" in result
    assert "if all" in result["pseudocode"]


def test_check_node():
    state = {
        "strategy_ir": {
            "strategy_id": "STRAT_001",
            "rules": [
                {
                    "rule_id": "R001",
                    "op": "all",
                    "conditions": [{"lhs": "A", "cmp": "==", "rhs": "B"}],
                    "actions": [{"lhs": "C", "op": "==", "rhs": "D"}],
                }
            ],
        },
        "errors": [],
    }
    result = check_node(state)
    assert "completeness_report" in result
    assert "total_rules" in result["completeness_report"]


def test_report_node():
    state = {
        "pseudocode": "if all {\n    A == B;\n}\nthen {\n    C == D;\n}",
        "completeness_report": {"strategy_id": "STRAT_001", "total_rules": 1},
        "strategy_ir": {"strategy_id": "STRAT_001"},
        "errors": [],
    }
    result = report_node(state)
    assert "final_output" in result
    assert result["final_output"]["pseudocode"] == state["pseudocode"]


def test_ir_build_node_llm_fallback():
    """Test that LLM failure falls back to rule parser."""
    mock_client = MagicMock()
    mock_client.extract_strategy_ir.side_effect = Exception("API error")
    state = {
        "normalized_text": "如果 充电状态==充电中;\n那么 充电指示灯==亮起;",
        "llm_client": mock_client,
        "errors": [],
    }
    result = ir_build_node(state)
    assert "strategy_ir" in result
    assert len(result["errors"]) > 0  # error logged
