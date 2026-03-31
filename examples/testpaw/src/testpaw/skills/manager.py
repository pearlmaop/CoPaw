from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass
class Skill:
    skill_id: str
    description: str
    enabled: bool = True


class SkillManager:
    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {
            "summary": Skill(
                skill_id="summary",
                description="Summarize long text into concise bullet points",
                enabled=True,
            ),
            "todo": Skill(
                skill_id="todo",
                description="Transform a goal into actionable todo list",
                enabled=True,
            ),
        }

    def list_skills(self) -> list[dict]:
        return [asdict(s) for s in self._skills.values()]

    def set_enabled(self, skill_id: str, enabled: bool) -> dict:
        if skill_id not in self._skills:
            raise ValueError("skill not found")
        self._skills[skill_id].enabled = enabled
        return asdict(self._skills[skill_id])

    def run(self, skill_id: str, text: str) -> dict:
        if skill_id not in self._skills:
            raise ValueError("skill not found")
        skill = self._skills[skill_id]
        if not skill.enabled:
            return {"ok": False, "result": f"skill '{skill_id}' is disabled"}

        if skill_id == "summary":
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            lines = lines[:5]
            result = "\n".join(f"- {line}" for line in lines) if lines else "- (empty)"
            return {"ok": True, "result": result}

        if skill_id == "todo":
            sentence = text.strip()
            if not sentence:
                return {"ok": True, "result": "1. Clarify goal\n2. Break into tasks\n3. Execute and review"}
            return {
                "ok": True,
                "result": (
                    f"1. Define scope for: {sentence}\n"
                    "2. Split into 3 executable tasks\n"
                    "3. Set deadline and owner\n"
                    "4. Review completion"
                ),
            }

        return {"ok": True, "result": text}
