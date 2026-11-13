"""
IRIS AI Desktop Overlay Manager

Coordinates the dual-window interface when running backend:
1. Top-Center Floating Mini-Blob Widget:
   - Discreet ~1 cm radius (76px diameter).
   - Frameless, transparent, pinned always on top.
   - Organic canvas fluid blob-in-blob animation syncing with Iris status.
   - Clicking toggles/restores the Main Assistant Window.

2. Main Assistant Window:
   - Animated organic "blob in blob" on top.
   - Full conversational chat box underneath.
   - Custom draggable title bar with minimize (➖) and close/hide (✖) buttons.
   - Full functional parity with the web frontend (commands, coding, hands, automations, speech).
"""

import os
import sys
import logging
import webview

logger = logging.getLogger("iris.overlay")

try:
    import win32gui
    import win32con
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False


class OverlayBridge:
    """
    Bridge exposed to PyWebView JavaScript.
    Note: Internal state attributes must be prefixed with '_' to prevent
    PyWebView's reflection engine from traversing WinForms/COM native objects.
    """
    def __init__(self):
        self._mini_window = None
        self._main_window = None
        self._is_main_visible = True

    def toggle_main(self):
        """Toggle main assistant window visibility."""
        if self._is_main_visible:
            return self.hide_main()
        else:
            return self.show_main()

    def hide_main(self):
        """Hide the main assistant window."""
        logger.info("Hiding main assistant window.")
        if self._main_window:
            try:
                self._main_window.hide()
            except Exception as e:
                logger.warning(f"Error hiding main window: {e}")
            self._is_main_visible = False
        return False

    def minimize_main(self):
        """Minimize the main assistant window."""
        logger.info("Minimizing main assistant window.")
        if self._main_window:
            try:
                self._main_window.minimize()
            except Exception as e:
                logger.warning(f"Error minimizing main window: {e}")
            self._is_main_visible = False
        return False

    def show_main(self):
        """Restore and bring the main assistant window to the foreground."""
        logger.info("Restoring main assistant window.")
        if self._main_window:
            try:
                self._main_window.show()
                self._main_window.restore()
            except Exception as e:
                logger.warning(f"Error showing main window: {e}")
            self._is_main_visible = True

            # Bring to front using Win32 API
            if HAS_WIN32:
                try:
                    hwnd = win32gui.FindWindow(None, "Iris AI Assistant")
                    if hwnd:
                        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                        win32gui.SetForegroundWindow(hwnd)
                except Exception as e:
                    logger.debug(f"win32gui foreground notification: {e}")
        return True

    def close_all(self):
        """Destroy both windows and terminate GUI."""
        logger.info("Closing all overlay windows.")
        try:
            if self._mini_window:
                self._mini_window.destroy()
        except Exception:
            pass
        try:
            if self._main_window:
                self._main_window.destroy()
        except Exception:
            pass

    # Direct In-Process Engine Communication (Bypasses any WebView2 CORS or proxy limits)
    def send_chat(self, message: str, voice: bool = True, is_voice: bool = False, conversation_id: str = None, person_name: str = None):
        """Send chat message to Iris engine backend directly."""
        try:
            import requests
            payload = {"message": message, "voice": bool(voice), "is_voice": bool(is_voice)}
            if conversation_id:
                payload["conversation_id"] = conversation_id
            if person_name:
                payload["person_name"] = person_name
            r = requests.post(
                "http://127.0.0.1:5743/chat",
                json=payload,
                timeout=60
            )
            return r.json()
        except Exception as e:
            logger.error(f"Bridge send_chat error: {e}")
            return {"response": f"⚠️ Could not connect to engine: {e}", "error": str(e)}



    def get_status(self):
        """Get engine status."""
        try:
            import requests
            r = requests.get("http://127.0.0.1:5743/status", timeout=4)
            return r.json()
        except Exception as e:
            return {"status": "offline", "speaking": False}

    def get_vision_last(self):
        """Get latest vision log events."""
        try:
            import requests
            r = requests.get("http://127.0.0.1:5743/vision/last", timeout=4)
            return r.json()
        except Exception:
            return {"events": []}

    def get_presence_hud(self):
        """Get biometric facial presence & emotion state."""
        try:
            import requests
            r = requests.get("http://127.0.0.1:5743/presence/hud-state", timeout=4)
            return r.json()
        except Exception:
            return {"user_detected": False, "emotion": "neutral"}

    def see_screen(self):
        """Trigger instant screen vision capture & AI analysis."""
        try:
            import requests
            r = requests.post("http://127.0.0.1:5743/vision/see", timeout=30)
            return r.json()
        except Exception as e:
            return {"error": str(e), "description": "Screen capture failed"}

    def see_camera(self):
        """Trigger instant camera vision photo & AI analysis."""
        try:
            import requests
            r = requests.post("http://127.0.0.1:5743/vision/camera", timeout=30)
            return r.json()
        except Exception as e:
            return {"error": str(e), "description": "Camera capture failed"}

    def listen_audio(self):
        """Record audio from physical microphone hardware and transcribe via backend Whisper."""
        try:
            import requests
            r = requests.post("http://127.0.0.1:5743/audio/listen", timeout=25)
            return r.json()
        except Exception as e:
            return {"text": "", "error": str(e)}

    def stop_voice(self):
        """Immediately stop voice output on the backend."""
        try:
            import requests
            r = requests.post("http://127.0.0.1:5743/voice/stop", timeout=2)
            return r.json()
        except Exception as e:
            return {"error": str(e)}

    def get_voice_listener_status(self):
        """Get live status of always-on continuous voice listener."""
        try:
            import requests
            r = requests.get("http://127.0.0.1:5743/voice/listener/status", timeout=2)
            return r.json()
        except Exception as e:
            return {"running": False, "error": str(e)}

    def toggle_voice_listener(self):
        """Toggle mute / active on the continuous voice listener."""
        try:
            import requests
            r = requests.post("http://127.0.0.1:5743/voice/listener/toggle", timeout=3)
            return r.json()
        except Exception as e:
            return {"error": str(e)}

    def get_voice_events(self, since=0.0):
        """Get newly transcribed utterances from always-on background listener."""
        try:
            import requests
            r = requests.get(f"http://127.0.0.1:5743/voice/listener/events?since={since}", timeout=3)
            return r.json()
        except Exception as e:
            return {"events": [], "error": str(e)}

    def get_vision_telemetry(self):
        """Get continuous camera + screen intelligence telemetry."""
        try:
            import requests
            r = requests.get("http://127.0.0.1:5743/vision/continuous/telemetry", timeout=3)
            return r.json()
        except Exception as e:
            return {"status": "offline", "error": str(e)}



def launch_overlay():
    """Create windows and start pywebview event loop on the main thread."""
    bridge = OverlayBridge()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    main_html = os.path.join(base_dir, "main_window.html")
    mini_html = os.path.join(base_dir, "mini_blob.html")

    main_url = f"file:///{os.path.abspath(main_html).replace(os.sep, '/')}"
    mini_url = f"file:///{os.path.abspath(mini_html).replace(os.sep, '/')}"

    # Detect screen bounds
    screen_w = 1536
    screen_h = 864
    try:
        screens = webview.screens
        if screens and len(screens) > 0:
            screen_w = screens[0].width
            screen_h = screens[0].height
    except Exception as e:
        logger.warning(f"Could not read screens: {e}")

    # Top-center 1cm radius mini-blob (~76px diameter)
    mini_size = 76
    mini_x = (screen_w - mini_size) // 2
    mini_y = 6

    # Main Assistant Window (right side dock)
    main_w = 440
    main_h = min(710, screen_h - 110)
    main_x = max(20, screen_w - main_w - 24)
    main_y = 54

    bridge._mini_window = webview.create_window(
        title="Iris Mini Orb",
        url=mini_url,
        js_api=bridge,
        width=mini_size,
        height=mini_size,
        x=mini_x,
        y=mini_y,
        frameless=True,
        transparent=True,
        on_top=True,
        resizable=False
    )

    bridge._main_window = webview.create_window(
        title="Iris AI Assistant",
        url=main_url,
        js_api=bridge,
        width=main_w,
        height=main_h,
        x=main_x,
        y=main_y,
        frameless=True,
        transparent=True,
        resizable=True
    )

    logger.info("Starting PyWebView desktop overlay...")
    storage_path = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "IrisAI", "webview")
    os.makedirs(storage_path, exist_ok=True)
    try:
        webview.start(storage_path=storage_path, private_mode=False)
    except TypeError:
        webview.start()


if __name__ == "__main__":
    launch_overlay()
