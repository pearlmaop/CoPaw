#!/usr/bin/env python3
"""Evaluate pipeline against golden outputs."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from copaw_tool.domain.rules.rule_parser import RuleParser
from copaw_tool.domain.generators.pseudocode_renderer import PseudocodeRenderer
from copaw_tool.domain.rules.terminology_normalizer import TerminologyNormalizer

FIXTURES_DIR = Path(__file__).parent.parent / "data" / "fixtures"
GOLDEN_DIR = Path(__file__).parent.parent / "data" / "golden"


def evaluate():
    fixture_path = FIXTURES_DIR / "sample_strategy.txt"
    golden_path = GOLDEN_DIR / "sample_pseudocode.txt"

    if not fixture_path.exists():
        print(f"ERROR: Fixture not found: {fixture_path}")
        sys.exit(1)

    text = fixture_path.read_text(encoding="utf-8")
    parser = RuleParser()
    normalizer = TerminologyNormalizer()
    renderer = PseudocodeRenderer()

    ir = parser.parse_from_text(text)
    ir = normalizer.normalize_ir(ir)
    pseudocode = renderer.render(ir)

    print("Generated pseudocode:")
    print("-" * 40)
    print(pseudocode)
    print("-" * 40)

    if golden_path.exists():
        golden = golden_path.read_text(encoding="utf-8")
        print("\nGolden pseudocode:")
        print("-" * 40)
        print(golden)
        print("-" * 40)
        if pseudocode.strip() == golden.strip():
            print("\n✅ PASS: Output matches golden!")
        else:
            print("\n⚠️  Output differs from golden (structural check)")
    else:
        print(f"\nSaving as new golden: {golden_path}")
        golden_path.parent.mkdir(parents=True, exist_ok=True)
        golden_path.write_text(pseudocode, encoding="utf-8")


if __name__ == "__main__":
    evaluate()
