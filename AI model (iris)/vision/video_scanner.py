import logging
import os
import tempfile
from typing import Optional

logger = logging.getLogger("igris.vision.video_scanner")


class VideoScanner:
    """
    Extracts frames from video files and describes content.
    """

    def __init__(self, image_analyzer=None):
        self._image_analyzer = image_analyzer
        logger.info("VideoScanner ready")

    def set_image_analyzer(self, analyzer):
        self._image_analyzer = analyzer

    def extract_frames(self, video_path: str, interval_sec: float = 5.0, max_frames: int = 10) -> list[str]:
        try:
            import cv2
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_interval = int(fps * interval_sec)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            frames = []
            frame_count = 0
            saved = 0
            tmp_dir = tempfile.mkdtemp(prefix="igris_video_")
            while saved < max_frames:
                ret, frame = cap.read()
                if not ret:
                    break
                if frame_count % frame_interval == 0:
                    path = os.path.join(tmp_dir, f"frame_{saved:04d}.jpg")
                    cv2.imwrite(path, frame)
                    frames.append(path)
                    saved += 1
                frame_count += 1
            cap.release()
            logger.info(f"Extracted {len(frames)} frames from {video_path}")
            return frames
        except ImportError:
            logger.warning("opencv-python not installed — video scanning unavailable")
            return []
        except Exception as e:
            logger.error(f"Video frame extraction failed: {e}")
            return []

    def describe_frames(self, frames: list[str]) -> list[dict]:
        if not self._image_analyzer:
            return [{"frame": f, "error": "No image analyzer available"} for f in frames]
        results = []
        for frame_path in frames:
            desc = self._image_analyzer.describe(frame_path)
            results.append({"frame": frame_path, "description": desc})
        return results

    def scan(self, video_path: str, interval_sec: float = 5.0, max_frames: int = 10) -> list[dict]:
        frames = self.extract_frames(video_path, interval_sec, max_frames)
        if not frames:
            return []
        descriptions = self.describe_frames(frames)
        self._cleanup_frames(frames)
        return descriptions

    def _cleanup_frames(self, frames: list[str]):
        for f in frames:
            try:
                os.remove(f)
            except Exception:
                pass
        parent = os.path.dirname(frames[0]) if frames else ""
        if parent and os.path.exists(parent):
            try:
                os.rmdir(parent)
            except Exception:
                pass

    def is_available(self) -> bool:
        try:
            import cv2
            return True
        except ImportError:
            return False

    def get_status(self) -> dict:
        return {"available": self.is_available(), "image_analyzer_available": self._image_analyzer is not None}
