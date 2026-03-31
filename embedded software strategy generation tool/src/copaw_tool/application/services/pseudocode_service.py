from copaw_tool.domain.model.strategy_ir import StrategyIR
from copaw_tool.domain.generators.pseudocode_renderer import PseudocodeRenderer
from copaw_tool.domain.rules.rule_parser import RuleParser
from copaw_tool.domain.rules.terminology_normalizer import TerminologyNormalizer


class PseudocodeService:
    def __init__(self):
        self._renderer = PseudocodeRenderer()
        self._parser = RuleParser()
        self._normalizer = TerminologyNormalizer()

    def generate_from_text(self, text: str, strategy_id: str = "STRAT_001") -> tuple:
        """Returns (pseudocode, ir) tuple."""
        ir = self._parser.parse_from_text(text, strategy_id=strategy_id)
        ir = self._normalizer.normalize_ir(ir)
        pseudocode = self._renderer.render(ir)
        return pseudocode, ir

    def generate_from_ir(self, ir: StrategyIR) -> str:
        return self._renderer.render(ir)
