from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SkillScanResult:
    safe: bool
    findings: list[str]


class SkillScanner:
    def scan(self, text: str) -> SkillScanResult:
        lowered = text.lower()
        patterns = ["subprocess", "os.system", "eval(", "exec("]
        findings = [p for p in patterns if p in lowered]
        return SkillScanResult(safe=len(findings) == 0, findings=findings)
