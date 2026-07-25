import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger("igris.vision.file_scanner")


class FileScanner:
    """
    Scans folders and files to understand what's stored where.
    Does NOT open private content unless explicitly requested.
    """

    MAX_DEPTH = 3
    SKIP_DIRS = {
        "__pycache__", ".git", "node_modules", ".venv", "venv",
        ".pytest_cache", ".idea", ".vscode", ".DS_Store", "dist", "build",
    }

    def __init__(self):
        logger.info("FileScanner ready")

    def scan_folder(self, folder_path: str, depth: int = 0) -> dict:
        if depth > self.MAX_DEPTH:
            return {"path": folder_path, "type": "max_depth"}
        path = Path(folder_path)
        if not path.exists():
            return {"path": folder_path, "error": "not_found"}
        if not path.is_dir():
            return {"path": folder_path, "error": "not_a_directory"}

        try:
            entries = []
            for entry in path.iterdir():
                if entry.name.startswith(".") or entry.name in self.SKIP_DIRS:
                    continue
                if entry.is_dir():
                    entries.append({
                        "name": entry.name,
                        "type": "directory",
                        "children": self.scan_folder(str(entry), depth + 1) if depth < self.MAX_DEPTH else [],
                    })
                else:
                    stat = entry.stat()
                    entries.append({
                        "name": entry.name,
                        "type": "file",
                        "size": stat.st_size,
                        "modified": stat.st_mtime,
                    })
            return {"path": folder_path, "type": "directory", "entries": entries, "total": len(entries)}
        except PermissionError:
            return {"path": folder_path, "error": "permission_denied"}
        except Exception as e:
            logger.error(f"Scan failed for {folder_path}: {e}")
            return {"path": folder_path, "error": str(e)}

    def scan_file(self, file_path: str, read_content: bool = False) -> dict:
        path = Path(file_path)
        if not path.exists():
            return {"error": "not_found"}
        if path.is_dir():
            return {"error": "is_a_directory"}

        result = {
            "name": path.name,
            "size": path.stat().st_size,
            "extension": path.suffix,
            "modified": path.stat().st_mtime,
        }

        if read_content:
            try:
                text_extensions = {".txt", ".md", ".py", ".js", ".jsx", ".ts", ".tsx", ".json", ".yaml", ".yml", ".csv", ".log", ".ini", ".cfg", ".conf"}
                if path.suffix.lower() in text_extensions:
                    content = path.read_text(encoding="utf-8", errors="ignore")
                    result["content"] = content[:2000]
                    result["truncated"] = len(content) > 2000
            except Exception as e:
                result["read_error"] = str(e)

        return result

    def find_files(self, folder_path: str, pattern: str, max_results: int = 20) -> list[dict]:
        path = Path(folder_path)
        if not path.exists():
            return []
        results = []
        try:
            for p in path.rglob(pattern):
                if p.name.startswith("."):
                    continue
                if len(results) >= max_results:
                    break
                results.append({
                    "path": str(p),
                    "name": p.name,
                    "size": p.stat().st_size,
                    "modified": p.stat().st_mtime,
                })
        except PermissionError:
            pass
        return results

    def get_status(self) -> dict:
        return {"max_depth": self.MAX_DEPTH}
