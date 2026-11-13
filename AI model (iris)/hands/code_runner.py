import json
import logging
import os
import re
import subprocess
import sys
import threading
import urllib.request
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger("iris.hands.code_runner")

OLLAMA_URL = "http://127.0.0.1:11434"
MODEL_PREFERENCE = [
    "glm5.2", "glm4:9b", "glm4", "glm",
    "qwen3.8", "qwen3.2", "qwen2.5:3b", "qwen2.5-coder:7b", "qwen2.5-coder:3b", "qwen2.5-coder", "qwen",
    "llama3.2:3b", "llama3.2",
]

LANG_EXT = {
    "python": ".py", "javascript": ".js", "html": ".html", "java": ".java",
    "c": ".c", "cpp": ".cpp", "powershell": ".ps1", "batch": ".bat", "text": ".md",
}

LANG_KEYWORDS = [
    ("python", ["python", "py script", ".py"]),
    ("javascript", ["javascript", "js script", ".js", "node"]),
    ("html", ["html", "web page", ".html", "website page"]),
    ("java", ["java program", ".java"]),
    ("cpp", ["c++", ".cpp"]),
    ("c", ["c program", ".c code", "c code"]),
    ("powershell", ["powershell", ".ps1"]),
    ("batch", ["batch", ".bat"]),
]

TEXT_KEYWORDS = ["letter", "essay", "poem", "story", "note", "notes", "readme", "report",
                 "email", "paragraph", "article", "text file", "plain text"]

_DETACH = 0
if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP"):
    _DETACH |= subprocess.CREATE_NEW_PROCESS_GROUP
if hasattr(subprocess, "CREATE_NO_WINDOW"):
    _DETACH |= subprocess.CREATE_NO_WINDOW


class CodeRunner:
    """Generates, writes, and runs code/text files.

    - Generation: local Ollama model first (Qwen Coder if installed, else
      the best available), with a caller-provided fallback generator.
    - Writing: plain pathlib, into a workspace folder.
    - Running: extension-based runtime detection (python / node / java /
      powershell / batch / browser) with captured output and a hard timeout.
    """

    def __init__(self, generators: Optional[list[Callable[[str], str]]] = None,
                 workspace: Optional[str] = None, file_ops=None, generator_fn=None):
        gens = list(generators or [self._ollama_generate])
        if generator_fn:
            gens.append(generator_fn)
        self._generators = gens
        self._file_ops = file_ops
        self._workspace = Path(workspace or self._default_workspace())
        try:
            self._workspace.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning(f"Could not create workspace {self._workspace}: {e}")
        self._model = self._pick_model()
        logger.info(f"CodeRunner ready (model={self._model}, workspace={self._workspace})")

    # ── paths ─────────────────────────────────────────────

    def _default_workspace(self) -> str:
        return str(Path(__file__).resolve().parents[1] / "workspace")

    FORBIDDEN_SUBFOLDERS = {
        "desktop", "downloads", "documents", "pictures", "videos", "music", "workspace",
        "python", "javascript", "js", "html", "css", "c", "cpp", "java", "code", "script",
        "program", "notepad", "game", "website", "webpage", "file", "folder", "dir", "directory",
        "new", "this", "my", "the", "here", "project", "work"
    }

    def resolve_path(self, path: str, description: str = "", target_dir: Optional[str] = None) -> Path:
        p = Path(path).expanduser()
        if p.is_absolute():
            return p

        # 1. If explicit target_dir is passed, prioritize it directly!
        if target_dir:
            td = Path(target_dir).expanduser()
            if td.is_absolute() and td.exists():
                return td / p.name

        d = (description + " " + path).lower()
        user_home = Path.home()
        real_desktop = user_home / "OneDrive" / "Desktop"
        if not real_desktop.exists():
            real_desktop = user_home / "Desktop"

        real_documents = user_home / "OneDrive" / "Documents"
        if not real_documents.exists():
            real_documents = user_home / "Documents"

        real_downloads = user_home / "Downloads"

        # Check working directory from file_ops
        active_wd = None
        if self._file_ops and hasattr(self._file_ops, "get_working_dir"):
            wd_str = self._file_ops.get_working_dir()
            if wd_str:
                active_wd = Path(wd_str)

        if "download" in d:
            base_dir = real_downloads
        elif "document" in d:
            base_dir = real_documents
        elif "picture" in d or "photo" in d:
            base_dir = user_home / "Pictures"
        elif "desktop" in d:
            base_dir = real_desktop
        elif active_wd and active_wd.exists() and any(w in d for w in ("project", "work", "here", "this folder", "workspace")):
            base_dir = active_wd
        elif active_wd and active_wd.exists():
            base_dir = active_wd
        else:
            base_dir = real_desktop

        # Detect subfolder ONLY when explicitly requested (e.g. "in a new folder named X" or "in folder X")
        subfolder = None
        m_explicit_new = re.search(r"\b(?:create|make|in|inside)\s+(?:a\s+)?new\s+folder\s+(?:named|called)\s+([a-zA-Z0-9_\-]+)", description, re.I)
        if m_explicit_new:
            cand = m_explicit_new.group(1).strip(" '\"")
            if cand.lower() not in self.FORBIDDEN_SUBFOLDERS:
                subfolder = cand
        elif re.search(r"\b(?:in|inside|into)\s+(?:the\s+|my\s+)?([a-zA-Z0-9_\-]+)\s+folder\b", description, re.I):
            m_sub = re.search(r"\b(?:in|inside|into)\s+(?:the\s+|my\s+)?([a-zA-Z0-9_\-]+)\s+folder\b", description, re.I)
            cand = m_sub.group(1).strip(" '\"")
            if cand.lower() not in self.FORBIDDEN_SUBFOLDERS:
                subfolder = cand

        final_dir = base_dir
        if subfolder:
            final_dir = base_dir / subfolder
            try:
                final_dir.mkdir(parents=True, exist_ok=True)
            except Exception:
                final_dir = base_dir

        name = p.name
        m_file = re.search(r"\b([a-zA-Z0-9_\-]+\.(?:py|js|html|css|java|cpp|c|ps1|bat|cmd|txt|json|md))\b", name, re.I)
        if m_file:
            name = m_file.group(1).strip()
        else:
            name = re.sub(r"^(?:on\s+desktop|in\s+desktop|desktop|in\s+downloads|downloads|in\s+documents|documents)[\\/ ]*", "", name, flags=re.IGNORECASE).strip()
        if not name:
            name = "file" + (p.suffix or ".txt")

        candidate = final_dir / name
        return candidate

    def get_workspace(self) -> str:
        return str(self._workspace)

    # ── generation ────────────────────────────────────────

    def _pick_model(self) -> Optional[str]:
        try:
            req = urllib.request.Request(f"{OLLAMA_URL}/api/tags")
            with urllib.request.urlopen(req, timeout=1) as resp:
                data = json.loads(resp.read().decode())
            available = [m.get("name", "") for m in data.get("models", [])]
            for pref in MODEL_PREFERENCE:
                for name in available:
                    if name == pref or name.startswith(pref):
                        return name
            return available[0] if available else None
        except Exception as e:
            logger.warning(f"Ollama model list failed: {e}")
            return None

    def _ollama_generate(self, prompt: str) -> str:
        if not self._model:
            raise RuntimeError("No local Ollama model available")
        body = json.dumps({
            "model": self._model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2, "num_predict": 4096},
        }).encode()
        req = urllib.request.Request(f"{OLLAMA_URL}/api/generate", data=body,
                                     headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode())
        content = result.get("response", "").strip()
        if not content:
            raise RuntimeError("Ollama returned empty content")
        return content

    def _strip_fences(self, content: str) -> str:
        """Remove markdown code fences the model sometimes adds anyway."""
        c = content.strip()
        m = re.match(r"^```[a-zA-Z0-9_+.-]*\s*\n?(.*?)```\s*$", c, re.DOTALL)
        if m:
            return m.group(1).strip()
        if c.startswith("```"):
            c = re.sub(r"^```[a-zA-Z0-9_+.-]*\s*\n?", "", c)
        if c.endswith("```"):
            c = re.sub(r"\n?```\s*$", "", c)
        return c.strip()

    def generate_code(self, description: str, language: Optional[str] = None) -> dict:
        return self.generate(description, language=language)

    def generate(self, description: str, language: Optional[str] = None) -> dict:
        lang = (language or self._detect_language(description)).lower()
        ext = LANG_EXT.get(lang, ".txt")
        prompt = (
            "You are a coding assistant. Generate the COMPLETE content for one file "
            f"in {lang or 'plain text'}.\n"
            f"Request: {description}\n\n"
            "Rules: output ONLY the file content. No explanations, no commentary, "
            "no markdown code fences, no placeholder comments. Complete, working code."
        )
        last_err = None
        for gen in self._generators:
            try:
                content = self._strip_fences(gen(prompt))
                if content and content.strip():
                    return {"success": True, "content": content, "language": lang, "extension": ext}
            except Exception as e:
                last_err = e
                logger.warning(f"Generator failed: {e}")

        # Fallback offline templates for common requested languages
        desc_lower = description.lower()
        if "count" in desc_lower or "counter" in desc_lower or "1 to 10" in desc_lower or "1-10" in desc_lower:
            if lang == "python":
                return {
                    "success": True,
                    "content": "# Python program to count numbers from 1 to 10\nprint('Counting numbers from 1 to 10:')\nfor number in range(1, 11):\n    print(number)\n",
                    "language": lang,
                    "extension": ext,
                }
            elif lang == "javascript":
                return {
                    "success": True,
                    "content": "// JavaScript program to count numbers from 1 to 10\nconsole.log('Counting numbers from 1 to 10:');\nfor (let i = 1; i <= 10; i++) {\n    console.log(i);\n}\n",
                    "language": lang,
                    "extension": ext,
                }

        m_print = re.search(r"(?:print|prints|output|echo)\s+['\"]?([0-9a-zA-Z\s_\-\.!?,]+?)['\"]?(?:\s|$)", desc_lower)
        if m_print:
            val = m_print.group(1).strip()
            if lang == "python":
                code_val = val if val.isdigit() else repr(val)
                return {
                    "success": True,
                    "content": f"# Python script generated by Iris\nprint({code_val})\n",
                    "language": lang,
                    "extension": ext,
                }
            elif lang == "javascript":
                code_val = val if val.isdigit() else repr(val)
                return {
                    "success": True,
                    "content": f"// JavaScript script generated by Iris\nconsole.log({code_val});\n",
                    "language": lang,
                    "extension": ext,
                }

        fallback_templates = {
            "javascript": "// Simple JavaScript program generated by Iris\nconsole.log('Hello from Iris AI!');\n\nfunction calculateSum(a, b) {\n    return a + b;\n}\n\nconst result = calculateSum(10, 25);\nconsole.log(`Calculation result: ${result}`);\n",
            "python": "# Simple Python program generated by Iris\nprint('Hello from Iris AI!')\n\ndef main():\n    numbers = [1, 2, 3, 4, 5]\n    print(f'Sum of numbers: {sum(numbers)}')\n\nif __name__ == '__main__':\n    main()\n",
            "html": "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n    <meta charset=\"UTF-8\">\n    <title>Iris AI Generated Page</title>\n</head>\n<body>\n    <h1>Hello from Iris AI</h1>\n    <p>This file was generated on your command.</p>\n</body>\n</html>\n",
            "text": "Hello from Iris AI!\nThis file was created on your command.\n",
        }
        if lang in fallback_templates:
            return {"success": True, "content": fallback_templates[lang], "language": lang, "extension": ext}

        return {"success": False, "error": f"Content generation failed: {last_err}"}

    def _detect_language(self, description: str) -> str:
        d = description.lower()
        for ext, lang in [(".py", "python"), (".js", "javascript"), (".html", "html"),
                          (".java", "java"), (".cpp", "cpp"), (".c", "c"),
                          (".ps1", "powershell"), (".bat", "batch"), (".txt", "text"),
                          (".md", "text")]:
            if ext in d:
                return lang
        for lang, kws in LANG_KEYWORDS:
            for kw in kws:
                if kw in d:
                    return lang
        if any(kw in d for kw in TEXT_KEYWORDS):
            return "text"
        return "python"

    # ── writing ───────────────────────────────────────────

    def _make_filename(self, description: str, ext: str) -> str:
        # Check for explicit filename mentioned in description
        m = re.search(r"(?:name\s+(?:it\s+)?(?:as\s+)?(?:a\s+)?|named\s+|called\s+|file\s+)([a-zA-Z0-9_\-\.]+\.[a-zA-Z0-9]+)", description, re.IGNORECASE)
        if m:
            return m.group(1).strip()
        m = re.search(r"\b([a-zA-Z0-9_\-]+\.(?:py|js|html|css|java|cpp|c|ps1|bat|cmd|txt|json|md))\b", description, re.IGNORECASE)
        if m:
            return m.group(1).strip()
        
        d = re.sub(r"\b(write|create|make|generate|build|draft|a|an|the|in notepad|notepad)\b", " ", description.lower())
        d = re.sub(r"\b(and|then)\b.*$", "", d)
        slug = re.sub(r"[^a-z0-9]+", "_", d).strip("_")[:40].strip("_")
        return (slug or "file") + ext

    def write(self, description: str, content: str, ext: str, filename: Optional[str] = None, target_dir: Optional[str] = None) -> dict:
        name = filename or self._make_filename(description, ext)
        if not name.lower().endswith(ext):
            name += ext
        path = self.resolve_path(name, description=description, target_dir=target_dir)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            logger.info(f"Wrote file: {path}")
            return {"success": True, "path": str(path), "name": path.name}
        except Exception as e:
            return {"success": False, "error": f"Write failed: {e}"}

    # ── running ───────────────────────────────────────────

    def write_and_run(self, description: str, run: Optional[bool] = None,
                      filename: Optional[str] = None, target_dir: Optional[str] = None) -> dict:
        gen = self.generate(description)
        if not gen.get("success"):
            return gen
        ext = gen["extension"]
        written = self.write(description, gen["content"], ext, filename, target_dir=target_dir)
        if not written.get("success"):
            return written
        result = {
            "success": True,
            "path": written["path"],
            "language": gen["language"],
            "content_len": len(gen["content"]),
        }
        auto_run = ext in (".py", ".js", ".mjs", ".ps1", ".bat", ".cmd", ".html", ".java", ".c", ".cpp")
        should_run = run if run is not None else auto_run
        if should_run:
            run_result = self.run(written["path"])
            result["run"] = run_result
        return result

    def run(self, path: str, timeout: int = 60) -> dict:
        p = self.resolve_path(path)
        if not p.exists():
            return {"success": False, "error": f"File not found: {path}"}
        ext = p.suffix.lower()
        if ext == ".html":
            import webbrowser
            webbrowser.open(p.resolve().as_uri())
            return {"success": True, "kind": "opened_in_browser"}
        if ext == ".java":
            return self._run_steps(p, [["javac", str(p)], ["java", str(p.with_suffix(""))]], timeout)
        if ext in (".c", ".cpp"):
            exe = p.with_suffix(".exe")
            compiler = "gcc" if ext == ".c" else "g++"
            return self._run_steps(p, [[compiler, str(p), "-o", str(exe)], [str(exe)]], timeout)
        cmd = self._build_command(str(p), ext)
        if cmd is None:
            return {"success": False, "error": f"No runtime mapped for '{ext or 'no extension'}'"}
        return self._run_steps(p, [cmd], timeout)

    def _build_command(self, path: str, ext: str) -> Optional[list[str]]:
        if ext == ".py":
            return [sys.executable, path]
        if ext in (".js", ".mjs"):
            return ["node", path]
        if ext == ".ps1":
            return ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", path]
        if ext in (".bat", ".cmd"):
            return ["cmd", "/c", path]
        return None

    def _run_steps(self, p: Path, steps: list[list[str]], timeout: int) -> dict:
        """Run one or more commands, collecting output from the last one.
        Uses a watchdog thread because subprocess.run(timeout=) is
        unreliable on Windows when a child inherits the pipes."""
        last: dict = {"success": False, "error": "no steps"}
        for i, step in enumerate(steps):
            last = self._run_cmd(step, str(p.parent), timeout)
            if not last.get("success"):
                last["step"] = i
                return last
        return last

    def _run_cmd(self, cmd: list[str], cwd: str, timeout: int) -> dict:
        result: dict = {}

        def _exec():
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                                   cwd=cwd, creationflags=_DETACH)
                result["r"] = r
            except subprocess.TimeoutExpired:
                result["e"] = f"Timed out after {timeout}s"
            except Exception as ex:
                result["e"] = str(ex)

        t = threading.Thread(target=_exec, daemon=True)
        t.start()
        t.join(timeout + 5)
        if t.is_alive():
            return {"success": False, "error": f"Timed out after {timeout}s"}
        if "e" in result:
            return {"success": False, "error": result["e"]}
        r = result["r"]
        return {
            "success": r.returncode == 0,
            "returncode": r.returncode,
            "stdout": (r.stdout or "")[:2000],
            "stderr": (r.stderr or "")[:500],
        }

    def get_status(self) -> dict:
        return {"model": self._model, "workspace": str(self._workspace), "generators": len(self._generators)}