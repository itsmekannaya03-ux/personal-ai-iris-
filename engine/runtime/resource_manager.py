"""Resource Manager — ensures IGRIS doesn't overload the user's PC."""

import os


class ResourceManager:
    def __init__(self):
        self._limits = {
            "ram_percent": 40,
            "model_ram_percent": 60,
            "memory_ram_percent": 15,
            "cpu_idle_percent": 2,
            "cpu_active_percent": 40,
            "cpu_background_percent": 5,
            "disk_alert_gb": 5,
            "disk_block_gb": 1,
        }

    def start(self):
        pass

    def stop(self):
        pass

    def check_ram(self) -> dict:
        try:
            import psutil
            total = psutil.virtual_memory().total // (1024 * 1024)
            available = psutil.virtual_memory().available // (1024 * 1024)
            used = total - available
            igris_budget = int(total * self._limits["ram_percent"] / 100)
            return {
                "total_mb": total,
                "available_mb": available,
                "used_mb": used,
                "igris_budget_mb": igris_budget,
                "model_budget_mb": int(igris_budget * self._limits["model_ram_percent"] / 100),
                "within_limits": used <= igris_budget,
            }
        except Exception:
            return {"total_mb": 0, "available_mb": 0, "within_limits": True}

    def check_cpu(self) -> dict:
        try:
            import psutil
            return {"cpu_percent": psutil.cpu_percent(interval=0.1)}
        except Exception:
            return {"cpu_percent": 0}

    def check_disk(self) -> dict:
        try:
            import psutil
            free_gb = psutil.disk_usage("/").free // (1024 * 1024 * 1024)
            return {
                "free_gb": free_gb,
                "alert": free_gb < self._limits["disk_alert_gb"],
                "block": free_gb < self._limits["disk_block_gb"],
            }
        except Exception:
            return {"free_gb": 99, "alert": False, "block": False}

    def get_all(self) -> dict:
        return {
            "ram": self.check_ram(),
            "cpu": self.check_cpu(),
            "disk": self.check_disk(),
            "limits": self._limits,
        }

    def get_limit(self, key: str) -> int:
        return self._limits.get(key, 0)

    def set_limit(self, key: str, value: int):
        if key in self._limits:
            self._limits[key] = value

    def health(self) -> dict:
        return {"status": "running", **self.get_all()}
