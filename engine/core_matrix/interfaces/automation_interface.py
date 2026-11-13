"""Automation Interface — connects Neural Core to PC Control Engine."""


class AutomationInterface:
    def __init__(self, pc_control):
        self._pc = pc_control
        self._enabled = True

    def open_app(self, name: str) -> dict:
        return self._execute(f"open {name}")

    def close_app(self, name: str) -> dict:
        return self._execute(f"close {name}")

    def click(self, target: str) -> dict:
        return self._execute(f"click {target}")

    def type_text(self, text: str) -> dict:
        return self._execute(f"type {text}")

    def screenshot(self) -> dict:
        return self._execute("screenshot")

    def read_file(self, path: str) -> dict:
        return self._execute(f"read {path}")

    def write_file(self, path: str, content: str) -> dict:
        return self._execute(f"write {path} {content[:50]}...")

    def delete_file(self, path: str, confirmed: bool = False) -> dict:
        if not confirmed:
            return {"status": "blocked", "reason": "Destructive action requires confirmation"}
        return self._execute(f"delete {path}")

    def create_folder(self, path: str) -> dict:
        return self._execute(f"mkdir {path}")

    def search_files(self, query: str) -> dict:
        return self._execute(f"search {query}")

    def run_command(self, command: str) -> dict:
        return self._execute(command)

    def browse_web(self, url: str = None) -> dict:
        return {"status": "not_implemented", "result": "Web browsing not available"}

    def set_setting(self, setting: str, value: str) -> dict:
        return self._execute(f"set {setting} {value}")

    def kill_process(self, name: str) -> dict:
        return self._execute(f"kill {name}")

    def get_system_resources(self) -> dict:
        return self._execute("resources")

    def _execute(self, command: str) -> dict:
        if not self._enabled:
            return {"status": "blocked", "reason": "Automation disabled by user"}
        try:
            result = self._pc.execute(command)
            return {"status": "success", "result": str(result)}
        except Exception as e:
            return {"status": "error", "reason": str(e)}

    def enable(self):
        self._enabled = True

    def disable(self):
        self._enabled = False
