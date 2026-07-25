"""Plugin Interface — manages all plugin communication."""


class PluginInterface:
    def __init__(self):
        self._plugins = {}
        self._permissions = {}
        self._sandboxes = {}

    def register(self, plugin_id: str, plugin_obj: object, permissions: list = None):
        self._plugins[plugin_id] = plugin_obj
        self._permissions[plugin_id] = permissions or []
        return {"status": "registered", "plugin_id": plugin_id}

    def load(self, plugin_id: str) -> dict:
        if plugin_id not in self._plugins:
            return {"status": "error", "reason": "Plugin not registered"}
        try:
            plugin = self._plugins[plugin_id]
            if hasattr(plugin, "load"):
                plugin.load()
            return {"status": "loaded", "plugin_id": plugin_id}
        except Exception as e:
            return {"status": "error", "reason": str(e)}

    def unload(self, plugin_id: str) -> dict:
        if plugin_id not in self._plugins:
            return {"status": "error", "reason": "Plugin not found"}
        try:
            plugin = self._plugins[plugin_id]
            if hasattr(plugin, "unload"):
                plugin.unload()
            return {"status": "unloaded", "plugin_id": plugin_id}
        except Exception:
            return {"status": "error", "reason": "Unload failed"}

    def call(self, plugin_id: str, function: str, args: dict = None, timeout_ms: int = 5000) -> dict:
        plugin = self._plugins.get(plugin_id)
        if not plugin:
            return {"status": "error", "reason": "Plugin not found"}
        fn = getattr(plugin, function, None)
        if not fn:
            return {"status": "error", "reason": f"Function '{function}' not found"}
        try:
            result = fn(**(args or {}))
            return {"status": "success", "result": result}
        except Exception as e:
            return {"status": "error", "reason": str(e)}

    def check_permissions(self, plugin_id: str, required: list) -> dict:
        allowed = self._permissions.get(plugin_id, [])
        missing = [p for p in required if p not in allowed]
        if missing:
            return {"status": "denied", "missing": missing}
        return {"status": "approved"}

    def list_plugins(self) -> list:
        return [{"id": pid, "permissions": self._permissions.get(pid, [])} for pid in self._plugins]

    def remove(self, plugin_id: str) -> dict:
        self._plugins.pop(plugin_id, None)
        self._permissions.pop(plugin_id, None)
        return {"status": "removed", "plugin_id": plugin_id}

    def health(self, plugin_id: str = None) -> dict:
        if plugin_id:
            return {"status": "running" if plugin_id in self._plugins else "not_found"}
        return {"total": len(self._plugins), "loaded": len(self._plugins)}
