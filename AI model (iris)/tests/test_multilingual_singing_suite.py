"""
IRIS AI — Multilingual & Musical Sing-Along Verification Suite
============================================================
Tests:
1. Catalog song identification (Hindi, Telugu, English, Spanish)
2. Song continuation and backstory generation
3. Memory persistence and anaphoric resolution ("play it")
4. Decider & YouTubeController resolving "play it" to the remembered song
5. Multilingual comprehension directive in system prompt
6. Intent classification for lyrics and playback
"""

import sys
import os
import unittest
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.intelligence.music_engine import get_music_lyrics_engine, POPULAR_SONG_CATALOG
from core.intent import IntentDetector
from core.decider import Decider
from core.model_router import ModelRouter


class TestMultilingualSingingSuite(unittest.TestCase):

    def setUp(self):
        self.engine = get_music_lyrics_engine()
        self.intent_detector = IntentDetector()
        self.decider = Decider()

    def test_catalog_identification_hindi(self):
        """Test instant identification of Hindi hits like Tum Hi Ho and Kesariya."""
        res1 = self.engine.identify_from_catalog("Hum tere bin ab reh nahi sakte tere bina kya wajood mera... kyunki tum hi ho ab tum hi ho")
        self.assertIsNotNone(res1)
        self.assertEqual(res1["title"], "Tum Hi Ho")
        self.assertEqual(res1["artist"], "Arijit Singh")
        self.assertIn("Aashiqui 2", res1["movie_or_album"])

        res2 = self.engine.identify_from_catalog("kesariya tera ishq hai piya rang jaaun jo main haath lagaun")
        self.assertIsNotNone(res2)
        self.assertEqual(res2["title"], "Kesariya")

    def test_catalog_identification_telugu(self):
        """Test instant identification of Telugu hits like Samajavaragamana & Naatu Naatu."""
        res1 = self.engine.identify_from_catalog("Samajavaragamana ninu choosi aagagalaana")
        self.assertIsNotNone(res1)
        self.assertEqual(res1["title"], "Samajavaragamana")
        self.assertEqual(res1["language"], "Telugu")

        res2 = self.engine.identify_from_catalog("Naatu Naatu Naatu Veera Naatu")
        self.assertIsNotNone(res2)
        self.assertEqual(res2["title"], "Naatu Naatu")

    def test_catalog_identification_english_spanish(self):
        """Test instant identification of English & Spanish hits."""
        res_en = self.engine.identify_from_catalog("I'm in love with the shape of you, we push and pull like a magnet do")
        self.assertIsNotNone(res_en)
        self.assertEqual(res_en["title"], "Shape of You")

        res_es = self.engine.identify_from_catalog("Despacito quiero respirar tu cuello despacito")
        self.assertIsNotNone(res_es)
        self.assertEqual(res_es["title"], "Despacito")

    def test_sing_along_response_english(self):
        """Verify sing-along response is in English and recites continuation lines."""
        song = self.engine.identify_from_catalog("ab tum hi ho zindagi ab tum hi ho")
        self.assertIsNotNone(song)
        reply = self.engine.generate_sing_along_response(song, wants_to_play=False)
        self.assertIn("Tum Hi Ho", reply)
        self.assertIn("Arijit Singh", reply)
        self.assertIn("sing the next lines with you", reply)
        self.assertIn("Chain bhi, mera dard bhi", reply)
        self.assertIn("YouTube?", reply)

    def test_anaphoric_play_it_resolution(self):
        """Test singing a song then saying 'play it' resolves directly to that song."""
        # 1. User sings Kesariya
        song = self.engine.identify_from_catalog("kesariya tera ishq hai piya")
        self.assertIsNotNone(song)
        self.engine.remember_song(song)

        # 2. Check remembered song
        last = self.engine.get_last_song()
        self.assertIsNotNone(last)
        self.assertEqual(last["title"], "Kesariya")

        # 3. Decider receives "play it" or "just play it"
        target1 = self.decider._extract_target("youtube_play", "play it")
        self.assertIn("Kesariya", target1)

        target2 = self.decider._extract_target("youtube_play", "just play this song on youtube")
        self.assertIn("Kesariya", target2)

    def test_multilingual_system_prompt_directive(self):
        """Verify ModelRouter system prompt contains explicit multilingual English directive."""
        router = ModelRouter()
        sp = router._build_system_prompt(intent="conversation", mode="general", context={})
        self.assertIn("MULTILINGUAL COMPREHENSION & ENGLISH REASONING", sp)
        self.assertIn("ALWAYS formulate and deliver your response in natural, fluent English", sp)
        self.assertIn("MUSICAL & LYRIC COMPANIONSHIP", sp)

    def test_intent_detection_lyrics_and_play(self):
        """Verify intent detection identifies 'sing with me' and 'play it' correctly."""
        res1 = self.intent_detector.analyze("can you sing with me")
        self.assertEqual(res1["intent"], "singing_lyrics")

        res2 = self.intent_detector.analyze("play it on youtube")
        self.assertEqual(res2["intent"], "youtube_play")

        res3 = self.intent_detector.analyze("just play it")
        self.assertEqual(res3["intent"], "youtube_play")

    def test_brain_end_to_end_singing_and_play_it(self):
        """End-to-end test of Brain thinking when user sings lyrics and then says 'play it'."""
        from core.brain import IrisBrain
        brain = IrisBrain()
        brain._intent = self.intent_detector
        brain._decider = self.decider

        # Step 1: User sings Hindi lyrics from 'Tum Hi Ho'
        res1 = brain.think("Hum tere bin ab reh nahi sakte tere bina kya wajood mera... kyunki tum hi ho")
        self.assertIn("Tum Hi Ho", res1["text"])
        self.assertIn("Arijit Singh", res1["text"])
        self.assertIn("sing the next lines with you", res1["text"])
        self.assertEqual(res1["intent"], "singing_lyrics")

        # Step 2: User immediately says "play it"
        res2 = brain.think("play it")
        self.assertEqual(res2["intent"], "youtube_play")
        self.assertIn("Tum Hi Ho", res2["text"])
        self.assertIn("Playing", res2["text"])

        # Check Decider extracts resolved target
        target = self.decider._extract_target("youtube_play", "play it")
        self.assertIn("Tum Hi Ho", target)


if __name__ == "__main__":
    unittest.main()
