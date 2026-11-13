"""Skills Interface — manages all skill module communication."""


class SkillsInterface:
    def __init__(self):
        self._skills = {}
        self._active = {}

    def activate(self, skill_id: str) -> dict:
        if skill_id not in self._skills:
            return {"status": "error", "reason": "Skill not installed"}
        self._active[skill_id] = True
        return {"status": "activated", "skill_id": skill_id}

    def deactivate(self, skill_id: str) -> dict:
        self._active.pop(skill_id, None)
        return {"status": "deactivated", "skill_id": skill_id}

    def call(self, skill_id: str, function: str, args: dict = None) -> dict:
        skill = self._skills.get(skill_id)
        if not skill:
            return {"status": "error", "reason": "Skill not found"}
        if not self._active.get(skill_id, False):
            return {"status": "error", "reason": "Skill not active"}
        fn = getattr(skill, function, None)
        if not fn:
            return {"status": "error", "reason": f"Function '{function}' not found"}
        try:
            result = fn(**(args or {}))
            return {"status": "success", "result": result}
        except Exception as e:
            return {"status": "error", "reason": str(e)}

    def install(self, skill_id: str, skill_obj: object) -> dict:
        self._skills[skill_id] = skill_obj
        self._active[skill_id] = True
        return {"status": "installed", "skill_id": skill_id}

    def remove(self, skill_id: str) -> dict:
        self._skills.pop(skill_id, None)
        self._active.pop(skill_id, None)
        return {"status": "removed", "skill_id": skill_id}

    def list_skills(self) -> list:
        return [{"id": sid, "active": self._active.get(sid, False)} for sid in self._skills]

    def health(self, skill_id: str = None) -> dict:
        if skill_id:
            return {"status": "running" if skill_id in self._skills else "not_found"}
        return {"total": len(self._skills), "active": sum(1 for v in self._active.values() if v)}
