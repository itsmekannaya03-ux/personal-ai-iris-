"""
STT — Speech-to-Text processing and transcript cleanup.

Processes raw speech transcripts by:
  - Cleaning filler words (um, uh, like, you know)
  - Fixing common ASR errors
  - Normalizing punctuation and casing
  - Detecting sentence boundaries
  
Integrated with browser SpeechRecognition API and optional local Whisper.
"""

import re
import logging
from typing import Optional

logger = logging.getLogger("iris.stt")


FILLER_WORDS = [
    r'\bum+\b', r'\buh+\b', r'\bah+\b', r'\ber+\b',
    r'\blike\b', r'\byou know\b', r'\bi mean\b',
    r'\bactually\b', r'\bbasically\b', r'\bhonestly\b',
    r'\bliterally\b', r'\bso yeah\b', r'\bwell\b',
    r'\bright\b', r'\bokay\b', r'\bso anyways?\b',
]

CONTRACTION_FIXES = {
    "dont": "don't", "cant": "can't", "wont": "won't",
    "im": "I'm", "ive": "I've", "id": "I'd",
    "ill": "I'll", "isnt": "isn't", "arent": "aren't",
    "wasnt": "wasn't", "werent": "weren't", "hasnt": "hasn't",
    "havent": "haven't", "hadnt": "hadn't", "doesnt": "doesn't",
    "dont": "don't", "didnt": "didn't", "couldnt": "couldn't",
    "wouldnt": "wouldn't", "shouldnt": "shouldn't", "mightnt": "mightn't",
    "mustnt": "mustn't", "theres": "there's", "heres": "here's",
    "thats": "that's", "whats": "what's", "whos": "who's",
    "its": "it's", "lets": "let's", "theyll": "they'll",
    "youre": "you're", "youll": "you'll", "youve": "you've",
    "theyre": "they're", "theyve": "they've",
}


class TranscriptCleaner:
    """
    Cleans and normalizes speech-to-text transcripts.
    """

    def __init__(self):
        self._filler_patterns = [re.compile(w, re.IGNORECASE) for w in FILLER_WORDS]

    def clean(self, text: str) -> str:
        """Full cleaning pipeline for a transcript."""
        if not text:
            return ""

        text = text.strip()
        text = self._remove_fillers(text)
        text = self._fix_contractions(text)
        text = self._fix_casing(text)
        text = self._fix_punctuation(text)
        return text

    def _remove_fillers(self, text: str) -> str:
        for pattern in self._filler_patterns:
            text = pattern.sub("", text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _fix_contractions(self, text: str) -> str:
        words = text.split()
        fixed = []
        for word in words:
            lower = word.lower()
            cleaned = re.sub(r'[^a-zA-Z\']', '', lower)
            if cleaned in CONTRACTION_FIXES:
                replacement = CONTRACTION_FIXES[cleaned]
                if word[0].isupper():
                    replacement = replacement[0].upper() + replacement[1:]
                fixed.append(replacement)
            else:
                fixed.append(word)
        return " ".join(fixed)

    def _fix_casing(self, text: str) -> str:
        if not text:
            return text
        text = text[0].upper() + text[1:]
        text = re.sub(r' i ', ' I ', text)
        text = re.sub(r'\. ([a-z])', lambda m: '. ' + m.group(1).upper(), text)
        text = re.sub(r'\? ([a-z])', lambda m: '? ' + m.group(1).upper(), text)
        text = re.sub(r'! ([a-z])', lambda m: '! ' + m.group(1).upper(), text)
        return text

    def _fix_punctuation(self, text: str) -> str:
        if text and not text[-1] in '.!?':
            text += '.'
        return text

    def get_status(self) -> dict:
        return {"filler_patterns": len(self._filler_patterns)}


class WakeWordDetector:
    """
    Simple wake word detection.
    Default wake word is "weak up". Also matches common variants.
    """

    WAKE_WORDS = [
        r'^weak up[,.!\s]',
        r'^wake up[,.!\s]',
        r'^hey iris[,.!\s]',
        r'^hello iris[,.!\s]',
        r'^iris[,.!\s]',
        r'^okay iris[,.!\s]',
        r'^iris[,]?\s',
    ]

    def __init__(self):
        self._patterns = [re.compile(w, re.IGNORECASE) for w in self.WAKE_WORDS]
        self._current_wake_word = "weak up"
        logger.info("Wake word detector initialized")

    def detect(self, text: str) -> bool:
        """Check if wake word is present in the text."""
        return any(p.search(text) for p in self._patterns)

    def strip_wake_word(self, text: str) -> str:
        """Remove wake word from the beginning of text."""
        for pattern in self._patterns:
            text = pattern.sub("", text).strip()
        return text

    def set_wake_word(self, word: str):
        self._current_wake_word = word.lower()
        logger.info(f"Wake word set to: {word}")

    def get_status(self) -> dict:
        return {
            "current_wake_word": self._current_wake_word,
            "patterns": self.WAKE_WORDS,
        }
