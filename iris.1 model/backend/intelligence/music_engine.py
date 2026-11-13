"""
IRIS AI — Music, Lyrics & Singing Recognition Engine
====================================================
Capabilities:
1. Detects when the user is singing, humming, or quoting song lyrics in ANY language
   (Hindi, Telugu, Tamil, Punjabi, Spanish, French, English, etc.).
2. Identifies song title, artist, movie/album, language, and next-line lyrics.
3. Maintains working song memory so subsequent commands ("play it", "play that song")
   resolve directly to the identified track.
4. Generates musical companion responses (discussing the track + singing along).
5. Hybrid recognition: Fast local database of top hits + LLM deep recognition for any song in the world.
"""

import re
import json
import time
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger("iris.music_engine")

# Fast local dictionary for top iconic songs across Hindi, English, and regional languages
POPULAR_SONG_CATALOG = [
    {
        "pattern": r"(?:tum\s+hi\s+ho|ab\s+tum\s+hi\s+ho|zindagi\s+ab\s+tum\s+hi\s+ho|chain\s+bhi\s+mera\s+dard\s+bhi)",
        "title": "Tum Hi Ho",
        "artist": "Arijit Singh",
        "movie_or_album": "Aashiqui 2",
        "language": "Hindi",
        "continuation": "Chain bhi, mera dard bhi... meri aashiqui ab tum hi ho!",
        "backstory": "An iconic romantic anthem from Aashiqui 2 composed by Mithoon that catapulted Arijit Singh to superstar status.",
    },
    {
        "pattern": r"(?:kesariya\s+tera\s+ishq\s+hai\s+piya|rang\s+jaaun\s+jo\s+main\s+haath\s+lagaun|ishq\s+hai\s+piya)",
        "title": "Kesariya",
        "artist": "Arijit Singh, Pritam",
        "movie_or_album": "Brahmāstra",
        "language": "Hindi",
        "continuation": "Beete saare haseen pal tere, saara sansaar tere naam likh doon!",
        "backstory": "A blockbuster romantic melody composed by Pritam with lyrics by Amitabh Bhattacharya for the film Brahmāstra.",
    },
    {
        "pattern": r"(?:sun\s+raha\s+hai\s+na\s+tu|ro\s+raha\s+hoon\s+main|yaara\s+manzilein\s+ruswa)",
        "title": "Sun Raha Hai Na Tu",
        "artist": "Ankit Tiwari",
        "movie_or_album": "Aashiqui 2",
        "language": "Hindi",
        "continuation": "Waqt bhi thehra hai kaise yahan, pal ho na ho kal ka pata!",
        "backstory": "A soaring emotional ballad sung and composed by Ankit Tiwari for Aashiqui 2.",
    },
    {
        "pattern": r"(?:jeene\s+laga\s+hoon|pehle\s+se\s+zyada|pehle\s+se\s+jyada|tumpe\s+marne\s+laga\s+hoon)",
        "title": "Jeene Laga Hoon",
        "artist": "Atif Aslam, Shreya Ghoshal",
        "movie_or_album": "Ramaiya Vastavaiya",
        "language": "Hindi",
        "continuation": "Rehte ho aake jo tum paas mere, tham jaati hai dhadkanein bas yahan!",
        "backstory": "A sweet, melodious romantic track composed by Sachin-Jigar and rendered by Atif Aslam.",
    },
    {
        "pattern": r"(?:channa\s+mereya|achha\s+chalta\s+hoon|mehfil\s+mein\s+teri\s+hum)",
        "title": "Channa Mereya",
        "artist": "Arijit Singh, Pritam",
        "movie_or_album": "Ae Dil Hai Mushkil",
        "language": "Hindi",
        "continuation": "O piya... channa mereya mereya, beliya...",
        "backstory": "A deeply emotional heartbreak masterpiece from Ae Dil Hai Mushkil by Pritam and Arijit Singh.",
    },
    {
        "pattern": r"(?:har\s+ghadi\s+badal\s+rahi\s+hai|kal\s+ho\s+naa?\s+ho|palkon\s+ke\s+chhaon)",
        "title": "Kal Ho Naa Ho",
        "artist": "Sonu Nigam, Shankar-Ehsaan-Loy",
        "movie_or_album": "Kal Ho Naa Ho",
        "language": "Hindi",
        "continuation": "Har pal yahan jee bhar jiyo, jo hai sama, kal ho naa ho!",
        "backstory": "The timeless title track celebrating life and love, sung soulfully by Sonu Nigam.",
    },
    {
        "pattern": r"(?:apna\s+bana\s+le\s+piya|tu\s+mera\s+koi\s+na\s+hoke\s+bhi\s+kuchh\s+laage|kuch\s+lage)",
        "title": "Apna Bana Le",
        "artist": "Arijit Singh, Sachin-Jigar",
        "movie_or_album": "Bhediya",
        "language": "Hindi",
        "continuation": "Apna bana le piya, apna bana le piya... dil ke nagar mein shehar tu basa le!",
        "backstory": "A chart-topping romantic melody by Sachin-Jigar with lyrics by Amitabh Bhattacharya.",
    },
    {
        "pattern": r"(?:raataan\s+lambiyan|kaate\s+kate\s+na\s+katena|chham\s+chham\s+barsa\s+paani)",
        "title": "Raataan Lambiyan",
        "artist": "Jubin Nautiyal, Asees Kaur",
        "movie_or_album": "Shershaah",
        "language": "Hindi",
        "continuation": "Kaate kate na re raataan lambiyan lambiyan re...",
        "backstory": "A beautiful Punjabi-Hindi romantic ballad from the biographical war film Shershaah.",
    },
    {
        "pattern": r"(?:samajavaragamana|kallathoni\s+kalchana|ala\s+vaikunthapurramuloo)",
        "title": "Samajavaragamana",
        "artist": "Sid Sriram, Thaman S",
        "movie_or_album": "Ala Vaikunthapurramuloo",
        "language": "Telugu",
        "continuation": "Samajavaragamana... neelothoni kalipave manasanta!",
        "backstory": "A mega-hit classical fusion melody composed by Thaman S and voiced with emotion by Sid Sriram.",
    },
    {
        "pattern": r"(?:butta\s+bomma|buttabomma|chinnaga\s+nannu\s+chusi)",
        "title": "Butta Bomma",
        "artist": "Armaan Malik, Thaman S",
        "movie_or_album": "Ala Vaikunthapurramuloo",
        "language": "Telugu",
        "continuation": "Butta bomma butta bomma, nannu suttu kuntivamma...",
        "backstory": "A sensationally viral acoustic rhythm song rendered by Armaan Malik.",
    },
    {
        "pattern": r"(?:naatu\s+naatu|natu\s+natu|polam\s+gattu\s+dummulo)",
        "title": "Naatu Naatu",
        "artist": "Rahul Sipligunj, Kaala Bhairava, M. M. Keeravani",
        "movie_or_album": "RRR",
        "language": "Telugu",
        "continuation": "Naatu Naatu Naatu... veera naatu naatu!",
        "backstory": "The historic Oscar and Golden Globe-winning dance explosion composed by M. M. Keeravani from RRR.",
    },
    {
        "pattern": r"(?:shape\s+of\s+you|club\s+isn't\s+the\s+best\s+place|girl\s+you\s+know\s+i\s+want\s+your\s+love)",
        "title": "Shape of You",
        "artist": "Ed Sheeran",
        "movie_or_album": "÷ (Divide)",
        "language": "English",
        "continuation": "I'm in love with the shape of you, we push and pull like a magnet do!",
        "backstory": "A global pop phenomenon by Ed Sheeran blending dancehall-infused pop with marimba loops.",
    },
    {
        "pattern": r"(?:first\s+things\s+first|pain!\s+you\s+made\s+me\s+a|believer\s+believer)",
        "title": "Believer",
        "artist": "Imagine Dragons",
        "movie_or_album": "Evolve",
        "language": "English",
        "continuation": "Pain! You made me a, you made me a believer, believer!",
        "backstory": "A powerful arena-rock anthem driven by thunderous tribal drums and Dan Reynolds' vocals.",
    },
    {
        "pattern": r"(?:found\s+a\s+love\s+for\s+me|darling\s+just\s+dive\s+right\s+in|dancing\s+in\s+the\s+dark)",
        "title": "Perfect",
        "artist": "Ed Sheeran",
        "movie_or_album": "÷ (Divide)",
        "language": "English",
        "continuation": "Barefoot on the grass, listening to our favorite song...",
        "backstory": "A quintessential modern wedding waltz written by Ed Sheeran.",
    },
    {
        "pattern": r"(?:despacito|quiero\s+respirar\s+tu\s+cuello|pasito\s+a\s+pasito)",
        "title": "Despacito",
        "artist": "Luis Fonsi, Daddy Yankee",
        "movie_or_album": "Vida",
        "language": "Spanish",
        "continuation": "Pasito a pasito, suave suavecito, nos vamos pegando poquito a poquito!",
        "backstory": "A record-smashing reggaeton-pop masterpiece from Puerto Rico that captured global audiences.",
    },
]


class MusicLyricsEngine:
    """
    Intelligent music and lyric perception subsystem for IRIS.
    Identifies songs from spoken/sung phrases, manages recent music memory,
    and supports sing-along dialogues.
    """

    def __init__(self, api_key_manager=None, hybrid_router=None):
        self.api_key_manager = api_key_manager
        if not self.api_key_manager:
            try:
                from backend.security.api_key_manager import ApiKeyManager
                self.api_key_manager = ApiKeyManager()
            except Exception:
                try:
                    from security.api_key_manager import ApiKeyManager
                    self.api_key_manager = ApiKeyManager()
                except Exception:
                    pass
        self.hybrid_router = hybrid_router

        # Working music memory
        self._last_identified_song: Optional[Dict[str, Any]] = None
        self._last_identified_time: float = 0.0
        self.MEMORY_TTL: float = 300.0  # 5 minutes memory of last sung song

    def get_last_song(self) -> Optional[Dict[str, Any]]:
        """Return the most recently identified song if within the 5-minute memory window."""
        if self._last_identified_song and (time.time() - self._last_identified_time < self.MEMORY_TTL):
            return self._last_identified_song
        return None

    def remember_song(self, song_data: Dict[str, Any]):
        """Persist a song into active working memory."""
        self._last_identified_song = song_data
        self._last_identified_time = time.time()
        logger.info(f"🎵 MusicEngine: Remembered song '{song_data.get('title')}' by {song_data.get('artist')}")

    def identify_from_catalog(self, text: str) -> Optional[Dict[str, Any]]:
        """Fast instant regex catalog match for top iconic hits (<0.001s)."""
        t = text.lower().strip()
        for entry in POPULAR_SONG_CATALOG:
            if re.search(entry["pattern"], t, re.IGNORECASE):
                result = {
                    "is_song": True,
                    "title": entry["title"],
                    "artist": entry["artist"],
                    "movie_or_album": entry["movie_or_album"],
                    "language": entry["language"],
                    "continuation": entry["continuation"],
                    "backstory": entry["backstory"],
                    "search_query": f"{entry['title']} {entry['artist']}",
                    "confidence": 0.98,
                }
                self.remember_song(result)
                return result
        return None

    def identify_lyrics_llm(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Deep LLM lyric recognition for ANY song in ANY language.
        Queries Groq / active model to extract structured metadata.
        """
        prompt = (
            "Analyze the following user input to determine if it contains song lyrics or singing in any language "
            "(Hindi, Telugu, Tamil, Punjabi, Spanish, French, English, etc.).\n"
            f"User input: \"{text}\"\n\n"
            "Respond ONLY with a JSON object in this exact format (no markdown, no other words):\n"
            "{\n"
            '  "is_song": true/false,\n'
            '  "title": "Song Title",\n'
            '  "artist": "Singer / Composer",\n'
            '  "movie_or_album": "Movie or Album Name",\n'
            '  "language": "Detected Language",\n'
            '  "continuation": "The next 1 or 2 lines of the song to sing along",\n'
            '  "backstory": "1 sentence interesting fact about the song",\n'
            '  "confidence": 0.0 to 1.0\n'
            "}"
        )

        try:
            # 1. Use Groq if available
            groq_key = None
            if self.api_key_manager:
                try:
                    groq_key = self.api_key_manager.get_key("groq")
                except Exception:
                    pass
            if not groq_key:
                import os
                groq_key = os.environ.get("GROQ_API_KEY")
            raw_json = None

            if groq_key:
                from openai import OpenAI
                client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=groq_key)
                res = client.chat.completions.create(
                    model="qwen/qwen3.8-27b",
                    messages=[
                        {"role": "system", "content": "You are a musical genius who identifies song lyrics accurately in all world languages."},
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=250,
                    temperature=0.1,
                )
                raw_json = res.choices[0].message.content.strip()

            # 2. Fallback to hybrid router if Groq direct was not used
            elif self.hybrid_router:
                res = self.hybrid_router.chat(
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=250,
                    temperature=0.1,
                )
                raw_json = res.get("response", "").strip()

            if raw_json:
                # Extract JSON block
                m = re.search(r"\{[\s\S]*\}", raw_json)
                if m:
                    data = json.loads(m.group(0))
                    if data.get("is_song") and data.get("title") and data.get("confidence", 0.0) >= 0.5:
                        data["search_query"] = f"{data.get('title')} {data.get('artist', '')}".strip()
                        self.remember_song(data)
                        return data

        except Exception as e:
            logger.debug(f"MusicEngine: LLM lyric recognition error: {e}")

        return None

    def analyze_input(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Full analysis pipeline:
        1. Try fast local catalog first (<0.001s).
        2. If not matched, try deep LLM identification.
        """
        if not text or len(text.strip().split()) < 2:
            return None

        # 1. Fast catalog
        fast_res = self.identify_from_catalog(text)
        if fast_res:
            return fast_res

        # 2. LLM detection if input contains rhythmic, melodic, or lyric-like cues
        # or if user explicitly mentioned singing / song
        t_low = text.lower()
        lyric_cues = ["sing", "song", "gana", "lyrics", "tune", "music", "la la", "oh oh", "hmm", "dil", "pyar", "ishq", "love", "baby", "yeah"]
        has_cues = any(w in t_low for w in lyric_cues) or (len(text.split()) >= 3 and not text.endswith("?"))

        if has_cues:
            return self.identify_lyrics_llm(text)

        return None

    def generate_sing_along_response(self, song_info: Dict[str, Any], wants_to_play: bool = False) -> str:
        """
        Generate a musical companion English response acknowledging the song
        and singing along with the user.
        """
        title = song_info.get("title", "this song")
        artist = song_info.get("artist", "")
        album = song_info.get("movie_or_album", "")
        cont = song_info.get("continuation", "")
        backstory = song_info.get("backstory", "")

        origin_str = f" from {album}" if album else ""
        by_str = f" sung by {artist}" if artist else ""

        if wants_to_play:
            return f"That's '{title}'{origin_str}{by_str}! Playing it right now on YouTube for you, Commander."

        response_parts = [
            f"That's '{title}'{origin_str}{by_str}! I love that song.",
        ]

        if backstory:
            response_parts.append(backstory)

        if cont:
            response_parts.append(f"Let me sing the next lines with you: \"{cont}\"")

        response_parts.append("Would you like me to play the original track on YouTube?")
        return " ".join(response_parts)


# Singleton instance
_music_engine_instance: Optional[MusicLyricsEngine] = None


def get_music_lyrics_engine(api_key_manager=None, hybrid_router=None) -> MusicLyricsEngine:
    global _music_engine_instance
    if _music_engine_instance is None:
        _music_engine_instance = MusicLyricsEngine(api_key_manager=api_key_manager, hybrid_router=hybrid_router)
    return _music_engine_instance

