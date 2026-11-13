import re
import logging

logger = logging.getLogger("iris.core.intent")


class IntentDetector:
    PATTERNS = {
        "greeting": r"^(?:hello|hi|hey|good morning|good evening|good afternoon|yo|sup|what's up|namaste|namaskar|kaisa hai|kaise ho|नमस्ते|नमस्कार|प्रणाम)(?:\s+(?:iris|iris|there|आइरिस|इग्रिस))?(?:\s+(?:how are you|kaise ho|kaisa hai|कैसे हो))?[,\.!\s]*$",
        "farewell": r"^(?:bye|goodbye|see you|talk later|good night|night|see ya)(?:\s+(?:iris|iris))?[,\.!\s]*$",
        "time": r"\b(what(?:'?s|\s+is)\s+(?:the\s+)?(?:current\s+)?time|what\s+time\s+is\s+it|current\s+time|tell\s+(?:me\s+)?(?:the\s+)?time|today'?s\s+date|current\s+date|what(?:'?s|\s+is)\s+(?:today'?s\s+|the\s+)?date|what\s+day\s+is\s+(?:it|today))\b|^time$|^clock$",
        "query": r"\b(who|what|when|where|why|how|tell me|explain|define|meaning of|what is|what are|can you explain)\b",
        "launch": r"\b(?:open|launch|start|run|opn|oepn|opne|lonch|lanch)\s+(?:the\s+|app\s+|application\s+)?(chrome|browser|google\s+chrome|brave|edge|notepad|calculator|calc|terminal|wt|cmd|powershell|vscod|vscode|code\s+editor|spotify|word|winword|excel|powerpoint|powerpnt|ppt|steam|discord|vlc|telegram|zoom|photoshop|blender|obs|paint|mspaint|explorer|settings|taskmgr|camera|clock|photos|store|whatsapp)\b|\b(?:open|launch|start|opn)\s+(?:the\s+|app\s+|application\s+)?[\w\-\.\:\/ ]+\b",
        "close_app": r"\b(close|exit|quit|kill)\s+(?:the\s+)?(?:app\s+|application\s+|window\s+)?\w+",
        "remember": r"\b(remember|save|store|note down|keep in mind)\b",
        "recall": r"\b(what.*remember|recall|what.*say|what.*tell|remind me)\b",
        "search": r"\b(?:search|google|look up|browse\s+for)\s+(?:for\s+|about\s+)?[\w\s\-\.\'\"]+",
        "create_game": r"\b(?:create|make|build|generate|code|program)\s+(?:a\s+|an\s+)?(?:offline\s+)?(?:game|games)\s*(?:to\s+play)?\b|\b(?:create|make|build|code|play)\s+(?:a\s+|an\s+)?(?:offline\s+)?([\w\s]+?)\s+game\s*(?:to\s+play)?\b|\b(?:create|make)\s+(?:a\s+|an\s+)?game\b",
        "create_website": r"\b(?:create|make|build|generate|design|code)\s+(?:a\s+|an\s+|the\s+)?(?:modern\s+|responsive\s+|beautiful\s+|landing\s+page\s+|portfolio\s+)?(?:website|web\s+site|webpage|web\s+page|landing\s+page)\b",
        "create": r"\b(?:create|make|build)\s+(?:a\s+|the\s+|new\s+)?(?:file|folder|directory|project|script|python\s+file|text\s+file|doc|document)\b|\b(?:write|create|make)\s+(?:some\s+|a\s+)?(?:code|script|program)\s+(?:to|for|in)\b",
        "system": r"\b(shutdown|restart|sleep|lock|unlock|log off|hibernate)\b",
        "delete": r"\b(?:delete|remove|erase|trash|get rid of)\s+(?:the\s+|this\s+)?(?:file|folder|directory|item|list|task|todo)\b",
        "help": r"\b(help|what can you do|commands|capabilities)\b",
        "mode_switch": r"\b(mode|switch to|change mode)\b",
        "status_check": r"\b(status|how are you|what's your status|systems? check)\b",
        "confirm": r"^(?:yes|yeah|yep|sure|confirm|confirmed|approve|approved|approve\s+it|i\s+approve|do\s+it|ok|okay|proceed|go\s+ahead|thumbs\s+up|👍)(?:[,\.!\s]+(?:please|iris|now|do\s+it|proceed))?[,\.!\s]*$|^(?:yes\s+|ok\s+|please\s+)?(?:do\s+it|proceed|go\s+ahead|approve\s+it|confirm\s+it)[,\.!\s]*$",
        "deny": r"\b(no|nope|nah|cancel|stop|don't|abort)\b",
        "silence_on": r"\b(tay\s+silence|stay\s+silence|stay\s+silent|be\s+silent|keep\s+silent|silence\s+mode|mute(?:\s+yourself)?|shut\s+up|be\s+quiet|stop\s+talking|don't\s+speak|dont\s+speak|keep\s+quiet|quiet\s+mode|chup\s+raho|shant\s+raho|bolna\s+band\s+karo|awaz\s+band)\b",
        "silence_off": r"\b(you\s+can\s+speak(?:\s+now)?|speak\s+now|start\s+speaking|talk\s+to\s+me|unmute(?:\s+yourself)?|resume\s+voice|stop\s+silence|disable\s+silence|voice\s+on|ab\s+bolo|bolo\s+ab|awaz\s+shuru)\b|^speak$",
        "music": r"\b(pause|resume|skip|next track|next song|previous track|prev song|stop music|music|songs?|playlist|album)\b|\b(?:play)\s+(?:a\s+|any\s+|some\s+|the\s+)?(?:music|songs?|track|playlist|tune|gana)\b",
        "rewind": r"\b(rewind|revind|rewnd|10 seconds back|go back 10 seconds|back 10 seconds)\b",
        "youtube_play": r"\b(?:play\s+(?:any\s+|a\s+|some\s+)?(?:songs?|music|tracks?)(?:\s+(?:in|on)\s+youtube)?|play\s+(?:the\s+)?(?:songs?|tracks?)\s+[\w\s\-\.\'\"]+|play\s+music(?:\s+(?:in|on)\s+youtube)?|play\s+[\w\s\-\.\'\"]+\s+(?:in|on)\s+youtube|play\s+(?:it|this|that|this\s+song|that\s+song|the\s+song)|just\s+play\s+(?:it|this|that)|gana\s+(?:chalao|sunao|bajao)|song\s+(?:chalao|bajao))\b",
        "singing_lyrics": r"\b(?:sing\s+(?:with\s+me|a\s+song|along|for\s+me)|can\s+you\s+sing|sing\s+this|do\s+you\s+know\s+this\s+song|identify\s+(?:this\s+)?(?:song|lyrics)|what\s+song\s+is\s+this|which\s+song\s+is\s+this|guess\s+this\s+song|who\s+sang\s+this|lyrics\s+of)\b",
        "code_editor_folder": r"\bopen\s+(?:any\s+|the\s+|this\s+|my\s+)?([\w\.\-\s]+?)?\s*(?:folder|directory|project)?(?:\s+(?:which\s+is\s+|which\s+was\s+)?(?:created|create|made)?\s*(?:by\s+it|by\s+you|newly)?)?\s*(?:in|inside|using|with)\s+(?:vs\s*code|code\s+editor|code)(?:\s+(?:which\s+is\s+|which\s+was\s+)?(?:created|create|made)?\s*(?:by\s+it|by\s+you|newly)?)?\b|\bopen\s+(?:vs\s*code|code\s+editor|code)\s+(?:with|in)\s+([\w\.\-\s]+?)\s*(?:folder|directory|project)?\b",
        "run_in_code_editor": r"\b(?:run|execute|start)\s+(?:and\s+execute\s+)?(?:the\s+|this\s+|my\s+)?(?:[\w\-]+\s+)?(?:program|code|script|file|project)?\s*(?:in|inside|using|with)\s+(?:vs\s*code|code\s+editor|code|visual\s+studio\s+code)\b|\b(?:in|inside)\s+(?:vs\s*code|code\s+editor|code|visual\s+studio\s+code)\s*(?:run|execute)\s+(?:the\s+|this\s+|my\s+)?(?:[\w\-]+\s+)?(?:program|code|script|file|project)?\b|\b(?:run|execute)\s+([\w\.\-\s]+?\.(?:py|js|ts|html|cpp|c|java))\s+(?:in|inside|using|with)\s+(?:vs\s*code|code\s+editor|code)\b|\b(?:run|execute)\s+(?:the\s+|this\s+)?(?:code|program|script)\s+in\s+vs\b|\b(?:abel\s+to\s+|able\s+to\s+)?(?:run|execute)\s+(?:and\s+execute\s+)?(?:the\s+|this\s+|my\s+)?(?:program|code|script)\s+in\s+(?:vs\s*code|vscode|code)\b",
        "use_folder_project": r"\buse\s+(?:the\s+|this\s+|that\s+)?(?:folder|directory|workspace)?\s*(?:to\s+do|for)?\s*(?:project|work|coding|development)\b|\bwork\s+(?:in|inside)\s+(?:the\s+|this\s+)?(?:folder|directory)\b|\bset\s+(?:as\s+)?(?:active\s+)?project\s+(?:folder|directory)\b",
        "social_msg": r"\b(?:send|message|text|tell|broadcast)\s+(?:a\s+)?(?:new\s+)?(?:message\s+(?:to\s+)?)?([+\w\s]+?)\s+(?:on|in|via)\s+(whatsapp|instagram|insta|telegram|discord|twitter|x|wathsapp|intsagram)(?:\s+(?:saying|that|:)?\s*(.*))?$|\bmessage\s+(?:to\s+)?([+\w\s]+?)\s+(?:in|on)\s+(whatsapp|instagram|insta|telegram|discord|twitter|x|wathsapp|intsagram)(?:\s+(?:saying|that|:)?\s*(.*))?$|\b(?:send|message|broadcast)\s+(?:a\s+)?(?:new\s+)?message\s+(?:in|on)\s+(whatsapp|instagram|insta|telegram|discord|twitter|x|wathsapp|intsagram)(?:\s+(?:to\s+)?([+\w\s]+?))?(?:\s+(?:saying|that|:)?\s*(.*))?$|\b(?:send|message|text|tell|broadcast)\s+(?:a\s+)?(?:new\s+)?(?:message\s+)?to\s+(?:the\s+)?([+\w\s]+?)(?:\s+(?:saying|that|:)\s*(.*)|\s+(?:hi|hello|hey|good|how|can|please|where|when|why|what|meet|call|love|ok|yes|no|[A-Za-z0-9]).*)?$|\b(?:send\s+(?:a\s+)?message\s+to\s+|message\s+|tell\s+|broadcast\s+(?:to\s+)?)(everyone|every\s+one|everybody|all\s+contacts|all\s+people|all\s+chats|all\s+friends)\b(?:\s+(?:saying|that|:)?\s*(.*))?$",
        "social_chat": r"\b(?:open|start|show|go to)\s+(?:the\s+|a\s+)?(?:new\s+)?([+\w\s]+?)?\s*(?:chat|chart|conversation|dm|messages?)\s+(?:in|on)\s+(whatsapp|instagram|insta|telegram|discord|wathsapp|intsagram)\b|\b(?:open|start|show|go to)\s+(?:the\s+|a\s+)?(?:new\s+)?(?:chat|chart|conversation|dm|messages?)\s+(?:with|to|of|for)\s+([+\w\s]+?)\s+(?:in|on)\s+(whatsapp|instagram|insta|telegram|discord|wathsapp|intsagram)\b|\b(?:open|start|show|go to)\s+(?:the\s+|a\s+)?(?:new\s+)?(whatsapp|instagram|insta|telegram|discord|wathsapp|intsagram)\s+(?:chat|chart|conversation|dm|inbox|messages?)(?:\s+(?:with|to|of|for)\s+([+\w\s]+))?\b",
        "whatsapp_msg": r"\b(?:send|message|text|tell|broadcast)\s+([+\w\s]+?)\s+(?:on|in|via)\s+whatsapp\s*(?:saying|that|:)?\s*(.*)$|\bmessage\s+(?:to\s+)?([+\w\s]+?)\s+(?:in\s+that\s+(?:chat|chart)|on\s+whatsapp)\s*(?:saying|that|:)?\s*(.*)$|\b(?:send\s+(?:a\s+)?message\s+to\s+|message\s+|tell\s+|broadcast\s+(?:to\s+)?)(everyone|every\s+one|everybody|all\s+contacts)\s+on\s+whatsapp\b(?:\s+(?:saying|that|:)?\s*(.*))?$",
        "whatsapp_chat": r"\b(?:open|start|show|go to)\s+(?:the\s+|a\s+)?(?:new\s+)?(?:chat|chart|conversation|dm)\s*(?:with|to|of|for)\s+([+\w\s]+?)(?:\s+(?:in|on)\s+whatsapp)?\b|\b(?:open|start|show|go to)\s+(?:the\s+|a\s+)?(?:new\s+)?([+\w\s]+?)\s+(?:chat|chart|conversation|dm)(?:\s+(?:in|on)\s+whatsapp)?\b|\b(?:chat|chart)\s+(?:with|to|of)\s+([+\w\s]+?)(?:\s+(?:in|on)\s+whatsapp)?\b|\bopen\s+(?:any\s+|a\s+)?(?:new\s+)?(?:chat|chart)\s+in\s+whatsapp\b|\bopen\s+whatsapp\s+(?:new\s+)?(?:chat|chart)(?:\s+(?:with|to|of|for)\s+([+\w\s]+))?\b|\b(?:open|start|show|go to)\s+(?:the\s+|a\s+)?(?:new\s+)?(?:chat|chart|conversation)\s*(?:with|to|of|for\s+)?([+\w\s]+?)?\s+(?:in|on)\s+whatsapp\b",
        "type_here": r"\btype\s+\[.+?\]|\b(?:type|write)\s+(?:\[.+?\]|[\w\s\.,!?@#\-\+=\(\)\{\}\<\>\/\\:\;\"\']+?)\s+(?:on\s+here|here|on\s+there|there)\b|^(?:please\s+|can\s+you\s+)?type\s+(?:the\s+(?:word|words|text)\s+)?\[?[\w\s\.,!?@#\-\+=\(\)\{\}\<\>\/\\:\;\"\']+?\]?(?:\s+(?:on\s+here|here|on\s+there|there))?$",
        "voice_switch": r"\b(?:speak|talk|switch|change)\s+(?:in|to)?\s*(?:the\s+)?(hindi|english)\s*(?:voice|language)?\b|\bhindi\s+(?:me\s+)?(?:baat\s+karo|bolo)\b|\b(?:use|switch\s+to)\s+hindi\s+voice\s*(?:clone)?\b",
        "todo": r"\b(?:make|create|add|show|view|check|open|list|clear|reset|wipe)\s+(?:a\s+|to\s+my\s+|my\s+|the\s+)?(?:to-do|todo|to\s+do|task)?\s*(?:list|tasks?)(?:\s+newly)?\b|\bnew\s+list\b|\bremind\s+(?:me\s+)?(?:to\s+|at\s+|in\s+)\b",
        "message": r"\b(send|message|text|email|whatsapp|telegram)\b",
        "file_op": r"\b(?:move|copy|rename|transfer|cut)\s+(?:the\s+|this\s+|my\s+)?(?:file|folder|directory|item|document|data)\b|\b(?:change\s+(?:the\s+)?name\s+of\s+)(?:the\s+|this\s+)?(?:file|folder)\b|\b(?:show|list|search|find)\s+(?:all\s+)?(?:my\s+)?(?:files|folders|directories)\b|\b(?:dir|ls)\b",
        "screenshot": r"\b(screenshot|screen capture|capture screen|print screen)\b",
        "web_nav": r"\b(go to|navigate|open website|visit|open link|open the link|link|open site|open the site|browse to)\b|https?://|www\.|\b[\w\-]+\.(com|org|net|io|in|co|gov|edu|ai|app|dev)\b|\b(youtube|yotube|google|github|reddit|stackoverflow|chatgpt|claude|netflix|whatsapp\s+web|instagram|facebook|twitter|amazon|gmail|discord|twitch|linkedin)\b",
        "auth": r"\b(log in|login|sign in|signin|log out|logout|sign out|signout)\b",
        "volume": r"\b(volume|mute|unmute|louder|quieter|sound level)\b",
        "brightness": r"\b(brightness|dim|brighten|screen light|display brightness)\b",
        "workspace": r"\b(work\s*space|work\s*setup|workday|developer setup|coding environment|my work)\b",
        "recycle_bin": r"\b(empty recycle bin|clean trash|clear trash|clean recycle bin|empty trash)\b",
        "clipboard": r"\b(clipboard|copy to clipboard|read clipboard|paste clipboard)\b",
        "folder": r"\b(?:open|show|explore|browse|view)\s+(?:the\s+|my\s+)?(?:[\w\.\-\s]+?\s+)?(?:folder|directory)\b|\bopen\s+(?:the\s+|my\s+)?(?:desktop|downloads|documents|pictures|photos|videos|music)\s*(?:folder|directory)?\b|\b(?:open|show)\s+folder\b|\bopen\s+[\w\.\-]+\s+(?:in|inside)\s+[\w\.\-\s]+?(?:folder|dir|directory|desktop|documents|downloads)\b",
        "space": r"\b(leave me alone|don't talk to me|dont talk to me|don't talk|dont talk|i need some space|i need space|give me space|stop talking|be quiet|stay quiet|not now|shut up|want to be alone|wanna be alone)\b|^stop$",
        "window": r"\b(?:go\s+to\s+desktop|show\s+(?:the\s+)?desktop)\b|\bminimize\b(?:\s+(?:all\s+)?(?:the\s+)?(?:windows?|tabs?|taps?|apps?|things?|everything|screen))?|\b(maximize|snap|restore)\b(?:\s+(?:the\s+)?(?:window|\w+))?",
        "battery": r"\b(battery|power level|charge|charging status)\b",
        "emotion": r"\b(?:(?:yes|yeah)\s+)?(?:i(?:'m|m|\s+am|\s+feel|\s+feeling)|feeling|felt|am)\s+(?:so\s+|very\s+|really\s+|just\s+)?(?:sad|happy|angry|mad|upset|frustrated|depressed|anxious|nervous|scared|worried|lonely|bored|tired|exhausted|stressed|excited|grateful|thankful|confused|lost|overwhelmed|hurt|disappointed|jealous|disgusted|surprised|hopeful|proud|ashamed|embarrassed|guilty|annoyed|irritated|furious|heartbroken|miserable|joyful|cheerful|delighted|gloomy|melancholy|content|peaceful|calm|afraid|terrified|panicked|down|low|blue)\b|\b(?:i(?:'m|m|\s+am)\s+not\s+(?:feeling\s+)?(?:well|good|great|okay|ok|fine|alright))\b|\b(?:so\s+|really\s+)?(?:heartbroken|depressed|miserable|crying|bursting into tears|in tears|so sad|feeling sad|very sad)\b",
        "companion": r"\b(?:stay\s+(?:with|beside|by|near)|beside\s+(?:of\s+)?me|be\s+with\s+me|stay\s+here|don't\s+leave|dont\s+leave|hold\s+(?:my\s+)?hand|talk\s+to\s+me|listen\s+to\s+me|be\s+my\s+friend|hug\s+me|comfort\s+me|sit\s+with\s+me|keep\s+me\s+company|with\s+me\s+for\s+a\s+moment|are\s+you\s+with\s+me|i\s+want\s+(?:someone|some\s+one|somebody|anybody)\s+to\s+love(?:\s+me)?|i\s+want\s+(?:someone|some\s+one)\s+love\s+me|want\s+someone\s+to\s+love|want\s+(?:someone|some\s+one)\s+love\s+me|i\s+want\s+to\s+be\s+loved|i\s+need\s+love|i\s+want\s+love|do\s+you\s+love\s+me|nobody\s+loves\s+me|no\s*one\s+loves\s+me|i\s+feel\s+unloved|i\s+feel\s+so\s+alone|wish\s+someone\s+loved\s+me|i\s+need\s+someone)\b",
        "face_scan": r"\b(scan\s+(?:my\s+)?face|enroll\s+(?:my\s+)?face|take\s+(?:my\s+)?face\s+parameters?|remember\s+(?:my\s+)?face|register\s+(?:my\s+)?face|update\s+(?:my\s+)?face|save\s+(?:my\s+)?face\s+parameters?|biometric\s+scan|reset\s+(?:my\s+)?face|remove\s+(?:the\s+)?(?:pevis|previous)\s+(?:one|face)?|register\s+newly|newly\s+register|re-?enroll\s+(?:my\s+)?face|reset\s+biometrics|re-?register|register\s+again)\b",
        "incomplete_command": r"^(?:please\s+|can\s+you\s+|iris\s+)?(open|launch|start|run|opn|close|quit|exit|search|google|find|play|create|make|delete|remove|show)$",
        "command": r"\b(?:run|execute)\s+(?:any\s+)?(?:command|commend|cmd|code)?\s*(?:in|on)\s*(?:the\s+)?(?:terminal|teminal|tarminel|cmd|powershell|command\s+prompt)\b|\b(?:run|execute)\s+(.+?)\s+(?:in|on)\s+(?:the\s+)?(?:terminal|teminal|tarminel|cmd|powershell|command\s+prompt)\b|\bopen\s+(?:the\s+)?(?:terminal|teminal|tarminel|cmd|powershell|command\s+prompt)\s+(?:and\s+)?(?:run|execute)\s+(.+)\b|\b(run\s+(?:in\s+)?(?:cmd|terminal|powershell|command\s+prompt)|open\s+(?:cmd|terminal|powershell|command\s+prompt)\s+(?:and\s+run|and\s+execute|to\s+run)|execute\s+command|run\s+command|cmd\s+run|terminal\s+run|system\s+scan|scan\s+system|pc\s+scan|sfc\s*/scannow|ipconfig|ping\s+[\w\.\-]+|netstat|traceroute|tracert|systeminfo|wmic|hostname|nslookup|tasklist)\b",
    }

    def __init__(self):
        self._compiled = {name: re.compile(patt, re.IGNORECASE) for name, patt in self.PATTERNS.items()}
        logger.info(f"IntentDetector ready ({len(self._compiled)} patterns)")

    def analyze(self, text: str) -> dict:
        text_lower = text.lower().strip()
        matches = {}
        for name, pattern in self._compiled.items():
            m = pattern.search(text_lower)
            if m:
                matches[name] = m.group()

        intent = self._resolve_intent(matches)
        confidence = self._calculate_confidence(matches)
        return {
            "intent": intent,
            "confidence": confidence,
            "matches": list(matches.keys()),
        }

    def _resolve_intent(self, matches: dict) -> str:
        # Guard: If query is present and launch/create/file_op/music also matched, query takes precedence
        # (e.g. "what is the code", "explain the code", "why did you make that", "tell me about this file")
        if "query" in matches and any(m in matches for m in ("launch", "create", "file_op", "music")):
            return "query"

        priority = [
            "silence_on",
            "voice_switch",
            "silence_off",
            "space",
            "incomplete_command",
            "face_scan",
            "emotion",
            "companion",
            "type_here",
            "social_msg", "social_chat", "whatsapp_msg", "whatsapp_chat",
            "run_in_code_editor", "code_editor_folder", "use_folder_project",
            "command", "workspace", "recycle_bin", "clipboard", "folder", "volume", "brightness", "window", "battery",
            "todo", "singing_lyrics", "youtube_play", "rewind",
            "system", "delete", "mode_switch", "auth", "launch", "web_nav", "file_op", "create_game", "create_website", "create", "close_app",
            "message", "music", "screenshot",
            "remember", "recall", "search", "time", "query",
            "confirm", "deny", "help", "status_check",
            "greeting", "farewell",
        ]
        for p in priority:
            if p in matches:
                return p
        return "conversation"

    def _calculate_confidence(self, matches: dict) -> float:
        if not matches:
            return 0.0
        total = len(matches)
        high_priority = sum(1 for m in matches if m in (
            "command", "launch", "close_app", "system", "delete", "mode_switch",
            "remember", "music", "message", "web_nav", "screenshot"
        ))
        score = min(1.0, 0.3 + (total * 0.2) + (high_priority * 0.15))
        return round(score, 2)
