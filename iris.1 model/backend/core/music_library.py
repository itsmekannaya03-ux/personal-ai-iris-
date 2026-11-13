"""
Music Library — Playlist and media management.

Manages a local music library with:
  - Song metadata (title, artist, path, album)
  - Playlist CRUD
  - YouTube song search
  - Favorites
"""

import os
import json
import logging
import time
from typing import Optional
from dataclasses import dataclass, field

logger = logging.getLogger("iris.music")


@dataclass
class Song:
    title: str
    artist: str = "Unknown"
    path: str = ""
    album: str = ""
    duration: int = 0
    favorite: bool = False
    added_at: float = field(default_factory=time.time)


class MusicLibrary:
    """
    Manages the AI's music library with playlist support.
    """

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or os.path.join(
            os.path.expanduser("~"), ".iris", "music_library.json"
        )
        self._songs: list[Song] = []
        self._playlists: dict[str, list[int]] = {}  # name -> indices
        self.load()
        logger.info(f"Music library initialized ({len(self._songs)} songs)")

    def load(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r") as f:
                    data = json.load(f)
                self._songs = [Song(**s) for s in data.get("songs", [])]
                self._playlists = data.get("playlists", {})
            except Exception as e:
                logger.error(f"Failed to load music library: {e}")

    def save(self):
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            data = {
                "songs": [s.__dict__ for s in self._songs],
                "playlists": self._playlists,
                "updated_at": time.time(),
            }
            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save music library: {e}")

    def add_song(self, title: str, artist: str = "Unknown", path: str = "",
                 album: str = "", duration: int = 0) -> Song:
        song = Song(title=title, artist=artist, path=path, album=album, duration=duration)
        self._songs.append(song)
        self.save()
        logger.info(f"Song added: {title} by {artist}")
        return song

    def remove_song(self, index: int) -> bool:
        if 0 <= index < len(self._songs):
            removed = self._songs.pop(index)
            # Clean up playlist references
            for pl_name in list(self._playlists.keys()):
                self._playlists[pl_name] = [
                    i for i in self._playlists[pl_name] if i != index
                ]
            self.save()
            logger.info(f"Song removed: {removed.title}")
            return True
        return False

    def search(self, query: str) -> list[dict]:
        query_lower = query.lower()
        results = []
        for i, song in enumerate(self._songs):
            if query_lower in song.title.lower() or query_lower in song.artist.lower():
                results.append({"index": i, "title": song.title, "artist": song.artist, "path": song.path})
        return results

    def get_all(self) -> list[dict]:
        return [
            {"index": i, "title": s.title, "artist": s.artist, "path": s.path,
             "album": s.album, "favorite": s.favorite}
            for i, s in enumerate(self._songs)
        ]

    def toggle_favorite(self, index: int) -> bool:
        if 0 <= index < len(self._songs):
            self._songs[index].favorite = not self._songs[index].favorite
            self.save()
            return self._songs[index].favorite
        return False

    def create_playlist(self, name: str) -> bool:
        if name not in self._playlists:
            self._playlists[name] = []
            self.save()
            return True
        return False

    def add_to_playlist(self, playlist_name: str, song_index: int) -> bool:
        if playlist_name in self._playlists and 0 <= song_index < len(self._songs):
            if song_index not in self._playlists[playlist_name]:
                self._playlists[playlist_name].append(song_index)
                self.save()
            return True
        return False

    def get_playlist(self, name: str) -> list[dict]:
        indices = self._playlists.get(name, [])
        return [
            {"index": i, "title": self._songs[i].title, "artist": self._songs[i].artist,
             "path": self._songs[i].path}
            for i in indices if 0 <= i < len(self._songs)
        ]

    def list_playlists(self) -> list[str]:
        return list(self._playlists.keys())

    def get_status(self) -> dict:
        return {
            "song_count": len(self._songs),
            "playlist_count": len(self._playlists),
            "storage_path": self.storage_path,
        }


class YouTubeSearcher:
    """
    Search YouTube for songs/videos.
    Uses yt-search if available, otherwise falls back to web search.
    """

    def __init__(self):
        self._available = False
        self._check_deps()

    def _check_deps(self):
        try:
            import yt_dlp
            self._ytdlp_available = True
        except ImportError:
            self._ytdlp_available = False
        self._available = self._ytdlp_available

    def search(self, query: str, max_results: int = 5) -> list[dict]:
        try:
            from yt_dlp import YoutubeDL
            ydl = YoutubeDL({"quiet": True, "no_warnings": True, "extract_flat": True})
            results = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
            entries = []
            if results and "entries" in results:
                for entry in results["entries"][:max_results]:
                    if entry:
                        entries.append({
                            "title": entry.get("title", ""),
                            "url": f"https://youtube.com/watch?v={entry.get('id', '')}",
                            "duration": entry.get("duration", 0),
                            "channel": entry.get("channel", ""),
                        })
            return entries
        except ImportError:
            return [{"error": "yt-dlp not installed"}]
        except Exception as e:
            logger.error(f"YouTube search failed: {e}")
            return [{"error": str(e)}]

    def get_status(self) -> dict:
        return {"available": self._available, "ytdlp": self._ytdlp_available}
