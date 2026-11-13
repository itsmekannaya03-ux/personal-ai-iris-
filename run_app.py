"""
Iris AI - Native Desktop Application Window
Launches Iris in a dedicated, standalone application window (no browser tabs, no address bar).
"""

import sys
import os
import time
import urllib.request
import subprocess

CANDIDATE_PORTS = [3001, 3002, 3000]
BACKEND_URL = "http://127.0.0.1:5743/health"


def wait_for_backend(timeout=15):
    """Wait for Iris backend API (:5743) to respond."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(BACKEND_URL, timeout=1) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.5)
    return False


def find_ui_url(timeout=25):
    """Wait for Vite frontend dev server to become reachable."""
    start = time.time()
    while time.time() - start < timeout:
        for port in CANDIDATE_PORTS:
            url = f"http://127.0.0.1:{port}"
            try:
                with urllib.request.urlopen(url, timeout=0.8) as resp:
                    if resp.status == 200:
                        return url
            except Exception:
                pass
        time.sleep(0.5)
    return f"http://127.0.0.1:{CANDIDATE_PORTS[0]}"


def launch_native(target_url):
    try:
        import webview
        window = webview.create_window(
            title="Iris AI",
            url=target_url,
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


def launch_app_mode(target_url):
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
            proc = subprocess.Popen([path, f"--app={target_url}", "--window-size=1280,820"])
            proc.wait()
            return True

    proc = subprocess.Popen(f'msedge.exe --app="{target_url}"', shell=True)
    proc.wait()
    return True


def cleanup_services():
    """When the user closes the Iris Desktop window, cleanly stop background services."""
    try:
        # Free ports 5743 and 3001
        kill_script = (
            "[subprocess.run(f'taskkill /F /PID {p[-1]}', shell=True, capture_output=True) "
            "for port in (5743, 3001) "
            "for l in subprocess.run('netstat -ano', shell=True, capture_output=True, text=True).stdout.splitlines() "
            "if f':{port}' in l and 'LISTENING' in l and (p := l.strip().split()) and p[-1].isdigit() and p[-1] != '0']"
        )
        exec(f"import subprocess; {kill_script}")
    except Exception:
        pass


if __name__ == "__main__":
    wait_for_backend(timeout=10)
    resolved_url = find_ui_url(timeout=20)
    print(f"[INFO] Launching Iris UI at {resolved_url}...")
    try:
        if not launch_native(resolved_url):
            launch_app_mode(resolved_url)
    finally:
        cleanup_services()

