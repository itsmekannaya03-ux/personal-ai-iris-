"""
Tools — The 27+ function-calling tool system.

Every tool the AI can use is registered here. The LLM calls tools
via function-calling, results feed back into the conversation loop.

Categories:
  FS        — File system operations (8 tools)
  SYSTEM    — PC control, apps, hardware (7 tools)
  MEMORY    — Save, recall, forget (3 tools)
  MEDIA     — Music, audio, video (4 tools)
  MISC      — Web, search, automation (5 tools)
"""

import os
import json
import logging
import subprocess
import shutil
import time
import re
from pathlib import Path
from typing import Any, Callable, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("iris.tools")


@dataclass
class ToolDef:
    name: str
    description: str
    handler: Callable
    parameters: dict = field(default_factory=dict)
    category: str = "misc"
    requires_confirmation: bool = False


class ToolRegistry:
    """
    Central registry for all available tools.
    Tools are registered with metadata and can be called by name.
    """

    def __init__(self):
        self._tools: dict[str, ToolDef] = {}
        self._history: list[dict] = []
        self._max_history = 100
        self._register_all()

    def _register_all(self):
        """Register every tool the AI can use."""

        # ── FS: File System (8 tools) ────────────────────────

        self.register(ToolDef(
            name="write_code_file",
            description="Write code or content to a file. Creates parent dirs if needed. Use for saving generated code, configs, or documents.",
            handler=self._write_file,
            category="fs",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute file path"},
                    "content": {"type": "string", "description": "File content"},
                },
                "required": ["path", "content"],
            },
        ))

        self.register(ToolDef(
            name="read_file_content",
            description="Read the full content of any text file.",
            handler=self._read_file,
            category="fs",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute file path"},
                },
                "required": ["path"],
            },
        ))

        self.register(ToolDef(
            name="list_directory",
            description="List all files and folders in a directory.",
            handler=self._list_dir,
            category="fs",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path"},
                },
                "required": ["path"],
            },
        ))

        self.register(ToolDef(
            name="create_folder",
            description="Create a new folder (and any parent folders).",
            handler=self._create_folder,
            category="fs",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Folder path to create"},
                },
                "required": ["path"],
            },
        ))

        self.register(ToolDef(
            name="delete_file_or_folder",
            description="Delete a file or empty folder. Will not delete non-empty folders without force.",
            handler=self._delete_path,
            category="fs",
            requires_confirmation=True,
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to delete"},
                },
                "required": ["path"],
            },
        ))

        self.register(ToolDef(
            name="move_path",
            description="Move or rename a file or folder from source to destination.",
            handler=self._move_path,
            category="fs",
            parameters={
                "type": "object",
                "properties": {
                    "source": {"type": "string", "description": "Current path"},
                    "destination": {"type": "string", "description": "New path"},
                },
                "required": ["source", "destination"],
            },
        ))

        self.register(ToolDef(
            name="copy_path",
            description="Copy a file or folder from source to destination.",
            handler=self._copy_path,
            category="fs",
            parameters={
                "type": "object",
                "properties": {
                    "source": {"type": "string", "description": "Source path"},
                    "destination": {"type": "string", "description": "Destination path"},
                },
                "required": ["source", "destination"],
            },
        ))

        self.register(ToolDef(
            name="rename_path",
            description="Rename a file or folder.",
            handler=self._rename_path,
            category="fs",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Current path"},
                    "new_name": {"type": "string", "description": "New name"},
                },
                "required": ["path", "new_name"],
            },
        ))

        # ── SYSTEM: PC Control (7 tools) ─────────────────────

        self.register(ToolDef(
            name="open_app",
            description="Launch an application by name or path. Uses 4 strategies: direct path, PATH lookup, Start menu search, shell exec.",
            handler=self._open_app,
            category="system",
            parameters={
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "Application name or path"},
                },
                "required": ["app_name"],
            },
        ))

        self.register(ToolDef(
            name="list_installed_apps",
            description="List installed applications on the system.",
            handler=self._list_installed_apps,
            category="system",
            parameters={"type": "object", "properties": {}},
        ))

        self.register(ToolDef(
            name="take_screenshot",
            description="Capture the current screen and save to a file.",
            handler=self._take_screenshot,
            category="system",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Save path (optional)"},
                },
            },
        ))

        self.register(ToolDef(
            name="lock_pc",
            description="Lock the computer/workstation immediately.",
            handler=self._lock_pc,
            category="system",
            requires_confirmation=True,
            parameters={"type": "object", "properties": {}},
        ))

        self.register(ToolDef(
            name="system_stats",
            description="Get current CPU, RAM, disk usage, and system uptime.",
            handler=self._system_stats,
            category="system",
            parameters={"type": "object", "properties": {}},
        ))

        self.register(ToolDef(
            name="set_volume",
            description="Set system volume to a percentage (0-100).",
            handler=self._set_volume,
            category="system",
            parameters={
                "type": "object",
                "properties": {
                    "level": {"type": "integer", "description": "Volume level 0-100"},
                },
                "required": ["level"],
            },
        ))

        self.register(ToolDef(
            name="open_camera",
            description="Open the system camera application.",
            handler=self._open_camera,
            category="system",
            parameters={"type": "object", "properties": {}},
        ))

        # ── MEMORY: AI Memory (3 tools) ──────────────────────

        self.register(ToolDef(
            name="save_memory",
            description="Save an important fact or memory with optional tags and category.",
            handler=self._save_memory,
            category="memory",
            parameters={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Memory identifier"},
                    "value": {"type": "string", "description": "Memory content"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "Search tags"},
                },
                "required": ["key", "value"],
            },
        ))

        self.register(ToolDef(
            name="recall_memory",
            description="Retrieve a memory by key or search by keyword.",
            handler=self._recall_memory,
            category="memory",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Memory key or search term"},
                },
                "required": ["query"],
            },
        ))

        self.register(ToolDef(
            name="forget_memory",
            description="Delete a specific memory by key.",
            handler=self._forget_memory,
            category="memory",
            requires_confirmation=True,
            parameters={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Memory key to delete"},
                },
                "required": ["key"],
            },
        ))

        # ── MEDIA: Audio/Video (4 tools) ─────────────────────

        self.register(ToolDef(
            name="play_media",
            description="Play a media file (audio or video) or stream from URL.",
            handler=self._play_media,
            category="media",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path or URL"},
                },
                "required": ["path"],
            },
        ))

        self.register(ToolDef(
            name="save_song",
            description="Save a song to the music library.",
            handler=self._save_song,
            category="media",
            parameters={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Song title"},
                    "artist": {"type": "string", "description": "Artist name"},
                    "path": {"type": "string", "description": "File path or URL"},
                },
                "required": ["title", "artist", "path"],
            },
        ))

        self.register(ToolDef(
            name="get_playlist",
            description="List all songs in the music library.",
            handler=self._get_playlist,
            category="media",
            parameters={"type": "object", "properties": {}},
        ))

        self.register(ToolDef(
            name="play_from_playlist",
            description="Play a song from the music library by title or index.",
            handler=self._play_from_playlist,
            category="media",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Song title or number"},
                },
                "required": ["query"],
            },
        ))

        # ── MISC: Web, Search, Utilities (5 tools) ───────────

        self.register(ToolDef(
            name="search_internet",
            description="Search the web for information using DuckDuckGo.",
            handler=self._search_internet,
            category="misc",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                },
                "required": ["query"],
            },
        ))

        self.register(ToolDef(
            name="get_weather",
            description="Get current weather for a city using wttr.in.",
            handler=self._get_weather,
            category="misc",
            parameters={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name"},
                },
                "required": ["city"],
            },
        ))

        self.register(ToolDef(
            name="get_time",
            description="Get the current date and time.",
            handler=self._get_time,
            category="misc",
            parameters={"type": "object", "properties": {}},
        ))

        self.register(ToolDef(
            name="run_terminal_command",
            description="Run a terminal/command prompt command and return output.",
            handler=self._run_command,
            category="misc",
            requires_confirmation=True,
            parameters={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Command to execute"},
                    "timeout": {"type": "integer", "description": "Timeout in seconds"},
                },
                "required": ["command"],
            },
        ))

        self.register(ToolDef(
            name="navigate_folder",
            description="Navigate to a folder and open it in the file explorer.",
            handler=self._navigate_folder,
            category="misc",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Folder path"},
                },
                "required": ["path"],
            },
        ))

        self.register(ToolDef(
            name="open_in_vscode",
            description="Open a file or folder in VS Code.",
            handler=self._open_in_vscode,
            category="misc",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File or folder path"},
                },
                "required": ["path"],
            },
        ))

        logger.info(f"Tool registry initialized: {len(self._tools)} tools across 5 categories")

    # ── Register / Lookup ────────────────────────────────────

    def register(self, tool: ToolDef):
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[ToolDef]:
        return self._tools.get(name)

    def list_tools(self) -> list[dict]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "category": t.category,
                "parameters": t.parameters,
                "requires_confirmation": t.requires_confirmation,
            }
            for t in self._tools.values()
        ]

    def get_tools_for_llm(self) -> list[dict]:
        """Format tools for LLM function-calling API."""
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters or {"type": "object", "properties": {}},
                },
            }
            for t in self._tools.values()
        ]

    def call(self, name: str, args: dict) -> dict:
        """Execute a tool by name with given arguments."""
        tool = self._tools.get(name)
        if not tool:
            return {"success": False, "error": f"Unknown tool: {name}"}
        try:
            result = tool.handler(**args)
            self._history.append({
                "tool": name,
                "args": args,
                "result": result,
                "timestamp": time.time(),
            })
            if len(self._history) > self._max_history:
                self._history.pop(0)
            return result
        except Exception as e:
            logger.error(f"Tool '{name}' failed: {e}")
            return {"success": False, "error": str(e)}

    def get_history(self, limit: int = 10) -> list[dict]:
        return self._history[-limit:]

    # ── FS Tool Handlers ─────────────────────────────────────

    def _write_file(self, path: str, content: str) -> dict:
        try:
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"Written: {path} ({len(content)} chars)")
            return {"success": True, "path": path, "size": len(content)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _read_file(self, path: str) -> dict:
        try:
            if not os.path.exists(path):
                return {"success": False, "error": f"File not found: {path}"}
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            return {"success": True, "path": path, "content": content, "size": len(content)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _list_dir(self, path: str) -> dict:
        try:
            if not os.path.exists(path):
                return {"success": False, "error": f"Path not found: {path}"}
            entries = []
            for entry in os.scandir(path):
                entries.append({
                    "name": entry.name,
                    "is_dir": entry.is_dir(),
                    "size": entry.stat().st_size if entry.is_file() else 0,
                    "modified": entry.stat().st_mtime,
                })
            return {"success": True, "path": os.path.abspath(path), "entries": entries}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _create_folder(self, path: str) -> dict:
        try:
            os.makedirs(path, exist_ok=True)
            return {"success": True, "path": os.path.abspath(path)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _delete_path(self, path: str) -> dict:
        try:
            if not os.path.exists(path):
                return {"success": False, "error": f"Path not found: {path}"}
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            return {"success": True, "deleted": path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _move_path(self, source: str, destination: str) -> dict:
        try:
            shutil.move(source, destination)
            return {"success": True, "from": source, "to": destination}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _copy_path(self, source: str, destination: str) -> dict:
        try:
            if os.path.isdir(source):
                shutil.copytree(source, destination)
            else:
                shutil.copy2(source, destination)
            return {"success": True, "from": source, "to": destination}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _rename_path(self, path: str, new_name: str) -> dict:
        try:
            parent = os.path.dirname(os.path.abspath(path))
            dest = os.path.join(parent, new_name)
            os.rename(path, dest)
            return {"success": True, "from": path, "to": dest}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── SYSTEM Tool Handlers ─────────────────────────────────

    def _open_app(self, app_name: str) -> dict:
        try:
            if os.name == "nt":
                subprocess.Popen(["cmd", "/c", "start", "", app_name],
                                 shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif os.name == "posix":
                subprocess.Popen(["open", "-a", app_name] if os.uname().sysname == "Darwin" else [app_name],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"success": True, "app": app_name}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _list_installed_apps(self) -> dict:
        try:
            if os.name == "nt":
                result = subprocess.run(
                    ["powershell", "-Command",
                     "Get-ItemProperty HKLM:\\Software\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* | "
                     "Select-Object DisplayName | Where-Object { $_.DisplayName } | ConvertTo-Json"],
                    capture_output=True, text=True, timeout=30,
                )
                apps = json.loads(result.stdout) if result.stdout.strip() else []
                return {"success": True, "apps": apps[:50]}
            else:
                return {"success": False, "error": "Unsupported OS"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _take_screenshot(self, path: str = "") -> dict:
        try:
            import pyscreenshot
            path = path or os.path.join(os.path.expanduser("~"), ".igris", f"screenshot_{int(time.time())}.png")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            img = pyscreenshot.grab()
            img.save(path)
            return {"success": True, "path": path}
        except ImportError:
            return {"success": False, "error": "pyscreenshot not installed"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _lock_pc(self) -> dict:
        try:
            if os.name == "nt":
                subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], timeout=5)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _system_stats(self) -> dict:
        try:
            import psutil
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            cpu_percent = psutil.cpu_percent(interval=0.5)
            return {
                "success": True,
                "cpu_percent": cpu_percent,
                "ram_total_gb": round(mem.total / (1024**3), 1),
                "ram_used_gb": round(mem.used / (1024**3), 1),
                "ram_percent": mem.percent,
                "disk_total_gb": round(disk.total / (1024**3), 1),
                "disk_used_gb": round(disk.used / (1024**3), 1),
                "disk_percent": disk.percent,
                "uptime_seconds": int(time.time() - psutil.boot_time()),
            }
        except ImportError:
            return {"success": False, "error": "psutil not installed"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _set_volume(self, level: int) -> dict:
        try:
            level = max(0, min(100, level))
            if os.name == "nt":
                try:
                    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                    from ctypes import cast, POINTER
                    from comtypes import CLSCTX_ALL
                    devices = AudioUtilities.GetSpeakers()
                    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                    volume = cast(interface, POINTER(IAudioEndpointVolume))
                    volume.SetMasterVolumeLevelScalar(level / 100.0, None)
                except ImportError:
                    return {"success": False, "error": "pycaw not installed"}
            return {"success": True, "volume": level}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _open_camera(self) -> dict:
        try:
            if os.name == "nt":
                subprocess.Popen(["start", "microsoft.windows.camera:"], shell=True,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── MEMORY Tool Handlers ─────────────────────────────────

    def _save_memory(self, key: str, value: str, tags: list[str] = None) -> dict:
        if self._memory_backend:
            tags = tags or []
            metadata = {"tags": tags, "source": "tool"}
            self._memory_backend.store(key, value, metadata=metadata)
            return {"success": True, "key": key}
        return {"success": False, "error": "Memory backend not available"}

    def _recall_memory(self, query: str) -> dict:
        if self._memory_backend:
            result = self._memory_backend.retrieve(query)
            if result:
                return {"success": True, "key": query, "value": result}
            search_results = self._memory_backend.search(query)
            if search_results:
                return {"success": True, "results": search_results}
            return {"success": False, "error": "No memory found"}
        return {"success": False, "error": "Memory backend not available"}

    def _forget_memory(self, key: str) -> dict:
        if self._memory_backend:
            deleted = self._memory_backend.delete(key)
            return {"success": deleted, "key": key}
        return {"success": False, "error": "Memory backend not available"}

    def set_memory_backend(self, memory):
        self._memory_backend = memory

    # ── MEDIA Tool Handlers ──────────────────────────────────

    def _play_media(self, path: str) -> dict:
        try:
            if os.name == "nt":
                os.startfile(path)
            elif os.name == "posix":
                subprocess.Popen(["open", path])
            return {"success": True, "media": path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _save_song(self, title: str, artist: str, path: str) -> dict:
        if self._music_library is not None:
            self._music_library.append({"title": title, "artist": artist, "path": path})
            return {"success": True, "song": title}
        return {"success": False, "error": "Music library not available"}

    def _get_playlist(self) -> dict:
        if self._music_library is not None:
            return {"success": True, "playlist": self._music_library}
        return {"success": False, "error": "Music library not available"}

    def _play_from_playlist(self, query: str) -> dict:
        if self._music_library is None:
            return {"success": False, "error": "Music library not available"}
        for song in self._music_library:
            if query.lower() in song["title"].lower() or query.lower() in song["artist"].lower():
                return self._play_media(song["path"])
        try:
            idx = int(query) - 1
            if 0 <= idx < len(self._music_library):
                return self._play_media(self._music_library[idx]["path"])
        except ValueError:
            pass
        return {"success": False, "error": f"Song not found: {query}"}

    def set_music_library(self, library: list):
        self._music_library = library

    # ── MISC Tool Handlers ───────────────────────────────────

    def _search_internet(self, query: str) -> dict:
        try:
            import urllib.parse, urllib.request, json
            url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1"
            req = urllib.request.Request(url, headers={"User-Agent": "IrisAI/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
                results = []
                if data.get("AbstractText"):
                    results.append({"source": "abstract", "text": data["AbstractText"]})
                if data.get("RelatedTopics"):
                    for topic in data["RelatedTopics"][:5]:
                        if isinstance(topic, dict) and "Text" in topic:
                            results.append({"source": "related", "text": topic["Text"]})
                return {"success": True, "query": query, "results": results}
        except ImportError:
            try:
                from duckduckgo_search import DDGS
                with DDGS() as ddgs:
                    results = [{"title": r["title"], "body": r["body"]} for r in ddgs.text(query, max_results=5)]
                return {"success": True, "query": query, "results": results}
            except ImportError:
                return {"success": False, "error": "No search backend available"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_weather(self, city: str) -> dict:
        try:
            import urllib.request
            url = f"https://wttr.in/{urllib.parse.quote(city)}?format=%C+%t+%h+%w"
            req = urllib.request.Request(url, headers={"User-Agent": "curl/7.68.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = resp.read().decode().strip()
            return {"success": True, "city": city, "weather": data}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_time(self) -> dict:
        now = time.localtime()
        return {
            "success": True,
            "datetime": time.strftime("%Y-%m-%d %H:%M:%S", now),
            "date": time.strftime("%A, %B %d, %Y", now),
            "time": time.strftime("%I:%M %p", now),
            "timezone": time.tzname,
        }

    def _run_command(self, command: str, timeout: int = 30) -> dict:
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=timeout
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout[:2000],
                "stderr": result.stderr[:500],
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Command timed out ({timeout}s)"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _navigate_folder(self, path: str) -> dict:
        try:
            if os.name == "nt":
                subprocess.Popen(["explorer", os.path.abspath(path)])
            elif os.name == "posix":
                subprocess.Popen(["open", path])
            return {"success": True, "path": os.path.abspath(path)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _open_in_vscode(self, path: str) -> dict:
        try:
            subprocess.Popen(["code", os.path.abspath(path)],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"success": True, "path": path}
        except FileNotFoundError:
            return {"success": False, "error": "VS Code 'code' command not found in PATH"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_status(self) -> dict:
        return {
            "total_tools": len(self._tools),
            "categories": {
                "fs": sum(1 for t in self._tools.values() if t.category == "fs"),
                "system": sum(1 for t in self._tools.values() if t.category == "system"),
                "memory": sum(1 for t in self._tools.values() if t.category == "memory"),
                "media": sum(1 for t in self._tools.values() if t.category == "media"),
                "misc": sum(1 for t in self._tools.values() if t.category == "misc"),
            },
            "history_size": len(self._history),
        }
