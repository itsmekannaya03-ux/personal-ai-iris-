"""
Iris AI - Native Desktop Application Window
Launches Iris in a dedicated, standalone application window (no browser tabs, no address bar).
"""

import sys
import os
import time
import urllib.request
import subprocess

PORT = 3001
URL = f"http://localhost:{PORT}"


def wait_for_ui(timeout=25):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(URL, timeout=1) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.5)
    return False


def launch_native():
    try:
        import webview
        window = webview.create_window(
            title="Iris AI",
            url=URL,
            width=1280,
            height=820,
            min_size=(900, 600),
            text_select=True,
            confirm_close=False,
        )
        webview.start(private_mode=False)
        return True
    except Exception as e:
        print(f"[WARN] Native webview failed ({e}), falling back to standalone App Mode...")
        return False


def launch_app_mode():
    edge_paths = [
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
    ]
    chrome_paths = [
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]

    for path in edge_paths + chrome_paths:
        if os.path.isfile(path):
            subprocess.Popen([path, f"--app={URL}", "--window-size=1280,820"])
            return True

    subprocess.Popen(f'start "" msedge.exe --app="{URL}"', shell=True)
    return True


if __name__ == "__main__":
    wait_for_ui(timeout=20)
    if not launch_native():
        launch_app_mode()
