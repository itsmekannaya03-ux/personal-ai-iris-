"""Planning Engine — handles multi-step task execution."""


class PlanningEngine:
    def __init__(self):
        self._active_plans = {}

    def should_activate(self, message: str, intent: str) -> bool:
        complex_keywords = ["and then", "first", "then", "finally", "research",
                            "write a report", "compare", "multiple steps", "plan"]
        return any(kw in message.lower() for kw in complex_keywords)

    def create_plan(self, goal: str, context: dict = None) -> dict:
        plan_id = f"plan_{hash(goal) % 10000:04d}"
        steps = [
            {"step": 1, "action": "Analyze request", "module": "neural_core", "status": "pending"},
            {"step": 2, "action": "Identify required modules", "module": "planner", "status": "pending"},
            {"step": 3, "action": "Execute subtasks", "module": "inference", "status": "pending"},
            {"step": 4, "action": "Compile results", "module": "neural_core", "status": "pending"},
            {"step": 5, "action": "Return to user", "module": "neural_core", "status": "pending"},
        ]
        plan = {
            "plan_id": plan_id,
            "goal": goal,
            "steps": steps,
            "current_step": 0,
            "status": "created",
            "results": [],
            "dependencies": [],
        }
        self._active_plans[plan_id] = plan
        return plan

    def get_next_step(self, plan_id: str) -> dict | None:
        plan = self._active_plans.get(plan_id)
        if not plan or plan["current_step"] >= len(plan["steps"]):
            return None
        step = plan["steps"][plan["current_step"]]
        step["status"] = "in_progress"
        return step

    def complete_step(self, plan_id: str, result: dict):
        plan = self._active_plans.get(plan_id)
        if not plan:
            return
        step = plan["steps"][plan["current_step"]]
        step["status"] = "complete"
        plan["results"].append(result)
        plan["current_step"] += 1
        if plan["current_step"] >= len(plan["steps"]):
            plan["status"] = "complete"

    def fail_step(self, plan_id: str, error: str):
        plan = self._active_plans.get(plan_id)
        if not plan:
            return
        plan["steps"][plan["current_step"]]["status"] = "failed"
        plan["status"] = "failed"
        plan["error"] = error

    def get_plan(self, plan_id: str) -> dict | None:
        return self._active_plans.get(plan_id)

    def list_active_plans(self) -> list:
        return [p for p in self._active_plans.values() if p["status"] in ("created", "in_progress")]
