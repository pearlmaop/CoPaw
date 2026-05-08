import pytest
from pathlib import Path
from copaw_tool.domain.rules.rule_parser import RuleParser
from copaw_tool.domain.generators.pseudocode_renderer import PseudocodeRenderer
from copaw_tool.domain.rules.terminology_normalizer import TerminologyNormalizer

FIXTURES_DIR = Path(__file__).parent.parent.parent / "data" / "fixtures"
GOLDEN_DIR = Path(__file__).parent.parent.parent / "data" / "golden"


def test_golden_output_exists():
    """Ensure golden fixture files exist."""
    assert (FIXTURES_DIR / "sample_strategy.txt").exists(), "Sample strategy fixture not found"
    assert (GOLDEN_DIR / "sample_pseudocode.txt").exists(), "Golden pseudocode file not found"


def test_pipeline_produces_output():
    """Test that the pipeline produces output from the fixture."""
    fixture = (FIXTURES_DIR / "sample_strategy.txt").read_text(encoding="utf-8")
    parser = RuleParser()
    normalizer = TerminologyNormalizer()
    renderer = PseudocodeRenderer()

    ir = parser.parse_from_text(fixture)
    ir = normalizer.normalize_ir(ir)
    pseudocode = renderer.render(ir)

    assert isinstance(pseudocode, str)
    assert len(pseudocode) > 0


def test_golden_pseudocode_match():
    """Test output matches golden pseudocode (structure check)."""
    fixture = (FIXTURES_DIR / "sample_strategy.txt").read_text(encoding="utf-8")
    golden = (GOLDEN_DIR / "sample_pseudocode.txt").read_text(encoding="utf-8")

    parser = RuleParser()
    renderer = PseudocodeRenderer()

    ir = parser.parse_from_text(fixture)
    pseudocode = renderer.render(ir)

    # Check structural elements are present
    assert "if" in pseudocode
    assert "then" in pseudocode
    # Check golden file has same structural elements
    assert "if" in golden
    assert "then" in golden
