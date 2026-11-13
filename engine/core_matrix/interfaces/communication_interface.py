"""Communication Interface — manages all external communication paths."""


class CommunicationInterface:
    def __init__(self):
        self._routes = {}
        self._rate_limits = {}

    def register_route(self, path: str, handler: callable):
        self._routes[path] = handler

    def receive(self, path: str, data: dict, auth_token: str = None) -> dict:
        handler = self._routes.get(path)
        if not handler:
            return {"status": "error", "reason": f"No handler for {path}"}
        try:
            result = handler(data)
            return {"status": "success", "data": result}
        except Exception as e:
            return {"status": "error", "reason": str(e)}

    def authenticate(self, token: str) -> bool:
        if not token:
            return False
        try:
            from pathlib import Path
            key_path = Path.home() / ".iris" / "api.key"
            if key_path.exists():
                stored = key_path.read_text().strip()
                return token == stored
        except Exception:
            pass
        return False

    def authorize(self, token: str, required_permission: str = None) -> dict:
        if not self.authenticate(token):
            return {"status": "denied", "reason": "Authentication failed"}
        return {"status": "authorized"}

    def send_response(self, data: dict) -> dict:
        return {"status": "sent", "data": data}

    def stream_response(self, data_generator) -> dict:
        return {"status": "streaming"}

    def handle_error(self, error: Exception) -> dict:
        return {"status": "error", "message": str(error)}

    def check_rate_limit(self, client_id: str, max_requests: int = 60, window_seconds: int = 60) -> bool:
        import time
        now = time.time()
        if client_id not in self._rate_limits:
            self._rate_limits[client_id] = []
        window = [t for t in self._rate_limits[client_id] if now - t < window_seconds]
        self._rate_limits[client_id] = window
        if len(window) >= max_requests:
            return False
        self._rate_limits[client_id].append(now)
        return True
