"""System monitoring (psutil): CPU, RAM, disk, processes, kill process."""

import logging
import time
from typing import Optional

logger = logging.getLogger("iris.hands.system_monitor")


class SystemMonitor:
    """System stats and process control via psutil."""

    def __init__(self):
        self._has_psutil = False
        try:
            import psutil  # noqa: F401
            self._has_psutil = True
        except ImportError:
            logger.warning("psutil not installed - system monitoring unavailable")
        logger.info(f"SystemMonitor ready (psutil={self._has_psutil})")

    def stats(self) -> dict:
        if not self._has_psutil:
            return {"success": False, "error": "psutil not installed"}
        import psutil
        try:
            cpu = psutil.cpu_percent(interval=0.4)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage("C:\\" if __import__("os").name == "nt" else "/")
            return {
                "success": True,
                "cpu_percent": cpu,
                "cpu_cores": psutil.cpu_count(logical=True),
                "ram_percent": mem.percent,
                "ram_used_gb": round(mem.used / 1024 ** 3, 2),
                "ram_total_gb": round(mem.total / 1024 ** 3, 2),
                "disk_percent": disk.percent,
                "disk_free_gb": round(disk.free / 1024 ** 3, 2),
                "processes": len(psutil.pids()),
                "uptime_seconds": int(time.time() - psutil.boot_time()),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def top_processes(self, limit: int = 8) -> dict:
        if not self._has_psutil:
            return {"success": False, "error": "psutil not installed"}
        import psutil
        try:
            procs = []
            for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
                try:
                    info = p.info
                    procs.append({
                        "pid": info["pid"],
                        "name": info["name"],
                        "cpu": round(info["cpu_percent"] or 0, 1),
                        "ram": round(info["memory_percent"] or 0, 1),
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            procs.sort(key=lambda x: x["cpu"], reverse=True)
            return {"success": True, "processes": procs[:limit]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def kill_process(self, name: str, pid: Optional[int] = None) -> dict:
        if not self._has_psutil:
            return {"success": False, "error": "psutil not installed"}
        import psutil
        try:
            killed = []
            for p in psutil.process_iter(["pid", "name"]):
                try:
                    if pid is not None and p.info["pid"] != pid:
                        continue
                    if name and (name.lower() not in (p.info["name"] or "").lower()):
                        continue
                    if name or pid is not None:
                        p.kill()
                        killed.append({"pid": p.info["pid"], "name": p.info["name"]})
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            if killed:
                return {"success": True, "killed": killed}
            return {"success": False, "error": f"No process matching '{name}'"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_status(self) -> dict:
        return {"psutil": self._has_psutil}

    def get_stats(self) -> dict:
        return self.stats()

    def get_cpu_usage(self) -> float:
        st = self.stats()
        return st.get("cpu_percent", 0.0)

    def get_memory_usage(self) -> dict:
        st = self.stats()
        return {"percent": st.get("ram_percent", 0.0), "used_gb": st.get("ram_used_gb", 0.0)}

    def get_battery_status(self) -> dict:
        if not self._has_psutil:
            return {"percent": 0, "charging": False}
        import psutil
        try:
            batt = psutil.sensors_battery()
            if batt:
                return {"percent": batt.percent, "charging": batt.power_plugged, "secsleft": batt.secsleft}
        except Exception:
            pass
        return {"percent": 100, "charging": True}