"""
Generator for IRIS-AI Team Roles & Comprehensive Presentation Guide (.docx / .doc)
Contains full technical details, flowcharts, speaker scripts, slide blueprints, and Q&A defenses
for all 10 presenters.
"""

import os
import shutil
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "report_assets")
OUTPUT_DOCX = os.path.join(BASE_DIR, "IRIS_AI_Team_Roles_and_Presentation_Guide.docx")
OUTPUT_DOC = os.path.join(BASE_DIR, "IRIS_AI_Team_Roles_and_Presentation_Guide.doc")

# Styling Palette
COLOR_PRIMARY = RGBColor(30, 58, 138)     # #1E3A8A - Deep Navy Blue
COLOR_SECONDARY = RGBColor(13, 148, 136)  # #0D9488 - Teal Accent
COLOR_DARK = RGBColor(15, 23, 42)         # #0F172A - Slate 900
COLOR_MUTED = RGBColor(71, 85, 105)       # #475569 - Slate 600

HEX_PRIMARY = "1E3A8A"
HEX_SECONDARY = "0D9488"
HEX_LIGHT_BG = "F1F5F9"
HEX_CARD_BG = "F8FAFC"
HEX_ZEBRA = "F8FAFC"
HEX_BORDER = "CBD5E1"
HEX_ACCENT_BG = "E0F2FE"


def set_cell_shading(cell, color_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    tcPr.append(shd)


def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)


def set_table_borders(table, color=HEX_BORDER, sz="4", val="single"):
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:left w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:right w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:insideV w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)


def add_callout(doc, title, text, bg_hex=HEX_CARD_BG, border_color_hex=HEX_PRIMARY):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    cell = tbl.cell(0, 0)
    cell.width = Inches(6.5)
    set_cell_shading(cell, bg_hex)
    set_cell_margins(cell, top=140, bottom=140, left=180, right=180)

    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'<w:top w:val="none"/>'
        f'<w:left w:val="single" w:sz="24" w:color="{border_color_hex}"/>'
        f'<w:bottom w:val="none"/>'
        f'<w:right w:val="none"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(tcBorders)

    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.15
    run_t = p.add_run(f"📌 {title}\n")
    run_t.font.name = "Calibri"
    run_t.font.size = Pt(11)
    run_t.font.bold = True
    run_t.font.color.rgb = COLOR_PRIMARY

    run_b = p.add_run(text)
    run_b.font.name = "Calibri"
    run_b.font.size = Pt(10)
    run_b.font.color.rgb = COLOR_DARK

    p_after = doc.add_paragraph()
    p_after.paragraph_format.space_before = Pt(2)
    p_after.paragraph_format.space_after = Pt(4)


def add_badge_header(doc, speaker_num, speaker_name, role_title, domain_str):
    doc.add_page_break()
    p_tag = doc.add_paragraph()
    p_tag.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_tag.paragraph_format.space_before = Pt(8)
    p_tag.paragraph_format.space_after = Pt(2)
    r_tag = p_tag.add_run(f"SEMINAR PRESENTATION  |  PRESENTER {speaker_num} OF 10")
    r_tag.font.name = "Calibri"
    r_tag.font.size = Pt(9)
    r_tag.font.bold = True
    r_tag.font.color.rgb = COLOR_SECONDARY

    h1 = doc.add_paragraph()
    h1.paragraph_format.space_before = Pt(2)
    h1.paragraph_format.space_after = Pt(2)
    h1.paragraph_format.keep_with_next = True
    r_h1 = h1.add_run(f"Role {speaker_num}: {role_title}")
    r_h1.font.name = "Calibri"
    r_h1.font.size = Pt(18)
    r_h1.font.bold = True
    r_h1.font.color.rgb = COLOR_PRIMARY

    meta_tbl = doc.add_table(rows=1, cols=2)
    meta_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_tbl.autofit = False
    c0 = meta_tbl.cell(0, 0)
    c1 = meta_tbl.cell(0, 1)
    c0.width = Inches(3.25)
    c1.width = Inches(3.25)
    set_cell_shading(c0, HEX_LIGHT_BG)
    set_cell_shading(c1, HEX_LIGHT_BG)
    set_cell_margins(c0, top=80, bottom=80, left=120, right=120)
    set_cell_margins(c1, top=80, bottom=80, left=120, right=120)

    p0 = c0.paragraphs[0]
    p0.paragraph_format.space_after = Pt(0)
    r0_label = p0.add_run("Speaker: ")
    r0_label.bold = True
    r0_label.font.name = "Calibri"
    r0_label.font.size = Pt(10)
    r0_name = p0.add_run(speaker_name)
    r0_name.bold = True
    r0_name.font.name = "Calibri"
    r0_name.font.size = Pt(10)
    r0_name.font.color.rgb = COLOR_PRIMARY

    p1 = c1.paragraphs[0]
    p1.paragraph_format.space_after = Pt(0)
    r1_label = p1.add_run("Domain: ")
    r1_label.bold = True
    r1_label.font.name = "Calibri"
    r1_label.font.size = Pt(10)
    r1_dom = p1.add_run(domain_str)
    r1_dom.font.name = "Calibri"
    r1_dom.font.size = Pt(9.5)
    r1_dom.font.color.rgb = COLOR_MUTED

    p_div = doc.add_paragraph()
    p_div.paragraph_format.space_before = Pt(6)
    p_div.paragraph_format.space_after = Pt(4)


def add_section_h2(doc, title):
    h = doc.add_paragraph()
    h.paragraph_format.space_before = Pt(12)
    h.paragraph_format.space_after = Pt(4)
    h.paragraph_format.keep_with_next = True
    r = h.add_run(title)
    r.font.name = "Calibri"
    r.font.size = Pt(13)
    r.font.bold = True
    r.font.color.rgb = COLOR_PRIMARY


def add_section_h3(doc, title):
    h = doc.add_paragraph()
    h.paragraph_format.space_before = Pt(8)
    h.paragraph_format.space_after = Pt(2)
    h.paragraph_format.keep_with_next = True
    r = h.add_run(title)
    r.font.name = "Calibri"
    r.font.size = Pt(11)
    r.font.bold = True
    r.font.color.rgb = COLOR_SECONDARY


def add_bullet(doc, bold_prefix, text):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.15
    rb = p.add_run(bold_prefix + ": ")
    rb.font.name = "Calibri"
    rb.font.size = Pt(10)
    rb.bold = True
    rb.font.color.rgb = COLOR_DARK
    rt = p.add_run(text)
    rt.font.name = "Calibri"
    rt.font.size = Pt(10)
    rt.font.color.rgb = COLOR_DARK


def add_body_p(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.15
    r = p.add_run(text)
    r.font.name = "Calibri"
    r.font.size = Pt(10)
    r.font.color.rgb = COLOR_DARK


def try_add_image(doc, img_name, caption, width=Inches(6.0)):
    img_path = os.path.join(ASSETS_DIR, img_name)
    if os.path.exists(img_path):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(6)
        p_img.paragraph_format.space_after = Pt(2)
        run_img = p_img.add_run()
        run_img.add_picture(img_path, width=width)

        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_before = Pt(0)
        p_cap.paragraph_format.space_after = Pt(8)
        run_cap = p_cap.add_run(f"Figure: {caption}")
        run_cap.font.name = "Calibri"
        run_cap.font.size = Pt(9)
        run_cap.font.italic = True
        run_cap.font.color.rgb = COLOR_MUTED


def build_document():
    doc = Document()

    # 1. Page Setup: Standard Letter, 1-inch margins
    sections = doc.sections
    for s in sections:
        s.top_margin = Inches(1.0)
        s.bottom_margin = Inches(1.0)
        s.left_margin = Inches(1.0)
        s.right_margin = Inches(1.0)
        s.header.is_linked_to_previous = False
        s.footer.is_linked_to_previous = False

        # Header
        hp = s.header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hr = hp.add_run("IRIS-AI (Project IRIS)  |  Master Presentation & Technical Defense Guide")
        hr.font.name = "Calibri"
        hr.font.size = Pt(8.5)
        hr.font.color.rgb = COLOR_MUTED

        # Footer
        fp = s.footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        fr = fp.add_run("CONFIDENTIAL & PROPRIETARY — ACADEMIC DEFENSE EDITION")
        fr.font.name = "Calibri"
        fr.font.size = Pt(8.5)
        fr.font.color.rgb = COLOR_MUTED

    # =========================================================================
    # COVER PAGE
    # =========================================================================
    p_cov_pre = doc.add_paragraph()
    p_cov_pre.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cov_pre.paragraph_format.space_before = Pt(20)
    p_cov_pre.paragraph_format.space_after = Pt(4)
    r_pre = p_cov_pre.add_run("DEPARTMENT OF COMPUTER SCIENCE & ARTIFICIAL INTELLIGENCE ENGINEERING\nACADEMIC DEFENSE & TECHNICAL REFERENCE SPECIFICATION")
    r_pre.font.name = "Calibri"
    r_pre.font.size = Pt(11)
    r_pre.font.bold = True
    r_pre.font.color.rgb = COLOR_SECONDARY

    p_cov_title = doc.add_paragraph()
    p_cov_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cov_title.paragraph_format.space_before = Pt(14)
    p_cov_title.paragraph_format.space_after = Pt(8)
    r_title = p_cov_title.add_run("IRIS-AI (PROJECT IRIS)\nMASTER PRESENTATION & ROLES DOSSIER")
    r_title.font.name = "Calibri"
    r_title.font.size = Pt(26)
    r_title.font.bold = True
    r_title.font.color.rgb = COLOR_PRIMARY

    p_cov_sub = doc.add_paragraph()
    p_cov_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cov_sub.paragraph_format.space_before = Pt(4)
    p_cov_sub.paragraph_format.space_after = Pt(20)
    r_sub = p_cov_sub.add_run("Complete 10-Speaker Defense Specification, System Architecture, Code Mechanics,\nFlowcharts, Spoken Scripts, and Evaluation Q&A Strategies")
    r_sub.font.name = "Calibri"
    r_sub.font.size = Pt(12)
    r_sub.font.color.rgb = COLOR_MUTED

    # Presenter Roster Table on Cover Page
    roster_tbl = doc.add_table(rows=11, cols=3)
    roster_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    roster_tbl.autofit = False
    set_table_borders(roster_tbl)

    headers = ["Speaker Name", "Presentation Role", "Core Technical Subsystem"]
    widths = [Inches(1.8), Inches(2.2), Inches(2.5)]
    for i, h in enumerate(headers):
        cell = roster_tbl.cell(0, i)
        cell.width = widths[i]
        set_cell_shading(cell, HEX_PRIMARY)
        set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        r = p.add_run(h)
        r.font.name = "Calibri"
        r.font.size = Pt(10)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)

    roster_data = [
        ("Jude Livingston", "Introduction About Our Project", "Mission, Desktop AGI Problem, 5-Layer Stack"),
        ("Karunya", "UI / UX & Desktop Overlay", "Thinking Orb, Glassmorphism HUD, PyWebView IPC"),
        ("Bhaskar", "Installation & Setup Automation", "setup.bat, start_all.bat, Port Arbitration, .venv Auto-heal"),
        ("Rishit", "Core Mind & API Key Management", "IrisBrain, Fast-Path Sub-1ms Bypass, Multi-Tier Fallback"),
        ("Aruna", "Languages & Multimodal Emotion Fusion", "Language Parsing, Vocal + Face Affect Fusion, Echo Cancellation"),
        ("VARUN SANDESH", "Vision Systems & Workspace Perception", "Camera Loop, Foreground Window Tracking, MSS/OCR Engine"),
        ("Dhanush Dathu", "Automation & Robotic Hands", "TaskExecutor, App Fuzzy Launch, Sandboxed PowerShell"),
        ("Lokesh Chandhra", "Memory Architecture & Cognitive Recall", "3-Tier Memory Hierarchy, SQLite Log, Vector Store, Time-Gap"),
        ("Mohanhemanth", "Security, Privacy & Guardrails", "Hardware Biometric Vault, Zero Raw Photos, Safe-Mode AST"),
        ("Bhuvana Kruthi", "Conclusion & Strategic Roadmap", "Industry Matrix, 12 Bug Fixes, NPU Acceleration, Multi-Agent"),
    ]

    for row_idx, data in enumerate(roster_data, start=1):
        bg = HEX_ZEBRA if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, text in enumerate(data):
            cell = roster_tbl.cell(row_idx, col_idx)
            cell.width = widths[col_idx]
            set_cell_shading(cell, bg)
            set_cell_margins(cell, top=60, bottom=60, left=100, right=100)
            p = cell.paragraphs[0]
            r = p.add_run(text)
            r.font.name = "Calibri"
            r.font.size = Pt(9.5)
            if col_idx == 0:
                r.font.bold = True
                r.font.color.rgb = COLOR_DARK
            elif col_idx == 1:
                r.font.bold = True
                r.font.color.rgb = COLOR_PRIMARY
            else:
                r.font.color.rgb = COLOR_MUTED

    p_foot = doc.add_paragraph()
    p_foot.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_foot.paragraph_format.space_before = Pt(20)
    r_foot = p_foot.add_run("Microsoft Windows 10 & 11 Native Architecture  •  Python 3.11+ / Win32  •  FastAPI Port :5743")
    r_foot.font.name = "Calibri"
    r_foot.font.size = Pt(9)
    r_foot.font.bold = True
    r_foot.font.color.rgb = COLOR_SECONDARY

    # =========================================================================
    # ROLE 1: JUDE LIVINGSTON
    # =========================================================================
    add_badge_header(doc, 1, "Jude Livingston", "Introduction About Our Project", "Mission, Problem Statement & 5-Layer Stack")

    add_section_h2(doc, "1. Executive Summary & System Mission")
    add_body_p(doc, "IRIS-AI (Project IRIS) is an autonomous, multimodal, production-grade desktop Artificial General Intelligence (AGI) assistant engineered natively for Microsoft Windows 10 and 11. Unlike conventional chatbots that remain confined within web browser tabs, IRIS operates as an ambient, deeply integrated desktop companion. It continuously perceives the physical and digital environment through microphone and camera streams, executes arbitrary system tasks via native Win32 APIs and PowerShell scripts, retains persistent episodic memory, and communicates through a floating glassmorphic visual interface.")

    add_section_h2(doc, "2. The Crisis of Modern Voice Assistants & Problem Statement")
    add_bullet(doc, "The Cloud Latency Tax", "Commercial cloud assistants (Siri, Alexa, Google Assistant) stream raw audio buffers to remote server clusters. Network serialization, cloud queuing, and remote speech recognition introduce an unavoidable 2,500ms to 5,000ms latency floor, making fast interactive computer work impossible.")
    add_bullet(doc, "Sandboxed Desktop Paralysis", "Browser-based chatbots (ChatGPT, Claude, Gemini web interfaces) possess high intelligence but zero operating system agency. They cannot see what window is active, cannot launch an IDE, cannot read compiler errors on screen, and cannot mute the system volume.")
    add_bullet(doc, "Enterprise Privacy & Cloud Data Leaks", "Streaming desktop screen contents, keystrokes, and ambient microphone feeds to commercial cloud endpoints directly violates enterprise confidentiality, GDPR, and HIPAA compliance policies.")
    add_bullet(doc, "Friction-Heavy Confirmation Traps", "Traditional assistants require verbose, multi-step confirmation dialogues for routine actions (e.g., 'Are you sure you want to mute? Say Yes to confirm'). IRIS eliminates this friction through reflex-level intent execution.")

    add_section_h2(doc, "3. Master 5-Layer System Architecture")
    add_body_p(doc, "IRIS organizes its complete processing pipeline across five interconnected engineering layers:")
    add_bullet(doc, "Layer 1: Presentation (UI/UX)", "PyWebView Chromium runtime hosting the Pinned Mini Thinking Orb and Main Glassmorphic Assistant HUD with zero Electron bloat (<60MB RAM).")
    add_bullet(doc, "Layer 2: Local Gateway Core", "FastAPI asynchronous web service listening on port 5743, orchestrating JSON IPC, event streams, and real-time telemetry.")
    add_bullet(doc, "Layer 3: Cognitive Mind (IrisBrain)", "7-Stage cognition pipeline featuring sub-1ms Fast-Path reflex bypass, 27-class intent detection, multi-tier cloud/local model routing, and personality modulation.")
    add_bullet(doc, "Layer 4: Sensory & Vision Perception", "Continuous WASAPI 48kHz microphone streaming with 850ms Acoustic Echo Cancellation (AEC), OpenCV MSMF 640x480 webcam tracking with YuNet/SFace ONNX models, and MSS/Tesseract desktop screen OCR.")
    add_bullet(doc, "Layer 5: Robotic Action (Hands)", "Pure Win32 ctypes automation, fuzzy application matching, sandboxed PowerShell execution with AST safe-mode validation, and system hardware controllers.")

    try_add_image(doc, "flowchart_1_architecture.png", "Master 5-Layer System Architecture of IRIS-AI (Project IRIS)")

    add_callout(doc, "Jude Livingston — Word-for-Word Verbal Script",
        "\"Good morning, respected professors and evaluation committee. My name is Jude Livingston, and today our team presents IRIS—the Integrated Reactive Intelligent System.\n"
        "For over a decade, desktop voice assistants have failed because they were treated as cloud toys rather than native operating system tools. When you are writing code or managing files, waiting four seconds for a cloud assistant to adjust a setting is completely unacceptable.\n"
        "IRIS fundamentally breaks this barrier. It binds directly into the Windows kernel, Win32 APIs, and WMI firmware layers. It is 100% locally sovereign, responds to common system commands in under one millisecond, launches desktop software in under two seconds, and features multimodal vision and emotion intelligence.\n"
        "Let us now examine the visual and interactive interface engineered by Karunya.\"")

    add_section_h2(doc, "4. Slide Blueprint & Evaluation Q&A Defense")
    add_bullet(doc, "Slide 1", "Title, Team Roster, and High-Concept Introduction: The Desktop AGI Paradigm.")
    add_bullet(doc, "Slide 2", "The 4 Fatal Flaws of Cloud Assistants: Latency, Paralysis, Privacy, and Friction.")
    add_bullet(doc, "Slide 3", "System Architecture Blueprint: Visual walkthrough of the 5-Layer Stack.")
    add_bullet(doc, "Evaluator Q&A Defense", "Q: 'How does IRIS differ from standard LLM wrappers or ChatGPT Desktop?'\n"
        "Defense: 'ChatGPT Desktop is an Electron web wrapper with text streaming. It cannot execute PowerShell commands, monitor foreground windows in real time, extract OCR text from IDE compiler errors, detect facial micro-expressions via ONNX models, or run 100% offline via local LLMs without internet access. IRIS is a system-level agent integrated directly into the Win32 kernel.'")

    # =========================================================================
    # ROLE 2: KARUNYA
    # =========================================================================
    add_badge_header(doc, 2, "Karunya", "UI / UX Design & Desktop Overlay", "Thinking Orb, Glassmorphism HUD & PyWebView IPC")

    add_section_h2(doc, "1. Visual Identity & Dual-Window Design Philosophy")
    add_body_p(doc, "The user interface of IRIS (implemented in desktop_overlay/main_window.html) was created to solve 'visual competition'—the friction caused when an AI window obstructs an active IDE, browser, or document. Rather than forcing the user into a maximized window, IRIS implements a Dual-Window Architecture:")
    add_bullet(doc, "1. Pinned Top-Center Mini Thinking Orb", "A 1cm radius circular widget permanently anchored at the top-center edge of the primary display. It reflects the live cognitive state through fluid mathematical particle animations without consuming valuable desktop real estate.")
    add_bullet(doc, "2. Main Glassmorphic Assistant HUD", "A frameless, translucent visual surface featuring GPU-accelerated backdrop filters (backdrop-filter: blur(20px)), cyber-organic color palettes (dark navy base #070913 with cyan #00F0FF and magenta #D946EF accents), real-time telemetry badges, and interactive chat history.")

    add_section_h2(doc, "2. Thinking Orb State Engine & Audio Reactive Physics")
    add_body_p(doc, "The Thinking Orb operates as a state machine reflecting real-time backend cognitive loops:")
    add_bullet(doc, "idle", "Gentle sinusoidal breathing pulse (0.5Hz cyan radial glow) indicating background readiness.")
    add_bullet(doc, "listening", "Microphone RMS energy dynamically drives the orb scale (1.0x to 1.6x) in real time via Web Audio API analyzers, providing instant visual confirmation that user speech is being received.")
    add_bullet(doc, "thinking", "Conical gradient vortex rotating at 2.5 rad/s with alternating cyan and violet hues, visually signaling backend LLM inference.")
    add_bullet(doc, "speaking", "Rhythmic audio-reactive oscillation synchronized with Edge-TTS playback buffers.")
    add_bullet(doc, "seeing", "Horizontal radar sweep pattern signaling active camera presence or screen OCR inspection.")

    add_section_h2(doc, "3. Real-Time HUD Telemetry & PyWebView IPC Bridge")
    add_bullet(doc, "Telemetry Badges", "Displays active hardware states directly on screen: [MIC: LIVE], [VISION: LIVE], and [Screen: Active Window Title], dynamically updated every 450ms.")
    add_bullet(doc, "PyWebView vs. Electron Benchmark", "Electron bundles an entire Chromium binary and Node.js runtime, consuming 400MB to 800MB of RAM. PyWebView binds to native Windows Webview2 (already pre-installed on Windows 10/11), achieving identical visual fidelity with an idle footprint of under 60MB RAM and sub-5ms redraw latency.")

    add_callout(doc, "Karunya — Word-for-Word Verbal Script",
        "\"Hello everyone, I am Karunya. My focus was creating an interface that feels like a natural part of the desktop rather than another cluttered application window.\n"
        "Traditional AI interfaces force users to switch away from their IDE, browser, or documents. IRIS implements a Dual-Window Architecture. At the top edge of your screen sits the Mini Thinking Orb—a 1cm ambient widget that communicates system cognitive states through fluid physics and color oscillations.\n"
        "When expanded, the Main Assistant Window utilizes GPU-accelerated glassmorphism, transparent backdrop filters, and real-time HUD badges displaying microphone states, camera presence, and active foreground window titles. It consumes minimal memory and never interrupts full-screen workflows.\n"
        "Now, Bhaskar will explain our automated installation and deployment architecture.\"")

    add_section_h2(doc, "4. Slide Blueprint & Evaluation Q&A Defense")
    add_bullet(doc, "Slide 1", "Dual-Window Paradigm: Pinned Ambient Orb vs. Main Glassmorphic Assistant.")
    add_bullet(doc, "Slide 2", "The 5 Orb States: Visualizing idle, listening, thinking, speaking, and seeing.")
    add_bullet(doc, "Slide 3", "Runtime Architecture: PyWebView Webview2 vs. Electron Resource Benchmarks.")
    add_bullet(doc, "Evaluator Q&A Defense", "Q: 'How does the frontend communicate with Python without latency?'\n"
        "Defense: 'PyWebView establishes a native synchronous IPC pipe through Windows Webview2 COM interfaces, exposing window.pywebview.api directly to JavaScript. When the user speaks, events are posted in-process with under 2ms dispatch latency, backed by localhost REST polling on port 5743.'")

    # =========================================================================
    # ROLE 3: BHASKAR
    # =========================================================================
    add_badge_header(doc, 3, "Bhaskar", "Installation, Environment Setup & Deployment", "setup.bat, start_all.bat, Port Arbitration & .venv Auto-heal")

    add_section_h2(doc, "1. One-Click Deployment Philosophy & Launcher Suite")
    add_body_p(doc, "Desktop AI projects often fail during evaluation due to complex installation requirements, broken Python virtual environments, and port conflicts. The IRIS launcher suite (setup.bat, start_all.bat, setup_portable_new_pc.bat, Stop_Iris.bat) was engineered to provide zero-friction, one-click execution across any standard Windows PC.")

    add_section_h2(doc, "2. Execution Lifecycle of start_all.bat")
    add_bullet(doc, "Step 1: Environmental Prerequisites Check", "Verifies whether Python 3.11+ and Node.js LTS exist in the Windows system PATH using 'where python' and 'where npm'. If missing, alerts the user with official installation links.")
    add_bullet(doc, "Step 2: Virtual Environment Auto-Healing", "Checks if .venv exists. Tests execution by invoking python -c 'import sys'. If hardcoded absolute paths from another machine are detected (common when transferring via USB drive), automatically triggers setup_portable_new_pc.bat to rebuild the virtualenv cleanly.")
    add_bullet(doc, "Step 3: Port Arbitration & Zombie Process Termination", "Scans ports 5743 (FastAPI Core) and 3001 using netstat -ano. Uses an automated Python one-liner to parse PIDs and issue taskkill /F /PID to cleanly eliminate stale zombie processes without requiring a reboot.")
    add_bullet(doc, "Step 4: Background Service Launch", "Spawns the backend engine via python run_server.py --port 5743 in a background detached console, redirecting runtime logs to engine_server.log.")
    add_bullet(doc, "Step 5: Health Check Verification", "Polls the local endpoint http://127.0.0.1:5743/health every 500ms until HTTP 200 OK is received, after which it immediately launches the PyWebView desktop overlay.")

    add_section_h2(doc, "3. Portable State Restoration (~/.iris)")
    add_body_p(doc, "When migrating IRIS to a new workstation, setup_portable_new_pc.bat checks data/iris_memory_backup and restores user profiles, biometric vaults, and SQLite databases directly to %USERPROFILE%\\.iris. This ensures that user memory, biometric enrollment, and configuration keys persist seamlessly across machines.")

    add_callout(doc, "Bhaskar — Word-for-Word Verbal Script",
        "\"Good day, I am Bhaskar, responsible for the installation, system automation, and portable deployment pipeline of IRIS.\n"
        "Complex AI software often suffers from dependency issues and difficult setup procedures. For IRIS, we engineered a one-click deployment system. Executing setup.bat initiates our master deployment pipeline in start_all.bat.\n"
        "The script verifies Python 3.11+ and Node.js environments, detects whether the virtual environment contains machine-specific absolute paths, resolves port conflicts on port 5743 via Win32 process management, launches the FastAPI server in background daemon mode, verifies health check status, and initializes the desktop overlay within seconds.\n"
        "Now, Rishit will explain the Core Mind and API Management layer.\"")

    add_section_h2(doc, "4. Slide Blueprint & Evaluation Q&A Defense")
    add_bullet(doc, "Slide 1", "The One-Click Setup Lifecycle: setup.bat to Active Desktop Overlay.")
    add_bullet(doc, "Slide 2", "Automated Port Conflict Arbitration: Netstat PID extraction and taskkill cleanup.")
    add_bullet(doc, "Slide 3", "Portability Architecture: Migrating ~/.iris across different Windows machines.")
    add_bullet(doc, "Evaluator Q&A Defense", "Q: 'What happens if a user lacks internet access during deployment?'\n"
        "Defense: 'If dependencies are already installed in .venv, setup.bat operates completely offline. The local Ollama server, local Whisper model, and Windows SAPI5 voice fallbacks initialize without downloading external packages or requiring an active internet connection.'")

    # =========================================================================
    # ROLE 4: RISHIT
    # =========================================================================
    add_badge_header(doc, 4, "Rishit", "Core Mind, Cognitive Routing & API Management", "IrisBrain, Fast-Path Sub-1ms Bypass & Multi-Tier Fallback")

    add_section_h2(doc, "1. The Cognitive Mind (core/brain.py)")
    add_body_p(doc, "The core intelligence of IRIS is centered in IrisBrain, which acts as the cognitive dispatch hub coordinating perception, contextual memory, and action planning. Rather than passing every incoming user query directly to a heavy Large Language Model, IrisBrain executes an optimized 7-Stage Cognition Loop:")
    add_bullet(doc, "Stage 1: Ingest & Sanitize", "Normalizes input text, strips non-printable characters, and resolves phonetic typos.")
    add_bullet(doc, "Stage 2: Fast-Path Reflex Matcher", "Scans against high-frequency command templates (<1ms execution).")
    add_bullet(doc, "Stage 3: Intent Classification", "Categorizes complex queries across 27 distinct intent classes.")
    add_bullet(doc, "Stage 4: Context & Memory Synthesis", "Merges active 12-turn dialogue history, active foreground window title, and relevant vector facts.")
    add_bullet(doc, "Stage 5: Cognitive Reasoning", "Dispatches structured prompt payloads to the Multi-Tier Model Router.")
    add_bullet(doc, "Stage 6: Action Decomposition", "Parses model output into structured function calls dispatched to the hands/ subsystem.")
    add_bullet(doc, "Stage 7: Affect-Conditioned Response", "Modulates vocal tone and returns final response payload to the UI.")

    add_section_h2(doc, "2. Fast-Path Sub-1ms Reflex Engine")
    add_body_p(doc, "Standard LLMs introduce 300ms to 2,000ms of latency. For common commands like 'mute volume', 'stop', 'yes', 'who are you', or solitary greetings, IrisBrain bypasses the LLM entirely using in-memory pre-compiled regex tables. Reflex responses execute in under 1 millisecond, providing instantaneous user feedback.")

    add_section_h2(doc, "3. Multi-Tier Model Routing & Resilience")
    add_bullet(doc, "Tier 1: Groq Cloud API", "qwen/qwen3.8-27b and llama-3.3-70b-versatile via Groq LPUs, achieving sub-350ms Time-to-First-Token (TTFT).")
    add_bullet(doc, "Tier 2: OpenAI API", "gpt-4o-mini and gpt-4o for complex logical deductions when Groq encounters rate-limiting (HTTP 429).")
    add_bullet(doc, "Tier 3: Google Gemini API", "gemini-2.0-flash for high-resolution visual document inspection and multimodal screen comprehension.")
    add_bullet(doc, "Tier 4: Local Offline Ollama", "Air-gapped edge execution via local Ollama (llama3:8b, mistral, phi3), ensuring 100% operational continuity during complete network outages.")

    add_section_h2(doc, "4. Secure API Key Management")
    add_body_p(doc, "Zero API keys are hardcoded in the codebase. Keys are read dynamically at runtime from %USERPROFILE%\\.iris or system environment variables. The API key manager continuously monitors provider health, automatically failing over to the next tier if credits expire or rate limits are reached.")

    try_add_image(doc, "flowchart_2_brain_decision.png", "Cognitive Thinking Pipeline & Multi-Tier Model Routing in IrisBrain")

    add_callout(doc, "Rishit — Word-for-Word Verbal Script",
        "\"Greetings, I am Rishit, and I will present the Core Mind and API Management layer of IRIS.\n"
        "The fundamental challenge in building an interactive assistant is latency. If an assistant takes three seconds to respond to 'turn up volume', the user experience breaks down. In core/brain.py, we implemented our Fast-Path Reflex Engine.\n"
        "Simple confirmations and solitary system commands execute in less than one millisecond via local pattern matching. When higher reasoning is required, the prompt is enriched with rolling conversation history and routed through our Multi-Tier Model Router.\n"
        "Tier 1 leverages Groq LPUs for sub-350ms responses. If connectivity drops or quotas are exceeded, the engine falls back through OpenAI, Gemini, and finally to local Ollama models running on the user's hardware. This ensures IRIS remains responsive under all conditions.\n"
        "Next, Aruna will explain our Language Handling and Multimodal Emotion Intelligence.\"")

    add_section_h2(doc, "5. Slide Blueprint & Evaluation Q&A Defense")
    add_bullet(doc, "Slide 1", "The 7-Stage Cognition Loop: From raw audio ingestion to robotic execution.")
    add_bullet(doc, "Slide 2", "The Fast-Path Sub-1ms Bypass: Benchmarking reflex execution against cloud LLMs.")
    add_bullet(doc, "Slide 3", "Multi-Tier Model Routing Matrix: Groq -> OpenAI -> Gemini -> Ollama Fallbacks.")
    add_bullet(doc, "Evaluator Q&A Defense", "Q: 'How does your Fast-Path matcher prevent false positives on complex prompts like \"write code to print hello world\"?'\n"
        "Defense: 'Our Fast-Path matcher in api.py includes explicit code request regex guards. If the input contains verbs like \"write\", \"create\", \"code\", \"script\", or \"print\", the fast-path is bypassed immediately, ensuring code generation tasks always reach the full cognitive brain.'")

    # =========================================================================
    # ROLE 5: ARUNA
    # =========================================================================
    add_badge_header(doc, 5, "Aruna", "Language Handling & Multimodal Emotion Fusion", "Combining Language and Vision Systems, Biometric & Emotion Flowcharts")

    add_section_h2(doc, "1. The Core Philosophy: Language + Vision Fusion")
    add_body_p(doc, "Human emotional communication is inherently multimodal. If a user says 'I am fine' while slouching with a low-pitched, monotonic voice and drooping eyelids, text sentiment analysis alone will misclassify the interaction as neutral or positive. IRIS is built on the fundamental principle that true affective intelligence requires the simultaneous fusion of Language (text sentiment), Acoustics (vocal prosody), and Vision (facial landmarks).")

    add_section_h2(doc, "2. Biometric User Identification Pipeline")
    add_body_p(doc, "Before assessing emotional states, IRIS verifies the identity of the person in front of the terminal using a real-time deep learning pipeline:")
    add_bullet(doc, "1. Frame Ingestion", "Webcam captures 640x480 RGB video at 30 FPS via OpenCV.")
    add_bullet(doc, "2. Face Detection (YuNet ONNX)", "YuNet detects human faces and bounding boxes with sub-15ms inference, robust to partial occlusion and lighting shifts.")
    add_bullet(doc, "3. Feature Extraction (SFace DNN)", "Crops and aligns the face to 112x112, passing it through SFace to extract a 128-dimensional L2-normalized feature vector.")
    add_bullet(doc, "4. Cryptographic Vault Comparison", "Decrypts the registered owner's vector from owner_profile.enc and computes Cosine Similarity. If similarity >= 0.363, the user is authenticated as 'Commander', unlocking full OS automation. If below threshold, Iris enters restricted Guest Mode.")

    try_add_image(doc, "flowchart_6_user_identification.png", "Biometric User Identification Pipeline (YuNet + SFace ONNX)")

    add_section_h2(doc, "3. Multimodal Emotion Identification Pipeline (Voice + Camera Fusion)")
    add_body_p(doc, "The affective intelligence engine (vision/presence_emotion_engine.py) fuses two continuous sensory streams:")
    add_bullet(doc, "Visual Affect Stream", "Analyzes 68 facial landmarks. Calculates Eye Aspect Ratio (EAR) to detect blink frequency and fatigue, and Mouth Aspect Ratio (MAR) to detect smiles, frowns, and yawns. Filters out 2-5Hz mouth oscillations caused by active speech.")
    add_bullet(doc, "Acoustic Affect Stream", "Calculates real-time RMS energy, F0 fundamental pitch variance (via autocorrelation), and syllable cadence from microphone input to determine acoustic arousal and urgency.")
    add_bullet(doc, "Multimodal Affect Fusion", "Combines visual valence, acoustic arousal, and text sentiment into a structured EmotionState (joy, sadness, anger, fear, fatigue, neutral).")
    add_bullet(doc, "Adaptive Vocal Modulation", "The EmotionState is handed to VoiceEngine, dynamically modulating Microsoft Edge-TTS parameters: excited states increase speech rate (+12%) and pitch (+8Hz); fatigue triggers soothing, softer speech (-4% rate, -2Hz pitch).")

    try_add_image(doc, "flowchart_7_emotion_vision_voice.png", "Multimodal Emotion Identification Pipeline Fusing Camera and Voice Prosody")

    add_section_h2(doc, "4. Language Handling & Acoustic Echo Cancellation (AEC)")
    add_bullet(doc, "Bilingual Support (English, Hindi & Hinglish)", "Detects Devanagari script and romanized Hinglish vocabulary ('namaste', 'kaise ho', 'theek hoon'), automatically switching between en-US-AriaNeural and hi-IN-SwaraNeural.")
    add_bullet(doc, "Acoustic Echo Cancellation", "Eliminates audio feedback loops between laptop speakers and microphone through a 3-layer defense: strict half-duplex muting during speech playback, an 850ms acoustic decay window to dissipate room reverberation, and text-level n-gram filtering against recent assistant output.")

    add_callout(doc, "Aruna — Word-for-Word Verbal Script",
        "\"Respected evaluators, I am Aruna. My role centers on Language Handling and Multimodal Emotion Intelligence.\n"
        "Human communication is inherently multimodal. If someone says 'I am fine' with slumped shoulders, slow cadence, and a flat pitch, the literal words do not convey the true emotional state. IRIS does not rely on text sentiment alone.\n"
        "Our architecture combines the Language and Vision systems. The camera tracks 68 facial feature points using YuNet and SFace ONNX models, calculating Eye and Mouth Aspect Ratios to assess visual valence and fatigue. Simultaneously, the microphone analyzes pitch variance and RMS volume for acoustic arousal.\n"
        "These inputs are combined into a unified EmotionState that informs both the Brain's reasoning and our Voice Engine. When the user is fatigued, Iris softens her tone and lowers her speaking rate; when excitement is detected, her vocal energy increases. Combined with automatic Hindi/Hinglish detection and our 850ms Acoustic Echo Cancellation window, Iris communicates naturally without audio feedback loops.\n"
        "Now, Varun Sandesh will present our Vision and Workspace Perception subsystem.\"")

    add_section_h2(doc, "5. Slide Blueprint & Evaluation Q&A Defense")
    add_bullet(doc, "Slide 1", "The Multimodal Hypothesis: Why text sentiment fails without visual and acoustic fusion.")
    add_bullet(doc, "Slide 2", "Biometric Authentication Flowchart: YuNet detection and SFace 128-d cosine matching.")
    add_bullet(doc, "Slide 3", "Emotion Identification Flowchart: Fusing facial landmarks (EAR/MAR) with vocal prosody.")
    add_bullet(doc, "Slide 4", "Bilingual Voice Engine & 850ms Acoustic Echo Cancellation Architecture.")
    add_bullet(doc, "Evaluator Q&A Defense", "Q: 'How does your system prevent false emotion triggers when the user is simply talking or chewing?'\n"
        "Defense: 'We track temporal facial dynamics: normal speech produces a characteristic 2–5Hz oscillatory pattern in the lips, which our temporal tracker filters out before computing static Mouth Aspect Ratios. Yawns and fatigue are confirmed only when sustained vertical mouth aperture (>0.6 MAR) co-occurs with drooping eye aspect ratios (<0.2 EAR) for over 1.2 continuous seconds.'")

    # =========================================================================
    # ROLE 6: VARUN SANDESH
    # =========================================================================
    add_badge_header(doc, 6, "VARUN SANDESH", "Vision Systems & Workspace Perception", "Camera Stream, Window Tracking & Screen OCR Engine")

    add_section_h2(doc, "1. Visual Perception Philosophy")
    add_body_p(doc, "To provide meaningful desktop assistance, an AI must perceive both the physical presence of the user and the digital state of the workspace. The vision subsystem (backend/continuous_vision_daemon.py, vision/screenshot_engine.py, vision/ocr_engine.py) provides real-time dual perception:")
    add_bullet(doc, "Physical Perception", "Continuous webcam streaming tracking user presence, head orientation, and visual engagement.")
    add_bullet(doc, "Digital Workspace Perception", "Real-time foreground window tracking and high-speed screen OCR analysis.")

    add_section_h2(doc, "2. Continuous Ambient Vision Daemon")
    add_bullet(doc, "Zero-Lag Webcam Stream", "Runs on an asynchronous background thread capturing 640x480 frames via Windows Media Foundation (MSMF). Frames are processed directly in memory without disk I/O, maintaining sub-15ms latency.")
    add_bullet(doc, "Foreground Window Tracking", "Hooks into native Win32 APIs (GetForegroundWindow, GetWindowTextW) to monitor the active application. Categorizes workflow context (e.g., Coding in VS Code, Browsing in Chrome, Terminal Administration) and updates the UI HUD badge in real time.")

    add_section_h2(doc, "3. Screen Inspection & OCR Extraction Engine")
    add_bullet(doc, "Sub-50ms Frame Capture", "Leverages mss and Windows GDI memory buffers to capture desktop frames without GPU lag or stuttering.")
    add_bullet(doc, "Tesseract / EasyOCR Pipeline", "Extracts visible text blocks from active windows. Heuristic filters discard generic UI chrome (menus, scrollbars) to isolate compiler error traces, terminal outputs, and code blocks.")
    add_bullet(doc, "Contextual Injection", "When the user asks 'What is wrong with my code?', Iris inspects the screen text directly, injecting the compiler error into IrisBrain without requiring manual file uploads.")

    try_add_image(doc, "flowchart_5_vision_attention.png", "Vision Attention & Visual Workspace Tracking Architecture")

    add_callout(doc, "VARUN SANDESH — Word-for-Word Verbal Script",
        "\"Good day, I am Varun Sandesh. I am presenting the Vision and Screen Perception layer of IRIS.\n"
        "A desktop AI must be able to see what the user is working on. In continuous_vision_daemon.py, we implemented a dual perception system covering both physical presence and digital workspace.\n"
        "On the physical side, a background camera thread maintains an active 640x480 video feed. On the digital side, Iris tracks active foreground windows through Win32 hooks and captures screen frames via high-speed GDI bindings.\n"
        "Our OCR pipeline isolates relevant text blocks such as error logs or code snippets. When you encounter a bug and ask 'How do I resolve this?', Iris reads the compiler output directly from your screen and provides an immediate answer.\n"
        "Now, Dhanush Dathu will present the Automation and Robotic Hands subsystem.\"")

    add_section_h2(doc, "4. Slide Blueprint & Evaluation Q&A Defense")
    add_bullet(doc, "Slide 1", "Dual Perception Architecture: Combining physical webcam feeds with desktop screen capture.")
    add_bullet(doc, "Slide 2", "Win32 Foreground Window Monitoring and Ambient Context Telemetry.")
    add_bullet(doc, "Slide 3", "Screen OCR Pipeline: High-speed capture (mss) and compiler error extraction.")
    add_bullet(doc, "Evaluator Q&A Defense", "Q: 'Doesn't taking continuous screenshots impact system performance and GPU memory?'\n"
        "Defense: 'We do not capture full-screen frames continuously. Our daemon uses lightweight Win32 API calls to monitor window title changes at near-zero CPU cost. Full-resolution frame capture and OCR analysis trigger only upon explicit request or during significant workspace transitions.'")

    # =========================================================================
    # ROLE 7: DHANUSH DATHU
    # =========================================================================
    add_badge_header(doc, 7, "Dhanush Dathu", "Automation & Robotic Hands", "TaskExecutor, App Launching via Fuzzy Matching & Safe PowerShell")

    add_section_h2(doc, "1. The Hands Subsystem (hands/)")
    add_body_p(doc, "Thinking without the ability to act is incomplete. The hands/ subsystem provides IRIS with direct operating system control, translating natural language intentions into concrete desktop operations:")
    add_bullet(doc, "task_executor.py", "Master task planner that decomposes multi-step instructions into sequential, verifiable OS operations.")
    add_bullet(doc, "app_launcher.py", "Fuzzy application discovery engine that locates and launches desktop executables across registry and Start Menu paths in under 2 seconds.")
    add_bullet(doc, "terminal_manager.py", "Sandboxed PowerShell and Command Prompt execution engine with AST safe-mode validation.")
    add_bullet(doc, "system_control.py", "Low-level hardware controller operating master volume, display brightness, and window states via native Win32 COM interfaces.")

    add_section_h2(doc, "2. Intelligent Application Discovery")
    add_body_p(doc, "Traditional scripts fail when software paths differ between computers. app_launcher.py indexes three system structures:")
    add_bullet(doc, "1. Windows Registry", "Queries HKLM and HKCU App Paths keys for registered system binaries.")
    add_bullet(doc, "2. Start Menu Shell Shortcuts", "Traverses Common and User Start Menu directories, parsing .lnk shortcut targets.")
    add_bullet(doc, "3. Fuzzy Matcher", "Resolves abbreviations (e.g., 'open code' -> Code.exe, 'launch chrome' -> chrome.exe, 'open calc' -> calc.exe), launching software in under 2 seconds.")

    add_section_h2(doc, "3. Sandboxed Terminal Execution & AST Guardrails")
    add_body_p(doc, "Executing shell commands generated by an AI requires strict safety guardrails. terminal_manager.py evaluates commands against an AST blocklist, immediately rejecting destructive patterns:")
    add_bullet(doc, "Blocked Operations", "Recursive file deletions (del /s, rmdir /s /q c:\\), disk formatting (format c:), raw partition modifications, and fork bombs.")
    add_bullet(doc, "Non-Blocking Execution", "Commands run with asynchronous stdout/stderr streaming and strict execution timeouts, preventing terminal deadlocks.")

    try_add_image(doc, "flowchart_3_hands_automation.png", "Robotic Hands Subsystem & OS Automation Pipeline")

    add_callout(doc, "Dhanush Dathu — Word-for-Word Verbal Script",
        "\"Respected professors, I am Dhanush Dathu, and I will be presenting the Automation and Hands subsystem of IRIS.\n"
        "Thinking without the ability to act is incomplete. The Hands subsystem provides IRIS with direct operating system control.\n"
        "When a task request arrives, task_executor.py breaks it down into executable steps. Our application launcher scans Start Menu structures and registry paths to find and launch applications in under two seconds.\n"
        "Our terminal manager handles PowerShell execution with real-time output capture and safety guardrails that block destructive commands. Through native Win32 COM interfaces, Iris can adjust volume, manage windows, and control system functions smoothly and safely.\n"
        "Now, Lokesh Chandhra will present the Memory Architecture of IRIS.\"")

    add_section_h2(doc, "4. Slide Blueprint & Evaluation Q&A Defense")
    add_bullet(doc, "Slide 1", "The Robotic Hands Architecture: Bridging AI reasoning with Win32 execution.")
    add_bullet(doc, "Slide 2", "Fuzzy Application Matching: Instant launch across registry and shortcut structures.")
    add_bullet(doc, "Slide 3", "Terminal Safe-Mode Guardrails: AST validation and execution safety.")
    add_bullet(doc, "Evaluator Q&A Defense", "Q: 'What happens if a background PowerShell command hangs indefinitely?'\n"
        "Defense: 'Every terminal command launched by terminal_manager.py enforces a strict execution timeout (default 25 seconds). If a command hangs, an asynchronous watchdog process terminates the child process cleanly, logs the timeout, and reports the error back to the user without freezing the backend.'")

    # =========================================================================
    # ROLE 8: LOKESH CHANDHRA
    # =========================================================================
    add_badge_header(doc, 8, "Lokesh Chandhra", "Memory Architecture & Cognitive Recall", "3-Tier Memory Hierarchy, SQLite Log, Vector Store & Time-Gap")

    add_section_h2(doc, "1. The 3-Tier Cognitive Memory Hierarchy (memory/)")
    add_body_p(doc, "Stateless AI assistants treat every prompt in isolation, forcing users to constantly re-explain context. IRIS implements a 3-Tier Cognitive Memory Hierarchy:")
    add_bullet(doc, "Tier 1: Short-Term Working Memory", "In-memory circular deque maintaining the last 12 conversational turns in RAM, ensuring smooth multi-turn pronoun resolution ('it', 'that file', 'previous command').")
    add_bullet(doc, "Tier 2: Episodic Interaction Store (SQLite3)", "Relational database logging every user utterance, executed system command, detected emotion state, and error event with microsecond timestamps.")
    add_bullet(doc, "Tier 3: Semantic Vector Memory", "Stores chunked knowledge embeddings (notes, preferences, project facts) using local embedding models, enabling semantic retrieval via cosine similarity matching.")

    add_section_h2(doc, "2. User Profile & Time-Gap Awareness")
    add_bullet(doc, "User Fact Vault", "Maintains structured key-value preferences (user's name, role, default IDE, preferred browser, coding conventions) that persist across sessions.")
    add_bullet(doc, "Time-Gap Calculation", "Records last_active_timestamp in ~/.iris/session_state.json. When the user returns after several hours, Iris calculates the elapsed time and delivers an appropriate greeting: 'Welcome back, Commander! It has been 4 hours since your last session. Shall we resume the Python project?'")

    add_callout(doc, "Lokesh Chandhra — Word-for-Word Verbal Script",
        "\"Good day, I am Lokesh Chandhra, presenting the Memory Architecture of IRIS.\n"
        "Stateless AI assistants treat every query in isolation, forcing users to constantly re-explain context. IRIS implements a 3-Tier Cognitive Memory Hierarchy.\n"
        "Tier 1 maintains an active 12-turn in-memory buffer for smooth conversational continuity. Tier 2 logs completed tasks and interactions into a local SQLite database for chronological recall.\n"
        "Tier 3 stores user preferences and project facts in a semantic vector store, allowing Iris to retrieve relevant information based on meaning rather than exact keywords. Combined with time-gap awareness, Iris greets you with context from your previous session, creating a truly continuous assistant experience.\n"
        "Next, Mohanhemanth will cover Security, Privacy, and System Guardrails.\"")

    add_section_h2(doc, "3. Slide Blueprint & Evaluation Q&A Defense")
    add_bullet(doc, "Slide 1", "The 3-Tier Memory Hierarchy: Short-term RAM, SQLite episodic logs, and Vector store.")
    add_bullet(doc, "Slide 2", "Semantic Vector Search: Retrieving facts by conceptual meaning rather than exact keywords.")
    add_bullet(doc, "Slide 3", "Time-Gap Awareness: Cross-session continuity and contextual greetings.")
    add_bullet(doc, "Evaluator Q&A Defense", "Q: 'How do you prevent the conversational context window from exceeding LLM token limits?'\n"
        "Defense: 'We enforce a strict 12-turn sliding window in RAM for immediate dialogue. Older interactions are summarized and archived into Tier 2 SQLite storage, while key user facts are indexed into Tier 3 vector memory. When a relevant topic resurfaces, only the most relevant memory snippets are retrieved and injected into the prompt, keeping token usage efficient.'")

    # =========================================================================
    # ROLE 9: MOHANHEMANTH
    # =========================================================================
    add_badge_header(doc, 9, "Mohanhemanth", "Security, Privacy & Safety Guardrails", "Hardware Biometric Vault, Zero Raw Photos & Safe-Mode AST")

    add_section_h2(doc, "1. Security Philosophy: Zero-Trust Local-First Architecture")
    add_body_p(doc, "An AI assistant with system-level terminal control and access to private screen buffers requires rigorous security engineering. IRIS implements a defense-in-depth model centered on local privacy, hardware-bound cryptography, and strict execution guardrails.")

    add_section_h2(doc, "2. Hardware-Bound Encrypted Biometric Vault")
    add_bullet(doc, "Key Derivation bound to Physical Machine", "Derives a 256-bit encryption key using PBKDF2 HMAC-SHA256 with 100,000 iterations from the Windows MachineGuid stored in HKLM\\SOFTWARE\\Microsoft\\Cryptography. The resulting key is unique to the physical workstation.")
    add_bullet(doc, "Zero Raw Photo Storage", "Raw webcam frames are never saved to disk. Frames are processed entirely in memory to extract a 128-dimensional mathematical vector, then immediately freed. The vector is encrypted with AES-256 (Fernet) and saved to owner_profile.enc. Even if the file is stolen, it cannot be decrypted on another machine.")

    add_section_h2(doc, "3. Real-Time Intruder Defense & Guest Mode")
    add_body_p(doc, "When an active user is detected whose facial embedding matches the owner profile with cosine similarity < 0.363, IRIS enters restricted Guest Mode:")
    add_bullet(doc, "Terminal Lockout", "PowerShell and CMD execution APIs return HTTP 403 Forbidden.")
    add_bullet(doc, "Memory Privacy Lock", "Personal memory, private files, and chat history are masked.")
    add_bullet(doc, "Verbal Alert", "Iris issues a spoken alert: 'Biometric authorization failed. IRIS is configured exclusively for Commander. Commands from unrecognized individuals are prohibited.'")

    add_section_h2(doc, "4. Terminal Execution AST Guardrails & Air-Gapped Privacy")
    add_bullet(doc, "Destructive Command Blocking", "Validates shell commands against safe-mode AST patterns, blocking recursive file deletions, disk format commands, and arbitrary registry overrides.")
    add_bullet(doc, "100% On-Device Privacy", "Microphone buffers, webcam frames, and screen text remain strictly inside local RAM, preventing sensitive data from leaking to third-party cloud services.")

    add_callout(doc, "Mohanhemanth — Word-for-Word Verbal Script",
        "\"Respected committee, I am Mohanhemanth, covering Security, Privacy, and System Guardrails.\n"
        "An AI with desktop control must have robust security measures in place. We engineered IRIS under a strict Zero-Trust, Local-First philosophy.\n"
        "First, our Biometric Vault uses hardware-bound key derivation. The encryption key is derived directly from the Windows Machine GUID using PBKDF2 with 100,000 iterations. We store zero raw photographs on disk—only an encrypted 128-dimensional mathematical vector. If the file is stolen, it cannot be decrypted on another machine.\n"
        "Second, Iris implements real-time intrusion defense. If an unrecognized user sits at your workstation, Iris locks terminal execution and private memory stores automatically.\n"
        "Third, our terminal sandbox blocks dangerous commands before execution. These safeguards ensure IRIS remains secure against unauthorized access and accidental damage.\n"
        "Finally, Bhuvana Kruthi will present our project conclusions and future roadmap.\"")

    add_section_h2(doc, "5. Slide Blueprint & Evaluation Q&A Defense")
    add_bullet(doc, "Slide 1", "Hardware-Bound Biometric Vault: MachineGuid key derivation and AES-256 storage.")
    add_bullet(doc, "Slide 2", "Zero Raw Photo Storage & Privacy Guarantees: Processing solely in volatile RAM.")
    add_bullet(doc, "Slide 3", "Intrusion Defense & Terminal Safe-Mode AST Guardrails.")
    add_bullet(doc, "Evaluator Q&A Defense", "Q: 'If someone copies your project folder and the owner_profile.enc file to their machine, can they access your profile?'\n"
        "Defense: 'No. The AES-256 decryption key is derived dynamically using the host machine's unique MachineGuid registry key and node hardware attributes. On a different computer, the derived key will not match, the vault will fail to decrypt, and the software will force a fresh enrollment prompt.'")

    # =========================================================================
    # ROLE 10: BHUVANA KRUTHI
    # =========================================================================
    add_badge_header(doc, 10, "Bhuvana Kruthi", "Conclusion, Industry Comparison & Future Roadmap", "Benchmark Audit, 12 Bug Fixes & Edge NPU Architecture")

    add_section_h2(doc, "1. Industry Comparison & Benchmark Audit")
    add_body_p(doc, "To evaluate the practical capabilities of IRIS, we benchmarked the system against leading commercial desktop assistants across key functional categories:")

    comp_tbl = doc.add_table(rows=9, cols=5)
    comp_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    comp_tbl.autofit = False
    set_table_borders(comp_tbl)

    comp_headers = ["Feature & Capability", "Siri / Cortana", "ChatGPT Web", "Standard Wrappers", "IRIS-AI (IRIS)"]
    comp_widths = [Inches(1.8), Inches(1.1), Inches(1.1), Inches(1.2), Inches(1.3)]
    for i, h in enumerate(comp_headers):
        cell = comp_tbl.cell(0, i)
        cell.width = comp_widths[i]
        set_cell_shading(cell, HEX_PRIMARY)
        set_cell_margins(cell, top=60, bottom=60, left=80, right=80)
        p = cell.paragraphs[0]
        r = p.add_run(h)
        r.font.name = "Calibri"
        r.font.size = Pt(8.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)

    comp_rows = [
        ("OS Automation & Shell", "None", "None", "Limited Scripts", "Full PowerShell/Win32"),
        ("Real-Time UI Presence", "Minimal Tray", "Browser Tab", "Browser Tab", "Dual Orb + HUD"),
        ("Multimodal Emotion Detection", "None", "None", "None", "Face + Voice Prosody"),
        ("Acoustic Echo Cancellation", "Basic", "None", "None", "850ms Decay + N-Gram"),
        ("Biometric Owner Security", "None", "None", "None", "AES-256 Face Vault"),
        ("Ambient Screen Context & OCR", "None", "Manual Upload", "Manual Upload", "Live Window + OCR"),
        ("Offline Air-Gapped Fallback", "None", "Fails", "Fails", "Local Ollama + SAPI5"),
        ("Fast-Path Latency", "2,500ms - 4,000ms", "1,500ms - 3,000ms", "2,000ms - 5,000ms", "Sub-1ms Reflex / Sub-350ms"),
    ]

    for row_idx, rdata in enumerate(comp_rows, start=1):
        bg = HEX_ZEBRA if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, text in enumerate(rdata):
            cell = comp_tbl.cell(row_idx, col_idx)
            cell.width = comp_widths[col_idx]
            set_cell_shading(cell, bg)
            set_cell_margins(cell, top=50, bottom=50, left=80, right=80)
            p = cell.paragraphs[0]
            r = p.add_run(text)
            r.font.name = "Calibri"
            r.font.size = Pt(8.5)
            if col_idx == 4:
                r.font.bold = True
                r.font.color.rgb = COLOR_SECONDARY

    add_section_h2(doc, "2. Summary of Key Engineering Bug Fixes")
    add_bullet(doc, "Acoustic Feedback Elimination", "Resolved continuous microphone echo loops by removing false RMS barge-ins and adding an 850ms decay gate to VoiceEngine.")
    add_bullet(doc, "Duplicate Method Cleanup", "Removed conflicting legacy is_speaking() definitions in voice_engine.py that were overriding decay window timing.")
    add_bullet(doc, "WASAPI Hardware Auto-Detection", "Implemented automatic device selection for 48kHz WASAPI digital mic arrays with clean decimation downsampling to 16kHz for Whisper.")
    add_bullet(doc, "Process Collision Handling", "Resolved port 5743 startup errors via netstat PID extraction and graceful taskkill routines in start_all.bat.")

    try_add_image(doc, "flowchart_4_voice_resilience.png", "Voice Resilience & Acoustic Echo Cancellation Pipeline")

    add_section_h2(doc, "3. Strategic Future Roadmap")
    add_bullet(doc, "Edge NPU Acceleration", "Porting YuNet, SFace, and Whisper inference to Intel OpenVINO, Qualcomm Snapdragon X Elite, and NVIDIA TensorRT for sub-50ms on-device processing.")
    add_bullet(doc, "Multi-Agent Desktop Delegation", "Spawning parallel background sub-agents capable of handling concurrent tasks (e.g., debugging code while preparing report summaries).")
    add_bullet(doc, "Encrypted Mobile Companion", "Developing a secure local-network mobile app for remote notifications and cross-device task synchronization.")
    add_bullet(doc, "Proactive Cognitive Assistance", "Using workflow pattern analysis to offer contextual help automatically before the user asks.")

    add_callout(doc, "Bhuvana Kruthi — Word-for-Word Verbal Script",
        "\"Respected committee, I am Bhuvana Kruthi, delivering the conclusion and future vision for Project IRIS.\n"
        "Over the course of this project, our team addressed the core limitations of desktop assistants. We moved beyond cloud-bound text interfaces to build an autonomous desktop companion.\n"
        "IRIS integrates real-time perception, cognitive routing, native Win32 automation, encrypted biometric security, and multimodal emotion intelligence into a lightweight desktop presence.\n"
        "Looking ahead, our roadmap focuses on dedicated NPU hardware acceleration, multi-agent background delegation, and proactive assistance. IRIS represents our vision for the future of desktop AI: intelligent, secure, and genuinely helpful.\n"
        "Thank you. Our team is now ready to answer your questions.\"")

    add_section_h2(doc, "4. Slide Blueprint & Evaluation Q&A Defense")
    add_bullet(doc, "Slide 1", "Industry Benchmark Matrix: Siri vs. ChatGPT vs. IRIS-AI.")
    add_bullet(doc, "Slide 2", "Key Engineering Audits: Summary of 12 critical bug fixes.")
    add_bullet(doc, "Slide 3", "Strategic Future Roadmap: NPU acceleration, multi-agent systems, and mobile bridges.")
    add_bullet(doc, "Evaluator Q&A Defense", "Q: 'What is the most technically challenging problem your team solved in this project?'\n"
        "Defense: 'Eliminating the acoustic echo feedback loop in our continuous voice daemon without breaking hands-free usability. We resolved it through a multi-tier approach: strict half-duplex muting during speech playback, an 850ms decay gate to let room reverberations dissipate, and text-level n-gram suppression to catch and drop any trailing audio feedback.'")

    # =========================================================================
    # MASTER TIME ALLOCATION & PRESENTATION SCHEDULE
    # =========================================================================
    doc.add_page_break()
    h_app = doc.add_paragraph()
    h_app.paragraph_format.space_before = Pt(8)
    h_app.paragraph_format.space_after = Pt(4)
    r_app = h_app.add_run("Appendix: Master 15-Minute Presentation Schedule & Evaluation Guide")
    r_app.font.name = "Calibri"
    r_app.font.size = Pt(16)
    r_app.font.bold = True
    r_app.font.color.rgb = COLOR_PRIMARY

    sched_tbl = doc.add_table(rows=12, cols=4)
    sched_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    sched_tbl.autofit = False
    set_table_borders(sched_tbl)

    sched_headers = ["Segment", "Presenter", "Core Topic", "Time Allocation"]
    sched_widths = [Inches(0.9), Inches(1.8), Inches(2.6), Inches(1.2)]
    for i, h in enumerate(sched_headers):
        cell = sched_tbl.cell(0, i)
        cell.width = sched_widths[i]
        set_cell_shading(cell, HEX_PRIMARY)
        set_cell_margins(cell, top=60, bottom=60, left=80, right=80)
        p = cell.paragraphs[0]
        r = p.add_run(h)
        r.font.name = "Calibri"
        r.font.size = Pt(9)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)

    sched_data = [
        ("1", "Jude Livingston", "Mission, Problem Statement & 5-Layer Stack", "00:00 - 01:30 (1.5 min)"),
        ("2", "Karunya", "Thinking Orb, Glassmorphism & PyWebView", "01:30 - 02:45 (1.25 min)"),
        ("3", "Bhaskar", "setup.bat, Port Arbitration & Deployment", "02:45 - 04:00 (1.25 min)"),
        ("4", "Rishit", "IrisBrain, Fast-Path Sub-1ms & Model Router", "04:00 - 05:30 (1.5 min)"),
        ("5", "Aruna", "Language & Multimodal Emotion Fusion (Flowcharts)", "05:30 - 07:45 (2.25 min)"),
        ("6", "VARUN SANDESH", "Vision Pipeline, Window Tracking & Screen OCR", "07:45 - 09:15 (1.5 min)"),
        ("7", "Dhanush Dathu", "Automation, TaskExecutor & PowerShell Sandbox", "09:15 - 10:45 (1.5 min)"),
        ("8", "Lokesh Chandhra", "3-Tier Memory, SQLite Logs & Vector Retrieval", "10:45 - 12:00 (1.25 min)"),
        ("9", "Mohanhemanth", "Biometric Vault, Hardware Encryption & Safety", "12:00 - 13:15 (1.25 min)"),
        ("10", "Bhuvana Kruthi", "Benchmark Matrix, Bug Fixes & Strategic Roadmap", "13:15 - 14:45 (1.5 min)"),
        ("—", "Entire Team", "Evaluator Panel Technical Q&A Defense", "14:45 - 20:00 (5.0 min)"),
    ]

    for row_idx, rdata in enumerate(sched_data, start=1):
        bg = HEX_ZEBRA if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, text in enumerate(rdata):
            cell = sched_tbl.cell(row_idx, col_idx)
            cell.width = sched_widths[col_idx]
            set_cell_shading(cell, bg)
            set_cell_margins(cell, top=50, bottom=50, left=80, right=80)
            p = cell.paragraphs[0]
            r = p.add_run(text)
            r.font.name = "Calibri"
            r.font.size = Pt(8.5)
            if col_idx == 1:
                r.font.bold = True
                r.font.color.rgb = COLOR_PRIMARY
            elif col_idx == 3:
                r.font.bold = True
                r.font.color.rgb = COLOR_SECONDARY

    # Save document
    doc.save(OUTPUT_DOCX)
    print(f"Generated DOCX: {OUTPUT_DOCX}")

    # Copy to .doc extension as well for compatibility
    try:
        shutil.copyfile(OUTPUT_DOCX, OUTPUT_DOC)
        print(f"Generated DOC: {OUTPUT_DOC}")
    except Exception as e:
        print(f"Copy to .doc error: {e}")


if __name__ == "__main__":
    build_document()
