"""Security Interface — connects Core Matrix to PIE."""


class SecurityInterface:
    def __init__(self, pie_router, pie_anonymizer, privacy_profile):
        self._router = pie_router
        self._anonymizer = pie_anonymizer
        self._profile = privacy_profile
        self._log = []

    def classify(self, text: str) -> dict:
        result = self._router.route(text)
        entry = {
            "level": result.privacy_result.level.value,
            "categories": result.privacy_result.categories,
            "can_cloud": result.privacy_result.can_cloud,
            "confidence": result.privacy_result.confidence,
        }
        self._log.append(entry)
        return entry

    def score_risk(self, text: str) -> int:
        result = self._router.route(text)
        return int(result.privacy_result.confidence * 100)

    def anonymize(self, text: str) -> dict:
        try:
            anon = self._anonymizer.anonymize(text)
            return {"anonymized": anon.anonymized, "entity_map": anon.entity_map}
        except Exception:
            return {"anonymized": text, "entity_map": {}}

    def check_profile(self) -> dict:
        return {
            "mode": self._profile.privacy_mode,
            "cloud_enabled": self._profile.is_cloud_enabled(),
            "anonymization": self._profile.anonymization_level,
        }

    def block_request(self, reason: str) -> dict:
        return {"status": "blocked", "reason": reason, "action": "request_denied"}

    def ask_user(self, text: str) -> dict:
        return {"status": "ambiguous", "question": f"This request needs your approval: {text[:100]}", "requires_input": True}

    def log_decision(self, decision: dict):
        self._log.append(decision)

    def audit_log(self) -> list:
        return self._log[-100:]

    def get_stats(self) -> dict:
        return {"total_decisions": len(self._log), "recent": self._log[-10:]}
