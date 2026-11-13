"""
Generate high-resolution technical diagrams for the Iris AI Project Report.
Uses Matplotlib to render clean, publication-grade flowcharts and architecture diagrams.
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Output directory for diagram images
DIAGRAMS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "report_assets")
os.makedirs(DIAGRAMS_DIR, exist_ok=True)

# Common styling palette
PRIMARY_COLOR = "#1E3A8A"      # Deep Royal Blue
SECONDARY_COLOR = "#0D9488"    # Teal Accent
ACCENT_COLOR = "#6366F1"       # Indigo
LIGHT_BG = "#F8FAFC"           # Off-white / light slate
CARD_BG = "#FFFFFF"            # Pure White
TEXT_DARK = "#0F172A"          # Slate 900
TEXT_MUTED = "#475569"         # Slate 600
BORDER_COLOR = "#CBD5E1"       # Slate 300
HIGHLIGHT_GREEN = "#10B981"    # Emerald
HIGHLIGHT_AMBER = "#F59E0B"    # Amber
HIGHLIGHT_RED = "#EF4444"      # Red/Rose
HIGHLIGHT_PURPLE = "#8B5CF6"   # Purple


def draw_box(ax, x, y, width, height, title, subtitle="", bg_color=CARD_BG, border_color=BORDER_COLOR, title_color=TEXT_DARK, sub_color=TEXT_MUTED, fontsize=9, corner_radius=0.04):
    box = patches.FancyBboxPatch(
        (x, y), width, height,
        boxstyle=f"round,pad=0.01,rounding_size={corner_radius}",
        facecolor=bg_color,
        edgecolor=border_color,
        linewidth=1.5,
        zorder=2
    )
    ax.add_patch(box)
    
    if subtitle:
        ax.text(x + width / 2, y + height * 0.62, title,
                ha="center", va="center", fontsize=fontsize, fontweight="bold", color=title_color, zorder=3)
        ax.text(x + width / 2, y + height * 0.30, subtitle,
                ha="center", va="center", fontsize=fontsize - 1.5, color=sub_color, zorder=3)
    else:
        ax.text(x + width / 2, y + height * 0.5, title,
                ha="center", va="center", fontsize=fontsize, fontweight="bold", color=title_color, zorder=3)


def draw_arrow(ax, start, end, label="", color="#475569", width=1.5, text_offset=(0, 0.02), fontsize=8):
    ax.annotate(
        "", xy=end, xytext=start,
        arrowprops=dict(arrowstyle="-|>", color=color, lw=width, mutation_scale=14, shrinkA=3, shrinkB=3),
        zorder=4
    )
    if label:
        mid_x = (start[0] + end[0]) / 2 + text_offset[0]
        mid_y = (start[1] + end[1]) / 2 + text_offset[1]
        ax.text(mid_x, mid_y, label, ha="center", va="center", fontsize=fontsize,
                fontweight="semibold", color=color, bbox=dict(boxstyle="round,pad=0.2", facecolor="#FFFFFF", edgecolor="none", alpha=0.85), zorder=5)


def generate_architecture_diagram():
    """Figure 3.1: Iris AI Unified System Architecture"""
    fig, ax = plt.subplots(figsize=(12, 7.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    fig.patch.set_facecolor("#FFFFFF")
    
    # Title
    ax.text(50, 97, "IRIS AI: Unified Multimodal Architecture", ha="center", va="center",
            fontsize=15, fontweight="bold", color=PRIMARY_COLOR)
    ax.text(50, 93.5, "Perception, Cognitive Decision-Making, Automation Hands & Memory Stack", ha="center", va="center",
            fontsize=9.5, color=TEXT_MUTED)

    # 1. Multimodal Input Layer (Left)
    input_box = patches.FancyBboxPatch((2, 10), 18, 78, boxstyle="round,pad=0.5,rounding_size=1",
                                       facecolor="#F1F5F9", edgecolor="#94A3B8", lw=1.2, ls="--")
    ax.add_patch(input_box)
    ax.text(11, 85, "MULTIMODAL\nINPUT LAYER", ha="center", va="center", fontsize=10, fontweight="bold", color=PRIMARY_COLOR)
    
    draw_box(ax, 3.5, 68, 15, 11, "Voice Input", "Web Speech API (en-IN/hi)", bg_color="#E0F2FE", border_color="#38BDF8")
    draw_box(ax, 3.5, 53, 15, 11, "Vision & Gaze", "Webcam + OpenCV YuNet", bg_color="#E0E7FF", border_color="#818CF8")
    draw_box(ax, 3.5, 38, 15, 11, "Desktop Screen", "Fast Screenshot & OCR", bg_color="#FEF3C7", border_color="#FBBF24")
    draw_box(ax, 3.5, 23, 15, 11, "Keyboard & UI", "Vite React HUD Client", bg_color="#F3E8FF", border_color="#C084FC")
    draw_box(ax, 3.5, 11, 15, 9, "System Monitor", "psutil Hardware Metrics", bg_color="#DCFCE7", border_color="#4ADE80")

    # 2. Central Core: IrisBrain Orchestrator
    brain_box = patches.FancyBboxPatch((25, 20), 45, 68, boxstyle="round,pad=0.8,rounding_size=1",
                                       facecolor="#F8FAFC", edgecolor=PRIMARY_COLOR, lw=2)
    ax.add_patch(brain_box)
    ax.text(47.5, 84.5, "COGNITIVE BRAIN & INFERENCE CORE", ha="center", va="center", fontsize=11, fontweight="bold", color=PRIMARY_COLOR)

    draw_box(ax, 28, 71, 39, 9, "TypoCorrector & Devanagari Shield", "Phonetic matching, typo normalization & Unicode protection", bg_color="#EFF6FF", border_color="#60A5FA")
    draw_box(ax, 28, 58, 39, 10, "IntentDetector (52+ Patterns)", "Compound regex, entity extraction, natural keyword guards", bg_color="#EEF2FF", border_color="#818CF8")
    draw_box(ax, 28, 45, 39, 10, "Decider & Safety Guard", "Action spec routing, confirmation gate, parameter validation", bg_color="#ECFDF5", border_color="#34D399")
    draw_box(ax, 28, 32, 39, 10, "ModelRouter (Hybrid Inference)", "Ollama (Llama 3.2 / Qwen 2.5) ⇄ Cloud Groq (Qwen 3.8 / OpenAI)", bg_color="#FFFBEB", border_color="#FCD34D")
    draw_box(ax, 28, 22, 39, 8, "Personality & Emotion Engine", "Adaptive tone: Sweet, Professional, Hindi/English bilingual", bg_color="#FAF5FF", border_color="#D8B4FE")

    # 3. 3-Tier Hierarchical Memory (Below Brain)
    mem_box = patches.FancyBboxPatch((25, 2), 45, 15, boxstyle="round,pad=0.5,rounding_size=0.8",
                                     facecolor="#F1F5F9", edgecolor="#64748B", lw=1.2)
    ax.add_patch(mem_box)
    ax.text(47.5, 14.5, "3-TIER HIERARCHICAL MEMORY ORCHESTRATOR", ha="center", va="center", fontsize=9, fontweight="bold", color="#334155")
    draw_box(ax, 27, 4, 12, 8, "TempLayer", "Active Turn RAM", bg_color="#FFFFFF", border_color="#94A3B8", fontsize=7.5)
    draw_box(ax, 41.5, 4, 12, 8, "LongTempLayer", "Session Summary", bg_color="#FFFFFF", border_color="#94A3B8", fontsize=7.5)
    draw_box(ax, 56, 4, 12, 8, "DeepLayer", "SQLite Persistent", bg_color="#FFFFFF", border_color="#94A3B8", fontsize=7.5)

    # 4. Hands & Automation Layer (Right)
    hands_box = patches.FancyBboxPatch((75, 10), 23, 78, boxstyle="round,pad=0.5,rounding_size=1",
                                       facecolor="#F0FDF4", edgecolor="#16A34A", lw=1.5)
    ax.add_patch(hands_box)
    ax.text(86.5, 85, "HANDS AUTOMATION\n& SYSTEM CONTROL", ha="center", va="center", fontsize=10, fontweight="bold", color="#15803D")

    draw_box(ax, 77, 72, 19, 9, "Window Manager", "Win32 Focus, Snap, Minimize", bg_color="#FFFFFF", border_color="#86EFAC")
    draw_box(ax, 77, 61, 19, 9, "Social Controller", "WhatsApp, Instagram, Telegram", bg_color="#FFFFFF", border_color="#86EFAC")
    draw_box(ax, 77, 50, 19, 9, "Code Runner", "Zero-subfolder code writing & run", bg_color="#FFFFFF", border_color="#86EFAC")
    draw_box(ax, 77, 39, 19, 9, "Game & Web Builder", "HTML5 Games & Modern Websites", bg_color="#FFFFFF", border_color="#86EFAC")
    draw_box(ax, 77, 28, 19, 9, "System & Terminal", "PowerShell/CMD, Volume, Power", bg_color="#FFFFFF", border_color="#86EFAC")
    draw_box(ax, 77, 13, 19, 12, "Dual Voice Engine", "Edge-TTS ⇄ SAPI5 Offline\nWatchdog Auto-Healing", bg_color="#FEF2F2", border_color="#FCA5A5", fontsize=8)

    # Connecting Arrows
    draw_arrow(ax, (18.5, 73.5), (28, 75.5), "Text/Audio", color="#0284C7")
    draw_arrow(ax, (18.5, 58.5), (28, 63), "Gaze/Face", color="#4F46E5")
    draw_arrow(ax, (18.5, 43.5), (28, 50), "Context", color="#D97706")
    draw_arrow(ax, (18.5, 28.5), (28, 37), "UI Events", color="#7C3AED")
    
    # Brain to Memory
    draw_arrow(ax, (40, 22), (40, 17), "Store", color="#475569")
    draw_arrow(ax, (55, 17), (55, 22), "Recall", color="#475569")

    # Brain to Hands
    draw_arrow(ax, (67, 50), (77, 50), "Exec Plan", color="#16A34A", width=2)
    draw_arrow(ax, (77, 45), (67, 45), "Result", color="#0D9488", width=1.5)

    plt.tight_layout()
    output_path = os.path.join(DIAGRAMS_DIR, "flowchart_1_architecture.png")
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Generated: {output_path}")


def generate_brain_decision_diagram():
    """Figure 3.2: Cognitive Intent Decision & Action Planning Pipeline"""
    fig, ax = plt.subplots(figsize=(11, 7), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    fig.patch.set_facecolor("#FFFFFF")

    ax.text(50, 96, "Cognitive Intent Decision & Action Planning Pipeline", ha="center", va="center",
            fontsize=14, fontweight="bold", color=PRIMARY_COLOR)
    ax.text(50, 92.5, "Stage-by-stage progression from user utterance to safe automated OS execution", ha="center", va="center",
            fontsize=9, color=TEXT_MUTED)

    # Stages as vertical flowchart
    draw_box(ax, 32, 80, 36, 8, "User Command Input", "Voice transcription (Web Speech API) or Chat Text", bg_color="#E0F2FE", border_color="#38BDF8")
    draw_arrow(ax, (50, 80), (50, 73), "Raw String")

    draw_box(ax, 32, 65, 36, 8, "Stage 1: Pre-Processing & Shielding", "Typo correction, phonetic mapping, Devanagari unicode protection", bg_color="#EFF6FF", border_color="#60A5FA")
    draw_arrow(ax, (50, 65), (50, 58), "Normalized Text")

    draw_box(ax, 28, 50, 44, 8, "Stage 2: Multi-Pattern Intent Detection", "52 Regex patterns, compound keywords, negative phrase exclusion", bg_color="#EEF2FF", border_color="#818CF8")
    draw_arrow(ax, (50, 50), (50, 43), "Intent & Target Entities")

    # Decision Diamond / Split Box
    draw_box(ax, 28, 34, 44, 9, "Stage 3: Decider Action Specification", "Is intent ACTION_ONLY, QUESTION/QUERY, or SYSTEM CONFIG?", bg_color="#FEF3C7", border_color="#F59E0B")

    # Left Branch: Query / LLM
    draw_box(ax, 6, 18, 30, 10, "ModelRouter / LLM Fallback", "Query Ollama Local (Qwen/Llama) or\nCloud Groq for conversational response", bg_color="#FFFBEB", border_color="#FCD34D", fontsize=8)
    # Right Branch: Action Execution
    draw_box(ax, 54, 18, 40, 10, "Stage 4: Multi-Step Plan Generation", "Translate intent to discrete step objects\n(Params: target_dir, app, contact, code, game)", bg_color="#ECFDF5", border_color="#34D399", fontsize=8)

    draw_arrow(ax, (38, 34), (21, 28), "Knowledge Query", color="#D97706")
    draw_arrow(ax, (62, 34), (74, 28), "Action Required", color="#16A34A")

    # Safety Gate
    draw_box(ax, 54, 4, 40, 9, "Stage 5: TaskExecutor Hands Dispatch", "Execute via Win32 ctypes, WebBrowser, Subprocess,\nand return structured execution result", bg_color="#DCFCE7", border_color="#22C55E", fontsize=8)
    draw_arrow(ax, (74, 18), (74, 13), "Execute Steps", color="#16A34A")

    # Feedback Loop
    draw_box(ax, 6, 4, 30, 9, "Response Synthesis & Speech", "Format confirmation text, speak via Dual VoiceEngine", bg_color="#FAF5FF", border_color="#C084FC", fontsize=8)
    draw_arrow(ax, (54, 8.5), (36, 8.5), "Execution Status", color="#6366F1")
    draw_arrow(ax, (21, 18), (21, 13), "LLM Text", color="#6366F1")

    plt.tight_layout()
    output_path = os.path.join(DIAGRAMS_DIR, "flowchart_2_brain_decision.png")
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Generated: {output_path}")


def generate_hands_automation_diagram():
    """Figure 3.3: Hands Execution & OS Automation Subsystems"""
    fig, ax = plt.subplots(figsize=(11, 7), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    fig.patch.set_facecolor("#FFFFFF")

    ax.text(50, 96, "Hands OS Automation & Subsystem Execution Architecture", ha="center", va="center",
            fontsize=14, fontweight="bold", color=PRIMARY_COLOR)
    ax.text(50, 92.5, "TaskExecutor dispatching specialized handlers directly into Windows 11 subsystems", ha="center", va="center",
            fontsize=9, color=TEXT_MUTED)

    # Master TaskExecutor Box at Top
    draw_box(ax, 30, 78, 40, 10, "TaskExecutor Orchestrator", "Validates step schema, sequences dependencies, reports execution progress", bg_color="#EEF2FF", border_color="#6366F1")

    # 5 Subsystem Branches
    # 1. Window Manager
    draw_box(ax, 2, 50, 17, 16, "Window Manager", "• Win32 EnumWindows\n• AttachThreadInput\n• Focus, Minimize, Snap\n• Hide to Tray Recovery", bg_color="#F8FAFC", border_color="#38BDF8", fontsize=7.5)
    # 2. Social Controller
    draw_box(ax, 22, 50, 17, 16, "Social Controller", "• WhatsApp Desktop\n• Instagram Direct\n• Coordinate click nav\n• Win32 Clipboard paste", bg_color="#F8FAFC", border_color="#34D399", fontsize=7.5)
    # 3. Code Runner
    draw_box(ax, 42, 50, 17, 16, "Code Runner", "• Forbidden folder filter\n• Custom target_dir\n• Python, JS, HTML, C\n• Non-blocking write", bg_color="#F8FAFC", border_color="#F59E0B", fontsize=7.5)
    # 4. Game & Web Builder
    draw_box(ax, 62, 50, 17, 16, "Game & Web Builder", "• HTML5 Canvas Games\n• Chess, Ludo, Carrom\n• Responsive Websites\n• Auto browser launch", bg_color="#F8FAFC", border_color="#EC4899", fontsize=7.5)
    # 5. System & Terminal
    draw_box(ax, 81, 50, 17, 16, "System Control", "• PowerShell / CMD\n• Safe command check\n• Audio volume & power\n• App discovery & run", bg_color="#F8FAFC", border_color="#A855F7", fontsize=7.5)

    # Arrows from Orchestrator to handlers
    draw_arrow(ax, (38, 78), (10.5, 66), "window", color="#0284C7")
    draw_arrow(ax, (44, 78), (30.5, 66), "social_msg", color="#10B981")
    draw_arrow(ax, (50, 78), (50.5, 66), "write/run", color="#D97706")
    draw_arrow(ax, (56, 78), (70.5, 66), "create_game/site", color="#DB2777")
    draw_arrow(ax, (62, 78), (89.5, 66), "sys/launch", color="#9333EA")

    # Native OS Target Bar (Bottom)
    draw_box(ax, 5, 12, 90, 22, "Native Windows 11 Operating System Target Layer",
             "Interfacing via user32.dll, kernel32.dll, Shell32, Process Subprocesses & Local Storage FileSystem",
             bg_color="#0F172A", border_color="#334155", title_color="#FFFFFF", sub_color="#94A3B8")

    draw_box(ax, 8, 15, 24, 11, "Win32 GUI Subsystem", "HWND, SetForegroundWindow,\nkeybd_event, mouse_event", bg_color="#1E293B", border_color="#475569", title_color="#F8FAFC", sub_color="#94A3B8", fontsize=7)
    draw_box(ax, 38, 15, 24, 11, "Process & Shell Engine", "Detached process groups, CMD /k,\nPowerShell script execution", bg_color="#1E293B", border_color="#475569", title_color="#F8FAFC", sub_color="#94A3B8", fontsize=7)
    draw_box(ax, 68, 15, 24, 11, "Default Web Browser", "Edge/Chrome HTML5 Canvas,\nInteractive Games & Sites", bg_color="#1E293B", border_color="#475569", title_color="#F8FAFC", sub_color="#94A3B8", fontsize=7)

    # Connections to OS
    draw_arrow(ax, (10.5, 50), (15, 26), color="#0284C7")
    draw_arrow(ax, (30.5, 50), (22, 26), color="#10B981")
    draw_arrow(ax, (50.5, 50), (50, 26), color="#D97706")
    draw_arrow(ax, (70.5, 50), (80, 26), color="#DB2777")
    draw_arrow(ax, (89.5, 50), (58, 26), color="#9333EA")

    plt.tight_layout()
    output_path = os.path.join(DIAGRAMS_DIR, "flowchart_3_hands_automation.png")
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Generated: {output_path}")


def generate_voice_resilience_diagram():
    """Figure 3.4: Dual-Pipeline Voice Engine & Speech Watchdog Auto-Recovery"""
    fig, ax = plt.subplots(figsize=(11, 7), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    fig.patch.set_facecolor("#FFFFFF")

    ax.text(50, 96, "Dual-Pipeline Speech Synthesis & Auto-Healing Watchdog", ha="center", va="center",
            fontsize=14, fontweight="bold", color=PRIMARY_COLOR)
    ax.text(50, 92.5, "Zero-dropout voice synthesis with Windows native SAPI5 fallback and continuous microphone monitoring", ha="center", va="center",
            fontsize=9, color=TEXT_MUTED)

    # Left Container: Speech Synthesis (TTS)
    tts_cont = patches.FancyBboxPatch((3, 6), 45, 82, boxstyle="round,pad=0.5,rounding_size=1",
                                      facecolor="#F8FAFC", edgecolor="#3B82F6", lw=1.5)
    ax.add_patch(tts_cont)
    ax.text(25.5, 84, "OUTPUT: SPEECH SYNTHESIS ENGINE", ha="center", va="center", fontsize=9.5, fontweight="bold", color="#1D4ED8")

    draw_box(ax, 7, 72, 37, 8, "Speech Request Queued", "IrisBrain generates conversational response", bg_color="#EFF6FF", border_color="#60A5FA", fontsize=8)
    draw_arrow(ax, (25.5, 72), (25.5, 65))

    draw_box(ax, 7, 57, 37, 8, "Attempt Neural Edge-TTS", "Online WebSocket: SwaraNeural / AriaNeural", bg_color="#E0F2FE", border_color="#0284C7", fontsize=8)
    draw_arrow(ax, (25.5, 57), (25.5, 48), "Enforce 8.0s Timeout")

    draw_box(ax, 7, 39, 37, 9, "Decision: Succeeded within 8s?", "Check synthesis status before audio lock", bg_color="#FEF3C7", border_color="#F59E0B", fontsize=8)

    # Succeeded
    draw_box(ax, 5, 23, 19, 10, "Play Neural WAV", "High clarity natural tone\n(Hindi & English clones)", bg_color="#DCFCE7", border_color="#22C55E", fontsize=7.5)
    # Failed / Timeout
    draw_box(ax, 26, 23, 20, 10, "SAPI5 Offline Fallback", "Win32 SpVoice (Hazel/Zira)\n100% Offline WAV Synthesis", bg_color="#FEE2E2", border_color="#EF4444", fontsize=7.5)

    draw_arrow(ax, (17, 39), (14.5, 33), "Yes (<8s)", color="#16A34A")
    draw_arrow(ax, (34, 39), (36, 33), "Timeout / Offline", color="#DC2626")

    draw_box(ax, 7, 9, 37, 9, "Audio Hardware Playback & Flag Clear", "Pygame audio playback -> Clear speaking flag -> Ready for mic", bg_color="#F1F5F9", border_color="#94A3B8", fontsize=7.5)
    draw_arrow(ax, (14.5, 23), (20, 18), color="#16A34A")
    draw_arrow(ax, (36, 23), (31, 18), color="#DC2626")

    # Right Container: Speech Recognition (STT) Watchdog
    stt_cont = patches.FancyBboxPatch((52, 6), 45, 82, boxstyle="round,pad=0.5,rounding_size=1",
                                      facecolor="#F8FAFC", edgecolor="#10B981", lw=1.5)
    ax.add_patch(stt_cont)
    ax.text(74.5, 84, "INPUT: MICROPHONE & WATCHDOG", ha="center", va="center", fontsize=9.5, fontweight="bold", color="#047857")

    draw_box(ax, 56, 72, 37, 8, "Continuous STT Listening", "Web Speech API (en-IN fallback)", bg_color="#ECFDF5", border_color="#34D399", fontsize=8)
    draw_arrow(ax, (74.5, 72), (74.5, 65))

    draw_box(ax, 56, 55, 37, 10, "1000ms Watchdog Heartbeat", "Monitors recognitionActiveRef in React lifecycle;\nprevents silent 60s silence timeout freeze", bg_color="#EEF2FF", border_color="#818CF8", fontsize=8)
    draw_arrow(ax, (74.5, 55), (74.5, 47), "Query Status")

    draw_box(ax, 56, 38, 37, 9, "Is Recognizer Inactive && convOn?", "Did browser silently drop the audio track?", bg_color="#FEF3C7", border_color="#F59E0B", fontsize=8)

    # Restart
    draw_box(ax, 54, 22, 19, 11, "Auto-Revive Listener", "Call rec.start() seamlessly;\nZero user intervention", bg_color="#FEE2E2", border_color="#EF4444", fontsize=7.5)
    # Healthy
    draw_box(ax, 75, 22, 20, 11, "Maintain Connection", "Pass transcribed text to\nTurn Queue & Brain", bg_color="#DCFCE7", border_color="#22C55E", fontsize=7.5)

    draw_arrow(ax, (66, 38), (63.5, 33), "Silent Dropout", color="#DC2626")
    draw_arrow(ax, (83, 38), (85, 33), "Active", color="#16A34A")

    draw_box(ax, 56, 9, 37, 8, "Zero-Break Continuous Conversation", "Long-term sessions run stably for hours without restart", bg_color="#F1F5F9", border_color="#94A3B8", fontsize=7.5)
    draw_arrow(ax, (63.5, 22), (70, 17), color="#DC2626")
    draw_arrow(ax, (85, 22), (79, 17), color="#16A34A")

    plt.tight_layout()
    output_path = os.path.join(DIAGRAMS_DIR, "flowchart_4_voice_resilience.png")
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Generated: {output_path}")


def generate_vision_attention_diagram():
    """Figure 3.5: Vision Perception, Biometrics & Playful Attention-Attraction State Machine"""
    fig, ax = plt.subplots(figsize=(11, 7), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    fig.patch.set_facecolor("#FFFFFF")

    ax.text(50, 96, "Vision Perception & Attention-Attraction State Machine", ha="center", va="center",
            fontsize=14, fontweight="bold", color=PRIMARY_COLOR)
    ax.text(50, 92.5, "Biometric face verification, facial landmark gaze tracking, and proactive user re-engagement", ha="center", va="center",
            fontsize=9, color=TEXT_MUTED)

    draw_box(ax, 32, 80, 36, 8, "Webcam Video Stream", "OpenCV VideoCapture(0) Keep-Alive daemon", bg_color="#EFF6FF", border_color="#3B82F6")
    draw_arrow(ax, (50, 80), (50, 73), "Frame")

    draw_box(ax, 30, 64, 40, 9, "YuNet ONNX Face Detector", "Detects face bounding box + 5 facial landmarks\n(Right Eye, Left Eye, Nose, Mouth Corners)", bg_color="#EEF2FF", border_color="#6366F1", fontsize=8)
    draw_arrow(ax, (50, 64), (50, 56), "Landmarks")

    draw_box(ax, 28, 47, 44, 9, "SFace Biometric Single-Owner Vault", "Cosine similarity vs enrolled Commander profile (thresh=0.68)", bg_color="#FEF3C7", border_color="#F59E0B", fontsize=8)

    # Left: Unauthorized
    draw_box(ax, 4, 32, 26, 10, "Stranger Lockout", "Reject voice command;\nProhibit unauthorized OS access", bg_color="#FEE2E2", border_color="#EF4444", fontsize=7.5)
    draw_arrow(ax, (28, 51.5), (17, 42), "Similarity < 0.68", color="#DC2626")

    # Center/Right: Authorized Commander
    draw_box(ax, 40, 31, 56, 11, "Gaze Vector Displacement Computation", "Compute deviation: dev_x = |nose_x - eye_center_x| / eye_distance\nQuantifies whether user is looking directly at screen or distracted away", bg_color="#ECFDF5", border_color="#10B981", fontsize=8)
    draw_arrow(ax, (72, 47), (72, 42), "Owner Verified", color="#16A34A")

    # Condition branch: Looking away > 14s
    draw_box(ax, 54, 11, 42, 14, "Trigger Playful Attention Attraction", "dev_x > 0.23 for 14+ seconds:\n'Hey Commander, over here! 😊'\n'Commander, idhar bhi dhyan dijiye!'\nCooldown: 45s", bg_color="#FAF5FF", border_color="#A855F7", fontsize=8)
    draw_arrow(ax, (75, 31), (75, 25), "dev_x > 0.23 (t ≥ 14s)", color="#9333EA")

    # Reset Branch
    draw_box(ax, 6, 11, 40, 14, "Attentive Focus Maintained", "dev_x ≤ 0.22 (User returns gaze):\nReset inattention counter to 0s immediately;\nMaintain silent ambient readiness", bg_color="#F0FDF4", border_color="#22C55E", fontsize=8)
    draw_arrow(ax, (50, 31), (26, 25), "dev_x ≤ 0.22 (Eye Contact)", color="#16A34A")

    plt.tight_layout()
    output_path = os.path.join(DIAGRAMS_DIR, "flowchart_5_vision_attention.png")
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Generated: {output_path}")


def generate_user_identification_diagram():
    """Figure 4.1: Biometric User Identification & Owner Vault Verification"""
    fig, ax = plt.subplots(figsize=(11, 7), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    fig.patch.set_facecolor("#FFFFFF")

    ax.text(50, 96, "Biometric User Identification & Single-Owner Verification Pipeline", ha="center", va="center",
            fontsize=14, fontweight="bold", color=PRIMARY_COLOR)
    ax.text(50, 92.5, "YuNet landmark alignment, SFace 128-d embedding extraction, and AES-256 encrypted vault cosine matching", ha="center", va="center",
            fontsize=9, color=TEXT_MUTED)

    # 1. Video Frame
    draw_box(ax, 32, 81, 36, 8, "Webcam Video Capture", "OpenCV VideoCapture(0) Keep-Alive daemon (640x480 @ 30fps)", bg_color="#EFF6FF", border_color="#3B82F6")
    draw_arrow(ax, (50, 81), (50, 74), "Raw BGR Frame")

    # 2. YuNet Detection & Alignment
    draw_box(ax, 28, 65, 44, 9, "YuNet ONNX Face Detection & Alignment", "Detects face bounding box + 5 landmarks (Eyes, Nose, Mouth corners)\nAffine warp alignment to 112x112 canonical facial pose", bg_color="#EEF2FF", border_color="#6366F1", fontsize=8)
    draw_arrow(ax, (50, 65), (50, 58), "Aligned Face (112x112)")

    # 3. SFace Feature Extractor
    draw_box(ax, 28, 49, 44, 9, "SFace Deep Metric Feature Extractor", "Extracts 128-dimensional L2-normalized feature vector V_live\n(Zero raw photographs or video frames ever saved to disk)", bg_color="#ECFDF5", border_color="#10B981", fontsize=8)
    draw_arrow(ax, (50, 49), (50, 42), "128-d Vector")

    # 4. Biometric Vault Decryption
    draw_box(ax, 2, 33, 30, 10, "Encrypted Biometric Vault", "PBKDF2 + AES-256 (Fernet)\nHardware-bound MachineGuid key\nDecrypts stored V_vault to RAM", bg_color="#FFFBEB", border_color="#F59E0B", fontsize=7.5)
    draw_arrow(ax, (32, 38), (39, 38), "V_vault", color="#D97706")

    # 5. Cosine Similarity Matching
    draw_box(ax, 39, 33, 40, 10, "Cosine Similarity Comparator", "Cosine Similarity: Sim = (V_live · V_vault) / (||V_live|| ||V_vault||)\nEvaluates biometric distance against threshold (0.68)", bg_color="#FEF3C7", border_color="#F59E0B", fontsize=8)
    draw_arrow(ax, (59, 33), (59, 25), "Sim Metric")

    # 6. Branching Output
    # Authorized
    draw_box(ax, 54, 8, 42, 14, "Owner Authenticated ('Commander')", "Cosine Similarity ≥ 0.68:\n• Access granted to private chat & memory\n• Full Win32 OS hands automation authorized\n• Emotion-conditioned greeting synthesized", bg_color="#F0FDF4", border_color="#22C55E", fontsize=7.5)
    # Unauthorized
    draw_box(ax, 4, 8, 42, 14, "Stranger Lockout (Access Denied)", "Cosine Similarity < 0.68:\n• Automatic execution refusal\n• Proactive audio alert: 'Biometric authorization failed'\n• Sensitive terminal commands prohibited", bg_color="#FEF2F2", border_color="#EF4444", fontsize=7.5)

    draw_arrow(ax, (68, 25), (75, 22), "Sim ≥ 0.68", color="#16A34A")
    draw_arrow(ax, (50, 25), (25, 22), "Sim < 0.68", color="#DC2626")

    plt.tight_layout()
    output_path = os.path.join(DIAGRAMS_DIR, "flowchart_6_user_identification.png")
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Generated: {output_path}")


def generate_emotion_fusion_diagram():
    """Figure 4.2: Multimodal Emotion Recognition Combining Vision & Voice"""
    fig, ax = plt.subplots(figsize=(11, 7), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    fig.patch.set_facecolor("#FFFFFF")

    ax.text(50, 96, "Multimodal Emotion Recognition Combining Vision & Voice", ha="center", va="center",
            fontsize=14, fontweight="bold", color=PRIMARY_COLOR)
    ax.text(50, 92.5, "Synergistic fusion of visual facial micro-expressions and acoustic vocal prosody for adaptive personality", ha="center", va="center",
            fontsize=9, color=TEXT_MUTED)

    # Left: Vision Emotion Pipeline
    vis_cont = patches.FancyBboxPatch((3, 40), 45, 48, boxstyle="round,pad=0.5,rounding_size=1",
                                      facecolor="#F8FAFC", edgecolor="#3B82F6", lw=1.5)
    ax.add_patch(vis_cont)
    ax.text(25.5, 85, "1. VISUAL EMOTION PIPELINE (CAMERA)", ha="center", va="center", fontsize=9, fontweight="bold", color="#1D4ED8")

    draw_box(ax, 5, 73, 41, 8, "Webcam Video Stream", "High-speed 30fps OpenCV capture", bg_color="#EFF6FF", border_color="#60A5FA", fontsize=7.5)
    draw_arrow(ax, (25.5, 73), (25.5, 66))

    draw_box(ax, 5, 58, 41, 9, "YuNet Facial Landmark Dynamics", "Calculates Eye Aspect Ratio (EAR), Mouth Aspect Ratio (MAR),\nEyebrow Furrow & Lip oscillation (2-5Hz speaking detector)", bg_color="#EEF2FF", border_color="#818CF8", fontsize=7)
    draw_arrow(ax, (25.5, 58), (25.5, 51))

    draw_box(ax, 5, 43, 41, 8, "Visual Classifier", "Joy, Sadness, Anger, Contempt, Fatigue, Neutral", bg_color="#ECFDF5", border_color="#34D399", fontsize=7.5)

    # Right: Acoustic / Voice Emotion Pipeline
    voc_cont = patches.FancyBboxPatch((52, 40), 45, 48, boxstyle="round,pad=0.5,rounding_size=1",
                                      facecolor="#F8FAFC", edgecolor="#10B981", lw=1.5)
    ax.add_patch(voc_cont)
    ax.text(74.5, 85, "2. ACOUSTIC EMOTION PIPELINE (VOICE)", ha="center", va="center", fontsize=9, fontweight="bold", color="#047857")

    draw_box(ax, 54, 73, 41, 8, "Microphone Audio Input", "Continuous audio stream via sounddevice", bg_color="#ECFDF5", border_color="#34D399", fontsize=7.5)
    draw_arrow(ax, (74.5, 73), (74.5, 66))

    draw_box(ax, 54, 58, 41, 9, "Acoustic Prosody Analyzer", "Extracts Fundamental Pitch (F0), Root-Mean-Square Energy,\nand Speech Cadence (Speaking rate & pause duration)", bg_color="#FEF3C7", border_color="#F59E0B", fontsize=7)
    draw_arrow(ax, (74.5, 58), (74.5, 51))

    draw_box(ax, 54, 43, 41, 8, "Vocal & Lexical Sentiment", "Arousal (calm vs agitated) + Valence (negative vs positive)", bg_color="#FFFBEB", border_color="#FCD34D", fontsize=7.5)

    # Center Bottom: Multimodal Fusion Engine
    draw_box(ax, 20, 24, 60, 11, "Multimodal Presence & Emotion Intelligence Engine",
             "Bayesian Confidence Fusion: Integrates Visual Micro-Expressions with Acoustic Prosody\nResolves ambiguities (e.g. distinguishing a smile from a sarcastic smirk or fatigue from sadness)",
             bg_color="#FAF5FF", border_color="#A855F7", title_color="#581C87", fontsize=8)

    draw_arrow(ax, (25.5, 43), (35, 35), "Visual State", color="#1D4ED8")
    draw_arrow(ax, (74.5, 43), (65, 35), "Acoustic State", color="#047857")
    draw_arrow(ax, (50, 24), (50, 17), "Unified EmotionState", color="#7E22CE")

    # Final Output: Personality Adaptation
    draw_box(ax, 10, 5, 80, 12, "IrisPersonality Adaptive Response & Neural Voice Modulation",
             "• Dynamic Pitch & Speech Rate: Calms excited tone, speaks soothingly if anger/fatigue detected\n"
             "• Tailored Verbal Companion: 'Whatever it is, we will take it one step at a time, Commander'\n"
             "• Cybernetic HUD Reaction: Updates visual facial hologram emotion rings and live state markers",
             bg_color="#F0FDF4", border_color="#22C55E", title_color="#14532D", fontsize=7.5)

    plt.tight_layout()
    output_path = os.path.join(DIAGRAMS_DIR, "flowchart_7_emotion_vision_voice.png")
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Generated: {output_path}")


if __name__ == "__main__":
    generate_architecture_diagram()
    generate_brain_decision_diagram()
    generate_hands_automation_diagram()
    generate_voice_resilience_diagram()
    generate_vision_attention_diagram()
    generate_user_identification_diagram()
    generate_emotion_fusion_diagram()
    print("All 7 technical diagrams successfully generated in:", DIAGRAMS_DIR)
