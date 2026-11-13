# Research & Literature Survey — Member 5

## Your Job
- Study similar products (ChatGPT, Siri, Alexa, local AI assistants)
- Prepare comparison tables
- Define USP (Unique Selling Proposition)
- Write problem statement and objectives

---

## 1. Comparison Table Template

Create a table comparing IRIS with:

| Feature | ChatGPT | Siri | Alexa | IRIS |
|---------|---------|------|-------|-------|
| Runs locally | ❌ | ❌ | ❌ | ✅ |
| Private data | ❌ | ❌ | ❌ | ✅ |
| Full PC access | ❌ | ❌ | ⚠️ | ✅ |
| Learns over time | ⚠️ | ❌ | ❌ | ✅ |
| Custom name/look | ❌ | ❌ | ❌ | ✅ |
| Terminal access | ❌ | ❌ | ❌ | ✅ |
| Works offline | ❌ | ❌ | ❌ | ✅ |
| One-time payment | ❌ | ❌ | ❌ | ✅ (₹999) |

### Research Sources
Look at:
- ChatGPT (OpenAI) — Architecture, limitations
- Siri (Apple) — On-device processing vs cloud
- Alexa (Amazon) — Privacy concerns
- IRIS Neural Core — Local LLM runtime
- LocalAI — Open-source local AI
- PrivateGPT — Privacy-focused document QA

---

## 2. Problem Statement Template

```
Title: [Your Title Here]

Background:
[2-3 paragraphs about current AI landscape and privacy concerns]

Problem:
Current AI assistants (ChatGPT, Siri, Alexa) send user data to
cloud servers, creating privacy risks, requiring internet access,
and offering no PC control or personalization.

Solution:
IRIS is a privacy-first, local AI assistant that runs 100% on
the user's machine with zero data leaving the PC, featuring
3-tier memory, PC control, voice interaction, and a web dashboard.

Objectives:
1. Develop a fully local AI assistant with zero data exfiltration
2. Implement 3-tier memory system that learns user preferences
3. Enable full PC control through natural language
4. Provide multiple interaction modes (Web UI, CLI, Voice)
5. Create one-command installer for Windows/macOS/Linux
```

---

## 3. Literature Survey Structure

1. **Introduction** — Rise of AI assistants, privacy concerns
2. **Cloud-Based Assistants** — ChatGPT, Siri, Alexa, Google Assistant
3. **Local AI Alternatives** — IRIS Neural Core, LocalAI, PrivateGPT, GPT4All
4. **Memory Systems** — RAG, vector databases, personalization
5. **PC Automation** — PyAutoGUI, OS automation tools
6. **Voice Processing** — Whisper, STT/TTS systems
7. **Gap Analysis** — What existing solutions lack
8. **IRIS Approach** — How we fill the gaps

---

## 4. Deliverables

| File | Content | Due |
|------|---------|-----|
| `comparison-table.md` | Feature comparison with 5+ products | Week 2 |
| `problem-statement.md` | Problem + solution + objectives | Week 2 |
| `literature-survey.md` | Full survey of existing work | Week 4 |
| `usp.md` | Unique selling proposition doc | Week 3 |
