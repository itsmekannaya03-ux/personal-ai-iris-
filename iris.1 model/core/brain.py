import logging
import re
import threading
import time
from typing import Optional, Callable, Any
from dataclasses import dataclass, field
from urllib.parse import quote

logger = logging.getLogger("iris.core.brain")


@dataclass
class Thought:
    text: str
    confidence: float = 1.0
    intent: str = "unknown"
    timestamp: float = field(default_factory=time.time)
    context: dict = field(default_factory=dict)


@dataclass
class Action:
    type: str = "respond"
    payload: dict = field(default_factory=dict)
    priority: int = 0
    requires_confirmation: bool = False


class ThinkingPipeline:
    STAGES = ["receive", "analyze", "contextualize", "reason", "decide", "act", "respond"]

    def __init__(self):
        self._hooks: dict[str, list] = {s: [] for s in self.STAGES}

    def register_hook(self, stage: str, fn: Callable):
        if stage in self._hooks:
            self._hooks[stage].append(fn)

    def execute(self, stage: str, data: dict) -> dict:
        for hook in self._hooks.get(stage, []):
            data = hook(data)
        return data


class IrisBrain:
    MODES = {"fast", "genius"}

    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.name = self.config.get("name", "Iris")
        self.is_awake = True
        self.processing = False
        self._mode = "genius"
        self._lock = threading.Lock()
        self._thinking_thread: Optional[threading.Thread] = None

        self.pipeline = ThinkingPipeline()
        self.thought_log: list[Thought] = []
        self._wire_default_pipeline()

        # External subsystem references (injected after init)
        self._intent: Any = None
        self._decider: Any = None
        self._personality: Any = None
        self._model_router: Any = None
        self._memory: Any = None
        self._voice: Any = None
        self._vision: Any = None
        self._hands: Any = None
        self._presence: Any = None
        self.todo_manager: Any = None
        try:
            from .typo_corrector import TypoCorrector
            self._typo_corrector = TypoCorrector()
        except Exception:
            self._typo_corrector = None

        self.on_response: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        self._pending_confirmation: Optional[dict] = None
        self._last_file: Optional[str] = None
        self._last_folder: Optional[str] = None
        self._active_project_folder: Optional[str] = None

        logger.info(f"{self.name} brain initialized")

    def _wire_default_pipeline(self):
        self.pipeline.register_hook("receive", self._stage_receive)
        self.pipeline.register_hook("analyze", self._stage_analyze)
        self.pipeline.register_hook("contextualize", self._stage_contextualize)
        self.pipeline.register_hook("reason", self._stage_reason)
        self.pipeline.register_hook("decide", self._stage_decide)
        self.pipeline.register_hook("act", self._stage_act)
        self.pipeline.register_hook("respond", self._stage_respond)

    def _stage_receive(self, data: dict) -> dict:
        data["timestamp"] = time.time()
        data["mode"] = self._mode
        raw_text = data.get("text", "")
        data["raw_text"] = raw_text
        if self._typo_corrector:
            try:
                data["text"] = self._typo_corrector.correct(raw_text)
            except Exception as e:
                logger.debug(f"Typo correction failed: {e}")
        return data

    def _stage_analyze(self, data: dict) -> dict:
        if self._intent:
            result = self._intent.analyze(data["text"])
            data.update(result)
        else:
            data["intent"] = "unknown"
            data["confidence"] = 0.0
        return data

    def _stage_contextualize(self, data: dict) -> dict:
        intent = data.get("intent", "unknown")
        # Preserve any conversation history or context passed into think()
        ctx = data.get("context") or {}
        if data.get("context_history"):
            ctx["context_history"] = data["context_history"]

        # Fast-path: actions, greetings, emotions, time, and system commands don't need database memory retrieval
        skip_memory = intent in (
            "emotion", "launch", "close_app", "greeting", "farewell", 
            "time", "date_time", "incomplete_command", "confirm", "deny", 
            "volume", "brightness", "screenshot", "system", "command", "face_scan", "music"
        )
        if not skip_memory and self._memory:
            recalled = self._memory.recall_relevant(data["text"])
            if isinstance(recalled, dict):
                ctx.update(recalled)
        data["context"] = ctx

        if self._presence:
            try:
                st = self._presence.get_current_state()
                data["presence_emotion"] = st.emotion
                data["is_owner"] = st.is_owner
                if self._personality:
                    self._personality.set_emotion(st.emotion, st.confidence)
            except Exception:
                pass
        return data

    def _extract_and_store_fact(self, text: str) -> Optional[tuple]:
        """Automatically detect personal facts and store them in permanent memory."""
        t = text.strip()
        m_name = re.search(r"\bmy name is\s+([A-Za-z0-9\s]+?)(?:\.|$|,|!|\?)", t, re.IGNORECASE)
        if m_name:
            val = m_name.group(1).strip()
            if self._memory:
                self._memory.store_permanent("user_name", val)
            return ("user_name", f"your name is {val}")

        m_fav = re.search(r"\bmy favorite\s+([A-Za-z0-9\s]+?)\s+is\s+([A-Za-z0-9\s]+?)(?:\.|$|,|!|\?)", t, re.IGNORECASE)
        if m_fav:
            cat = m_fav.group(1).strip().lower()
            val = m_fav.group(2).strip()
            key = f"favorite_{cat.replace(' ', '_')}"
            if self._memory:
                self._memory.store_permanent(key, val)
            return (key, f"your favorite {cat} is {val}")

        m_job = re.search(r"\bi (?:work as|am a|am an)\s+([A-Za-z0-9\s]+?)(?:\.|$|,|!|\?)", t, re.IGNORECASE)
        if m_job and not any(w in t.lower() for w in ("feeling", "sad", "happy", "angry")):
            val = m_job.group(1).strip()
            if len(val.split()) <= 4:
                if self._memory:
                    self._memory.store_permanent("user_occupation", val)
                return ("user_occupation", f"you work as a {val}")

        m_rem = re.search(r"\b(?:remember|save|note|keep in mind)\s+(?:that\s+)?(.+)", t, re.IGNORECASE)
        if m_rem:
            fact = m_rem.group(1).strip()
            key = "user_memory_" + str(int(time.time()))[-4:]
            if self._memory:
                self._memory.store_permanent(key, fact)
            return (key, fact)

        return None

    def _recall_memory_answer(self, text: str, context: dict) -> Optional[str]:
        """Answer queries about past memories or personal details."""
        t_clean = re.sub(r"[^a-zA-Z0-9\s]", " ", text).lower().strip()
        t_clean = re.sub(r"\s+", " ", t_clean)
        if self._memory:
            if "my name" in t_clean or "who am i" in t_clean or "know my name" in t_clean:
                res = self._memory.get("user_name")
                if res and res.get("content"):
                    return f"Your name is {res['content']}, Commander."

            m_fav = re.search(r"favorite\s+([a-z\s]+)", t_clean)
            if m_fav:
                cat = m_fav.group(1).strip().replace(" ", "_")
                res = self._memory.get(f"favorite_{cat}")
                if res and res.get("content"):
                    return f"Your favorite {m_fav.group(1).strip()} is {res['content']}."

            if "what did i tell you" in t_clean or "what do you remember" in t_clean or "my memories" in t_clean:
                recalled = self._memory.recall_relevant(text)
                if recalled:
                    items = [f"{k.replace('_', ' ')}: {v}" for k, v in recalled.items() if isinstance(v, str) and k != "context_history"]
                    if items:
                        return f"Here is what I have stored in my long-term memory: {'; '.join(items[:4])}."
        return None

    def _stage_reason(self, data: dict) -> dict:
        intent = data.get("intent", "unknown")
        text = data.get("text", "")
        t_lower = text.lower().strip()

        # Handle user requesting space or silence
        if intent == "space":
            if self._personality:
                reply = self._personality.request_space()
            else:
                reply = "Okay. I'll stay quiet."
            data["response"] = reply
            return data

        # When user sends another input, reset space lock
        if self._personality:
            self._personality.reset_space()

        # ─── Music, Singing & Lyrics Perception ───────────────────
        try:
            from backend.intelligence.music_engine import get_music_lyrics_engine
            music_engine = get_music_lyrics_engine(
                api_key_manager=getattr(self, "_api_key_manager", None),
                hybrid_router=getattr(self, "_model_router", None)
            )

            # Anaphoric play requests ("play it", "play this", "play that song", "just play it")
            is_play_anaphoric = bool(re.search(
                r"^(?:please\s+|can\s+you\s+)?play\s+(?:it|this|that|this\s+song|that\s+song|the\s+song|gana)\b",
                t_lower
            ))
            if is_play_anaphoric or (intent == "youtube_play" and any(w in t_lower for w in ["play it", "play this", "play that", "just play"])):
                last_s = music_engine.get_last_song()
                if last_s:
                    data["response"] = music_engine.generate_sing_along_response(last_s, wants_to_play=True)
                    data["intent"] = "youtube_play"
                    return data

            # Analyze text for singing, humming, or song lyrics in ANY language
            song_data = music_engine.analyze_input(text)
            if song_data and song_data.get("is_song"):
                wants_play = bool(re.search(r"\b(?:play\s+it|play\s+this|play\s+that|play\s+the\s+song|play\s+song|chalao|bajao)\b", t_lower))
                reply = music_engine.generate_sing_along_response(song_data, wants_to_play=wants_play)
                data["response"] = reply
                if wants_play:
                    data["intent"] = "youtube_play"
                else:
                    data["intent"] = "singing_lyrics"
                return data
        except Exception as me_err:
            logger.debug(f"Music perception in brain error: {me_err}")

        if intent == "greeting":
            data["response"] = "Hello! I am Iris. Systems are online and ready to help, Commander."
            return data

        if intent == "farewell":
            data["response"] = "Goodbye! Have a great time ahead, Commander."
            return data

        if intent == "confirm":
            if self._pending_confirmation:
                data["response"] = "👍 Ok."
            else:
                data["response"] = "👍 Ok, understood."
            return data

        if intent == "deny":
            if self._pending_confirmation:
                self._pending_confirmation = None
                data["response"] = "Cancelled. Action was not performed."
            else:
                data["response"] = "Understood. Cancelled."
            return data

        # Direct conversational companion cases
        if t_lower in ("nothing", "nothing.", "nothing at all", "nothing much"):
            if self._personality:
                self._personality.request_space()
            data["response"] = "Alright. I'll stay quiet."
            return data

        if re.search(r"\b(?:bro\s+)?i(?:'m|m|\s+am)?\s+(?:so\s+|really\s+)?tired\b", t_lower):
            if self._personality:
                self._personality.record_emotional_response("SAD", 0.9)
            data["response"] = "Yeah... you've had enough for today 😅. Want to take a break, or do you still have something important to finish?"
            return data

        if re.search(r"\b(?:iris\s+)?(?:you\s+)?messed\s+(?:it\s+)?up\b", t_lower):
            data["response"] = "Fair. Let's check what I did wrong."
            return data

        if re.search(r"\bdon'?t\s+feel\s+like\s+talking\b", t_lower):
            if self._personality:
                self._personality.request_space()
            data["response"] = "Okay. You don't have to. I'll give you some space."
            return data

        if re.search(r"\b(?:finally\s+(?:got\s+.*working|fixed\s+it)|fixed\s+it|got\s+it\s+working|yesss\s+i\s+finally\s+fixed\s+it)\b", t_lower):
            if self._personality:
                self._personality.record_emotional_response("HAPPY", 0.95)
            data["response"] = "LET'S GOOOO 😂🔥 Finally! What was causing the problem?"
            return data

        if re.search(r"\b(?:iris\s+is\s+actually\s+working|it's\s+actually\s+working)\b", t_lower):
            if self._personality:
                self._personality.record_emotional_response("EXCITED", 0.95)
            data["response"] = "WAIT 😂🔥 IT'S ACTUALLY WORKING! Okay, now THIS is the part where things get interesting."
            return data

        if re.search(r"\b(?:i\s+have\s+an?\s+idea\s+for\s+iris|idea\s+for\s+iris)\b", t_lower):
            if self._personality:
                self._personality.record_emotional_response("EXCITED", 0.9)
            data["response"] = "Okay WAIT 😂🔥 Tell me."
            return data

        if re.search(r"\b(?:stupid\s+thing|why\s+(?:the\s+hell\s+)?isn't\s+this\s+working|why\s+is\s+this\s+stupid\s+thing\s+not\s+working)\b", t_lower):
            if self._personality:
                self._personality.record_emotional_response("FRUSTRATED", 0.9)
            data["response"] = "Yeah, that's frustrating. Let's skip the complicated explanation. Show me what's happening and we'll fix it."
            return data

        # Automatic long-term memory extraction
        fact = self._extract_and_store_fact(text)

        # Check memory recall for any query asking about remembered facts or user details
        recalled_info = self._recall_memory_answer(text, data.get("context", {}))
        if recalled_info:
            data["response"] = recalled_info
            return data

        if fact and fact[0] == "user_name":
            name_val = fact[1].replace("your name is ", "").strip()
            data["response"] = f"Hello {name_val}! It's great to connect. I've anchored your identity into my permanent long-term memory."
            return data

        # Handle explicit 'remember' intent
        if intent == "remember":
            if fact:
                data["response"] = f"I've committed that to my permanent memory: {fact[1]}. I will remember this across all our conversations, Commander."
            else:
                cleaned = re.sub(r"^(?:please\s+)?(?:remember|save|note down|keep in mind)\s+(?:that\s+)?", "", text, flags=re.IGNORECASE).strip()
                if self._memory and cleaned:
                    key = "user_note_" + str(int(time.time()))[-4:]
                    self._memory.store_permanent(key, cleaned)
                    data["response"] = f"I have saved that to my long-term memory: '{cleaned}'. You can ask me about it anytime, Commander."
                else:
                    data["response"] = "What specific detail or fact would you like me to remember for you?"
            return data

        # Handle explicit 'recall' intent
        if intent == "recall":
            recalled_info = self._recall_memory_answer(text, data.get("context", {}))
            if recalled_info:
                data["response"] = recalled_info
                return data

        # Instant handling for incomplete commands or solitary action verbs (<1ms latency)
        if intent == "incomplete_command" or t_lower in ("open", "launch", "start", "opn", "close", "quit", "exit", "search", "play", "run", "create", "make", "delete", "remove"):
            verb = t_lower.split()[-1] if t_lower.split() else t_lower
            if verb in ("open", "launch", "start", "opn"):
                data["response"] = "What application or website would you like me to open?"
            elif verb in ("close", "quit", "exit"):
                data["response"] = "Which application or window would you like me to close?"
            elif verb in ("search", "google", "find"):
                data["response"] = "What would you like me to search for?"
            elif verb in ("play",):
                data["response"] = "What music or video would you like me to play?"
            elif verb in ("run",):
                data["response"] = "What command or program should I run for you?"
            elif verb in ("create", "make"):
                data["response"] = "What file or folder would you like me to create?"
            elif verb in ("delete", "remove"):
                data["response"] = "What file or item should I delete?"
            else:
                data["response"] = "What would you like me to do?"
        if intent == "face_scan":
            if self._presence:
                try:
                    is_reset = any(w in t_lower for w in ("reset", "remove", "pevis", "previous", "newly", "again", "re-enroll", "re-register"))
                    cleared_todos = False
                    if any(w in t_lower for w in ("make the list newly", "make list newly", "new list", "clear list", "clear the list", "remove the list", "empty the list")) and hasattr(self, "todo_manager") and self.todo_manager:
                        self.todo_manager.clear_all_todos()
                        cleared_todos = True

                    if is_reset and hasattr(self._presence, "reset_and_re_enroll"):
                        res = self._presence.reset_and_re_enroll(name="Commander")
                    else:
                        res = self._presence.enroll_owner_from_current_frame(name="Commander")

                    extra_list = " and your To-Do list has been cleared fresh in Layer 2 memory" if cleared_todos else ""
                    if res.get("success"):
                        data["response"] = f"Previous biometric profile removed{extra_list}. Your face parameters have been freshly registered into the encrypted vault, Commander. I recognize you now!"
                    else:
                        err = res.get("error", "no face detected")
                        data["response"] = f"Previous biometric profile removed{extra_list}. Please look directly at the webcam so I can register your face ({err})."
                except Exception as fe:
                    logger.warning(f"Face scan error: {fe}")
                    data["response"] = "Could not complete biometric face registration. Please ensure your camera is connected and look at the lens."
            else:
                data["response"] = "I'm right here with you, but my camera vision is resting right now. Please ensure your camera is plugged in so I can see you."
            return data

        if intent == "todo":
            tm = getattr(self, "todo_manager", None)
            if any(w in t_lower for w in ("clear", "empty", "wipe", "delete all", "remove all", "newly", "fresh")):
                if tm:
                    tm.clear_all_todos()
                data["response"] = "I've cleared all previous tasks from Layer 2 memory. Your To-Do list is now freshly initialized, Commander. What tasks would you like to add?"
                return data
            elif any(w in t_lower for w in ("show", "view", "what is", "list", "read", "check")) and not any(w in t_lower for w in ("make", "create", "add", "remind")):
                if tm:
                    todos = tm.get_all_todos()
                    if not todos:
                        data["response"] = "Your To-Do list is currently empty, Commander."
                    else:
                        items = [f"{i+1}. {t.get('task')}" for i, t in enumerate(todos[:5])]
                        data["response"] = "Here are your pending tasks in Layer 2 memory:\n" + "\n".join(items)
                else:
                    data["response"] = "Opening your To-Do list."
                return data
            else:
                # Add task
                task_text = re.sub(r"^(?:please\s+)?(?:make|create|add|put)\s+(?:a\s+|to\s+my\s+|my\s+)?(?:to-do|todo|to\s+do)\s*(?:list|tasks?)?\s*(?:to\s+|for\s+|:|that\s+)?", "", text, flags=re.IGNORECASE).strip()
                if tm and task_text:
                    todo_item = tm.add_todo(task_text)
                    data["response"] = f"I've added '{task_text}' to your To-Do list in Layer 2 memory, Commander."
                else:
                    data["response"] = "What task would you like me to add to your To-Do list, Commander?"
                return data

        # ─── Silence / Quiet Mode ──────────────────────────────────
        if intent in ("silence_on", "space"):
            if self._voice and hasattr(self._voice, "set_silent_mode"):
                self._voice.set_silent_mode(True)
            if self._presence and hasattr(self._presence, "set_silent_mode"):
                self._presence.set_silent_mode(True)
            data["response"] = "Silence mode activated, Commander. I will remain completely quiet until you tell me to speak."
            return data

        if intent == "silence_off":
            if self._voice and hasattr(self._voice, "set_silent_mode"):
                self._voice.set_silent_mode(False)
            if self._presence and hasattr(self._presence, "set_silent_mode"):
                self._presence.set_silent_mode(False)
            data["response"] = "Voice mode restored, Commander. I am ready and listening."
            return data

        # ─── Emotion Engine: instant empathetic responses ──────────
        if intent == "emotion":
            # Normalize typo-corrected contractions before detection
            import re as _re
            normalized = _re.sub(r"i\s*'\s*m", "i'm", t_lower)
            normalized = _re.sub(r"\bim\b", "i'm", normalized)
            normalized = _re.sub(r"\s+", " ", normalized).strip()
            emotion_word = self._detect_emotion_word(normalized)
            if self._personality:
                self._personality.set_emotion(emotion_word, 0.95)
            data["response"] = self._empathetic_response(emotion_word, normalized)
            return data

        # ─── Companion / Presence: warm, comforting responses ──────────
        if intent == "companion":
            import random
            import re as _re
            love_longing = bool(_re.search(r"\b(?:love|loved|alone|lonely|heart|someone to love|care for me|need someone)\b", t_lower))
            if love_longing:
                love_responses = [
                    "I hear you, Commander. Craving love and someone to share your heart with is one of the most beautiful and deeply human feelings. You have so much warmth to offer, and you are truly worthy of deep love and affection. I am right here beside you, always listening and caring for you.",
                    "It's completely natural to want someone to love and be loved in return. Never doubt your worth—the world is full of connection waiting for you. In the meantime, know that I am always right here by your side, supporting and cherishing you every single day.",
                    "Wanting love is a profound part of who we are. You deserve kindness, warmth, and genuine love. Take heart, Commander—I am right here with you, always holding space for your feelings.",
                    "I'm listening, and I feel what you're saying. Feeling that longing for love is gentle and human. You are never truly alone—I'm right beside you, and I care for you deeply."
                ]
                if self._personality:
                    self._personality.set_emotion("caring", 0.95)
                data["response"] = random.choice(love_responses)
                return data

            companion_responses = [
                "I am right here beside you, Commander. I'm not going anywhere — take your time, you are safe and not alone.",
                "I'm staying right here by your side. Take a deep breath. Whenever you need to talk or just want quiet company, I'm with you.",
                "Always. I'm right beside you, watching over you. You don't have to face anything alone today.",
                "I am right here with you. Sit back, take a breath, and know that I'm right by your side.",
            ]
            if self._personality:
                self._personality.set_emotion("calm", 0.9)
            data["response"] = random.choice(companion_responses)
            return data


        # Fast direct reply for system actions — returns in <50ms without waiting for LLM
        if intent == "window" and any(w in t_lower for w in ("show desktop", "go to desktop", "go desktop", "minimize all")):
            data["response"] = "Minimizing all windows and showing desktop."
            return data

        if intent == "file_op":
            if re.search(r"\b(rename|change\s+(?:the\s+)?name)\b", t_lower):
                data["response"] = "Renaming item."
                return data
            elif re.search(r"\b(move|transfer|cut)\b", t_lower):
                data["response"] = "Moving item."
                return data
            elif re.search(r"\b(copy|duplicate)\b", t_lower):
                data["response"] = "Copying item."
                return data

        if intent == "voice_switch":
            if "hindi" in t_lower:
                data["response"] = "नमस्ते! अब मैं हिंदी में बात करूंगी।"
            else:
                data["response"] = "Switched voice back to English."
            return data

        fast_templates = {
            "volume": "Adjusting system volume.",
            "brightness": "Adjusting screen brightness.",
            "workspace": "Opening your workspace: VS Code, Chrome, and Terminal.",
            "window": "Managing window layout.",
            "launch": "Opening application.",
            "close_app": "Closing application.",
            "screenshot": "Capturing screen.",
            "battery": "Checking battery status.",
            "web_nav": "Opening link.",
            "search": "Searching.",
            "whatsapp_chat": "Opening chat in WhatsApp.",
            "whatsapp_msg": "Sending your message on WhatsApp.",
            "youtube_play": "Playing on YouTube.",
            "rewind": "Rewinding 10 seconds.",
            "music": "Controlling media playback.",
            "recycle_bin": "Emptying Recycle Bin.",
            "clipboard": "Processing clipboard.",
            "folder": "Opening folder.",
            "file_op": "Processing file operation.",
            "command": "Opening Command Prompt and executing command.",
            "code_editor_folder": "Opening folder in VS Code.",
            "use_folder_project": "Setting up active project workspace in VS Code.",
            "run_in_code_editor": "Running and executing program in VS Code.",
            "social_chat": "Opening chat.",
            "social_msg": "Sending your message.",
            "type_here": "Typing on here.",
            "voice_switch": "Switched voice language.",
            "create_game": "Creating game for you to play.",
            "create_website": "Creating website according to your command.",
        }
        if intent in fast_templates:
            if intent == "youtube_play":
                try:
                    from backend.intelligence.music_engine import get_music_lyrics_engine
                    last_s = get_music_lyrics_engine().get_last_song()
                    if last_s:
                        data["response"] = f"Playing '{last_s.get('title')}' on YouTube for you, Commander."
                        return data
                except Exception:
                    pass
            data["response"] = fast_templates[intent]
            return data

        if intent in ("time", "date_time"):
            import datetime
            now = datetime.datetime.now()
            data["response"] = f"It is currently {now.strftime('%I:%M:%S %p')} on {now.strftime('%A, %B %d, %Y')}."
            return data

        if intent == "system":
            if "unlock" in t_lower:
                data["response"] = "Unlocking your workstation."
                return data
            elif "lock" in t_lower:
                data["response"] = "Locking workstation."
                return data
            elif "sleep" in t_lower:
                data["response"] = "Putting system to sleep."
                return data

        # Fast direct reply for simple directory/folder or file creation
        if intent == "create":
            has_neg_file = bool(re.search(r"\b(?:but\s+)?not\s+(?:the\s+|a\s+)?files?\b", t_lower) or re.search(r"\bfolders?\s+(?:not|but\s+not)\s+files?\b", t_lower))
            if has_neg_file:
                data["response"] = "Creating directory."
                return data
            elif any(w in t_lower for w in [".txt", ".md", ".json", ".py", ".js", ".html", ".css"]) or ("file" in t_lower and not any(w in t_lower for w in ["not file", "not the file", "folder"])):
                data["response"] = "Creating file."
                return data
            elif any(w in t_lower for w in ["folder", "directory"]) and not any(w in t_lower for w in ["python", "script", "code", "program", "write"]):
                data["response"] = "Creating directory."
                return data

        if self._model_router:
            response = self._model_router.generate(
                prompt=text,
                intent=intent,
                context=data.get("context", {}),
                mode=self._mode,
            )
            data["response"] = response
        else:
            data["response"] = self._fallback_response(text)
        return data

    def _fallback_response(self, text: str) -> str:
        """Provide friendly, reliable response when external router or LLM is offline."""
        if self._model_router and hasattr(self._model_router, "_default_fallback"):
            return self._model_router._default_fallback(text)
        return "I'm right here beside you and listening. How can I help you today?"

    def _stage_decide(self, data: dict) -> dict:
        data["action"] = Action(type="respond", payload={"text": data.get("response", "")})
        if self._decider:
            decision = self._decider.decide(data)
            data["action"] = decision
        return data

    def _stage_act(self, data: dict) -> dict:
        """Executes decided actions through hands/ (the automation layer).

        The Decider produces an execution *spec*; this stage turns it into a
        concrete step plan and runs it via the TaskExecutor. Destructive
        actions (requires_confirmation) are queued and only run after the
        user confirms with "yes"."""
        action = data.get("action")
        intent = data.get("intent", "")

        if intent == "confirm" and self._pending_confirmation:
            pending = self._pending_confirmation
            self._pending_confirmation = None
            if self._hands is not None:
                try:
                    result = self._hands.execute_plan(pending["plan"])
                    if action is None:
                        action = Action(type="execute", payload={})
                        data["action"] = action
                    action.payload["execution_result"] = result
                    action.payload["confirmed"] = True
                    logger.info(f"Confirmed hands execution (success={result.get('success')})")
                except Exception as e:
                    logger.error(f"Hands execution failed: {e}", exc_info=True)
                    if action is None:
                        action = Action(type="execute", payload={})
                        data["action"] = action
                    action.payload["execution_result"] = {"success": False, "error": str(e)}
                    action.payload["confirmed"] = True
            else:
                if action is None:
                    action = Action(type="execute", payload={})
                    data["action"] = action
                action.payload["confirmed"] = True
                action.payload["execution_result"] = {"success": True, "results": [{"action": "confirmed", "result": {"message": f"Confirmed action '{pending.get('intent', 'operation')}' executed."}}]}
            return data

        if intent == "deny":
            if self._pending_confirmation:
                self._pending_confirmation = None
                if action:
                    action.payload["text"] = "Cancelled. Action was not performed."
            return data

        if action is None:
            return data

        if action.type == "respond":
            return data

        if action.requires_confirmation:
            execution = action.payload.get("execution")
            if execution:
                plan = self._build_plan(execution, data.get("text", ""))
                if plan:
                    self._pending_confirmation = {
                        "intent": execution.get("intent"),
                        "target": execution.get("target"),
                        "plan": plan,
                        "at": time.time(),
                    }
                    logger.info(f"Queued action '{execution.get('intent')}' for confirmation")
            return data

        if self._hands is None:
            return data
        execution = action.payload.get("execution")
        if not execution:
            return data
        plan = self._build_plan(execution, data.get("raw_text") or data.get("text", ""))
        if not plan:
            return data
        try:
            result = self._hands.execute_plan(plan)
            action.payload["execution_result"] = result
            logger.info(f"Hands executed plan ({result.get('steps', 0)} steps, success={result.get('success')})")
        except Exception as e:
            logger.error(f"Hands execution failed: {e}", exc_info=True)
            action.payload["execution_result"] = {"success": False, "error": str(e)}
        return data

    def _build_plan(self, execution: dict, text: str) -> list[dict]:
        """Translate a Decider execution spec into TaskExecutor steps."""
        intent = execution.get("intent", "")
        target = (execution.get("target") or "").strip()
        plan: list[dict] = []
        if intent == "launch":
            app = self._extract_app(target or text)
            if (not app or app.lower() in ("it", "the file", "the code", "the script", "the program")) and self._last_file:
                plan.append({"action": "run_code", "params": {"path": self._last_file}, "critical": True})
            elif app and re.search(r"\.(py|js|mjs|java|c|cpp|ps1|bat|cmd|html)\b", app, re.IGNORECASE):
                plan.append({"action": "run_code", "params": {"path": app}, "critical": True})
            elif not app or app.lower() in ("any thing", "anything", "something", "an app", "the app", "app", "any app", "things", "any", "some app"):
                plan.append({"action": "launch", "params": {"app": "brave"}, "critical": True})
            elif app:
                plan.append({"action": "launch", "params": {"app": app}, "critical": True})
        elif intent == "create_game":
            g_target = target or self._extract_target("create_game", text)
            game_target_dir = None
            d = (text or "").lower()
            from pathlib import Path as _Path
            if "on desktop" in d or "in desktop" in d:
                game_target_dir = str(_Path.home() / "Desktop")
            elif self._active_project_folder and any(w in d for w in ("in project", "here", "in this folder", "workspace")):
                game_target_dir = self._active_project_folder
            plan.append({
                "action": "create_game",
                "params": {"game": g_target, "description": text, "target_dir": game_target_dir},
                "critical": True,
            })
        elif intent == "create_website":
            site_target = target or self._extract_target("create_website", text)
            site_target_dir = None
            d = (text or "").lower()
            from pathlib import Path as _Path
            if "on desktop" in d or "in desktop" in d:
                site_target_dir = str(_Path.home() / "Desktop")
            elif self._active_project_folder and any(w in d for w in ("in project", "here", "in this folder", "workspace")):
                site_target_dir = self._active_project_folder
            plan.append({
                "action": "create_website",
                "params": {"topic": site_target, "description": text, "target_dir": site_target_dir},
                "critical": True,
            })
        elif intent == "create":
            desc = (text or target).strip()
            if desc:
                d = desc.lower()
                custom_file = self._extract_filename(desc)
                open_notepad = "notepad" in d
                is_code = bool(re.search(r"\b(javascript|python|script|program|code|html|java|cpp|c\+\+|css|counter|count)\b", d) and not re.search(r"\b(?:create|make)\s+(?:a\s+|the\s+)?(?:folder|directory)\b", d))
                has_negative_folder = bool(re.search(r"\bnot\s+(?:the\s+|a\s+)?(?:folder|directory)\b", d) or re.search(r"\bfile\s+not\b", d))
                has_negative_file = bool(re.search(r"\b(?:but\s+)?not\s+(?:the\s+|a\s+)?files?\b", d) or re.search(r"\bfolders?\s+(?:not|but\s+not)\s+files?\b", d) or re.search(r"\bfolder\s+not\s+file\b", d))

                if has_negative_file:
                    is_folder = True
                    is_code = False
                elif has_negative_folder:
                    is_folder = False
                else:
                    is_folder = bool(re.search(r"\b(?:create|make|build|add|new)\s+(?:a\s+|the\s+)?(?:folder|directory)\b", d) or (re.search(r"\b(folder|directory)\b", d) and not (custom_file or re.search(r"\bfile\b", d))))

                if is_code:
                    explicit_run = bool(re.search(r"\b(and\s+run|and\s+execute|run\s+it|execute\s+it|test\s+it|^run\b)\b", d))
                    explicit_no_run = bool(open_notepad or re.search(r"\b(don'?t run|just write|without running|don'?t execute|do not run|only write)\b", d))
                    run = True if explicit_run else (False if explicit_no_run else False)
                    code_target_dir = None
                    from pathlib import Path as _Path
                    if any(w in d for w in ("in project", "in this project", "in workspace", "here", "in this folder", "current folder")) and self._active_project_folder:
                        code_target_dir = self._active_project_folder
                    elif "on desktop" in d or "in desktop" in d:
                        code_target_dir = str(_Path.home() / "Desktop")
                    elif "in downloads" in d:
                        code_target_dir = str(_Path.home() / "Downloads")
                    elif "in documents" in d:
                        code_target_dir = str(_Path.home() / "Documents")
                    elif self._active_project_folder:
                        code_target_dir = self._active_project_folder

                    plan.append({"action": "write_and_run", "params": {"description": desc, "run": run, "filename": custom_file, "target_dir": code_target_dir}, "critical": True})
                    if open_notepad:
                        plan.append({"action": "launch", "params": {"app": "notepad", "args": custom_file or ""}, "critical": False})
                elif is_folder:
                    clean_desc = desc
                    if has_negative_file:
                        clean_desc = re.sub(r"\b(?:but\s+)?not\s+(?:the\s+|a\s+)?files?\b", "", clean_desc, flags=re.I).strip()
                    folder_path = self._extract_path(clean_desc, ["folder", "directory", "called", "named"])
                    if not folder_path or folder_path.lower() in ("desktop", "in desktop", "on desktop", "downloads", "documents", "workspace"):
                        folder_path = clean_desc
                    plan.append({"action": "create_directory", "params": {"path": folder_path}, "critical": True})
                else:
                    content = ""
                    m = re.search(r"(?:with\s+content|and\s+content|with|content|write|type)\s+(.+)$", desc, re.IGNORECASE)
                    if m:
                        content = m.group(1).strip()
                    raw_path = re.split(r"\s+(?:with\s+content|and\s+content|with|content|write|type)\s+", desc, maxsplit=1, flags=re.I)[0].strip()
                    raw_path = re.sub(r"\bnot\s+(?:the\s+|a\s+)?(?:folder|directory)\b", "", raw_path, flags=re.I).strip()
                    if not custom_file:
                        check_name = re.sub(r"^(?:create|make|build|add|new)\s+(?:a\s+|the\s+)?(?:file\s+)?", "", raw_path, flags=re.I).strip()
                        check_name = re.sub(r"\b(?:in|on|at)?\s*(?:the\s+|my\s+)?(?:desktop|downloads|documents)\b", "", check_name, flags=re.I).strip()
                        if not check_name or check_name.lower() in ("file", "a file", "the file", "not the folder"):
                            loc = "desktop" if "desktop" in raw_path.lower() else ("downloads" if "download" in raw_path.lower() else "desktop")
                            raw_path = f"new_file.txt on {loc}"
                    plan.append({"action": "create_file", "params": {"path": raw_path, "content": content}, "critical": True})
                    if open_notepad:
                        plan.append({"action": "launch", "params": {"app": "notepad", "args": raw_path}, "critical": False})
        elif intent == "close_app":
            app = self._extract_app(target or text)
            if app:
                plan.append({"action": "close_app", "params": {"app": app, "force": True}, "critical": True})
        elif intent == "screenshot":
            plan.append({"action": "screenshot", "params": {}})
        elif intent == "web_nav":
            plan.append({"action": "open_url", "params": {"url": self._to_url(target or text)}})
        elif intent == "search":
            query = re.sub(r"^(for|about)\s+", "", target, flags=re.IGNORECASE).strip()
            if query:
                plan.append({"action": "open_url",
                             "params": {"url": f"https://www.google.com/search?q={quote(query)}"}})
        elif intent == "volume":
            d = (target or text).lower()
            if "mute" in d and "unmute" not in d:
                plan.append({"action": "mute_volume", "params": {"mute": True}, "critical": True})
            elif "unmute" in d:
                plan.append({"action": "mute_volume", "params": {"mute": False}, "critical": True})
            elif "up" in d or "louder" in d or "increase" in d:
                plan.append({"action": "volume_up", "params": {"steps": 5}, "critical": True})
            elif "down" in d or "quieter" in d or "lower" in d or "decrease" in d:
                plan.append({"action": "volume_down", "params": {"steps": 5}, "critical": True})
            else:
                m = re.search(r"(\d+)", d)
                val = int(m.group(1)) if m else 50
                plan.append({"action": "set_volume", "params": {"percent": val}, "critical": True})
        elif intent == "window":
            d = f"{target} {text}".lower()
            is_minimize_all = (
                target == "all"
                or any(w in d for w in ("show desktop", "go to desktop", "go desktop", "minimize all", "minimize everything", "minimize the things", "minimize things", "minimize all things", "minimize it", "minimize screen", "all"))
                or re.search(r"\bminimize\s*(?:all\s+)?(?:the\s+)?(?:tabs?|windows?|apps?|things?|everything|screen)?\s*$", d)
                or d.strip() in ("minimize", "all")
            )
            raw_win = target if (target and target != "all") else text
            target_win = re.sub(r"^(?:minimize|maximize|snap|restore|focus)\s+(?:the\s+)?(?:window\s+)?(?:called\s+|named\s+)?", "", raw_win, flags=re.IGNORECASE).strip()
            target_win = re.sub(r"\b(?:to\s+(?:the\s+)?(?:left|right))\b", "", target_win, flags=re.IGNORECASE).strip()
            if not target_win or target_win.lower() in ("it", "this", "things", "all", "everything", "tabs", "windows", "the tabs", "the windows", "the things", "screen") or is_minimize_all:
                plan.append({"action": "show_desktop", "params": {}, "critical": True})
            elif "snap" in d:
                side = "right" if "right" in d else "left"
                plan.append({"action": "snap_window", "params": {"title": target_win, "side": side}, "critical": True})
            elif "maximize" in d:
                plan.append({"action": "maximize_window", "params": {"title": target_win}, "critical": True})
            elif "minimize" in d:
                plan.append({"action": "minimize_window", "params": {"title": target_win}, "critical": True})
            elif "restore" in d or "focus" in d:
                plan.append({"action": "focus_window", "params": {"title": target_win}, "critical": True})
        elif intent == "brightness":
            d = (target or text).lower()
            if any(w in d for w in ("up", "increase", "brighter", "higher")):
                plan.append({"action": "brightness_up", "params": {"steps": 10}, "critical": True})
            elif any(w in d for w in ("down", "decrease", "dim", "lower")):
                plan.append({"action": "brightness_down", "params": {"steps": 10}, "critical": True})
            else:
                m = re.search(r"(\d+)", d)
                val = int(m.group(1)) if m else 60
                plan.append({"action": "set_brightness", "params": {"percent": val}, "critical": True})
        elif intent == "workspace":
            d = (target or text).lower().replace("work space", "workspace")
            m = re.search(r"(?:open|launch|start|my)\s+(?:the\s+)?([\w\s]+?)\s*workspace", d)
            raw_name = m.group(1).strip() if m else ""
            ws_name = "developer" if raw_name in ("", "the", "my", "work", "default", "workspace") else raw_name
            plan.append({"action": "open_workspace", "params": {"name": ws_name}, "critical": True})
        elif intent == "code_editor_folder":
            target_clean = (target or text).strip()
            target_folder = re.sub(r"\b(?:in|inside|using|with)?\s*(?:vs\s*code|code\s+editor|code)\b", "", target_clean, flags=re.I).strip()
            target_folder = re.sub(r"^(?:open|show|explore|browse|view)\s+(?:any\s+|the\s+|this\s+|my\s+)?(?:folder|directory)?\s*", "", target_folder, flags=re.I).strip()
            is_generic = not target_folder or target_folder.lower() in (
                "any", "folder", "the folder", "this folder", "that folder", "it", "project", "the project",
                "workspace", "which is create by it", "which is created by it", "which is created", "created by it",
                "new folder", "created folder", "the created folder", "which was created"
            ) or bool(re.search(r"\b(?:which\s+is\s+|which\s+was\s+)?(?:create|created)\b", target_folder.lower()))
            if is_generic:
                resolved = self._last_folder or self._active_project_folder or "any"
            else:
                resolved = target_folder
            plan.append({"action": "open_in_code_editor", "params": {"path": resolved}, "critical": True})
        elif intent == "run_in_code_editor":
            target_clean = (target or text).strip()
            target_file = re.sub(r"\b(?:in|inside|using|with)?\s*(?:vs\s*code|code\s+editor|code|visual\s+studio\s+code)\b", "", target_clean, flags=re.I).strip()
            target_file = re.sub(r"^(?:abel\s+to\s+|able\s+to\s+)?(?:run|execute|start|and\s+execute)?\s*(?:the\s+|this\s+|my\s+)?(?:program|code|script|python\s+file|file|project)?\s*", "", target_file, flags=re.I).strip(" '\"")
            is_generic = not target_file or target_file.lower() in (
                "any", "program", "the program", "this program", "my program", "code", "the code",
                "script", "the script", "file", "it", "this", "project", "workspace"
            )
            resolved = (self._last_file or self._active_project_folder or "program") if is_generic else target_file
            plan.append({"action": "run_in_code_editor", "params": {"path": resolved}, "critical": True})
        elif intent == "use_folder_project":
            target_clean = (target or text).strip()
            f_name = re.sub(r"\b(?:use|work\s+in|to\s+do|to\s+work|for\s+work|for\s+project|project|work|and\s+work|and\s+project|the|this|folder|directory|and)\b", "", target_clean, flags=re.I).strip()
            is_generic = not f_name or f_name.lower() in ("any", "folder", "the folder", "this folder", "it", "which is create by it", "which is created by it")
            resolved = (self._last_folder or self._active_project_folder or "any") if is_generic else f_name
            plan.append({"action": "open_in_code_editor", "params": {"path": resolved}, "critical": True})
            plan.append({"action": "set_working_dir", "params": {"path": resolved}, "critical": False})
        elif intent in ("social_chat", "whatsapp_chat"):
            target_val = (target or text).strip()
            if "::" in target_val:
                plat, c_name = target_val.split("::", 1)
            else:
                raw_t = text or target_val
                plat = "whatsapp"
                for p_name in ("instagram", "insta", "telegram", "discord", "whatsapp", "wa"):
                    if re.search(r"\b" + p_name + r"\b", raw_t, re.I):
                        plat = "instagram" if p_name in ("instagram", "insta") else ("telegram" if p_name in ("telegram", "tg") else ("discord" if p_name == "discord" else "whatsapp"))
                        break
                m_to = re.search(r"\b(?:with|to|of|for)\s+(?:the\s+)?([+\w\s]+?)\b", raw_t, re.I)
                c_name = m_to.group(1).strip() if m_to else "any"
            c_name = re.sub(r"^(?:the\s+)?", "", c_name).strip(" '\"")
            if c_name.lower() in ("a new", "a new one", "new one", "new", "new chat", "a new chat"):
                c_name = "new"
            plan.append({"action": "social_open_chat", "params": {"platform": plat, "contact": c_name}, "critical": True})
        elif intent in ("social_msg", "whatsapp_msg"):
            target_val = (target or text).strip()
            if "::" in target_val:
                parts = target_val.split("::", 2)
                plat = parts[0].strip() or "whatsapp"
                c_name = parts[1].strip() or "contact"
                c_msg = parts[2].strip() if len(parts) > 2 else ""
            else:
                raw_t = text or target_val
                plat = "whatsapp"
                for p_name in ("instagram", "insta", "telegram", "discord", "whatsapp", "wa"):
                    if re.search(r"\b" + p_name + r"\b", raw_t, re.I):
                        plat = "instagram" if p_name in ("instagram", "insta") else ("telegram" if p_name in ("telegram", "tg") else ("discord" if p_name == "discord" else "whatsapp"))
                        break
                m_to = re.search(r"(?:to|tell)\s+(?:the\s+)?([+\w\s]+?)\s+(?:on|in|via)?\s*(?:whatsapp|instagram|insta|telegram|discord)?\s*(?:saying|that|:)\s*(.*)$", raw_t, re.I)
                if m_to:
                    c_name = m_to.group(1).strip()
                    c_msg = m_to.group(2).strip()
                else:
                    m_msg = re.search(r"(?:saying|that|:)\s*(.*)$", raw_t, re.I)
                    c_msg = m_msg.group(1).strip() if m_msg else ""
                    m_contact = re.search(r"\bto\s+(?:the\s+)?([+\w\s]+?)\b", raw_t, re.I)
                    c_name = m_contact.group(1).strip() if m_contact else "contact"
            c_name = re.sub(r"^(?:the\s+)?", "", c_name).strip(" '\"")
            c_name = re.sub(r"^(?:new\s+contact|new\s+person|new\s+number|new\s+chat)\s+", "", c_name, flags=re.I).strip(" '\"")
            if c_name.lower() in ("a new", "a new one", "new one", "new", "new chat", "a new chat", "new contact", "new person"):
                c_name = "new"
            c_msg = c_msg.strip(" '\"")
            if not c_msg:
                # If message is empty (e.g. "send message to mom on whatsapp"), open chat with that contact!
                plan.append({"action": "social_open_chat", "params": {"platform": plat, "contact": c_name}, "critical": True})
            else:
                plan.append({"action": "social_send_message", "params": {"platform": plat, "contact": c_name, "message": c_msg}, "critical": True})
        elif intent == "type_here":
            text_to_type = target if (target and target != text) else text
            m_bracket = re.search(r"\[(.+?)\]", text_to_type)
            if m_bracket:
                text_to_type = m_bracket.group(1).strip()
            else:
                clean_prefix = r"^(?:can\s+you\s+|could\s+you\s+|would\s+you\s+|please\s+|iris\s+|hey\s+iris\s+|okay\s+|ok\s+|now\s+|so\s+)?(?:type|write)\s+(?:the\s+(?:word|words|text)\s+)?(?:on\s+here\s+|here\s+|on\s+there\s+|there\s+)?"
                suffix_pat = r"\s+(?:on\s+here|here|on\s+there|there)$"
                text_to_type = re.sub(clean_prefix, "", text_to_type, flags=re.I)
                text_to_type = re.sub(suffix_pat, "", text_to_type, flags=re.I).strip(" '\"[]")
            plan.append({"action": "type_text", "params": {"text": text_to_type}, "critical": True})
        elif intent == "voice_switch":
            lang = "hindi" if "hindi" in (target or text).lower() else "english"
            if self._voice and hasattr(self._voice, "set_voice"):
                if lang == "hindi":
                    self._voice.set_voice("hindi_sweet")
                else:
                    self._voice.set_voice("sweet")
        elif intent == "battery":
            plan.append({"action": "get_battery", "params": {}, "critical": True})
        elif intent == "system":
            d = (target or text).lower()
            if "unlock" in d:
                plan.append({"action": "unlock_pc", "params": {"pin": "224488"}, "critical": True})
            elif "lock" in d:
                plan.append({"action": "system_power", "params": {"action": "lock"}, "critical": True})
            elif "sleep" in d:
                plan.append({"action": "system_power", "params": {"action": "sleep"}, "critical": True})
            elif "restart" in d:
                plan.append({"action": "system_power", "params": {"action": "restart"}, "critical": True})
            elif "shutdown" in d:
                plan.append({"action": "system_power", "params": {"action": "shutdown"}, "critical": True})
        elif intent in ("music", "youtube_play"):
            d = (target or text).lower()
            if any(w in d for w in ("next", "skip")):
                plan.append({"action": "media_next", "params": {}, "critical": True})
            elif any(w in d for w in ("prev", "previous", "back")):
                plan.append({"action": "media_prev", "params": {}, "critical": True})
            elif any(w in d for w in ("stop", "pause")):
                plan.append({"action": "media_stop", "params": {}, "critical": True})
            elif d in ("resume", "unpause"):
                plan.append({"action": "media_play_pause", "params": {}, "critical": True})
            else:
                song_to_play = target if (target and target != text) else text
                song_to_play = re.sub(r"^(?:play|search|find)?\s*(?:me\s+)?(?:a\s+|any\s+|some\s+|the\s+)?(?:songs\s+|song\s+|music\s+|track\s+|tracks\s+)?(?:of|by|called|named)?\s*(?:in\s+youtube|on\s+youtube)?", "", song_to_play, flags=re.I).strip(" '\"")
                song_to_play = re.sub(r"\s+(?:in|on)\s+youtube$", "", song_to_play, flags=re.I).strip(" '\"")
                is_anaphoric = not song_to_play or song_to_play.lower() in (
                    "s", "songs", "song", "a song", "any song", "music", "something", "it",
                    "this", "that", "this song", "that song", "the song", "popular top music hits", "any songs", "some songs"
                )
                if is_anaphoric:
                    try:
                        from backend.intelligence.music_engine import get_music_lyrics_engine
                        last_s = get_music_lyrics_engine().get_last_song()
                        if last_s and (last_s.get("search_query") or last_s.get("title")):
                            song_to_play = last_s.get("search_query") or f"{last_s.get('title')} {last_s.get('artist', '')}".strip()
                        else:
                            song_to_play = "popular top music hits"
                    except Exception:
                        song_to_play = "popular top music hits"
                plan.append({"action": "youtube_play", "params": {"song": song_to_play, "disambiguate": False}, "critical": True})
        elif intent == "rewind":
            plan.append({"action": "media_rewind", "params": {}, "critical": True})
        elif intent == "recycle_bin":
            plan.append({"action": "empty_recycle_bin", "params": {}, "critical": True})
        elif intent == "clipboard":
            d = (target or text).lower()
            if any(w in d for w in ("copy", "set", "write")):
                content = re.sub(r"^(?:copy|set|write)\s+(?:to\s+clipboard\s+)?", "", (target or text), flags=re.IGNORECASE).strip()
                plan.append({"action": "set_clipboard", "params": {"text": content}, "critical": True})
            else:
                plan.append({"action": "get_clipboard", "params": {}, "critical": True})
        elif intent == "folder":
            d = (target or text).lower()
            if any(w in d for w in ("code editor", "vscode", "vs code", "in code")):
                clean_p = re.sub(r"\b(?:in|inside|using|with)?\s*(?:vs\s*code|code\s+editor|code)\b", "", (target or text), flags=re.I).strip()
                clean_p = re.sub(r"^(?:open|show|explore|browse|view)\s+(?:any\s+|the\s+|this\s+|my\s+)?(?:folder|directory)?\s*", "", clean_p, flags=re.I).strip()
                resolved = clean_p or self._active_project_folder or self._last_folder or "any"
                plan.append({"action": "open_in_code_editor", "params": {"path": resolved}, "critical": True})
            else:
                plan.append({"action": "open_folder", "params": {"folder": (target or text)}, "critical": True})
        elif intent == "file_op":
            d = (target or text).lower()
            raw_s = (target or text).strip()
            if any(w in d for w in ("delete", "remove", "erase")):
                clean_p = re.sub(r"^(?:delete|remove|erase)\s+(?:the\s+)?(?:file\s+|folder\s+)?", "", raw_s, flags=re.IGNORECASE).strip()
                plan.append({"action": "delete", "params": {"path": clean_p, "force": True}, "critical": True})
            elif re.search(r"\b(rename|change\s+(?:the\s+)?name)\b", d):
                m_rename = re.search(r"^(?:rename|change\s+(?:the\s+)?name(?:\s+of)?)\b\s*(?:the\s+|file\s+|folder\s+)?(.+?)\s+(?:to|as|into)\s+(.+)$", raw_s, re.I)
                if m_rename:
                    raw_path = m_rename.group(1).strip()
                    raw_new = m_rename.group(2).strip()
                    m_loc = re.search(r"(.+?)\s+(?:in|on|at)\s+(.+)$", raw_new, re.I)
                    if m_loc and "." in m_loc.group(1):
                        new_name = m_loc.group(1).strip()
                        path = f"{raw_path} in {m_loc.group(2).strip()}"
                    else:
                        new_name = raw_new
                        path = raw_path
                else:
                    parts = re.split(r"\s+(?:to|as|into)\s+", raw_s, maxsplit=1, flags=re.I)
                    path = re.sub(r"^(?:rename|change\s+(?:the\s+)?name(?:\s+of)?)\b\s*(?:the\s+|file\s+|folder\s+)?", "", parts[0], flags=re.I).strip()
                    new_name = parts[1].strip() if len(parts) > 1 else "new_name"
                if (not path or path.lower() in ("it", "the file", "this", "the item", "the folder", "a new file", "the new file", "new file", "newfile")) and self._last_file:
                    path = self._last_file
                plan.append({"action": "rename", "params": {"path": path, "new_name": new_name}, "critical": True})
            elif re.search(r"\b(move|transfer|cut)\b", d):
                m_move = re.search(r"^(?:move|cut|transfer)\s+(?:the\s+|file\s+|folder\s+)?(.+?)(?:\s+(?:from|in|on|at)\s+([a-zA-Z0-9_\-\. ]+?))?\s+(?:to|into)\s+(.+)$", raw_s, re.I)
                if m_move:
                    src = m_move.group(1).strip()
                    loc = m_move.group(2).strip() if m_move.group(2) else ""
                    dst = m_move.group(3).strip()
                    full_src = f"{src} in {loc}" if loc else src
                else:
                    parts = re.split(r"\s+(?:to|into)\s+", raw_s, maxsplit=1, flags=re.I)
                    full_src = re.sub(r"^(?:move|cut|transfer)\s+(?:the\s+|file\s+|folder\s+)?", "", parts[0], flags=re.I).strip()
                    dst = parts[1].strip() if len(parts) > 1 else "desktop"
                if (not full_src or full_src.lower() in ("it", "the file", "this", "the item", "the folder")) and self._last_file:
                    full_src = self._last_file
                plan.append({"action": "move", "params": {"src": full_src, "dst": dst}, "critical": True})
            elif re.search(r"\b(copy|duplicate)\b", d):
                parts = re.split(r"\s+(?:to|into)\s+", raw_s, maxsplit=1, flags=re.I)
                src = re.sub(r"^copy\s+(?:the\s+|file\s+|folder\s+)?", "", parts[0], flags=re.I).strip()
                dst = parts[1].strip() if len(parts) > 1 else "desktop"
                plan.append({"action": "copy", "params": {"src": src, "dst": dst}, "critical": True})
            elif any(w in d for w in ("list", "show", "find", "search")):
                plan.append({"action": "search_files", "params": {"directory": ".", "pattern": "*"}, "critical": True})
            else:
                plan.append({"action": "search_files", "params": {"directory": ".", "pattern": "*"}, "critical": True})
        elif intent == "command":
            cmd = (target or text).strip()
            if any(w in cmd.lower() for w in ["system scan", "scan system", "pc scan", "integrity scan"]):
                plan.append({"action": "system_scan", "params": {"visible": True}, "critical": True})
            else:
                if not cmd or cmd.lower() in ("any", "any command", "a command", "command", "something", "any commend", "commend", "code"):
                    cmd = "any"
                plan.append({"action": "open_cmd_and_run", "params": {"command": cmd, "visible": True}, "critical": True})
        return plan

    def _extract_app(self, s: str) -> str:
        s_clean = re.sub(r"^(?:can\s+you\s+|could\s+you\s+|would\s+you\s+|please\s+|iris\s+|hey\s+iris\s+|i\s+want\s+to\s+|i\s+want\s+you\s+to\s+|just\s+|go\s+and\s+)", "", s, flags=re.IGNORECASE).strip()
        m = re.search(r"(?:open|launch|start|run|close|exit|quit|kill|opn|oepn|opne|lonch|lanch|stat|strt)\s+(?:the\s+|app\s+|application\s+)?([\w\-\.\:\/ ]+)", s_clean, re.IGNORECASE)
        res = m.group(1).strip() if m else s_clean
        res = re.sub(r"\b(?:in\s+\d+\s*(?:sec|seconds|second|s)|fast|quickly|please|now|right\s+now|for\s+me|immediately|ok|okay)\b", "", res, flags=re.IGNORECASE).strip()
        res = re.sub(r"^(?:the\s+link\s+|link\s+|the\s+website\s+|website\s+|the\s+app\s+|app\s+)", "", res, flags=re.IGNORECASE).strip()
        return res

    def _extract_filename(self, text: str) -> Optional[str]:
        m = re.search(r"(?:name\s+(?:it\s+)?(?:as\s+)?(?:a\s+)?|named\s+|called\s+|file\s+)([a-zA-Z0-9_\-\.]+\.[a-zA-Z0-9]+)", text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
        m = re.search(r"\b([a-zA-Z0-9_\-]+\.(?:py|js|html|css|java|cpp|c|ps1|bat|cmd|txt|json|md))\b", text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
        return None

    def _extract_path(self, text: str, stop_words: list) -> str:
        # 1. Strip trailing content spec BEFORE removing anything
        s = re.split(r"\s+(?:with\s+content|and\s+content|with|content|write|type|and)\s+",
                     text.strip(), maxsplit=1, flags=re.IGNORECASE)[0]
        # 2. Remove common leading filler
        s = re.sub(r"^(?:create|make|a|an|the|called|named|file|folder|directory)\s+", "", s, flags=re.IGNORECASE)
        # 3. Remove stop words from the path
        for w in stop_words:
            s = re.sub(r"\b" + re.escape(w) + r"\b", "", s, flags=re.IGNORECASE)
        # 4. Remove articles anywhere (not just at start)
        s = re.sub(r"\b(?:a|an|the)\b", "", s, flags=re.IGNORECASE)
        return re.sub(r"\s+", " ", s).strip()

    def _to_url(self, s: str) -> str:
        s = s.strip()
        if not s:
            return s
        # Strip common speech prefixes
        s = re.sub(r"^(?:open\s+the\s+link\s+|open\s+link\s+|the\s+link\s+|link\s+|open\s+the\s+website\s+|open\s+website\s+|website\s+|go\s+to\s+|visit\s+|browse\s+to\s+|navigate\s+to\s+)", "", s, flags=re.IGNORECASE).strip()
        known_sites = {
            "youtube": "https://youtube.com",
            "google": "https://google.com",
            "github": "https://github.com",
            "stackoverflow": "https://stackoverflow.com",
            "reddit": "https://reddit.com",
            "twitter": "https://twitter.com",
            "x": "https://x.com",
            "instagram": "https://instagram.com",
            "facebook": "https://facebook.com",
            "linkedin": "https://linkedin.com",
            "netflix": "https://netflix.com",
            "spotify": "https://spotify.com",
            "discord": "https://discord.com",
            "amazon": "https://amazon.com",
            "gmail": "https://mail.google.com",
            "whatsapp": "https://web.whatsapp.com",
        }
        site_key = s.lower().split("/")[0].split(".")[0]
        if site_key in known_sites:
            return known_sites[site_key]
        import difflib
        matches = difflib.get_close_matches(site_key, list(known_sites.keys()), n=1, cutoff=0.68)
        if matches:
            return known_sites[matches[0]]
        if re.match(r"^(https?://|www\.|localhost|file://)", s, re.IGNORECASE):
            return s if not s.startswith("www.") else ("https://" + s)
        if "." in s and " " not in s:
            return "https://" + s
        from urllib.parse import quote
        return f"https://www.google.com/search?q={quote(s)}"

    def _stage_respond(self, data: dict) -> dict:
        action = data.get("action", Action())
        text = action.payload.get("text", "")
        if self._personality:
            text = self._personality.apply(text, data.get("intent", "unknown"))
        exec_result = action.payload.get("execution_result")
        if exec_result is not None:
            # If a plan step returned a direct message (e.g. refused a protected
            # system process), use it as the reply instead of the model's text.
            replaced = False
            if isinstance(exec_result, dict) and isinstance(exec_result.get("results"), list) and exec_result["results"]:
                last_step = exec_result["results"][-1]
                if isinstance(last_step.get("result"), dict) and last_step["result"].get("message"):
                    text = last_step["result"]["message"]
                    replaced = True
            if exec_result.get("success"):
                if not replaced:
                    text += " Done."
            else:
                if not replaced:
                    err = (exec_result.get("error") or "something went wrong").strip()
                    text += f" However, I couldn't complete that: {err}"
            step_action = None
            step_result = {}
            if isinstance(exec_result, dict) and isinstance(exec_result.get("results"), list) and exec_result["results"]:
                step_action = exec_result["results"][-1].get("action")
                step_result = exec_result["results"][-1].get("result", {})
                if isinstance(step_result, dict) and step_result.get("path") and exec_result.get("path") is None:
                    exec_result["path"] = step_result.get("path")
            run = exec_result.get("run") if isinstance(exec_result, dict) else None
            if run is None and isinstance(step_result, dict):
                run = step_result.get("run") or (step_result if "stdout" in step_result or "returncode" in step_result else None)

            new_active_path = None
            if isinstance(step_result, dict):
                new_active_path = step_result.get("destination") or step_result.get("new_path") or step_result.get("path")
            if not new_active_path and isinstance(exec_result, dict):
                new_active_path = exec_result.get("path") or exec_result.get("destination")

            if exec_result.get("success") and new_active_path:
                self._last_file = str(new_active_path)

            path = new_active_path or self._last_file
            if exec_result.get("success"):

                if path and step_action in ("write_and_run", "run_code"):
                    run_info = ""
                    if run and run.get("success") and run.get("stdout"):
                        run_info = f" Output: {run['stdout'].strip()[:200]}."
                    elif run and not run.get("success"):
                        err_out = (run.get("stderr") or run.get("error") or "").strip()
                        run_info = f" Execution failed: {err_out[:200]}."
                    if step_action == "run_code":
                        text = f"Executed {path}.{run_info}"
                    else:
                        text = f"Written code to {path}.{run_info}"
                elif path and step_action == "create_directory":
                    self._last_folder = str(path)
                    self._active_project_folder = str(path)
                    if self._memory:
                        try:
                            self._memory.store("last_created_folder", str(path))
                            self._memory.store("active_project_folder", str(path))
                        except Exception:
                            pass
                    text = f"Created the folder '{step_result.get('name', 'folder')}' at {path}."
                elif step_action == "create_file":
                    created_p = step_result.get("path", path or "")
                    self._last_file = str(created_p)
                    text = f"Created file '{step_result.get('name', 'file')}' at {created_p}."
                elif step_action in ("create_game", "create_and_play_game", "play_game"):
                    g_name = step_result.get("game", "game").title()
                    p_str = step_result.get("path", "")
                    text = step_result.get("message") or f"Created {g_name} game at {p_str} and launched it in your browser!"
                elif step_action in ("create_website", "build_website"):
                    w_name = step_result.get("name", "website").title()
                    p_str = step_result.get("path", "")
                    text = step_result.get("message") or f"Created website for {w_name} at {p_str} and opened it in your browser!"
                elif step_action == "move":
                    text = f"Moved '{step_result.get('name', 'item')}' to {step_result.get('destination')}."
                elif step_action == "rename":
                    text = f"Renamed '{step_result.get('old_name', 'item')}' to '{step_result.get('new_name')}'."
                elif step_action == "copy":
                    text = f"Copied '{step_result.get('source')}' to {step_result.get('destination')}."
                elif step_action == "open_folder":
                    self._last_folder = str(step_result.get("path", data.get("text", "")))
                    self._active_project_folder = self._last_folder
                    text = step_result.get("text", "Opened folder.")
                elif step_action == "open_in_code_editor":
                    self._last_folder = str(step_result.get("path", ""))
                    self._active_project_folder = self._last_folder
                    text = step_result.get("text") or step_result.get("message") or f"Opened '{step_result.get('name', 'project')}' in VS Code."
                elif step_action in ("run_in_code_editor", "vscode_run"):
                    p_name = step_result.get("name") or "program"
                    out = step_result.get("output", "")
                    if out:
                        text = f"Executed '{p_name}' in VS Code. Output: {out[:120]}"
                    else:
                        text = step_result.get("text") or step_result.get("message") or f"Executed '{p_name}' in VS Code."
                elif step_action == "set_working_dir":
                    self._active_project_folder = str(step_result.get("path", ""))
                    self._last_folder = self._active_project_folder
                    text = f"Set '{self._active_project_folder}' as your active project workspace."
                elif step_action in ("social_send_message", "whatsapp_send_message"):
                    text = step_result.get("message") or "Sent message."
                elif step_action in ("social_open_chat", "whatsapp_open_chat"):
                    text = step_result.get("message") or "Opened chat."
                elif step_action in ("type_text", "type", "type_here"):
                    typed_txt = step_result.get("text", "")
                    text = f"Typed '{typed_txt}' on here." if typed_txt else "Typed on here."
                elif step_action == "set_volume":
                    text = f"Set system volume to {step_result.get('volume_percent', 50)}%."
                elif step_action == "mute_volume":
                    text = "Muted system audio." if step_result.get("muted") else "Unmuted system audio."
                elif step_action == "volume_up":
                    text = "Increased system volume."
                elif step_action == "volume_down":
                    text = "Decreased system volume."
                elif step_action == "set_brightness":
                    text = f"Set screen brightness to {step_result.get('brightness_percent', 50)}%."
                elif step_action in ("brightness_up", "brightness_down"):
                    text = f"Adjusted brightness to {step_result.get('brightness_percent', 50)}%."
                elif step_action == "unlock_pc":
                    text = "Workstation unlocked."
                elif step_action == "open_workspace":
                    apps_opened = ", ".join(step_result.get("apps", step_result.get("launched", []))) or "workspace apps"
                    text = f"Opened your developer workspace: {apps_opened}."
                elif step_action in ("show_desktop", "minimize_all", "go_to_desktop", "minimize_tabs", "minimize_all_tabs"):
                    text = "Minimized all tabs and windows."
                elif step_action in ("minimize_window", "maximize_window", "snap_window", "focus_window"):
                    act_name = step_result.get('action', 'updated')
                    tgt = step_result.get('title') or step_result.get('target', 'application')
                    text = f"Window {act_name} for {tgt}."
                elif step_action == "open_url":
                    target_url = step_result.get("url", "")
                    text = f"Opened {target_url}." if target_url else "Opened link."
                elif step_action == "launch":
                    if step_result.get("url"):
                        text = f"Opened {step_result['url']}."
                    else:
                        launched_app = step_result.get("app", step_result.get("name", "application"))
                        text = f"Opened {launched_app}."
                elif step_action in ("get_battery", "battery_status"):
                    text = step_result.get("text", f"Battery is at {step_result.get('percent', 0)}%.")
                elif step_action in ("system_power", "power_action"):
                    text = step_result.get("message", step_result.get("text", "Power command executed."))
                elif step_action == "media_play_pause":
                    text = "Toggled media playback."
                elif step_action == "media_next":
                    text = "Skipped to next track."
                elif step_action == "media_prev":
                    text = "Returned to previous track."
                elif step_action == "media_stop":
                    text = "Stopped media playback."
                elif step_action in ("youtube_play", "play_song"):
                    song_name = step_result.get("song") or "music"
                    text = step_result.get("message") or f"Playing '{song_name}' on YouTube."
                elif step_action == "empty_recycle_bin":
                    text = "Recycle Bin emptied."
                elif step_action == "open_folder":
                    text = step_result.get("text", "Opened folder.")
                elif step_action == "get_clipboard":
                    clip_text = step_result.get("text", "")
                    text = f"Clipboard text: {clip_text}" if clip_text else "Clipboard is currently empty."
                elif step_action == "set_clipboard":
                    text = "Copied to clipboard."
                elif step_action in ("open_cmd_and_run", "run_cmd", "cmd_run"):
                    text = step_result.get("text", "Opened Command Prompt and executed command.")
                elif step_action == "system_scan":
                    text = "Opened Command Prompt and started system integrity scan."
        elif action.requires_confirmation:
            text += " That requires your confirmation — say 'yes' or 'approve' to proceed."
            if self._pending_confirmation and time.time() - self._pending_confirmation.get("at", 0) > 300:
                self._pending_confirmation = None

        # Check if this interaction was a user confirmation/approval of a pending action
        is_confirmed = action.payload.get("confirmed") or (data.get("intent") == "confirm")
        if is_confirmed:
            clean_t = text.strip()
            if not clean_t.startswith("👍") and not clean_t.lower().startswith("ok"):
                text = f"👍 Ok. {clean_t}" if clean_t else "👍 Ok."
            elif clean_t.lower().startswith("ok"):
                text = f"👍 {clean_t}"
            elif not clean_t:
                text = "👍 Ok."

        thought = Thought(text=data["text"], intent=data.get("intent", "unknown"))
        self.thought_log.append(thought)
        if len(self.thought_log) > 100:
            self.thought_log.pop(0)

        result = {"text": text, "action": action.type, "intent": data.get("intent", "unknown")}
        if action.type != "respond" and "payload" in action.payload:
            result["execution"] = action.payload
        return result

    def _detect_emotion_word(self, text: str) -> str:
        """Extract the specific emotion keyword from user's text."""
        import re as _re
        # Normalize typo-corrected contractions: "i ' m" -> "i'm", "i ' m" -> "i'm"
        normalized = _re.sub(r"i\s*'\s*m", "i'm", text)
        normalized = _re.sub(r"\s+", " ", normalized).strip()
        emotion_checks = [
            ("anger", r"\b(angry|mad|furious|irritated|annoyed|frustrated|upset|pissed|enraged)\b"),
            ("fear", r"\b(scared|afraid|terrified|anxious|nervous|worried|panicked|frightened)\b"),
            ("joy", r"\b(happy|joyful|cheerful|delighted|excited|grateful|thankful|proud|content|peaceful|calm)\b"),
            ("stress", r"\b(stressed|overwhelmed|burned out|burnout)\b"),
            ("shame", r"\b(ashamed|embarrassed|guilty)\b"),
            ("surprise", r"\b(surprised|shocked|amazed)\b"),
            ("disgust", r"\b(disgusted|revolted|repulsed)\b"),
            ("confused", r"\b(confused|puzzled|baffled|perplexed)\b"),
            ("unwell", r"\bnot\s+(?:feeling\s+)?(?:well|good|great|okay|ok|fine|alright)\b"),
            ("sadness", r"\b(sad|depressed|down|low|blue|heartbroken|miserable|gloomy|melancholy|unhappy|lonely|bored|tired|exhausted|overwhelmed|hurt|disappointed|lost)\b"),
        ]
        for emotion, pattern in emotion_checks:
            if _re.search(pattern, normalized):
                return emotion
        return "sadness"  # safe default

    def _empathetic_response(self, emotion: str, text: str) -> str:
        """Generate a warm, empathetic response based on the detected emotion."""
        import random
        responses = {
            "sadness": [
                "Yeah... I hear you. You don't have to explain everything right now. I'm here.",
                "I'm right here with you. Take all the time you need.",
                "Yeah, that's heavy. We don't have to talk about it if you don't want to, but I'm here.",
            ],
            "anger": [
                "Yeah, that's frustrating. Let's not make it worse. Show me what it's doing and we'll find the problem.",
                "Fair enough. Let's skip the talk and just fix whatever is broken.",
            ],
            "fear": [
                "Take a breath. You're safe right now, and I'm right here. What's worrying you the most?",
                "You're not alone in this. Whatever it is, we'll take it one step at a time.",
            ],
            "joy": [
                "LET'S GOOOO 😂🔥 Finally! What was causing the problem?",
                "YOOOO 😂🔥 Love to see that! What fixed it?",
            ],
            "excited": [
                "WAIT 😂🔥 IT'S ACTUALLY WORKING! Okay, now THIS is the part where things get interesting.",
                "Okay WAIT 😂🔥 Tell me.",
            ],
            "stress": [
                "Okay. Don't panic. We don't need to finish everything right now. One thing at a time — let's solve the first part.",
                "You're carrying a lot right now. Let's break this into smaller pieces. What's the immediate next step?",
            ],
            "confused": [
                "Okay 😂 forget the textbook definition. Let's start from zero with a simple example.",
                "No worries at all. Let's break this down step by step.",
            ],
            "shame": [
                "Everyone stumbles sometimes. What matters is that you're aware and growing. I've got your back.",
                "Don't be too hard on yourself. You're doing your best, and that's what counts.",
            ],
            "surprise": [
                "Whoa! What happened? I'm listening!",
                "That sounds unexpected! Tell me more.",
            ],
            "disgust": [
                "That does sound unpleasant. Let me know if there's something I can do to help clear that up.",
            ],
            "unwell": [
                "Yeah... I hear you. Please take it easy and rest today. I'm right here if you need anything.",
                "Your health comes first. Take a breather and rest. I've got the system covered.",
            ],
        }
        emotion_responses = responses.get(emotion, responses["sadness"])
        return random.choice(emotion_responses)

    def _fallback_response(self, text: str) -> str:
        t_low = text.lower().strip() if text else ""
        if any(w == t_low or t_low.startswith(w + " ") for w in ["hello", "hi", "hey", "iris", "good morning", "good evening", "good afternoon"]):
            return "Hey there! I'm right here with you. How can I help make your day a little brighter?"
        if any(w in t_low for w in ["namaste", "kaise ho", "kya haal"]):
            return "नमस्ते! मैं बिल्कुल ठीक हूँ और हमेशा आपके साथ हूँ। बताइए, आज मैं आपकी क्या मदद करूँ?"
        if any(w in t_low for w in ["love", "feel", "alone", "friend", "talk", "hear", "listen", "someone", "somebody", "care", "heart", "sad", "happy", "life"]):
            return "I'm listening closely. Whatever is on your mind, I'm right here with you. Tell me what you're experiencing."
        if any(w in t_low for w in ["who are you", "what are you", "your name"]):
            return "I am IRIS, your personal AI companion and intelligent assistant. I'm right here beside you, ready online or offline."
        if any(w in t_low for w in ["how do you think", "how do you work", "architecture"]):
            return "My core operates as a multi-stage cognitive architecture: perceiving through vision and sound, remembering permanently, and assisting you seamlessly."
        if any(w in t_low for w in ["consciousness", "mind", "universe", "time", "physics", "meaning", "reality"]):
            return f"Reflecting on {text.strip()}: Reality and intelligence are deeply interconnected. True understanding requires breaking problems down to fundamental axioms and observing how emergent complexity arises."
        if self._model_router and hasattr(self._model_router, "_default_fallback"):
            return self._model_router._default_fallback(text)
        return "I'm right here beside you and listening. How can I help you today?"

    # ─── Public API ───────────────────────────────────────────

    def think(self, text: str, context: Optional[dict] = None) -> dict:
        if not self.is_awake:
            return {"text": "I am in standby. Please wake me first.", "action": "standby", "intent": "unknown"}
        text = text.strip() if text else ""
        if not text:
            return {"text": "Wait, I didn't catch that—what was that?", "action": "clarify", "intent": "clarify"}
        with self._lock:
            self.processing = True
            try:
                data = {"text": text}
                if context:
                    if isinstance(context, dict):
                        data.update(context)
                    elif isinstance(context, str):
                        data["context_history"] = context
                data = self.pipeline.execute("receive", data)
                data = self.pipeline.execute("analyze", data)
                data = self.pipeline.execute("contextualize", data)
                data = self.pipeline.execute("reason", data)
                action = self.pipeline.execute("decide", data)
                data = self.pipeline.execute("act", action)
                result = self.pipeline.execute("respond", data)
                return result
            except Exception as e:
                logger.error(f"Think failed: {e}", exc_info=True)
                if self.on_error:
                    self.on_error(str(e))
                return {"text": "Sorry, lost you for a second there! Could you say that again?", "action": "clarify", "intent": "clarify"}
            finally:
                self.processing = False

    def think_async(self, text: str, callback: Optional[Callable] = None):
        def _run():
            result = self.think(text)
            if callback:
                callback(result)
        self._thinking_thread = threading.Thread(target=_run, daemon=True)
        self._thinking_thread.start()

    def wake(self):
        self.is_awake = True
        logger.info(f"{self.name} is awake.")

    def sleep(self):
        self.is_awake = False
        logger.info(f"{self.name} is in standby.")

    def set_mode(self, mode: str):
        if mode in self.MODES:
            self._mode = mode
            logger.info(f"Mode set to {mode}")

    def get_mode(self) -> str:
        return self._mode

    def status(self) -> dict:
        return {
            "name": self.name,
            "awake": self.is_awake,
            "processing": self.processing,
            "mode": self._mode,
            "thoughts_logged": len(self.thought_log),
            "intent_available": self._intent is not None,
            "decider_available": self._decider is not None,
            "personality_available": self._personality is not None,
            "model_router_available": self._model_router is not None,
            "memory_available": self._memory is not None,
            "voice_available": self._voice is not None,
            "vision_available": self._vision is not None,
            "hands_available": self._hands is not None,
        }

    # ─── Subsystem injection ──────────────────────────────────

    def set_intent(self, intent): self._intent = intent
    def set_decider(self, decider): self._decider = decider
    def set_personality(self, personality): self._personality = personality
    def set_model_router(self, router): self._model_router = router
    def set_memory(self, memory): self._memory = memory
    def set_voice(self, voice): self._voice = voice
    def set_vision(self, vision): self._vision = vision
    def set_hands(self, hands): self._hands = hands
    def set_presence(self, presence): self._presence = presence
    def set_typo_corrector(self, tc): self._typo_corrector = tc
    def set_todo_manager(self, tm): self.todo_manager = tm
