"""Runtime Interface — connects Core Matrix to Runtime."""


class RuntimeInterface:
    def __init__(self):
        self._services = {}

    def register_service(self, name: str, service: object):
        self._services[name] = service

    def check_health(self, service_name: str = None) -> dict:
        if service_name:
            svc = self._services.get(service_name)
            if not svc:
                return {"status": "not_found", "service": service_name}
            health = getattr(svc, "health", lambda: {"status": "unknown"})
            return health()
        results = {}
        for name, svc in self._services.items():
            health = getattr(svc, "health", lambda: {"status": "unknown"})
            try:
                results[name] = health()
            except Exception:
                results[name] = {"status": "error"}
        return results

    def start_service(self, name: str) -> dict:
        svc = self._services.get(name)
        if not svc:
            return {"status": "error", "reason": "Service not found"}
        start = getattr(svc, "start", None)
        if start:
            try:
                start()
                return {"status": "started", "service": name}
            except Exception as e:
                return {"status": "error", "reason": str(e)}
        return {"status": "error", "reason": "No start method"}

    def stop_service(self, name: str) -> dict:
        svc = self._services.get(name)
        if not svc:
            return {"status": "error", "reason": "Service not found"}
        stop = getattr(svc, "stop", None)
        if stop:
            try:
                stop()
                return {"status": "stopped", "service": name}
            except Exception as e:
                return {"status": "error", "reason": str(e)}
        return {"status": "error", "reason": "No stop method"}

    def restart_service(self, name: str) -> dict:
        self.stop_service(name)
        return self.start_service(name)

    def get_resources(self) -> dict:
        try:
            import psutil
            return {
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "ram_mb": psutil.virtual_memory().used // (1024 * 1024),
                "ram_total_mb": psutil.virtual_memory().total // (1024 * 1024),
                "disk_free_gb": psutil.disk_usage("/").free // (1024 * 1024 * 1024),
            }
        except Exception:
            return {"cpu_percent": 0, "ram_mb": 0, "ram_total_mb": 0, "disk_free_gb": 0}

    def trigger_recovery(self, component: str) -> dict:
        return {"status": "recovery_triggered", "component": component}

    def get_diagnostics(self) -> dict:
        resources = self.get_resources()
        resources["services"] = self.check_health()
        resources["status"] = "running"
        return resources
