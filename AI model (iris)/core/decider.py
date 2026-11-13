import logging
from typing import Optional

logger = logging.getLogger("iris.core.decider")


class Decider:
    """
    Decides whether IRIS should reply, perform an action, or both.
    Routes actions to hands/ and replies to voice/.
    """

    REPLY_ONLY = {"greeting", "farewell", "conversation", "query", "help", "status_check", "confirm", "deny", "auth", "incomplete_command", "time", "face_scan", "emotion", "silence_on", "silence_off", "space"}
    ACTION_ONLY = {
        "launch", "close_app", "system", "delete", "screenshot", "music", "message", "volume",
        "brightness", "workspace", "window", "recycle_bin", "clipboard", "folder", "command",
        "whatsapp_msg", "whatsapp_chat", "youtube_play", "rewind", "type_here",
        "social_msg", "social_chat", "code_editor_folder", "use_folder_project", "run_in_code_editor", "voice_switch",
        "create_game", "create_website",
    }
    BOTH = {"search", "create", "file_op", "web_nav", "remember", "recall", "mode_switch", "battery", "todo"}

    def __init__(self):
        self._hands: Optional[object] = None

    def set_hands(self, hands):
        self._hands = hands

    def decide(self, data: dict) -> object:
        from .brain import Action

        intent = data.get("intent", "unknown")
        response_text = data.get("response", "")
        text = data.get("text", "")

        if intent in self.REPLY_ONLY:
            return Action(type="respond", payload={"text": response_text}, priority=0)

        if intent in self.ACTION_ONLY:
            execution = self._build_execution(intent, text)
            return Action(
                type="execute",
                payload={"text": response_text, "execution": execution},
                priority=1,
                requires_confirmation=self._needs_confirmation(intent, text),
            )

        if intent in self.BOTH:
            execution = self._build_execution(intent, text)
            return Action(
                type="both",
                payload={"text": response_text, "execution": execution},
                priority=1,
                requires_confirmation=self._needs_confirmation(intent, text),
            )

        return Action(type="respond", payload={"text": response_text}, priority=0)

    def _build_execution(self, intent: str, text: str) -> dict:
        return {
            "intent": intent,
            "source_text": text,
            "target": self._extract_target(intent, text),
        }

    def _extract_target(self, intent: str, text: str) -> str:
        import re
        if intent in ("launch", "close_app"):
            s_clean = re.sub(r"^(?:can\s+you\s+|could\s+you\s+|would\s+you\s+|please\s+|iris\s+|hey\s+iris\s+|i\s+want\s+to\s+|i\s+want\s+you\s+to\s+|just\s+|go\s+and\s+)", "", text, flags=re.IGNORECASE).strip()
            m = re.search(r"(?:open|launch|start|run|close|exit|quit|kill|opn|oepn|opne|lonch|lanch|stat|strt)\s+(?:the\s+|app\s+|application\s+)?([\w\-\.\:\/ ]+)", s_clean, re.IGNORECASE)
            target = m.group(1).strip() if m else s_clean
            target = re.sub(r"\b(?:in\s+\d+\s*(?:sec|seconds|second|s)|fast|quickly|please|now|right\s+now|for\s+me|immediately|ok|okay)\b", "", target, flags=re.IGNORECASE).strip()
            target = re.sub(r"^(?:the\s+app\s+|app\s+|the\s+application\s+|application\s+|the\s+link\s+|link\s+)", "", target, flags=re.IGNORECASE).strip()
            return target
        if intent == "code_editor_folder":
            m = re.search(r"\bopen\s+(?:any\s+|the\s+|this\s+|my\s+)?([\w\.\-\s]+?)?\s*(?:folder|directory|project)?\s*(?:in|inside|using|with)\s+(?:vs\s*code|code\s+editor|code)\b", text, re.I)
            if m and m.group(1):
                return m.group(1).strip()
            return "any"
        if intent == "use_folder_project":
            m = re.search(r"(?:use|work\s+in)\s+(?:the\s+|this\s+)?([\w\.\-\s]+?)\s+(?:folder|directory)", text, re.I)
            if m:
                return m.group(1).strip()
            return "active"
        if intent == "create_game":
            d = text.lower()
            for g in ("chess", "chees", "ludo", "carrom", "stickman", "stick man", "car racing", "car", "snake", "pong", "brick", "arcade", "offline"):
                if g in d:
                    return "chess" if g == "chees" else ("stickman" if g == "stick man" else g)
            m = re.search(r"\b(?:create|make|build|code|play)\s+(?:a\s+|an\s+)?([a-zA-Z0-9_\-]+)\s+game\b", text, re.I)
            if m and m.group(1).lower() not in ("a", "an", "the", "new", "some", "offline", "any"):
                return m.group(1).strip()
            return "arcade"
        if intent == "create_website":
            clean_s = re.sub(r"^(?:can\s+you\s+|could\s+you\s+|please\s+|iris\s+|hey\s+iris\s+)?(?:create|make|build|generate|design|code)\s+(?:a\s+|an\s+|the\s+)?(?:modern\s+|responsive\s+|beautiful\s+|landing\s+page\s+|portfolio\s+)?(?:website|web\s+site|webpage|web\s+page|landing\s+page)\s*(?:for\s+|about\s+|on\s+)?", "", text, flags=re.I).strip()
            return clean_s if clean_s else "modern"
        if intent == "window":
            d = text.lower().strip()
            if any(w in d for w in ("show desktop", "go to desktop", "go desktop", "minimize all", "minimize everything", "minimize the things", "minimize things", "minimize all things", "minimize it", "minimize screen")) or re.search(r"\bminimize\s*(?:all\s+)?(?:the\s+)?(?:tabs?|windows?|apps?|things?|everything|screen)?\s*$", d) or d == "minimize":
                return "all"
            target = re.sub(r"^(?:minimize|maximize|snap|restore)\s+(?:the\s+)?(?:window\s+)?(?:called\s+|named\s+)?", "", text, flags=re.I).strip()
            target = re.sub(r"\b(?:to\s+(?:the\s+)?(?:left|right))\b", "", target, flags=re.I).strip()
            if not target or target.lower() in ("it", "this", "things", "all", "everything", "tabs", "windows", "the tabs", "the windows", "the things"):
                return "all"
            return target
        if intent == "type_here":
            m_bracket = re.search(r"\[(.+?)\]", text)
            if m_bracket:
                return m_bracket.group(1).strip()
            clean_prefix = r"^(?:can\s+you\s+|could\s+you\s+|would\s+you\s+|please\s+|iris\s+|hey\s+iris\s+|okay\s+|ok\s+|now\s+|so\s+)?(?:type|write)\s+(?:the\s+(?:word|words|text)\s+)?(?:on\s+here\s+|here\s+|on\s+there\s+|there\s+)?"
            suffix_pat = r"\s+(?:on\s+here|here|on\s+there|there)$"
            s = re.sub(clean_prefix, "", text, flags=re.I)
            s = re.sub(suffix_pat, "", s, flags=re.I).strip(" '\"[]")
            return s
        if intent in ("social_msg", "whatsapp_msg"):
            raw_t = text.strip()
            plat = "whatsapp"
            for p_name in ("instagram", "insta", "telegram", "discord", "whatsapp", "wa"):
                if re.search(r"\b" + p_name + r"\b", raw_t, re.I):
                    plat = "instagram" if p_name in ("instagram", "insta") else ("telegram" if p_name in ("telegram", "tg") else ("discord" if p_name == "discord" else "whatsapp"))
                    break

            # If platform is mentioned before "to <contact>", e.g. "send message in whatsapp to mom saying hello"
            clean_t = re.sub(r"\b(?:in|on|via)\s+(?:whatsapp|instagram|insta|telegram|discord|twitter|x)\s+", "", raw_t, flags=re.I).strip()

            # 0. Check for explicit "everyone" / "every one" / "all contacts" broadcast
            m_every = re.search(r"\b(?:to\s+)?(everyone|every\s+one|everybody|all\s+contacts|all\s+people|all\s+chats|all\s+friends)\b", raw_t, re.I)
            if m_every:
                c_name = "everyone"
                after_match = raw_t[m_every.end():].strip()
                after_match = re.sub(r"^(?:on|in|via)?\s*(?:whatsapp|instagram|insta|telegram|discord)?\s*", "", after_match, flags=re.I).strip()
                after_match = re.sub(r"^(?:saying|that|:)\s*", "", after_match, flags=re.I).strip(" '\"")
                c_msg = after_match
                return f"{plat}::{c_name}::{c_msg}"

            # 1. Send with explicit separator (saying, that, :)
            m_sep = re.search(r"(?:send|message|text|tell)\s+(?:a\s+)?(?:new\s+)?(?:message\s+(?:to\s+)?)?(?:to\s+)?(?:the\s+)?([+\w\s]+?)\s*(?:saying|that|:)\s*(.*)$", clean_t, re.I)
            if m_sep:
                usr = m_sep.group(1).strip()
                usr = re.sub(r"^(?:in|on|via)\s+(?:whatsapp|instagram|insta|telegram|discord)\s+(?:to\s+)?", "", usr, flags=re.I).strip()
                usr = re.sub(r"^to\s+", "", usr, flags=re.I).strip()
                msg = m_sep.group(2).strip()
                return f"{plat}::{usr}::{msg}"

            # 2. Check for explicit phone number target (e.g. 10 digits or international format)
            m_phone = re.search(r"\b(\+?\d[\d\s\-]{8,14}\d)\b", raw_t)
            if m_phone:
                usr = m_phone.group(1).replace(" ", "").replace("-", "").strip()
                # Message is the text after the phone number or before
                after = raw_t[m_phone.end():].strip()
                after = re.sub(r"^(?:saying|that|:|\s)+", "", after, flags=re.I).strip(" '\"")
                msg = after
                return f"{plat}::{usr}::{msg}"

            # 3. Handle explicit "new", "a new one", "new contact"
            m_new = re.search(r"\b(?:to\s+)?(?:a\s+)?new\s+(?:one|contact|person|chat|number)\b", raw_t, re.I)
            if m_new:
                after = raw_t[m_new.end():].strip()
                after = re.sub(r"^(?:saying|that|:|\s)+", "", after, flags=re.I).strip(" '\"")
                return f"{plat}::new::{after}"

            # 4. Standard format: send [message] to [contact] [msg]
            m_to = re.search(r"(?:send|message|text|tell)\s+(?:a\s+)?(?:new\s+)?(?:message\s+)?to\s+(?:the\s+)?([+\w\s]+?)(?:\s+(?:saying|that|:)?\s*(.*))?$", clean_t, re.I)
            if m_to:
                usr_cand = m_to.group(1).strip()
                msg_cand = (m_to.group(2) or "").strip()
                # If msg_cand is empty but usr_cand has multiple words, split first word as contact name only if second part is a message
                if not msg_cand and " " in usr_cand and not any(w in usr_cand.lower() for w in ("senior", "junior", "sir", "mam", "bro", "panda")):
                    parts = usr_cand.split(" ", 1)
                    usr = parts[0].strip()
                    msg = parts[1].strip()
                else:
                    usr = usr_cand
                    msg = msg_cand
                return f"{plat}::{usr}::{msg}"

            # 5. Direct message to contact: message [contact] [msg]
            m_direct = re.search(r"\bmessage\s+(?:to\s+)?(?:the\s+)?([+\w]+)\s+(.+)$", clean_t, re.I)
            if m_direct:
                return f"{plat}::{m_direct.group(1).strip()}::{m_direct.group(2).strip()}"

            return f"{plat}::contact::{text}"
        if intent in ("social_chat", "whatsapp_chat"):
            raw_t = text.strip()
            # 1. Detect platform if specified (defaults to whatsapp)
            plat = "whatsapp"
            for p_name in ("instagram", "insta", "telegram", "discord", "whatsapp", "wa"):
                if re.search(r"\b" + p_name + r"\b", raw_t, re.I):
                    plat = "instagram" if p_name in ("instagram", "insta") else ("telegram" if p_name in ("telegram", "tg") else ("discord" if p_name == "discord" else "whatsapp"))
                    break

            # Strip platform words and leadings
            clean_s = re.sub(r"\b(?:in|on|via)\s+(?:whatsapp|instagram|insta|telegram|discord)\b", "", raw_t, flags=re.I).strip()
            clean_s = re.sub(r"\b(?:whatsapp|instagram|insta|telegram|discord)\b", "", clean_s, flags=re.I).strip()

            # Pattern A: open (chat|chart|conversation|dm) (with|to|of|for) [contact]
            mA = re.search(r"(?:open|start|show|go to)\s+(?:the\s+|a\s+)?(?:new\s+)?(?:chat|chart|conversation|dm|messages?)\s+(?:with|to|of|for)\s+([+\w\s]+)", clean_s, re.I)
            if mA:
                c = mA.group(1).strip()
                return f"{plat}::{c}"

            # Pattern B: open [contact] (chat|chart|conversation|dm)
            mB = re.search(r"(?:open|start|show|go to)\s+(?:the\s+|a\s+)?(?:new\s+)?([+\w\s]+?)\s+(?:chat|chart|conversation|dm|messages?)\b", clean_s, re.I)
            if mB:
                c = mB.group(1).strip()
                if c.lower() not in ("a", "the", "new", "a new", "my"):
                    return f"{plat}::{c}"

            # Pattern C: chat with [contact]
            mC = re.search(r"(?:chat|chart)\s+(?:with|to|of)\s+([+\w\s]+)", clean_s, re.I)
            if mC:
                c = mC.group(1).strip()
                return f"{plat}::{c}"

            # Pattern D: new chat
            if "new" in raw_t.lower():
                return f"{plat}::new"

            return f"{plat}::any"
        if intent == "youtube_play":
            m = re.search(r"(?:play|search)\s+(.+?)(?:\s+(?:in|on)\s+youtube)?$", text, re.IGNORECASE)
            if m:
                clean_target = m.group(1).strip()
                clean_target = re.sub(r"^(?:me\s+)?(?:a\s+|any\s+|some\s+|the\s+)?(?:songs|song|music|track|tracks)?\s*(?:of|by|called|named)?\s*", "", clean_target, flags=re.I).strip(" '\"")
                is_anaphoric = not clean_target or clean_target.lower() in (
                    "songs", "song", "a song", "any song", "some song", "music", "it",
                    "this", "that", "this song", "that song", "the song", "something", "any songs", "some songs"
                )
                if is_anaphoric:
                    try:
                        from backend.intelligence.music_engine import get_music_lyrics_engine
                        last_s = get_music_lyrics_engine().get_last_song()
                        if last_s and (last_s.get("search_query") or last_s.get("title")):
                            return last_s.get("search_query") or f"{last_s.get('title')} {last_s.get('artist', '')}".strip()
                    except Exception:
                        pass
                    return "popular top music hits"
                return clean_target
            try:
                from backend.intelligence.music_engine import get_music_lyrics_engine
                last_s = get_music_lyrics_engine().get_last_song()
                if last_s and (last_s.get("search_query") or last_s.get("title")):
                    return last_s.get("search_query") or f"{last_s.get('title')} {last_s.get('artist', '')}".strip()
            except Exception:
                pass
            return "popular top music hits"
        if intent == "rewind":
            return "rewind"
        if intent == "run_in_code_editor":
            clean = re.sub(r"\b(?:in|inside|using|with)?\s*(?:vs\s*code|code\s+editor|code|visual\s+studio\s+code)\b", "", text, flags=re.I).strip()
            clean = re.sub(r"^(?:abel\s+to\s+|able\s+to\s+)?(?:run|execute|start)?\s*(?:and\s+execute)?\s*(?:the\s+|this\s+|my\s+)?(?:program|code|script|file|project)?\s*", "", clean, flags=re.I).strip(" '\"")
            return clean or "program"
        if intent == "todo":
            return text
        if intent == "search":
            m = re.search(r"(?:search|google|look up|find)\s+(.+?)$", text, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        if intent == "web_nav":
            m = re.search(r"(?:go to|navigate|open website|visit|open the link|open link|the link|link|open site|browse to)\s+(.+?)$", text, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        if intent == "music":
            m = re.search(r"(?:play|search)\s+(.+?)$", text, re.IGNORECASE)
            if m:
                clean_target = m.group(1).strip()
                if clean_target.lower() in ("song", "a song", "any song", "music", "some song", "it", "something"):
                    return "popular top music hits"
                return clean_target
            return "popular top music hits"
        if intent == "command":
            s_clean = re.sub(r"^(?:can\s+you\s+|could\s+you\s+|would\s+you\s+|please\s+|iris\s+|hey\s+iris\s+|i\s+want\s+to\s+|i\s+want\s+you\s+to\s+|just\s+|go\s+and\s+)", "", text, flags=re.IGNORECASE).strip()
            # 1. Check if user asked to run [cmd] in terminal/cmd/powershell
            m_in_term = re.search(r"(?:run|execute)\s+(?:any\s+)?(?:command|commend|cmd)?\s*(?:in|on)\s*(?:the\s+)?(?:terminal|teminal|tarminel|cmd|powershell|command\s+prompt)$", s_clean, re.I)
            if m_in_term:
                return "any"
            m_cmd_in = re.search(r"(?:run|execute)\s+(.+?)\s+(?:in|on)\s+(?:the\s+)?(?:terminal|teminal|tarminel|cmd|powershell|command\s+prompt)$", s_clean, re.I)
            if m_cmd_in:
                target = m_cmd_in.group(1).strip()
            else:
                m = re.search(r"(?:open\s+(?:the\s+)?(?:cmd|terminal|teminal|tarminel|powershell|command\s+prompt)\s+(?:and\s+run|and\s+execute|to\s+run)\s+|run\s+(?:in\s+)?(?:cmd|terminal|teminal|tarminel|powershell|command\s+prompt)\s+|cmd\s+run\s+|terminal\s+run\s+|execute\s+command\s+|run\s+command\s+)(.+)$", s_clean, re.IGNORECASE)
                if m:
                    target = m.group(1).strip()
                else:
                    target = re.sub(r"\b(?:in|on)\s+(?:the\s+)?(?:terminal|teminal|tarminel|cmd|powershell|command\s+prompt)\b", "", s_clean, flags=re.I).strip()
                    target = re.sub(r"^(?:run|execute)\s+", "", target, flags=re.I).strip()
            target = re.sub(r"\b(?:in\s+\d+\s*(?:sec|seconds|second|s)|fast|quickly|please|now|right\s+now|for\s+me|immediately|ok|okay)\b", "", target, flags=re.IGNORECASE).strip()
            if not target or target.lower() in ("any", "any command", "a command", "command", "something", "any commend", "commend", "code"):
                return "any"
            return target
        return text

    def _needs_confirmation(self, intent: str, text: str = "") -> bool:
        if intent in ("system",):
            t = (text or "").lower()
            # Lock, unlock, and sleep execute immediately with zero prompts
            if any(w in t for w in ("lock", "unlock", "sleep")):
                return False
            return any(w in t for w in ("shutdown", "restart", "reboot"))
        if intent == "command":
            return False
        return intent in {"delete", "message"}

    def get_supported_intents(self) -> dict:
        return {
            "reply_only": list(self.REPLY_ONLY),
            "action_only": list(self.ACTION_ONLY),
            "both": list(self.BOTH),
        }
