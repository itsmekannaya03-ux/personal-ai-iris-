"""Prompt Processor — builds the exact prompt sent to the AI model.

Structure:
┌─────────────────────────────┐
│ SYSTEM PROMPT               │
│ PERSONALITY LAYER           │
│ DEEP MEMORY CONTEXT         │
│ LONG-TERM CONTEXT           │
│ SHORT-TERM CONTEXT          │
│ CURRENT REQUEST             │
│ TASK INSTRUCTIONS           │
└─────────────────────────────┘
"""


class PromptProcessor:
    def build(
        self,
        system_prompt: str,
        personality_prompt: str,
        deep_memory: list = None,
        long_term_context: list = None,
        conversation_history: list = None,
        current_message: str = None,
        task_instructions: str = None,
        mode_prompt: str = None,
        pie_context: str = None,
    ) -> list[dict]:
        messages = [{"role": "system", "content": system_prompt}]

        if mode_prompt:
            messages.append({"role": "system", "content": mode_prompt})

        if personality_prompt:
            messages.append({"role": "system", "content": f"Personality: {personality_prompt}"})

        if deep_memory:
            import json
            messages.append({"role": "system", "content": f"Deep memories (user identity): {json.dumps(deep_memory[:5])}"})

        if long_term_context:
            import json
            messages.append({"role": "system", "content": f"Relevant long-term context: {json.dumps(long_term_context[:5])}"})

        if pie_context:
            messages.append({"role": "system", "content": pie_context})

        if task_instructions:
            messages.append({"role": "system", "content": f"Task: {task_instructions}"})

        if conversation_history:
            for msg in conversation_history[-15:]:
                messages.append(msg)

        if current_message:
            messages.append({"role": "user", "content": current_message})

        return messages

    def estimate_tokens(self, messages: list[dict]) -> int:
        return sum(len(m.get("content", "")) // 4 + len(m.get("role", "")) // 4 for m in messages)

    def trim_to_limit(self, messages: list[dict], max_tokens: int = 4096) -> list[dict]:
        while self.estimate_tokens(messages) > max_tokens and len(messages) > 3:
            for i, msg in enumerate(messages):
                if msg["role"] in ("user", "assistant") and i > 1:
                    messages.pop(i)
                    break
        return messages
