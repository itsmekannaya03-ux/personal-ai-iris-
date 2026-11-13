"""
Typo Corrector and Fuzzy Understanding Engine for IRIS AI.
Automatically detects, corrects, and normalizes user spelling mistakes,
phonetic speech recognition anomalies, and keyboard typos for commands,
applications, websites, and system controls.
"""

import re
import difflib
import logging
from typing import Optional, Tuple

logger = logging.getLogger("iris.core.typo_corrector")


class TypoCorrector:
    """
    High-speed rule-based and fuzzy typo correction engine.
    Executes in <1ms without calling heavy external models.
    """

    # ── 1. Action Verbs (Commands) ──
    ACTION_TYPOS = {
        "opn": "open",
        "oepn": "open",
        "opne": "open",
        "oppen": "open",
        "oepne": "open",
        "openup": "open",
        "open up": "open",
        "lonch": "launch",
        "lanch": "launch",
        "launc": "launch",
        "luanch": "launch",
        "launche": "launch",
        "stat": "start",
        "strt": "start",
        "strart": "start",
        "stert": "start",
        "starrt": "start",
        "runn": "run",
        "runnn": "run",
        "rnu": "run",
        "clos": "close",
        "clse": "close",
        "cloe": "close",
        "cls": "close",
        "quitt": "quit",
        "ext": "exit",
        "exitt": "exit",
        "lok": "lock",
        "loc": "lock",
        "lck": "lock",
        "unlok": "unlock",
        "unloc": "unlock",
        "unlck": "unlock",
        "slp": "sleep",
        "slepp": "sleep",
        "slepe": "sleep",
        "shutdon": "shutdown",
        "shutdwn": "shutdown",
        "restrt": "restart",
        "restrat": "restart",
        "rebot": "reboot",
    }

    # ── 2. Common Desktop Applications ──
    APP_TYPOS = {
        "chrom": "chrome",
        "crome": "chrome",
        "chroome": "chrome",
        "chrme": "chrome",
        "crom": "chrome",
        "google chrom": "chrome",
        "google crome": "chrome",
        "vscod": "code",
        "vs cod": "code",
        "vs cde": "code",
        "vcode": "code",
        "vscode": "code",
        "vs code": "code",
        "visual studio": "code",
        "visual studio code": "code",
        "visal studio": "code",
        "notepd": "notepad",
        "notpad": "notepad",
        "notepat": "notepad",
        "notped": "notepad",
        "notepade": "notepad",
        "termnl": "terminal",
        "termnal": "terminal",
        "trminal": "terminal",
        "teminal": "terminal",
        "cmd promt": "terminal",
        "cmd prompt": "terminal",
        "comand prompt": "terminal",
        "powershel": "powershell",
        "calclator": "calculator",
        "calcualtor": "calculator",
        "calclatr": "calculator",
        "calulator": "calculator",
        "clac": "calculator",
        "brwoser": "edge",
        "browzr": "edge",
        "ms edge": "edge",
        "micosoft edge": "edge",
        "settngs": "settings",
        "setings": "settings",
        "set tings": "settings",
        "tsk manager": "task manager",
        "taskmgr": "task manager",
        "task mangr": "task manager",
        "fil explorer": "explorer",
        "explorr": "explorer",
        "file explorr": "explorer",
        "whasapp": "whatsapp",
        "whatsap": "whatsapp",
        "whats app": "whatsapp",
        "watsapp": "whatsapp",
        "watsap": "whatsapp",
        "wathsapp": "whatsapp",
        "intsagram": "instagram",
        "instgram": "instagram",
        "spotfy": "spotify",
        "spootify": "spotify",
        "sportify": "spotify",
        "spotifi": "spotify",
        "disord": "discord",
        "dicord": "discord",
        "discrod": "discord",
        "daccord": "discord",
        "paint app": "paint",
        "mspaint": "paint",
    }

    # ── 3. Common Websites & Links ──
    WEB_TYPOS = {
        "yotube": "youtube",
        "ytube": "youtube",
        "you tube": "youtube",
        "youtub": "youtube",
        "yutube": "youtube",
        "yutu": "youtube",
        "yt": "youtube",
        "gogle": "google",
        "googl": "google",
        "goolge": "google",
        "googel": "google",
        "gogole": "google",
        "gthub": "github",
        "git hub": "github",
        "githb": "github",
        "githhub": "github",
        "reddt": "reddit",
        "redit": "reddit",
        "reditt": "reddit",
        "netflx": "netflix",
        "netfllix": "netflix",
        "netflex": "netflix",
        "netfix": "netflix",
        "instgram": "instagram",
        "insta": "instagram",
        "instagrm": "instagram",
        "ig": "instagram",
        "twiter": "twitter",
        "twtter": "twitter",
        "twiiter": "twitter",
        "linkden": "linkedin",
        "linkdin": "linkedin",
        "linkin": "linkedin",
        "linked in": "linkedin",
        "amazn": "amazon",
        "amzon": "amazon",
        "stckoverflow": "stackoverflow",
        "stack overflow": "stackoverflow",
        "stackover flow": "stackoverflow",
        "gmial": "gmail",
        "g mail": "gmail",
    }

    # ── 4. System Controls & Keywords ──
    KEYWORD_TYPOS = {
        "volme": "volume",
        "volum": "volume",
        "vlume": "volume",
        "voulme": "volume",
        "soud": "sound",
        "brigthness": "brightness",
        "brighness": "brightness",
        "bightness": "brightness",
        "brightnes": "brightness",
        "brigtness": "brightness",
        "wokrspace": "workspace",
        "workspce": "workspace",
        "wrkspace": "workspace",
        "wokr space": "workspace",
        "work space": "workspace",
        "work setup": "workspace",
        "linnk": "link",
        "lnik": "link",
        "likn": "link",
        "lik": "link",
        "linke": "link",
        "linkes": "link",
        "links": "link",
        "websit": "website",
        "websyte": "website",
        "wesbite": "website",
        "websiet": "website",
    }

    def __init__(self, app_launcher=None):
        self._app_launcher = app_launcher
        # Combined quick lookup table
        self._all_word_map = {}
        self._all_word_map.update(self.ACTION_TYPOS)
        self._all_word_map.update(self.KEYWORD_TYPOS)
        self._all_word_map.update(self.APP_TYPOS)
        self._all_word_map.update(self.WEB_TYPOS)
        logger.info(f"TypoCorrector ready ({len(self._all_word_map)} mapped corrections)")

    def correct(self, text: str) -> str:
        """
        Takes raw, misspelled user input and returns a corrected, clean string.
        Executes in <0.5ms.
        """
        if not text or not text.strip():
            return text or ""

        original = text.strip()
        # If text contains Hindi / Devanagari, preserve it directly
        if re.search(r"[\u0900-\u097F]", original):
            return re.sub(r"\s+", " ", original).strip()
        cleaned = original.lower()

        # 1. Multi-word phrase normalizations first
        cleaned = re.sub(r"\b(open\s+up|openup)\b", "open", cleaned)
        cleaned = re.sub(r"\b(please\s+open|can\s+you\s+open|pls\s+open)\b", "open", cleaned)
        cleaned = re.sub(r"\b(open\s+the\s+link|open\s+link|open\s+linkes|open\s+the\s+website)\b", "open link", cleaned)
        cleaned = re.sub(r"\b(wokr\s*space|work\s*spce|work\s*space)\b", "workspace", cleaned)
        cleaned = re.sub(r"\b(lok\s+my\s+pc|loc\s+my\s+pc|lock\s+pc)\b", "lock my pc", cleaned)
        cleaned = re.sub(r"\b(unlok\s+my\s+pc|unloc\s+my\s+pc|unlock\s+pc)\b", "unlock my pc", cleaned)
        cleaned = re.sub(r"\b(you\s*tube)\b", "youtube", cleaned)
        cleaned = re.sub(r"\b(vs\s*code|visual\s*studio\s*code)\b", "code", cleaned)
        cleaned = re.sub(r"\b(whats\s*app|wats\s*app)\b", "whatsapp", cleaned)
        cleaned = re.sub(r"\b(git\s*hub)\b", "github", cleaned)
        cleaned = re.sub(r"\b(stack\s*overflow)\b", "stackoverflow", cleaned)
        # Normalize "chart" / "charts" to "chat" in WhatsApp or messaging contexts
        cleaned = re.sub(r"\b(?:chart|charts)\s+(?:in|on)\s+whatsapp\b", "chat in whatsapp", cleaned)
        cleaned = re.sub(r"\bwhatsapp\s+(?:chart|charts)\b", "whatsapp chat", cleaned)
        cleaned = re.sub(r"\bopen\s+(?:any\s+)?(?:chart|charts)\b", "open chat", cleaned)
        cleaned = re.sub(r"\b(?:revind|rewnd)\b", "rewind", cleaned)
        cleaned = re.sub(r"\b(?:misatke|mistk)\b", "mistake", cleaned)
        cleaned = re.sub(r"\b(?:wordes|wrds)\b", "words", cleaned)
        cleaned = re.sub(r"\b(?:lisisng|listning)\b", "listening", cleaned)

        # 2. Tokenize and replace recognized single-word typos
        words = re.findall(r"[A-Za-z0-9_'][A-Za-z0-9_\.\:\/\-']*|[^\s]", cleaned)
        corrected_words = []
        for w in words:
            w_clean = w.lower().strip()
            if w_clean in self._all_word_map:
                corrected_words.append(self._all_word_map[w_clean])
            else:
                corrected_words.append(w)

        result = " ".join(corrected_words)
        # Normalize double spaces and punctuation gaps
        result = re.sub(r"\s+", " ", result).strip()

        # 3. Fuzzy match target if it starts with an action verb
        # E.g. "open blndr" -> check against installed apps if app_launcher is present
        m = re.match(r"^(open|launch|start|close|exit)\s+([a-zA-Z0-9_\-\. ]+)$", result)
        if m and self._app_launcher:
            verb = m.group(1)
            target = m.group(2).strip()
            # If target not directly recognized, try fuzzy matching against installed apps
            fuzzy_target = self._fuzzy_match_app_or_site(target)
            if fuzzy_target:
                result = f"{verb} {fuzzy_target}"

        if result != original.lower():
            logger.info(f"Typo corrected: '{original}' -> '{result}'")

        return result

    def _fuzzy_match_app_or_site(self, target: str) -> Optional[str]:
        """Check if target closely matches a known site or installed app."""
        t_low = target.lower().strip()
        # Check known sites first
        site_matches = difflib.get_close_matches(t_low, list(self.WEB_TYPOS.values()), n=1, cutoff=0.72)
        if site_matches:
            return site_matches[0]

        # Check known apps
        app_matches = difflib.get_close_matches(t_low, list(self.APP_TYPOS.values()), n=1, cutoff=0.72)
        if app_matches:
            return app_matches[0]

        if hasattr(self._app_launcher, "_apps") and self._app_launcher._apps:
            known_keys = list(self._app_launcher._apps.keys())
            matches = difflib.get_close_matches(t_low, known_keys, n=1, cutoff=0.68)
            if matches:
                return matches[0]

        return None

    def generate_human_clarification(self, raw_text: str, context: Optional[dict] = None) -> str:
        """
        Generate a warm, natural human-style clarification when an utterance is
        unclear, misheard, or missing key parameters — never like a scripted chatbot.
        """
        t = (raw_text or "").strip().lower()
        if not t:
            return "Wait, I didn't catch that—what was that?"

        # Missing targets on command verbs
        if t in ("open", "launch", "start", "opn"):
            return "Wait, which app or website did you want me to open?"
        if t in ("close", "exit", "quit"):
            return "Which window or application did you want me to close?"
        if t in ("play", "play a song", "play song", "play any song"):
            return "Sure! What song or artist did you have in mind?"
        if t in ("search", "find", "google"):
            return "What would you like me to look up?"
        if t in ("message", "send message", "text"):
            return "Who would you like me to message, and what should I say?"
        if t in ("make", "create"):
            return "What would you like me to create—a file, a folder, or something else?"

        # Ambiguous / garbled phrases
        if len(t.split()) <= 2:
            return f"Wait, did you say '{raw_text.strip()}'? Could you say that again in a full sentence?"

        import random
        prompts = [
            f"Wait, I didn't quite catch the last part of what you said—could you say that again?",
            f"Sorry, lost you for a second there! What did you say?",
            f"I heard you, but I didn't quite get the meaning of '{raw_text.strip()}'. What did you want me to do?",
            f"Wait, what was that? Say that one more time for me?",
        ]
        return random.choice(prompts)
