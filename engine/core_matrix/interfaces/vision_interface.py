"""Vision Interface — connects Neural Core to Vision Engine."""


class VisionInterface:
    def __init__(self):
        self._enabled = True
        self._camera_permitted = False

    def capture_screenshot(self) -> dict:
        return {"status": "not_implemented", "content": "Vision module not loaded"}

    def analyze_screen(self) -> dict:
        return {"status": "not_implemented", "content": ""}

    def ocr(self, image_path: str = None) -> dict:
        return {"status": "not_implemented", "text": ""}

    def detect_ui_elements(self) -> dict:
        return {"status": "not_implemented", "elements": []}

    def watch_for_changes(self, region: str = "full_screen") -> dict:
        return {"status": "not_implemented", "watching": False}

    def describe(self) -> dict:
        return {"status": "not_implemented", "description": ""}

    def find_element(self, target: str) -> dict:
        return {"status": "not_implemented", "found": False}

    def take_photo(self) -> dict:
        if not self._camera_permitted:
            return {"status": "permission_denied", "reason": "Camera access not granted"}
        return {"status": "not_implemented", "image": None}

    def analyze_image(self, path: str) -> dict:
        return {"status": "not_implemented", "analysis": ""}

    def set_camera_permission(self, permitted: bool):
        self._camera_permitted = permitted

    def enable(self):
        self._enabled = True

    def disable(self):
        self._enabled = False

    @property
    def is_enabled(self) -> bool:
        return self._enabled
