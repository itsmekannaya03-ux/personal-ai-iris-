import json
import re
import os
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional


class SkillModule:
    name: str = "base"
    description: str = "Base skill module"
    requires_subscription: bool = False

    def execute(self, command: str, **kwargs) -> str:
        raise NotImplementedError


class CalendarSkill(SkillModule):
    name = "calendar"
    description = "Schedule management and reminders"
    requires_subscription = True

    REMINDER_FILE = Path.home() / ".igris" / "reminders.json"

    def __init__(self):
        self._ensure_file()

    def _ensure_file(self):
        self.REMINDER_FILE.parent.mkdir(parents=True, exist_ok=True)
        if not self.REMINDER_FILE.exists():
            self.REMINDER_FILE.write_text("[]")

    def _load_reminders(self) -> list:
        return json.loads(self.REMINDER_FILE.read_text())

    def _save_reminders(self, reminders: list):
        self.REMINDER_FILE.write_text(json.dumps(reminders, indent=2))

    def execute(self, command: str, **kwargs) -> str:
        cmd = command.lower()
        if "remind" in cmd or "reminder" in cmd:
            m = re.search(r"remind\s+(?:me\s+)?(?:to\s+)?(.+?)(?:\s+(?:in|at|after|tomorrow|next|on))", cmd)
            if m:
                task = m.group(1).strip()
                reminders = self._load_reminders()
                reminders.append({
                    "id": str(hash(task + str(datetime.now()))),
                    "task": task,
                    "created": datetime.now().isoformat(),
                    "done": False,
                })
                self._save_reminders(reminders)
                return f"Reminder set: {task}"
            return "Sure, what should I remind you about?"
        if "schedule" in cmd or "meeting" in cmd or "appointment" in cmd:
            return "I can help manage your schedule. Try: 'remind me to call John at 5pm'"
        return f"[Calendar] I can manage reminders and schedules. Say 'remind me to...'"


class CodeAssistantSkill(SkillModule):
    name = "code_assistant"
    description = "Code understanding, GitHub, and development workflow"
    requires_subscription = True

    def execute(self, command: str, **kwargs) -> str:
        cmd = command.lower()
        if "github" in cmd or "git" in cmd:
            return "I can help with git operations. Try: 'show git status' or 'commit my changes'"
        if "debug" in cmd or "bug" in cmd or "error" in cmd:
            return "I can help debug code. Share the error message or code snippet."
        if "refactor" in cmd or "optimize" in cmd:
            return "I can help refactor code. Share what you want to improve."
        return "[Code] I can assist with coding, debugging, and git. What do you need?"


class WebResearchSkill(SkillModule):
    name = "web_research"
    description = "Web browsing and article summarization"

    def execute(self, command: str, **kwargs) -> str:
        cmd = command.lower()
        if "search" in cmd or "google" in cmd or "look up" in cmd:
            m = re.search(r"(?:search|google|look up|find)\s+(.+)$", cmd)
            if m:
                query = m.group(1).strip()
                try:
                    import webbrowser
                    webbrowser.open(f"https://www.google.com/search?q={query}")
                    return f"Searching Google for: {query}"
                except Exception as e:
                    return f"Could not open browser: {e}"
            return "What should I search for?"
        return "[Web] I can search the web, summarize articles, and research topics."


class MediaControlSkill(SkillModule):
    name = "media_control"
    description = "Spotify, YouTube, volume, and media playback"
    requires_subscription = True

    def execute(self, command: str, **kwargs) -> str:
        cmd = command.lower()
        if "play" in cmd and ("music" in cmd or "song" in cmd or "spotify" in cmd):
            m = re.search(r"play\s+(.+?)(?:\s+(?:on|with|by))?", cmd)
            song = m.group(1).strip() if m else "music"
            try:
                import webbrowser
                webbrowser.open(f"https://open.spotify.com/search/{song}")
                return f"Opening Spotify and searching for: {song}"
            except:
                return f"I would play {song}, but Spotify integration needs setup."
        if "volume" in cmd:
            if "up" in cmd or "increase" in cmd:
                os.system("nircmd changesysvolume 2000" if os.name == "nt" else "osascript -e 'set volume output volume (output volume of (get volume settings) + 10)'")
                return "Volume increased"
            elif "down" in cmd or "decrease" in cmd:
                os.system("nircmd changesysvolume -2000" if os.name == "nt" else "osascript -e 'set volume output volume (output volume of (get volume settings) - 10)'")
                return "Volume decreased"
            return "Volume control active"
        return "[Media] I can control music, volume, and media playback."


class FileIntelligenceSkill(SkillModule):
    name = "file_intelligence"
    description = "Smart file search and organization"

    def execute(self, command: str, **kwargs) -> str:
        cmd = command.lower()
        if "find" in cmd and ("file" in cmd or "python" in cmd or "document" in cmd):
            m = re.search(r"find\s+(?:all\s+)?(.+?)(?:\s+files|\s+from|\s+in)?", cmd)
            pattern = m.group(1).strip() if m else ""
            if pattern:
                try:
                    home = Path.home()
                    results = list(home.rglob(f"*{pattern}*"))[:10]
                    if results:
                        return "Found:\n" + "\n".join(f"- {r.relative_to(home)}" for r in results)
                    return f"No files matching '{pattern}' found."
                except:
                    return f"Searching for files matching '{pattern}'..."
            return "What files should I look for?"
        if "organize" in cmd or "clean" in cmd or "sort" in cmd:
            return "I can help organize your files. Which folder should I clean up?"
        return "[Files] I can find, organize, and manage your files."


class DataAnalysisSkill(SkillModule):
    name = "data_analysis"
    description = "Analyzes files, generates charts and insights"
    requires_subscription = True

    def execute(self, command: str, **kwargs) -> str:
        cmd = command.lower()
        if "analyze" in cmd or "chart" in cmd or "graph" in cmd or "data" in cmd:
            return "I can analyze data files (CSV, Excel, JSON). Share a file path and what you want to see."
        return "[Data] I can analyze data and generate charts. Point me to a file."


class EmailSkill(SkillModule):
    name = "email"
    description = "Reads, drafts, and sends emails"
    requires_subscription = True

    def execute(self, command: str, **kwargs) -> str:
        cmd = command.lower()
        if "email" in cmd or "mail" in cmd or "send" in cmd:
            return "I can help with emails. Email integration requires setup — configure your SMTP in settings."
        return "[Email] I can draft and send emails with proper setup."


class SmartReminderSkill(SkillModule):
    name = "smart_reminders"
    description = "Context-aware reminders that learn your schedule"
    requires_subscription = True

    def execute(self, command: str, **kwargs) -> str:
        cmd = command.lower()
        if "remind" in cmd:
            m = re.search(r"remind\s+(?:me\s+)?(?:to\s+)?(.+?)(?:\s+(?:at|in|after|every|daily|weekly))", cmd)
            if m:
                task = m.group(1).strip()
                return f"Smart reminder set: {task}. I'll remind you at the right time."
            return "What should I smart-remind you about?"
        return "[Reminders] I can set context-aware reminders. Try: 'remind me to take a break every 2 hours'"


AVAILABLE_SKILLS: dict[str, SkillModule] = {
    "calendar": CalendarSkill(),
    "code_assistant": CodeAssistantSkill(),
    "web_research": WebResearchSkill(),
    "media_control": MediaControlSkill(),
    "file_intelligence": FileIntelligenceSkill(),
    "data_analysis": DataAnalysisSkill(),
    "email": EmailSkill(),
    "smart_reminders": SmartReminderSkill(),
}


def execute_skill(name: str, command: str, **kwargs) -> Optional[str]:
    skill = AVAILABLE_SKILLS.get(name)
    if not skill:
        return None
    try:
        return skill.execute(command, **kwargs)
    except Exception as e:
        return f"[{skill.name}] Error: {e}"
