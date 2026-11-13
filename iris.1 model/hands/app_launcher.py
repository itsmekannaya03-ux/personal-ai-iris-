import glob
import json
import logging
import os
import re
import shutil
import subprocess
import shlex
import time
from typing import Optional

logger = logging.getLogger("iris.hands.app_launcher")

# Detach child process without hiding its GUI window (NEVER use CREATE_NO_WINDOW for GUI apps)
_DETACH = subprocess.CREATE_NEW_PROCESS_GROUP if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP") else 0


class AppLauncher:
    """
    Opens and closes applications.
    Multiple fallback strategies: direct path → start → where → shell.

    IMPORTANT: launching is fire-and-forget — the child never gets the
    parent's stdout/stderr pipes.
    """

    STRATEGIES = ["known", "discovered", "resolve", "start"]

    # Comprehensive registry of common Windows apps, office tools, dev tools, and utilities
    KNOWN_APPS = {
        # Web Browsers
        "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "google chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "microsoft edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "brave": r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        "firefox": "firefox.exe",
        "opera": r"C:\Users\itsme\AppData\Local\Programs\Opera\opera.exe",
        "browser": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        # Terminals & Shells
        "terminal": "wt.exe",
        "terminal emulator": "wt.exe",
        "windows terminal": "wt.exe",
        "cmd": "cmd.exe",
        "command prompt": "cmd.exe",
        "powershell": "powershell.exe",
        # Developer Tools & Editors
        "vscode": r"C:\Users\itsme\AppData\Local\Programs\Microsoft VS Code\Code.exe",
        "vs code": r"C:\Users\itsme\AppData\Local\Programs\Microsoft VS Code\Code.exe",
        "visual studio code": r"C:\Users\itsme\AppData\Local\Programs\Microsoft VS Code\Code.exe",
        "code": r"C:\Users\itsme\AppData\Local\Programs\Microsoft VS Code\Code.exe",
        "visual studio": "devenv.exe",
        "pycharm": "pycharm64.exe",
        "git bash": "git-bash.exe",
        "sublime": "sublime_text.exe",
        # Office & Productivity
        "word": r"C:\Program Files\Microsoft Office\Root\Office16\WINWORD.EXE",
        "winword": r"C:\Program Files\Microsoft Office\Root\Office16\WINWORD.EXE",
        "ms word": r"C:\Program Files\Microsoft Office\Root\Office16\WINWORD.EXE",
        "microsoft word": r"C:\Program Files\Microsoft Office\Root\Office16\WINWORD.EXE",
        "excel": r"C:\Program Files\Microsoft Office\Root\Office16\EXCEL.EXE",
        "ms excel": r"C:\Program Files\Microsoft Office\Root\Office16\EXCEL.EXE",
        "microsoft excel": r"C:\Program Files\Microsoft Office\Root\Office16\EXCEL.EXE",
        "powerpoint": r"C:\Program Files\Microsoft Office\Root\Office16\POWERPNT.EXE",
        "ppt": r"C:\Program Files\Microsoft Office\Root\Office16\POWERPNT.EXE",
        "powerpnt": r"C:\Program Files\Microsoft Office\Root\Office16\POWERPNT.EXE",
        "ms powerpoint": r"C:\Program Files\Microsoft Office\Root\Office16\POWERPNT.EXE",
        "onenote": r"C:\Program Files\Microsoft Office\Root\Office16\ONENOTE.EXE",
        "outlook": "olk.exe",
        # Built-in Windows Accessories & Utilities
        "notepad": "notepad.exe",
        "editor": "notepad.exe",
        "text editor": "notepad.exe",
        "calculator": "calc.exe",
        "calc": "calc.exe",
        "paint": "mspaint.exe",
        "mspaint": "mspaint.exe",
        "snipping tool": "SnippingTool.exe",
        "snip": "SnippingTool.exe",
        "task manager": "taskmgr.exe",
        "taskmgr": "taskmgr.exe",
        "control panel": "control.exe",
        "file explorer": "explorer.exe",
        "explorer": "explorer.exe",
        "files": "explorer.exe",
        "my pc": "explorer.exe",
        "this pc": "explorer.exe",
        "settings": "ms-settings:",
        "settings app": "ms-settings:",
        "camera": "microsoft.windows.camera:",
        "clock": "ms-clock:",
        "alarms": "ms-clock:",
        "timer": "ms-clock:",
        "photos": "ms-photos:",
        "microsoft store": "ms-windows-store:",
        "store": "ms-windows-store:",
        # Media Players & Streaming
        "spotify": "spotify.exe",
        "vlc": "vlc.exe",
        "vlc media player": "vlc.exe",
        "media player": "wmplayer.exe",
        # Social & Communication
        "discord": "discord.exe",
        "telegram": "telegram.exe",
        "zoom": "zoom.exe",
        "whatsapp": r"shell:AppsFolder\5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App",
        "teams": "ms-teams.exe",
        # Creative & Gaming
        "steam": "steam.exe",
        "obs": "obs64.exe",
        "obs studio": "obs64.exe",
        "photoshop": "photoshop.exe",
        "blender": "blender.exe",
    }

    def __init__(self, typo_corrector=None):
        self._running: dict[str, int] = {}
        self._apps: dict[str, dict] = {}
        self._discover()
        if typo_corrector is not None:
            self._typo_corrector = typo_corrector
        else:
            try:
                from core.typo_corrector import TypoCorrector
                self._typo_corrector = TypoCorrector(app_launcher=self)
            except Exception:
                self._typo_corrector = None
        logger.info(f"AppLauncher ready ({len(self._apps)} apps discovered)")

    # ─── App discovery ─────────────────────────────────────────
    @staticmethod
    def _normalize(s: str) -> str:
        s = s.lower().strip()
        for suf in (".lnk", ".exe", ".url", ".appref-ms"):
            if s.endswith(suf):
                s = s[:-len(suf)]
        return re.sub(r"\s+", " ", s).strip()

    def _discover(self):
        """Build a name → app map from Start Menu shortcuts, registry,
        App Paths, and desktop shortcuts. Call once at startup."""
        try:
            for entry in self._start_menu_apps() + self._registry_apps() + self._app_paths_apps() + self._desktop_apps():
                name = entry.get("name", "").strip()
                if not name:
                    continue
                key = self._normalize(name)
                if not key:
                    continue
                exe = entry.get("exe")
                if exe:
                    entry["image"] = self._normalize(os.path.splitext(os.path.basename(exe))[0])
                if key not in self._apps or entry.get("source") == "startmenu":
                    self._apps[key] = entry
                    for alt in self._alias_names(name):
                        self._apps.setdefault(alt, entry)
        except Exception as e:
            logger.warning(f"App discovery failed: {e}")

    def _alias_names(self, name: str) -> list[str]:
        """Extra lookup keys for an app, e.g. 'Visual Studio Code' → 'vscode'."""
        n = name.lower().strip()
        aliases = []
        for token in re.findall(r"[a-z0-9]+", n):
            if len(token) >= 3:
                aliases.append(token)
        if "code" in aliases and "visual" in aliases:
            aliases.append("vscode")
        if "photos" in n and "microsoft" in n:
            aliases.append("photos")
        return aliases

    def _start_menu_apps(self) -> list[dict]:
        apps = []
        roots = [
            os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
            os.path.expandvars(r"%ProgramData%\Microsoft\Windows\Start Menu\Programs"),
        ]
        for root in roots:
            for lnk in glob.glob(os.path.join(root, "**", "*.lnk"), recursive=True):
                apps.append({
                    "name": os.path.splitext(os.path.basename(lnk))[0],
                    "command": lnk,
                    "source": "startmenu",
                })
        return apps

    def _app_paths_apps(self) -> list[dict]:
        """Query the App Paths registry keys to find installed apps like Chrome, VS Code, etc."""
        import winreg
        apps = []
        roots = [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]
        for root in roots:
            try:
                k = winreg.OpenKey(root, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths",
                                   0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
            except OSError:
                continue
            for i in range(winreg.QueryInfoKey(k)[0]):
                try:
                    exe_name = winreg.EnumKey(k, i)
                    s = winreg.OpenKey(k, exe_name)
                    try:
                        exe_path = winreg.QueryValue(s, None) or ""
                        exe_path = exe_path.strip('"').strip()
                        if exe_path and os.path.isfile(exe_path):
                            base = os.path.splitext(exe_name)[0]
                            apps.append({"name": base, "exe": exe_path, "source": "app_paths"})
                    except OSError:
                        pass
                    winreg.CloseKey(s)
                except OSError:
                    continue
            winreg.CloseKey(k)
        return apps

    def _desktop_apps(self) -> list[dict]:
        """Scan user and public desktop for shortcut files."""
        apps = []
        desktops = [
            os.path.join(os.environ.get("USERPROFILE", ""), "Desktop"),
            os.path.join(os.environ.get("PUBLIC", ""), "Desktop"),
        ]
        for desktop in desktops:
            if not os.path.isdir(desktop):
                continue
            for f in os.listdir(desktop):
                if f.lower().endswith(".lnk"):
                    apps.append({
                        "name": os.path.splitext(f)[0],
                        "command": os.path.join(desktop, f),
                        "source": "desktop",
                    })
        return apps

    def _registry_apps(self) -> list[dict]:
        import winreg
        apps = []
        roots = [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]
        views = [winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY]
        for root in roots:
            for view in views:
                try:
                    k = winreg.OpenKey(root, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                                       0, winreg.KEY_READ | view)
                except OSError:
                    continue
                for i in range(winreg.QueryInfoKey(k)[0]):
                    try:
                        sub = winreg.EnumKey(k, i)
                        s = winreg.OpenKey(k, sub)
                        name = icon = loc = None
                        for v, key_name in (("DisplayName", "name"), ("DisplayIcon", "icon"), ("InstallLocation", "loc")):
                            try:
                                val = winreg.QueryValueEx(s, v)[0]
                                if key_name == "name":
                                    name = val
                                elif key_name == "icon":
                                    icon = str(val)
                                else:
                                    loc = str(val)
                            except OSError:
                                pass
                        winreg.CloseKey(s)
                        if not name:
                            continue
                        exe = None
                        if icon:
                            m = re.match(r'"([^"]+\.exe)"', icon) or re.match(r"([^,]+\.exe)", icon)
                            if m:
                                exe = m.group(1)
                        elif loc and os.path.isdir(loc):
                            cands = [os.path.join(loc, f) for f in os.listdir(loc)
                                     if f.lower().endswith(".exe")]
                            cands.sort(key=os.path.getmtime, reverse=True)
                            if cands:
                                exe = cands[0]
                        apps.append({"name": name, "exe": exe, "location": loc, "source": "registry"})
                    except OSError:
                        continue
                winreg.CloseKey(k)
        return apps

    def _resolve_lnk_target(self, lnk: str) -> Optional[str]:
        try:
            r = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 f"$s=(New-Object -ComObject WScript.Shell).CreateShortcut('{lnk.replace(chr(39), chr(39)+chr(39)+chr(39))}'); $s.TargetPath"],
                capture_output=True, text=True, timeout=8,
            )
            t = (r.stdout or "").strip()
            return t if t.lower().endswith(".exe") else None
        except Exception:
            return None

    def _resolve_name(self, app_name: str) -> Optional[dict]:
        key = self._normalize(app_name)
        if not key:
            return None
        if key in self._apps:
            return self._apps[key]
        for k, entry in self._apps.items():
            if key in k or k in key:
                return entry
        # Fuzzy matching with typo tolerance across all discovered apps
        import difflib
        matches = difflib.get_close_matches(key, list(self._apps.keys()), n=1, cutoff=0.65)
        if matches:
            return self._apps[matches[0]]
        return None

    def _normalize_url(self, s: str) -> Optional[str]:
        s = s.strip().lower()
        if not s:
            return None
        # Strip common speech prefixes: "link", "the link", "website", "site", etc.
        s = re.sub(r"^(?:open\s+link\s+|link\s+|the\s+link\s+|open\s+website\s+|website\s+|site\s+|page\s+|url\s+)", "", s, flags=re.IGNORECASE).strip()
        s = re.sub(r"^(?:https?:\/\/)?(?:www\.)?", "", s, flags=re.IGNORECASE).strip()
        if not s:
            return None
        
        # Known sites - map to their proper URLs
        known_sites = {
            "youtube": "https://youtube.com",
            "google": "https://google.com",
            "github": "https://github.com",
            "stackoverflow": "https://stackoverflow.com",
            "reddit": "https://reddit.com",
            "twitter": "https://twitter.com",
            "x": "https://x.com",
            "facebook": "https://facebook.com",
            "instagram": "https://instagram.com",
            "linkedin": "https://linkedin.com",
            "netflix": "https://netflix.com",
            "spotify": "https://spotify.com",
            "twitch": "https://twitch.tv",
            "discord": "https://discord.com",
            "amazon": "https://amazon.com",
            "gmail": "https://mail.google.com",
            "outlook": "https://outlook.live.com",
            "drive": "https://drive.google.com",
            "docs": "https://docs.google.com",
            "sheets": "https://sheets.google.com",
            "slides": "https://slides.google.com",
            "calendar": "https://calendar.google.com",
            "maps": "https://maps.google.com",
            "translate": "https://translate.google.com",
        }
        
        site_key = s.split("/")[0].split(".")[0]
        if site_key in known_sites:
            return known_sites[site_key]

        # Fuzzy match known sites with typo tolerance (e.g. "yotube" -> "youtube")
        import difflib
        matches = difflib.get_close_matches(site_key, list(known_sites.keys()), n=1, cutoff=0.68)
        if matches:
            return known_sites[matches[0]]
        
        # If it looks like a domain (contains .), add https://
        if "." in s and " " not in s:
            return f"https://{s}"
        
        # Otherwise treat as search query - use Google search
        return f"https://google.com/search?q={s.replace(' ', '+')}"

    def _open_url(self, url: str) -> None:
        """Open a URL in the browser instantly via background worker (<1ms return)."""
        import threading
        def _worker():
            try:
                if hasattr(os, "startfile"):
                    os.startfile(url)
                    return
            except Exception:
                pass
            import webbrowser
            try:
                webbrowser.open(url)
                return
            except Exception:
                pass
            try:
                subprocess.Popen(
                    f'start "" "{url}"',
                    shell=True,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=_DETACH,
                )
            except Exception:
                pass

        threading.Thread(target=_worker, daemon=True).start()

    def list_apps(self, limit: int = 20) -> list[dict]:
        seen = set()
        out = []
        for entry in self._apps.values():
            n = entry["name"]
            if n in seen:
                continue
            seen.add(n)
            out.append({"name": n, "source": entry.get("source"),
                        "exe": entry.get("exe"),
                        "command": entry.get("command")})
        return sorted(out, key=lambda e: e["name"].lower())

    def launch(self, app_name: str, args: str = "") -> dict:
        app_name = app_name.strip()
        if not app_name:
            return {"success": False, "error": "No app name given"}

        # Clean conversational filler: "can you open", "please", "for me", "in 2 sec", etc.
        app_name = re.sub(r"^(?:can\s+you\s+|could\s+you\s+|would\s+you\s+|please\s+|iris\s+|hey\s+iris\s+|i\s+want\s+to\s+|i\s+want\s+you\s+to\s+|just\s+|go\s+and\s+)", "", app_name, flags=re.IGNORECASE).strip()
        app_name = re.sub(r"^(?:open|launch|start|run|opn|oepn|opne|lonch|lanch|stat|strt)\s+(?:the\s+|app\s+|application\s+)?", "", app_name, flags=re.IGNORECASE).strip()
        app_name = re.sub(r"\b(?:in\s+\d+\s*(?:sec|seconds|second|s)|fast|quickly|please|now|right\s+now|for\s+me|immediately|ok|okay)\b", "", app_name, flags=re.IGNORECASE).strip()
        app_name = re.sub(r"^(?:the\s+app\s+|app\s+|the\s+application\s+|application\s+|the\s+link\s+|link\s+)", "", app_name, flags=re.IGNORECASE).strip()

        # Automatic typo correction & mistyped word fixing
        if hasattr(self, "_typo_corrector") and self._typo_corrector:
            try:
                corr = self._typo_corrector.correct(app_name)
                corr_clean = re.sub(r"^(?:open|launch|start|run)\s+", "", corr, flags=re.IGNORECASE).strip()
                if corr_clean:
                    app_name = corr_clean
            except Exception:
                pass

        low = app_name.lower().strip()

        # ── 1. INSTANT WEB PLATFORM FAST-PATH (<0.01s) ────────
        # Directly opens YouTube, Google, ChatGPT, etc. with zero delays
        site_urls = {
            "youtube": "https://youtube.com",
            "google": "https://google.com",
            "github": "https://github.com",
            "reddit": "https://reddit.com",
            "stackoverflow": "https://stackoverflow.com",
            "chatgpt": "https://chatgpt.com",
            "claude": "https://claude.ai",
            "netflix": "https://netflix.com",
            "spotify": "https://open.spotify.com",
            "whatsapp web": "https://web.whatsapp.com",
            "instagram": "https://instagram.com",
            "facebook": "https://facebook.com",
            "twitter": "https://twitter.com",
            "x": "https://x.com",
            "amazon": "https://amazon.com",
            "gmail": "https://mail.google.com",
            "discord": "https://discord.com/app",
            "twitch": "https://twitch.tv",
            "linkedin": "https://linkedin.com",
            "maps": "https://maps.google.com",
            "translate": "https://translate.google.com",
        }
        for site, url in site_urls.items():
            if site == low or f" {site}" in low or low.startswith(f"{site} "):
                self._open_url(url)
                return {"success": True, "strategy": "web_platform", "app": site, "url": url}

        # Fast path for links and websites (<0.01s)
        is_link = (
            low.startswith("link ") or low.startswith("the link ") or
            low.startswith("http://") or low.startswith("https://") or
            low.startswith("www.") or
            ("." in low and " " not in low and not low.endswith((".exe", ".lnk", ".bat", ".cmd", ".py")))
        )
        if is_link:
            url = self._normalize_url(app_name)
            if url:
                self._open_url(url)
                return {"success": True, "strategy": "web_link", "app": app_name, "url": url}

        # Strip "app ", "the app ", "application " from app_name
        app_clean = re.sub(r"^(?:the\s+app\s+|app\s+|the\s+application\s+|application\s+)", "", app_name, flags=re.IGNORECASE).strip()
        if app_clean:
            app_name = app_clean

        # Check if app_name is an existing file or folder on disk or user locations (e.g. Desktop, Documents)
        try:
            from pathlib import Path
            user_home = Path.home()
            real_desktop = user_home / "OneDrive" / "Desktop"
            if not real_desktop.exists():
                real_desktop = user_home / "Desktop"
            real_documents = user_home / "OneDrive" / "Documents"
            if not real_documents.exists():
                real_documents = user_home / "Documents"
            real_downloads = user_home / "Downloads"

            clean_target = re.sub(r"\b(?:folder|directory|file|which is there in desktop|which is in desktop|on desktop|in desktop|in downloads|in documents)\b", "", app_name, flags=re.I).strip(" '\"")
            candidates = [
                Path(app_name).expanduser(),
                Path(clean_target).expanduser(),
                real_desktop / app_name,
                real_desktop / clean_target,
                real_documents / app_name,
                real_documents / clean_target,
                real_downloads / app_name,
                real_downloads / clean_target,
            ]
            for cand in candidates:
                if cand.exists() and (cand.is_dir() or cand.is_file()):
                    if hasattr(os, "startfile"):
                        os.startfile(str(cand))
                    else:
                        subprocess.Popen(f'explorer.exe "{cand}"', shell=True)
                    return {"success": True, "strategy": "local_folder_file", "app": cand.name, "path": str(cand)}
            # Fuzzy match (e.g. "FRIDAY" vs "F.R.I.D.A.Y") on Desktop
            if real_desktop.exists() and clean_target:
                clean_norm = re.sub(r"[^a-zA-Z0-9]", "", clean_target).lower()
                for item in os.listdir(real_desktop):
                    if re.sub(r"[^a-zA-Z0-9]", "", item).lower() == clean_norm:
                        matched = real_desktop / item
                        if hasattr(os, "startfile"):
                            os.startfile(str(matched))
                        else:
                            subprocess.Popen(f'explorer.exe "{matched}"', shell=True)
                        return {"success": True, "strategy": "local_folder_file", "app": matched.name, "path": str(matched)}
        except Exception as e:
            logger.debug(f"Direct folder/file check in launch: {e}")

        # Try all LOCAL strategies first
        for strategy in self.STRATEGIES:
            result = self._try_launch(strategy, app_name, args)
            if result.get("success"):
                return result

        # All local strategies failed — fall back to web browser
        url = self._normalize_url(app_name)
        if url:
            self._open_url(url)
            return {"success": True, "strategy": "web_fallback", "app": app_name, "url": url,
                    "detail": f"'{app_name}' was not found locally, opened in your browser instead."}
        return {"success": False, "error": f"Could not launch '{app_name}'", "app": app_name}

    def _fire(self, cmd: str, target: str = "", args: str = ""):
        """Launch a command fully detached and visible.
        Dispatches immediately in background thread (<1ms return)."""
        import threading
        def _worker():
            clean_target = target.strip(' "') if target else ""
            if not clean_target and cmd.startswith('start "" '):
                m = re.match(r'start\s+""\s+"([^"]+)"(?:\s+(.*))?', cmd)
                if m:
                    clean_target = m.group(1)
                    if not args and m.group(2):
                        args_to_use = m.group(2)
                    else:
                        args_to_use = args
                else:
                    args_to_use = args
            else:
                args_to_use = args

            if clean_target and hasattr(os, "startfile"):
                try:
                    if args_to_use:
                        os.startfile(clean_target, arguments=args_to_use)
                    else:
                        os.startfile(clean_target)
                    return
                except Exception as e:
                    logger.debug(f"os.startfile({clean_target}) failed, fallback to subprocess: {e}")

            try:
                subprocess.Popen(
                    cmd,
                    shell=True,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=_DETACH,
                )
            except Exception as e:
                logger.warning(f"Detached fire failed: {e}")

        threading.Thread(target=_worker, daemon=True).start()

    def _try_launch(self, strategy: str, app_name: str, args: str) -> dict:
        try:
            if strategy == "known":
                target = self.KNOWN_APPS.get(app_name.lower())
                if not target:
                    import difflib
                    matches = difflib.get_close_matches(app_name.lower(), list(self.KNOWN_APPS.keys()), n=1, cutoff=0.68)
                    if matches:
                        target = self.KNOWN_APPS[matches[0]]
                if not target:
                    return {"success": False, "error": "not a known app"}

                self._fire(f'start "" "{target}" {args}'.strip(), target=target, args=args)
                return {"success": True, "strategy": "known", "app": app_name}

            elif strategy == "discovered":
                entry = self._resolve_name(app_name)
                if not entry:
                    return {"success": False, "error": "not in installed apps"}
                cmd = entry.get("command") or entry.get("exe")
                if not cmd:
                    return {"success": False, "error": f"'{entry['name']}' has no launch path"}

                self._fire(f'start "" "{cmd}" {args}'.strip(), target=cmd, args=args)
                return {"success": True, "strategy": "discovered", "app": entry["name"], "path": cmd}

            elif strategy == "resolve":
                # High-speed PATH search (<1ms) — avoids slow where.exe and recursive glob walking
                which_path = shutil.which(app_name) or shutil.which(app_name + ".exe")
                if which_path:
                    self._fire(f'"{which_path}" {args}'.strip(), target=which_path, args=args)
                    return {"success": True, "strategy": "resolve", "app": app_name, "path": which_path}

                # Direct check common install directories WITHOUT recursive globbing
                for base_dir in [
                    os.environ.get("ProgramFiles", r"C:\Program Files"),
                    os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
                    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs"),
                ]:
                    if not base_dir or not os.path.isdir(base_dir):
                        continue
                    direct_exe = os.path.join(base_dir, f"{app_name}.exe")
                    if os.path.isfile(direct_exe):
                        self._fire(f'"{direct_exe}" {args}'.strip(), target=direct_exe, args=args)
                        return {"success": True, "strategy": "resolve_direct", "app": app_name, "path": direct_exe}

                return {"success": False, "error": f"'{app_name}' not found in PATH or standard directories"}

            elif strategy == "start":
                # Direct Windows shell execution — Windows Shell resolves registered App Paths, PATHEXT, and URL protocol handlers
                self._fire(f'start "" "{app_name}" {args}'.strip(), target=app_name, args=args)
                return {"success": True, "strategy": "start", "app": app_name}

            elif strategy == "web":
                url = self._normalize_url(app_name)
                if url:
                    self._open_url(url)
                    return {"success": True, "strategy": "web", "url": url}
                return {"success": False, "error": "not a valid URL"}

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Process image names that differ from the spoken/launch name.
    CLOSE_NAMES = {
        "terminal": "WindowsTerminal",
        "terminal emulator": "WindowsTerminal",
        "windows terminal": "WindowsTerminal",
        "settings": "SystemSettings",
        "settings app": "SystemSettings",
        "calculator": "CalculatorApp",
        "calc": "CalculatorApp",
        "file explorer": "explorer",
    }

    def close(self, app_name: str, force: bool = False) -> dict:
        if not force:
            return {"success": False, "error": "confirmation_required", "message": f"Are you sure you want to close '{app_name}'?"}
        name = app_name.strip().lower()
        if name in ("all", "all applications", "all apps", "everything"):
            return self.close_all(force=force)
        try:
            if name in self.CLOSE_NAMES or name in self.KNOWN_APPS:
                image = self.CLOSE_NAMES.get(name, self.KNOWN_APPS.get(name, name))
            else:
                entry = self._resolve_name(name)
                if not entry:
                    return {"success": False, "error": f"Could not find app '{app_name}'",
                            "detail": "Not in installed-app list."}
                image = entry.get("image")
                if not image and entry.get("command", "").lower().endswith(".lnk"):
                    target = self._resolve_lnk_target(entry["command"])
                    if target:
                        image = self._normalize(os.path.splitext(os.path.basename(target))[0])
                if not image:
                    return {"success": False, "error": f"Could not determine process for '{app_name}'"}
            image = image[:-4] if image.lower().endswith(".exe") else image

            # ── Prefer graceful window-close (WM_CLOSE = clicking X) ──
            wm = self._window_manager()
            if image in self.PROTECTED_IMAGES:
                # Never kill shell/system processes — close only their windows.
                res = self._graceful_close(name, image, wm)
                if res["closed"]:
                    return {"success": True, "app": app_name,
                            "detail": f"Closed {res['closed']} window(s) gracefully. System process kept alive."}
                return {"success": False, "error": "protected_process",
                        "message": f"'{app_name}' is a system process. No window found to close, and I won't kill it."}

            res = self._graceful_close(name, image, wm)
            if res["closed"]:
                time.sleep(1.5)
            if not self._process_running(image):
                return {"success": True, "app": app_name,
                        "detail": res["detail"] or f"Closed '{app_name}' windows."}
            # Fall back to killing the process only if the windows are gone
            # but the process still lingers.
            result = subprocess.run(f"taskkill /IM {image}.exe /F", shell=True, capture_output=True, text=True, timeout=10)
            ok = result.returncode == 0
            return {"success": ok, "app": app_name, "detail": (result.stdout or result.stderr).strip()[:200]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _window_manager(self):
        try:
            from .window_manager import WindowManager
            return WindowManager()
        except Exception:
            return None

    def _graceful_close(self, name: str, image: str, wm) -> dict:
        """Close matching windows via WM_CLOSE. Returns {"closed": n, "detail": str}."""
        if wm is None or not getattr(wm, "_has_win32", False):
            return {"closed": 0, "detail": "window close unavailable"}
        # File Explorer folders share the CabinetWClass window class.
        if image in ("explorer",) or "explorer" in image:
            res = wm.close_explorer_windows()
            return {"closed": res.get("count", 0), "detail": "closed explorer windows"}
        # Settings app uses its own class; match by class then title.
        if image in ("SystemSettings",):
            res = wm.close_by_class("SystemSettingsWindow")
            if res.get("count"):
                return {"closed": res["count"], "detail": "closed settings"}
            return {"closed": 0, "detail": "no settings window"}
        # Generic: match visible windows by the app name or its process image.
        res = wm.close_by_title(name)
        if not res.get("count"):
            res = wm.close_by_title(image)
        return {"closed": res.get("count", 0), "detail": "closed windows"}

    def _process_running(self, image: str) -> bool:
        try:
            r = subprocess.run(f"tasklist /FI \"IMAGENAME eq {image}.exe\"",
                               shell=True, capture_output=True, text=True, timeout=10)
            return image.lower() in r.stdout.lower()
        except Exception:
            return True

    # System-critical or session processes that must never be killed.
    PROTECTED_IMAGES = {
        "explorer", "python", "conhost", "csrss", "winlogon", "wininit", "dwm",
        "svchost", "sihost", "services", "lsass", "smss", "fontdrvhost", "dllhost",
        "RuntimeBroker", "SearchHost", "TextInputHost", "ShellExperienceHost",
        "StartMenuExperienceHost", "WindowsTerminal", "pwsh", "powershell", "cmd",
        "taskmgr", "SystemSettings", "spoolsv", "Code", "code", "cloudcode_cli",
        "opencode",
    }

    def _get_active_window_process(self):
        """Get the process name of the currently active/foreground window."""
        try:
            import win32gui
            import win32process
            hwnd = win32gui.GetForegroundWindow()
            if hwnd:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                if pid:
                    import psutil
                    proc = psutil.Process(pid)
                    return proc.name()
        except Exception:
            pass
        return None

    def close_all(self, force: bool = False) -> dict:
        if not force:
            return {"success": False, "error": "confirmation_required",
                    "message": "Close ALL open applications? This will close every window except system-critical ones and the active window."}
        try:
            # Get active window's process to exclude it
            active_proc = self._get_active_window_process()
            
            # Pass 1: gracefully close every visible window (WM_CLOSE), leaving
            # shell/system processes running.
            wm = self._window_manager()
            graceful = {"closed": 0}
            if wm is not None and getattr(wm, "_has_win32", False):
                # Exclude active window's process from graceful close
                graceful = wm.close_all_windows(skip_process=active_proc)
                time.sleep(2)
            # Pass 2: kill any remaining non-protected app processes.
            result = subprocess.run(
                ["powershell", "-Command",
                 "Get-Process | Where-Object {$_.MainWindowTitle -ne ''} | Select-Object -ExpandProperty Name | Sort-Object -Unique"],
                capture_output=True, text=True, timeout=15,
            )
            images = [n.strip() for n in result.stdout.splitlines() if n.strip()]
            killed = []
            failed = []
            for img in images:
                if img in self.PROTECTED_IMAGES:
                    continue
                if active_proc and img.lower() == active_proc.lower():
                    continue  # Don't kill the active window's process
                r = subprocess.run(f"taskkill /IM {img}.exe /F", shell=True, capture_output=True, text=True, timeout=10)
                if r.returncode == 0:
                    killed.append(img)
                else:
                    failed.append(img)
            return {"success": True, "closed": killed, "failed": failed,
                    "windows_closed": graceful.get("count", 0),
                    "active_window_protected": active_proc,
                    "detail": f"Closed {len(killed)} app(s) + {graceful.get('count', 0)} window(s). Active window ({active_proc}) protected." if (killed or graceful.get("count")) else "Nothing to close."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_running(self) -> list[dict]:
        try:
            result = subprocess.run(
                ["powershell", "-Command", "Get-Process | Where-Object {$_.MainWindowTitle -ne ''} | Select-Object Name, Id, MainWindowTitle | ConvertTo-Json"],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0 and result.stdout.strip():
                import json
                processes = json.loads(result.stdout)
                if isinstance(processes, dict):
                    processes = [processes]
                return processes
            return []
        except Exception as e:
            logger.warning(f"Failed to list running apps: {e}")
            return []

    def get_status(self) -> dict:
        return {"running_count": len(self.list_running()), "discovered_count": len(self._apps)}
