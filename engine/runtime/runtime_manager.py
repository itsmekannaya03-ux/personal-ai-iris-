"""Runtime Manager — master controller of all runtime services."""


BOOT_ORDER = [
    "configuration_loader",
    "resource_manager",
    "health_monitor",
    "service_registry",
    "background_services",
    "update_manager",
    "recovery_manager",
    "logging",
    "diagnostics",
]


class RuntimeManager:
    def __init__(self):
        self._services = {}
        self._boot_order = BOOT_ORDER
        self._started = False

    def register(self, name: str, service: object):
        self._services[name] = service

    def get(self, name: str) -> object | None:
        return self._services.get(name)

    def start_all(self):
        for name in self._boot_order:
            svc = self._services.get(name)
            if svc and hasattr(svc, "start"):
                try:
                    svc.start()
                except Exception as e:
                    print(f"[Runtime] {name} failed to start: {e}")
        self._started = True

    def stop_all(self):
        for name in reversed(self._boot_order):
            svc = self._services.get(name)
            if svc and hasattr(svc, "stop"):
                try:
                    svc.stop()
                except Exception:
                    pass
        self._started = False

    def restart(self, name: str) -> bool:
        svc = self._services.get(name)
        if not svc:
            return False
        stop = getattr(svc, "stop", None)
        start = getattr(svc, "start", None)
        if stop:
            try:
                stop()
            except Exception:
                pass
        if start:
            try:
                start()
                return True
            except Exception:
                return False
        return True

    def health(self) -> dict:
        results = {}
        for name, svc in self._services.items():
            h = getattr(svc, "health", lambda: {"status": "unknown"})
            try:
                results[name] = h()
            except Exception:
                results[name] = {"status": "error"}
        return results

    @property
    def is_started(self) -> bool:
        return self._started

    def get_service_names(self) -> list:
        return list(self._services.keys())
