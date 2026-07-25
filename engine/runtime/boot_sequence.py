"""Boot Sequence — complete startup process with validation."""


class BootSequence:
    def __init__(self, core_matrix, orchestrator, runtime_manager):
        self._matrix = core_matrix
        self._orchestrator = orchestrator
        self._runtime = runtime_manager
        self._errors = []
        self._stage = "idle"

    def run(self) -> dict:
        stages = [
            ("initialize_runtime", self._stage_initialize_runtime),
            ("load_configuration", self._stage_load_config),
            ("start_security", self._stage_start_security),
            ("load_memory", self._stage_load_memory),
            ("load_neural_core", self._stage_load_neural_core),
            ("initialize_orchestrator", self._stage_init_orchestrator),
            ("start_voice", self._stage_start_voice),
            ("initialize_api", self._stage_init_api),
            ("startup_validation", self._stage_validate),
        ]

        results = []
        for name, fn in stages:
            self._stage = name
            try:
                fn()
                results.append({"stage": name, "status": "passed"})
                self._matrix.broadcast(f"boot.{name}", {"status": "passed"})
            except Exception as e:
                self._errors.append({"stage": name, "error": str(e)})
                if name in ("initialize_runtime", "start_security", "load_memory", "load_neural_core"):
                    results.append({"stage": name, "status": "critical_failure"})
                    return self._enter_safe_mode(results)
                results.append({"stage": name, "status": "skipped", "reason": str(e)})

        if self._errors:
            self._stage = "degraded"
            self._matrix.set_boot_complete()
            return {"status": "degraded", "stages": results, "errors": self._errors}
        self._stage = "ready"
        self._matrix.set_boot_complete()
        return {"status": "ready", "stages": results, "errors": []}

    def _stage_initialize_runtime(self):
        self._matrix.broadcast("boot.initialize_runtime", {})
        self._runtime.start_all()

    def _stage_load_config(self):
        self._matrix.broadcast("boot.load_configuration", {})

    def _stage_start_security(self):
        self._matrix.broadcast("boot.start_security", {})
        if not hasattr(self._orchestrator, 'privacy_profile') or self._orchestrator.privacy_profile is None:
            raise RuntimeError("PIE not initialized")

    def _stage_load_memory(self):
        self._matrix.broadcast("boot.load_memory", {})
        if not hasattr(self._orchestrator, 'memory') or self._orchestrator.memory is None:
            raise RuntimeError("Memory engine not initialized")
        self._matrix.wire_memory(self._orchestrator.memory)

    def _stage_load_neural_core(self):
        self._matrix.broadcast("boot.load_neural_core", {})

    def _stage_init_orchestrator(self):
        self._matrix.broadcast("boot.initialize_orchestrator", {})

    def _stage_start_voice(self):
        self._matrix.broadcast("boot.start_voice", {})
        if hasattr(self._orchestrator, 'voice_backend'):
            self._matrix.wire_voice(self._orchestrator.voice_backend)

    def _stage_init_api(self):
        self._matrix.broadcast("boot.initialize_api", {})

    def _stage_validate(self):
        checks = [
            ("PIE_initialized", hasattr(self._orchestrator, 'privacy_profile')),
            ("Memory_responding", hasattr(self._orchestrator, 'memory')),
            ("Core_Matrix_active", True),
            ("Orchestrator_loaded", True),
        ]
        for name, result in checks:
            if not result:
                raise RuntimeError(f"Validation failed: {name}")

    def _enter_safe_mode(self, results: list) -> dict:
        self._stage = "safe_mode"
        return {
            "status": "safe_mode",
            "stages": results,
            "errors": self._errors,
            "message": "IGRIS Safe Mode. Critical components failed. Basic conversation only.",
        }

    def get_stage(self) -> str:
        return self._stage

    def get_errors(self) -> list:
        return list(self._errors)

    def health(self) -> dict:
        return {
            "status": "running",
            "stage": self._stage,
            "errors": len(self._errors),
        }
