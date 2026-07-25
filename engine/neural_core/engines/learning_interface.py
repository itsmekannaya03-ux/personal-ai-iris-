"""Learning Interface — connects Neural Core to the learning system."""


class LearningInterface:
    def __init__(self, memory_manager=None):
        self._memory = memory_manager
        self._preferences = {}
        self._frequent_commands = {}
        self._common_mistakes = []

    def note_preference(self, topic: str, preference: str):
        if topic not in self._preferences:
            self._preferences[topic] = []
        self._preferences[topic].append(preference)
        if len(self._preferences[topic]) > 10:
            self._preferences[topic] = self._preferences[topic][-10:]

    def get_preference(self, topic: str) -> str | None:
        prefs = self._preferences.get(topic, [])
        if prefs:
            return prefs[-1]
        return None

    def note_command(self, command: str):
        self._frequent_commands[command] = self._frequent_commands.get(command, 0) + 1

    def get_frequent_commands(self, top_n: int = 5) -> list:
        sorted_cmds = sorted(self._frequent_commands.items(), key=lambda x: x[1], reverse=True)
        return [{"command": cmd, "count": count} for cmd, count in sorted_cmds[:top_n]]

    def note_mistake(self, mistake: str):
        self._common_mistakes.append(mistake)
        if len(self._common_mistakes) > 50:
            self._common_mistakes = self._common_mistakes[-50:]

    def get_preferred_response_style(self) -> str:
        if self._preferences.get("verbosity"):
            return self._preferences["verbosity"][-1]
        return "balanced"

    def get_user_topics(self) -> list:
        return list(self._preferences.keys())

    def get_stats(self) -> dict:
        return {
            "preferences": len(self._preferences),
            "frequent_commands": len(self._frequent_commands),
            "common_mistakes": len(self._common_mistakes),
        }

    def get_insights(self) -> str:
        parts = []
        if self._frequent_commands:
            top = self.get_frequent_commands(3)
            parts.append(f"Most used: {', '.join(c['command'] for c in top)}")
        if self._preferences:
            parts.append(f"Known topics: {', '.join(list(self._preferences.keys())[:5])}")
        return ". ".join(parts) or "Still learning about you."
