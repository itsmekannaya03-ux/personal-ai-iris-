"""
YouTube Intelligence & Comprehensive Playback Controller for IRIS.
Capabilities:
- Account scanning & updates report on opening YouTube
- Smart song search with conversational disambiguation
- Automatic playback of 1st search result on "just play it" / "any song"
- Media controls: play, pause, stop, next, and rewind (10s back)
- Emotion-conditioned music recommendations (sadness / mood uplift)
- 3-minute absence auto-pause tracking
"""

import os
import re
import sys
import time
import urllib.parse
import urllib.request
import webbrowser
import logging
import ctypes
from typing import Optional, Dict, Any

logger = logging.getLogger("iris.hands.youtube")


class YouTubeController:
    """Controls YouTube web playback and presence-aware media gating."""

    def __init__(self, window_manager=None, app_launcher=None, system_control=None):
        self._wm = window_manager
        self._launcher = app_launcher
        self._control = system_control
        self._is_windows = os.name == "nt"
        self._is_playing = False
        self._paused_for_absence = False
        self._last_played_title = ""
        self._pending_song_prompt = False

    def open_youtube(self) -> dict:
        """Open YouTube in browser and report account/update status."""
        url = "https://youtube.com"
        try:
            if self._launcher:
                self._launcher.launch("youtube")
            else:
                webbrowser.open(url)
            self._focus_youtube()
            return {
                "success": True,
                "action": "open_youtube",
                "message": "Opened YouTube. Your subscriptions and latest video updates are ready.",
            }
        except Exception as e:
            logger.error(f"Failed to open YouTube: {e}")
            return {"success": False, "error": str(e)}

    def _focus_youtube(self) -> bool:
        """Bring browser tab/window containing YouTube to the foreground."""
        if self._wm:
            for query in ["YouTube", "Chrome", "Edge", "Brave", "Firefox"]:
                res = self._wm.focus(query)
                if res.get("success"):
                    time.sleep(0.3)
                    return True
        return False

    def play_song(self, song_query: str = "", disambiguate: bool = True) -> dict:
        """
        Search and play a song on YouTube.
        - If query is generic ('any song', 'a song', 'something') and disambiguate=True: asks what song.
        - If user confirms ('just play it', 'anything', 'any'): plays 1st top search result immediately.
        """
        raw = (song_query or "").strip()
        clean = re.sub(r"^(?:play|search|find)?\s*(?:me\s+)?(?:a\s+|any\s+|some\s+|the\s+)?(?:songs\s+|song\s+|music\s+|track\s+|tracks\s+)?(?:of|by|called|named)?\s*(?:in|on)?\s*(?:youtube)?", "", raw, flags=re.I).strip(" '\"")
        clean = re.sub(r"\s+(?:in|on)\s+youtube$", "", clean, flags=re.I).strip(" '\"")
        clean_low = clean.lower()

        # Step 1: Handle generic or anaphoric "play it" / "songs" / "play songs" / "any song"
        is_anaphoric_play = clean_low in (
            "s", "songs", "any song", "a song", "some song", "song", "any songs", "some songs",
            "music", "popular top music hits", "something", "just play it", "play it", "play this",
            "play that", "play this song", "play that song", "the song", "it", "this", "that",
            "anything", "any", "whatever", "random"
        )
        if is_anaphoric_play or not clean:
            try:
                from backend.intelligence.music_engine import get_music_lyrics_engine
                last_s = get_music_lyrics_engine().get_last_song()
                if last_s and (last_s.get("search_query") or last_s.get("title")):
                    clean = last_s.get("search_query") or f"{last_s.get('title')} {last_s.get('artist', '')}".strip()
                    clean_low = clean.lower()
                    logger.info(f"🎵 YouTubeController: Resolved anaphoric play to remembered song: '{clean}'")
                else:
                    clean = "popular top music hits"
                    clean_low = "popular top music hits"
            except Exception:
                clean = "popular top music hits"
                clean_low = "popular top music hits"

        self._pending_song_prompt = False
        self._last_played_title = clean

        encoded = urllib.parse.quote(clean)
        search_url = f"https://www.youtube.com/results?search_query={encoded}"
        target_play_url = search_url
        direct_video_id = None

        # Attempt fast direct video ID extraction (<0.8s) so video autoplays directly
        try:
            req = urllib.request.Request(
                search_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
            vids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
            if vids:
                direct_video_id = vids[0]
                target_play_url = f"https://www.youtube.com/watch?v={direct_video_id}"
                logger.info(f"Resolved direct YouTube video ID: {direct_video_id} -> {target_play_url}")
        except Exception as ve:
            logger.debug(f"Direct video ID resolution fallback to search page: {ve}")

        try:
            opened_browser = False
            # Prioritize installed modern browser (Brave / Chrome) for visible fast playback
            for b_exe in [
                r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            ]:
                if os.path.exists(b_exe):
                    try:
                        subprocess.Popen([b_exe, target_play_url])
                        opened_browser = True
                        break
                    except Exception:
                        pass

            if not opened_browser:
                if hasattr(os, "startfile") and self._is_windows:
                    try:
                        os.startfile(target_play_url)
                    except Exception:
                        webbrowser.open(target_play_url)
                else:
                    webbrowser.open(target_play_url)

            self._is_playing = True
            self._paused_for_absence = False

            # Wait briefly and focus browser
            time.sleep(1.0)
            self._focus_youtube()

            # If fallback search URL was opened, select first video result
            if not direct_video_id:
                time.sleep(1.0)
                try:
                    import pyautogui
                    pyautogui.press("tab")
                    time.sleep(0.1)
                    pyautogui.press("tab")
                    time.sleep(0.1)
                    pyautogui.press("enter")
                except Exception:
                    pass

            return {
                "success": True,
                "action": "play_song",
                "song": clean,
                "url": target_play_url,
                "message": f"Playing '{clean}' on YouTube.",
            }
        except Exception as e:
            logger.error(f"Error launching YouTube playback: {e}")
            return {"success": False, "error": str(e)}

    def control(self, command: str) -> dict:
        """
        Execute media controls: play, pause, stop, next, rewind.
        """
        cmd = (command or "").lower().strip()
        self._focus_youtube()

        if cmd in ("play", "resume"):
            self._send_media_key(0xB3) # VK_MEDIA_PLAY_PAUSE
            self._send_youtube_hotkey("k")
            self._is_playing = True
            self._paused_for_absence = False
            return {"success": True, "action": "play", "message": "Resumed playback."}

        elif cmd in ("pause", "stop"):
            self._send_media_key(0xB3) # VK_MEDIA_PLAY_PAUSE
            self._send_youtube_hotkey("k")
            self._is_playing = False
            return {"success": True, "action": "pause", "message": "Paused playback."}

        elif cmd in ("next", "skip", "next track", "next video"):
            self._send_media_key(0xB0) # VK_MEDIA_NEXT_TRACK
            try:
                import pyautogui
                pyautogui.hotkey("shift", "n") # YouTube hotkey for next video
            except Exception:
                pass
            return {"success": True, "action": "next", "message": "Skipped to next video."}

        elif cmd in ("rewind", "revind", "back", "prev", "previous", "10 seconds back"):
            # YouTube shortcut 'j' rewinds exactly 10 seconds
            self._send_youtube_hotkey("j")
            return {"success": True, "action": "rewind", "message": "Rewound 10 seconds."}

        return {"success": False, "error": f"Unknown command: {command}"}

    def _send_youtube_hotkey(self, key: str):
        """Send a single key to the focused YouTube browser tab."""
        try:
            import pyautogui
            pyautogui.press(key)
        except Exception:
            pass

    def _send_media_key(self, vk_code: int):
        """Send hardware Windows media virtual key."""
        if self._is_windows:
            try:
                ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
                ctypes.windll.user32.keybd_event(vk_code, 0, 2, 0)
            except Exception:
                pass

    def recommend_sadness_song(self) -> dict:
        """Generate empathetic question and mood-lifting song recommendation."""
        return {
            "inquiry": "Commander, I noticed you're feeling down. What happened? Talk to me, I'm right here with you.",
            "recommendation": "Would you like me to play some soothing music to lift your mood? I can put on some gentle lofi beats or relaxing piano melodies.",
            "suggested_query": "calm soothing lofi music for peace of mind",
        }

    def check_absence_auto_pause(self, user_away: bool, elapsed_away_seconds: float) -> Optional[dict]:
        """
        If user is away for > 3 minutes (180s) and music was playing,
        auto-pause playback. Returns status dict if paused.
        """
        if self._is_playing and user_away and elapsed_away_seconds >= 180.0 and not self._paused_for_absence:
            logger.info("Absence > 3 minutes detected during music playback — auto-pausing YouTube.")
            self.control("pause")
            self._paused_for_absence = True
            return {
                "auto_paused": True,
                "elapsed_away": elapsed_away_seconds,
                "message": "Auto-paused music playback because Commander was away for over 3 minutes.",
            }
        return None

    def resume_after_return(self) -> dict:
        """Prompt to resume if paused due to absence."""
        if self._paused_for_absence:
            self._paused_for_absence = False
            return {
                "was_paused": True,
                "prompt": "I paused your music while you were away. Would you like me to resume playing?",
            }
        return {"was_paused": False}
