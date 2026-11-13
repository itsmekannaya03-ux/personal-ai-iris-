import logging
import shutil
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger("iris.hands.file_ops")


class FileOps:
    """
    File system operations: create, move, copy, delete, rename, organize.
    Destructive actions (delete) always require confirmation.
    """

    def __init__(self):
        self._working_dir: Optional[Path] = None
        logger.info("FileOps ready")

    def set_working_dir(self, path: str) -> bool:
        """Set the active working directory for project files."""
        try:
            p_str = (path or "").strip()
            if not p_str or p_str.lower() in ("any", "active", "folder", "project", "the folder", "this folder", "workspace"):
                p = Path(r"c:\Users\itsme\Desktop\IRIS-AI")
                if not p.exists():
                    p = self._get_base_dirs().get("desktop")
            else:
                p = Path(path).expanduser().resolve()
                if not (p.exists() and p.is_dir()):
                    desktop = self._get_base_dirs().get("desktop")
                    if desktop and (desktop / path).exists():
                        p = desktop / path
            if p and p.exists() and p.is_dir():
                self._working_dir = p
                logger.info(f"FileOps working directory set to: {self._working_dir}")
                return True
        except Exception as e:
            logger.warning(f"Failed to set working directory '{path}': {e}")
        return False

    def get_working_dir(self) -> Optional[Path]:
        return self._working_dir

    @staticmethod
    def _get_base_dirs() -> dict[str, Path]:
        user_home = Path.home()
        real_desktop = user_home / "OneDrive" / "Desktop"
        if not real_desktop.exists():
            real_desktop = user_home / "Desktop"

        real_documents = user_home / "OneDrive" / "Documents"
        if not real_documents.exists():
            real_documents = user_home / "Documents"

        real_downloads = user_home / "Downloads"
        return {
            "desktop": real_desktop,
            "documents": real_documents,
            "downloads": real_downloads,
            "pictures": user_home / "Pictures",
            "videos": user_home / "Videos",
            "music": user_home / "Music",
        }

    def resolve_target_path(self, path: str, default_name: str = "file.txt") -> Path:
        import re
        p = Path(path).expanduser()
        if p.is_absolute():
            return p

        raw = path.strip()
        # 1. Strip content specification if present
        raw_no_content = re.split(r"\s+(?:with\s+content|and\s+content|with|content|write|type)\s+", raw, maxsplit=1, flags=re.I)[0].strip()

        bases = self._get_base_dirs()
        path_lower = raw_no_content.lower()

        # 2. Determine base directory (respect active working directory for project work)
        if self._working_dir and any(w in path_lower for w in ("project", "work", "workspace", "here", "this folder")):
            base_dir = self._working_dir
        elif "download" in path_lower:
            base_dir = bases["downloads"]
        elif "document" in path_lower:
            base_dir = bases["documents"]
        elif "picture" in path_lower or "photo" in path_lower:
            base_dir = bases["pictures"]
        elif "music" in path_lower:
            base_dir = bases["music"]
        elif "video" in path_lower:
            base_dir = bases["videos"]
        elif "desktop" in path_lower:
            base_dir = bases["desktop"]
        elif self._working_dir:
            base_dir = self._working_dir
        else:
            base_dir = bases["desktop"]

        # 3. Detect subfolder: e.g. "in F.R.I.D.A.Y folder on desktop", "inside F.R.I.D.A.Y", "in my_project folder"
        subfolder = None
        m_sub = re.search(r"(?:in|inside|into)\s+(?:the\s+|my\s+)?([a-zA-Z0-9_\-\. ]+?)\s+(?:folder|dir|directory)", raw_no_content, re.I)
        if m_sub:
            cand_sub = m_sub.group(1).strip(" '\"")
            if cand_sub.lower() not in ("desktop", "downloads", "documents", "pictures", "videos", "music", "workspace"):
                subfolder = cand_sub
        if not subfolder:
            m_sub2 = re.search(r"(?:in|inside|into)\s+(?:the\s+|my\s+)?([a-zA-Z0-9_\-\. ]+?)(?:\s+(?:which\s+is\s+)?(?:there\s+)?(?:in|on|at)\s+(?:the\s+|my\s+)?(?:desktop|downloads|documents|pictures|photos|videos|music))", raw_no_content, re.I)
            if m_sub2:
                cand_sub = m_sub2.group(1).strip(" '\"")
                if cand_sub.lower() not in ("desktop", "downloads", "documents", "pictures", "videos", "music", "workspace"):
                    subfolder = cand_sub

        target_dir = base_dir
        if subfolder:
            # Check if subfolder already exists with exact or fuzzy match in base_dir
            matched_sub = None
            if base_dir.exists():
                for item in os.listdir(base_dir):
                    if item.lower() == subfolder.lower():
                        matched_sub = item
                        break
                    clean_item = re.sub(r"[^a-zA-Z0-9]", "", item).lower()
                    clean_sub = re.sub(r"[^a-zA-Z0-9]", "", subfolder).lower()
                    if clean_item and clean_item == clean_sub:
                        matched_sub = item
                        break
            target_dir = base_dir / (matched_sub or subfolder)

        try:
            target_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

        # 4. Extract filename with negative folder or negative file phrasing handling
        clean_s = raw_no_content
        # Detect and strip negative folder phrasing (e.g. "not the folder", "not a folder", "not folder")
        has_negative_folder = bool(re.search(r"\bnot\s+(?:the\s+|a\s+)?(?:folder|dir|directory)\b", clean_s, re.I))
        if has_negative_folder:
            clean_s = re.sub(r"\bnot\s+(?:the\s+|a\s+)?(?:folder|dir|directory)\b", "", clean_s, flags=re.I).strip()

        # Detect and strip negative file phrasing (e.g. "not files", "not the file", "but not files", "not file")
        has_negative_file = bool(re.search(r"\b(?:but\s+)?not\s+(?:the\s+|a\s+)?files?\b", clean_s, re.I) or re.search(r"\bfolders?\s+(?:not|but\s+not)\s+files?\b", clean_s, re.I))
        if has_negative_file:
            clean_s = re.sub(r"\b(?:but\s+)?not\s+(?:the\s+|a\s+)?files?\b", "", clean_s, flags=re.I).strip()

        if subfolder:
            clean_s = re.sub(r"(?:in|inside|into)\s+(?:the\s+|my\s+)?" + re.escape(subfolder) + r"(?:\s+(?:folder|dir|directory))?", "", clean_s, flags=re.I).strip()

        if has_negative_file:
            is_folder_request = True
        elif has_negative_folder:
            is_folder_request = False
        else:
            is_folder_request = bool(re.search(r"\b(folder|dir|directory)\b", clean_s, re.I) and not re.search(r"\bfile\b", clean_s, re.I))

        m_file = None
        if not is_folder_request:
            m_file = re.search(r"\b([a-zA-Z0-9_\-]+\.(?:txt|py|js|html|css|json|md|csv|docx|pdf|xml|bat|cmd|ps1|sh|c|cpp|h|java|zip|tar|gz|png|jpg))\b", clean_s, re.I)

        if m_file:
            filename = m_file.group(1).strip()
        else:
            m_named = re.search(r"(?:called|named|name\s+it\s+(?:as\s+)?)\s*['\"]?([a-zA-Z0-9_\-\. ]+?)['\"]?$", clean_s, flags=re.I)
            if m_named:
                filename = m_named.group(1).strip()
            else:
                s_clean = re.sub(r"^(?:create|make|build|add|new)\s+(?:a\s+|the\s+)?(?:folder|directory|file)\s*", "", clean_s, flags=re.I).strip()
                s_clean = re.sub(r"(?:\s+(?:which\s+is\s+)?(?:there\s+)?(?:in|on|at)\s+(?:the\s+|my\s+)?(?:desktop|downloads|documents|pictures|photos|videos|music))+$", "", s_clean, flags=re.I).strip()
                s_clean = re.sub(r"^(?:in|on|at)\s+(?:the\s+|my\s+)?(?:desktop|downloads|documents|pictures|photos|videos|music)\s*", "", s_clean, flags=re.I).strip()
                s_clean = re.sub(r"\b(?:on\s+desktop|in\s+desktop|desktop|in\s+downloads|downloads|in\s+documents|documents|in\s+workspace|workspace)\b", "", s_clean, flags=re.I).strip()
                s_clean = re.sub(r"^(?:in|on|at|called|named|a|the|not|the\s+folder|folder)\s+", "", s_clean, flags=re.I).strip()
                extracted = s_clean.strip(" /\\\"'")
                if not extracted or extracted.lower() in ("not the folder", "not a folder", "not folder", "file", "a file", "the file", "folder", "a folder", "the folder", "not files", "but not files"):
                    filename = default_name
                else:
                    filename = extracted

        return target_dir / filename

    def resolve_existing_path(self, path: str) -> Optional[Path]:
        import re
        p = Path(path).expanduser()
        if p.exists():
            return p

        bases = self._get_base_dirs()
        path_lower = path.lower()

        s = re.sub(r"^(?:the\s+)?(?:file|folder|dir|directory)\s+", "", path.strip(), flags=re.I).strip()
        s_clean = re.sub(r"(?:\s+(?:which\s+is\s+)?(?:there\s+)?(?:from|in|on|at)\s+(?:the\s+|my\s+)?(?:desktop|downloads|documents|pictures|photos|videos|music))+$", "", s, flags=re.I).strip()
        s_clean = re.sub(r"^(?:from|in|on|at)\s+(?:the\s+|my\s+)?(?:desktop|downloads|documents|pictures|photos|videos|music)\s*", "", s_clean, flags=re.I).strip()
        s_clean = re.sub(r"\b(?:folder|dir|directory)\b", "", s_clean, flags=re.I).strip(" '\"")

        if "document" in path_lower:
            search_bases = [bases["documents"], bases["desktop"], bases["downloads"]]
        elif "download" in path_lower:
            search_bases = [bases["downloads"], bases["desktop"], bases["documents"]]
        else:
            search_bases = [bases["desktop"], bases["documents"], bases["downloads"]]

        sub = None
        m_sub = re.search(r"(?:in|inside|into)\s+(?:the\s+|my\s+)?([a-zA-Z0-9_\-\. ]+?)(?:\s+(?:folder|dir|directory))?$", s_clean, re.I)
        if m_sub and m_sub.group(1).lower() not in ("desktop", "downloads", "documents", "pictures", "videos", "music"):
            sub = m_sub.group(1).strip(" '\"")
            s_clean = re.sub(r"\s+(?:in|inside|into)\s+(?:the\s+|my\s+)?" + re.escape(sub) + r"(?:\s+(?:folder|dir|directory))?$", "", s_clean, flags=re.I).strip(" '\"")

        for b in search_bases:
            if not b.exists():
                continue
            cur_base = b
            if sub:
                for item in os.listdir(b):
                    if item.lower() == sub.lower() or re.sub(r"[^a-zA-Z0-9]", "", item).lower() == re.sub(r"[^a-zA-Z0-9]", "", sub).lower():
                        cur_base = b / item
                        break

            # 1. Direct match
            cand = cur_base / s_clean
            if cand.exists():
                return cand

            # 2. Fuzzy match inside cur_base
            clean_target = re.sub(r"[^a-zA-Z0-9]", "", s_clean).lower()
            if cur_base.exists() and cur_base.is_dir():
                for item in os.listdir(cur_base):
                    clean_item = re.sub(r"[^a-zA-Z0-9]", "", item).lower()
                    if clean_item and clean_item == clean_target:
                        return cur_base / item

            # 3. Check immediate subdirectories
            if not sub and cur_base.exists() and cur_base.is_dir():
                for sub_dir in cur_base.iterdir():
                    if sub_dir.is_dir():
                        cand = sub_dir / s_clean
                        if cand.exists():
                            return cand
                        for item in os.listdir(sub_dir):
                            clean_item = re.sub(r"[^a-zA-Z0-9]", "", item).lower()
                            if clean_item and clean_item == clean_target:
                                return sub_dir / item
        return None

    def resolve_target_dir(self, dst: str) -> Path:
        bases = self._get_base_dirs()
        d = dst.lower().strip()

        if d in ("desktop", "the desktop", "my desktop", "on desktop", "to desktop"):
            return bases["desktop"]
        if d in ("documents", "the documents", "my documents", "in documents", "to documents"):
            return bases["documents"]
        if d in ("downloads", "the downloads", "my downloads", "in downloads", "to downloads"):
            return bases["downloads"]

        existing = self.resolve_existing_path(dst)
        if existing and existing.is_dir():
            return existing

        return self.resolve_target_path(dst, default_name="New Folder")

    def create_file(self, path: str, content: str = "") -> dict:
        try:
            p = self.resolve_target_path(path, default_name="file.txt")
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            logger.info(f"Created file: {p}")
            return {"success": True, "path": str(p), "name": p.name}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def append_file(self, path: str, content: str) -> dict:
        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            with p.open("a", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"Appended text to file: {path}")
            return {"success": True, "path": path, "appended_length": len(content)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def search_files(self, directory: str, pattern: str = "*") -> dict:
        try:
            p = Path(directory)
            if not p.exists():
                return {"error": "directory_not_found"}
            matches = []
            for item in p.rglob(pattern):
                matches.append({
                    "name": item.name,
                    "path": str(item),
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else 0,
                })
                if len(matches) >= 200:
                    break
            return {"success": True, "directory": directory, "matches": matches, "total": len(matches)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_directory(self, path: str) -> dict:
        try:
            p = self.resolve_target_path(path, default_name="New Folder")
            p.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {p}")
            return {"success": True, "path": str(p), "name": p.name}
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
            resolved_src = self.resolve_existing_path(src)
            if not resolved_src or not resolved_src.exists():
                return {"success": False, "error": f"Source item '{src}' not found"}

            resolved_dst = self.resolve_target_dir(dst)
            # If destination is a directory, move inside it
            if resolved_dst.is_dir():
                target_path = resolved_dst / resolved_src.name
            else:
                target_path = resolved_dst
                target_path.parent.mkdir(parents=True, exist_ok=True)

            if target_path.exists() and target_path != resolved_src:
                if target_path.is_file():
                    target_path.unlink()

            final_dest = shutil.move(str(resolved_src), str(target_path))
            logger.info(f"Moved {resolved_src} → {final_dest}")
            return {
                "success": True,
                "action": "move",
                "source": str(resolved_src),
                "destination": str(final_dest),
                "name": resolved_src.name,
                "target_dir": str(resolved_dst if resolved_dst.is_dir() else resolved_dst.parent),
            }
        except Exception as e:
            logger.error(f"Move failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def rename(self, path: str, new_name: str) -> dict:
        try:
            import re
            resolved_src = self.resolve_existing_path(path)
            if not resolved_src or not resolved_src.exists():
                return {"success": False, "error": f"Item '{path}' not found to rename"}

            clean_name = re.sub(r"^(?:to|as|called|named|into)\s+", "", new_name, flags=re.I).strip(" '\"")
            clean_name = re.sub(r"(?:\s+(?:which\s+is\s+)?(?:there\s+)?(?:in|on|at)\s+(?:the\s+|my\s+)?(?:desktop|downloads|documents|pictures|photos|videos|music))+$", "", clean_name, flags=re.I).strip(" '\"")
            if not clean_name:
                return {"success": False, "error": "New name cannot be empty"}
            if resolved_src.is_file() and "." not in clean_name and resolved_src.suffix:
                clean_name += resolved_src.suffix

            new_path = resolved_src.parent / clean_name
            if new_path.exists() and new_path != resolved_src:
                if new_path.is_file():
                    new_path.unlink()
                else:
                    return {"success": False, "error": f"A folder named '{clean_name}' already exists in {resolved_src.parent}"}

            resolved_src.rename(new_path)
            logger.info(f"Renamed {resolved_src} → {clean_name}")
            return {
                "success": True,
                "action": "rename",
                "old_path": str(resolved_src),
                "new_path": str(new_path),
                "old_name": resolved_src.name,
                "new_name": clean_name,
            }
        except Exception as e:
            logger.error(f"Rename failed: {e}", exc_info=True)
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
