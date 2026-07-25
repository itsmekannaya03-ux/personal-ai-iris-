import logging
import shutil
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger("igris.hands.file_ops")


class FileOps:
    """
    File system operations: create, move, copy, delete, rename, organize.
    Destructive actions (delete) always require confirmation.
    """

    def __init__(self):
        logger.info("FileOps ready")

    def create_file(self, path: str, content: str = "") -> dict:
        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content)
            logger.info(f"Created file: {path}")
            return {"success": True, "path": path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_directory(self, path: str) -> dict:
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {path}")
            return {"success": True, "path": path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def read_file(self, path: str, max_size: int = 100_000) -> dict:
        try:
            p = Path(path)
            if not p.exists():
                return {"error": "not_found"}
            if p.stat().st_size > max_size:
                return {"error": "file_too_large", "size": p.stat().st_size}
            content = p.read_text(encoding="utf-8", errors="replace")
            return {"success": True, "content": content, "size": len(content)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def copy(self, src: str, dst: str) -> dict:
        try:
            src_p = Path(src)
            if src_p.is_dir():
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
            logger.info(f"Copied {src} → {dst}")
            return {"success": True, "source": src, "destination": dst}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def move(self, src: str, dst: str) -> dict:
        try:
            shutil.move(src, dst)
            logger.info(f"Moved {src} → {dst}")
            return {"success": True, "source": src, "destination": dst}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def rename(self, path: str, new_name: str) -> dict:
        try:
            p = Path(path)
            new_path = p.parent / new_name
            p.rename(new_path)
            logger.info(f"Renamed {path} → {new_name}")
            return {"success": True, "old_path": path, "new_path": str(new_path)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete(self, path: str, force: bool = False) -> dict:
        if not force:
            return {"success": False, "error": "confirmation_required", "message": f"Are you sure you want to delete '{path}'? This cannot be undone."}
        try:
            p = Path(path)
            if not p.exists():
                return {"error": "not_found"}
            if p.is_dir():
                shutil.rmtree(path)
            else:
                p.unlink()
            logger.info(f"Deleted: {path}")
            return {"success": True, "path": path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_directory(self, path: str) -> dict:
        try:
            p = Path(path)
            if not p.exists():
                return {"error": "not_found"}
            entries = []
            for entry in p.iterdir():
                entries.append({
                    "name": entry.name,
                    "type": "directory" if entry.is_dir() else "file",
                    "size": entry.stat().st_size if entry.is_file() else 0,
                    "modified": entry.stat().st_mtime,
                })
            entries.sort(key=lambda e: (e["type"] != "directory", e["name"].lower()))
            return {"success": True, "path": path, "entries": entries, "total": len(entries)}
        except PermissionError:
            return {"error": "permission_denied"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_size(self, path: str) -> dict:
        try:
            p = Path(path)
            if not p.exists():
                return {"error": "not_found"}
            if p.is_file():
                size = p.stat().st_size
            else:
                size = sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
            return {"success": True, "path": path, "size": size, "size_readable": self._format_size(size)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _format_size(self, size: int) -> str:
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"

    def get_status(self) -> dict:
        return {"ready": True}
