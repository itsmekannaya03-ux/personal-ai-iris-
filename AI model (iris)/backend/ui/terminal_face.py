import logging
import threading

logger = logging.getLogger("iris.ui.face")

FACE_TEMPLATE = [
    "                        *******************",
    "                   ******                 ******",
    "                ****                           ****",
    "              ***                                 ***",
    "            ***                                     ***",
    "           **                                         **",
    "          **                                           **",
    "         **                                             **",
    "        **                                               **",
    "       **                                                 **",
    "       *      *****                   *****                *",
    "      **    ***   ***               ***   ***             **",
    "      **   **       **             **       **            **",
    "      **                                               **",
    "      **                                               **",
    "      **        **                       **             **",
    "      **         ***                   ***              **",
    "       *            ****           ****                 *",
    "        **              ***********                    **",
    "         **                                             **",
    "          **                                           **",
    "           ***                                       ***",
    "             ***                                   ***",
    "               ****                             ****",
    "                  ******                 ******",
    "                        *******************",
]

EYE_LINE = 10
LEFT_EYE_COL = 14
RIGHT_EYE_COL = 38
EYE_W = 5
MOUTH_LINE = 14
MOUTH_COL = 28
MOUTH_W = 7

EYE_PATTERNS = {
    "normal": "O   O",
    "happy": "^   ^",
    "sad": "u   u",
    "angry": "* * *",
    "excited": "0   0",
    "closed": "-   -",
    "sleep": "_   _",
}

MOUTH_PATTERNS = {
    "normal": "-------",
    "happy": "wwwwwww",
    "sad": ".......",
    "angry": "~~~~~~~",
    "excited": "OOOOOOO",
    "smile": "wwwwwww",
    "open": "ooooooo",
    "neutral": "-------",
}


FACE_W = 60


class TerminalFace:
    def __init__(self):
        self._mood = "neutral"
        self._speaking = False
        self._blink_state = False
        self._blink_counter = 0
        self._lock = threading.Lock()

    def set_mood(self, mood: str):
        with self._lock:
            self._mood = mood if mood in EYE_PATTERNS else "neutral"

    def set_speaking(self, speaking: bool):
        with self._lock:
            self._speaking = speaking

    def render_frame(self, width: int) -> list[str]:
        with self._lock:
            mood = self._mood
            speaking = self._speaking

        self._blink_counter += 1
        if self._blink_counter > 80:
            self._blink_state = not self._blink_state
            self._blink_counter = 0

        if self._blink_state:
            eye_pat = EYE_PATTERNS["closed"]
        else:
            eye_pat = EYE_PATTERNS.get(mood, EYE_PATTERNS["normal"])

        if speaking:
            mouth_pat = "ooooooo"
        else:
            mouth_pat = MOUTH_PATTERNS.get(mood, MOUTH_PATTERNS["neutral"])

        result = []
        for i, line in enumerate(FACE_TEMPLATE):
            if i == EYE_LINE:
                line = (
                    line[:LEFT_EYE_COL]
                    + eye_pat[:EYE_W]
                    + line[LEFT_EYE_COL + EYE_W:RIGHT_EYE_COL]
                    + eye_pat[:EYE_W]
                    + line[RIGHT_EYE_COL + EYE_W:]
                )
            elif i == MOUTH_LINE:
                line = line[:MOUTH_COL] + mouth_pat[:MOUTH_W] + line[MOUTH_COL + MOUTH_W:]
            result.append(line.rstrip())

        result.append("")
        return result

    def get_status(self) -> dict:
        with self._lock:
            return {"mood": self._mood, "speaking": self._speaking}
