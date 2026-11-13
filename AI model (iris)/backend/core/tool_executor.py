"""
ToolExecutor — Manages the tool feedback loop.

Flow:
  1. LLM generates response with tool calls
  2. ToolExecutor parses and executes each tool
  3. Results are formatted and fed back to the LLM
  4. LLM generates final response incorporating tool results
  5. Nuclear scrubber cleans artifacts from final output
"""

import json
import re
import logging
import time
from typing import Optional
from .tools import ToolRegistry

logger = logging.getLogger("iris.tool_executor")


class NuclearScrubber:
    """
    Removes code blocks, tool call artifacts, and raw JSON
    from AI responses to produce clean natural language.
    """

    def __init__(self):
        self.patterns = [
            (re.compile(r'```[\s\S]*?```', re.MULTILINE), ''),
            (re.compile(r'`[^`]+`', re.MULTILINE), ''),
            (re.compile(r'\{[^{}]*"tool"[^{}]*\}', re.MULTILINE), ''),
            (re.compile(r'<function_calls>[\s\S]*?</function_calls>', re.MULTILINE), ''),
            (re.compile(r'\n\s*\n\s*\n', re.MULTILINE), '\n\n'),
        ]

    def scrub(self, text: str) -> str:
        """Clean AI response of all tool artifacts."""
        result = text
        for pattern, replacement in self.patterns:
            result = pattern.sub(replacement, result)
        result = result.strip()
        return result


class ToolFeedbackLoop:
    """
    Executes tools and manages the feedback loop with the LLM.
    Supports up to 5 rounds of tool calls per request.
    """

    MAX_ROUNDS = 5

    def __init__(self, registry: ToolRegistry):
        self.registry = registry
        self.scrubber = NuclearScrubber()
        self._round_count = 0

    def execute_tool_calls(self, tool_calls: list[dict]) -> list[dict]:
        """
        Execute a batch of tool calls and return results.
        Each tool_call: {"name": "tool_name", "arguments": {...}}
        """
        results = []
        for call in tool_calls:
            name = call.get("name", call.get("function", {}).get("name", ""))
            args_raw = call.get("arguments", call.get("function", {}).get("arguments", "{}"))

            if isinstance(args_raw, str):
                try:
                    args = json.loads(args_raw)
                except json.JSONDecodeError:
                    args = {}
            else:
                args = args_raw or {}

            start = time.time()
            result = self.registry.call(name, args)
            elapsed = time.time() - start

            results.append({
                "tool": name,
                "result": result,
                "duration": round(elapsed, 3),
            })
            logger.info(f"Tool '{name}' executed in {elapsed:.2f}s")

        self._round_count += 1
        return results

    def format_results_for_llm(self, results: list[dict]) -> str:
        """Format tool execution results for LLM context."""
        parts = []
        for r in results:
            result_str = json.dumps(r["result"], indent=2)
            parts.append(
                f"<tool_result name=\"{r['tool']}\" duration=\"{r['duration']}s\">\n"
                f"{result_str}\n"
                f"</tool_result>"
            )
        return "\n\n".join(parts)

    def can_continue(self) -> bool:
        """Check if another round of tool calls is allowed."""
        return self._round_count < self.MAX_ROUNDS

    def reset(self):
        self._round_count = 0

    def parse_tool_calls_from_llm(self, llm_output: str) -> list[dict]:
        """
        Parse tool calls from LLM response.
        Supports both JSON mode and function-calling API format.
        """
        tool_calls = []

        # Try parsing as JSON array of tool calls
        try:
            data = json.loads(llm_output)
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and "name" in item:
                        tool_calls.append(item)
            elif isinstance(data, dict) and "tool_calls" in data:
                tool_calls = data["tool_calls"]
            elif isinstance(data, dict) and "name" in data:
                tool_calls.append(data)
        except (json.JSONDecodeError, TypeError):
            pass

        # Try extracting <tool_call> tags
        if not tool_calls:
            pattern = re.compile(r'<tool_call>\s*(\{.*?\})\s*</tool_call>', re.DOTALL)
            matches = pattern.findall(llm_output)
            for m in matches:
                try:
                    tc = json.loads(m)
                    tool_calls.append(tc)
                except json.JSONDecodeError:
                    pass

        # Try extracting function calls from OpenAI-style responses
        if not tool_calls:
            pattern = re.compile(r'"function"\s*:\s*\{[^}]+\}', re.DOTALL)
            matches = pattern.findall(llm_output)
            for m in matches:
                try:
                    tc = json.loads("{" + m + "}")
                    if "function" in tc:
                        tool_calls.append(tc["function"])
                except json.JSONDecodeError:
                    pass

        return tool_calls

    def get_status(self) -> dict:
        return {
            "rounds_used": self._round_count,
            "max_rounds": self.MAX_ROUNDS,
        }
