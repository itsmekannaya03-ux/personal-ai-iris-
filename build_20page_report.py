import os
import sys
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

OUTPUT_DOCX_1 = r"C:\Users\itsme\Desktop\IRIS-AI\IRIS_AI_Project_Report.docx"
OUTPUT_DOCX_2 = r"C:\Users\itsme\Desktop\IRIS_AI_Project_Report.docx"
ASSETS_DIR = r"C:\Users\itsme\Desktop\IRIS-AI\report_assets"

COLOR_PRIMARY = RGBColor(15, 23, 42)      # Deep Slate #0F172A
COLOR_SECONDARY = RGBColor(14, 116, 144)  # Deep Cyan #0E7490
COLOR_DARK = RGBColor(30, 41, 59)         # Dark Neutral #1E293B
COLOR_MUTED = RGBColor(100, 116, 139)     # Muted Slate #64748B
COLOR_HIGHLIGHT = RGBColor(3, 105, 161)   # Accent Blue #0369A1

HEX_PRIMARY = "0F172A"
HEX_SECONDARY = "0E7490"
HEX_LIGHT_BG = "F8FAFC"
HEX_BORDER = "CBD5E1"
HEX_ZEBRA = "F1F5F9"


def set_cell_shading(cell, color_hex):
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shd)


def set_cell_margins(cell, top=45, bottom=45, left=65, right=65):
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


def add_custom_heading(doc, text, level=1, presenter=None):
    if presenter:
        p_badge = doc.add_paragraph()
        p_badge.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p_badge.paragraph_format.space_before = Pt(0)
        p_badge.paragraph_format.space_after = Pt(1)
        p_badge.paragraph_format.keep_with_next = True
        r_b = p_badge.add_run(f"SEMINAR PRESENTATION  |  {presenter}")
        r_b.font.name = "Calibri"
        r_b.font.size = Pt(7.5)
        r_b.bold = True
        r_b.font.color.rgb = COLOR_SECONDARY

    p = doc.add_paragraph()
    p.paragraph_format.keep_with_next = True
    if level == 1:
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(2)
        run = p.add_run(text)
        run.font.name = "Calibri"
        run.font.size = Pt(12.5)
        run.bold = True
        run.font.color.rgb = COLOR_PRIMARY
    elif level == 2:
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(1.5)
        run = p.add_run(text)
        run.font.name = "Calibri"
        run.font.size = Pt(10)
        run.bold = True
        run.font.color.rgb = COLOR_SECONDARY
    elif level == 3:
        p.paragraph_format.space_before = Pt(2.5)
        p.paragraph_format.space_after = Pt(1)
        run = p.add_run(text)
        run.font.name = "Calibri"
        run.font.size = Pt(9)
        run.bold = True
        run.font.color.rgb = COLOR_DARK
    return p


def add_body_p(doc, text, bold_prefix=None, space_after=2.5):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.10
    if bold_prefix:
        r_pre = p.add_run(bold_prefix + " ")
        r_pre.bold = True
        r_pre.font.name = "Calibri"
        r_pre.font.size = Pt(8.5)
        r_pre.font.color.rgb = COLOR_PRIMARY
    r_body = p.add_run(text)
    r_body.font.name = "Calibri"
    r_body.font.size = Pt(8.5)
    r_body.font.color.rgb = COLOR_DARK
    return p


def add_bullet(doc, text, bold_prefix=None, space_after=1.2):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.08
    if bold_prefix:
        r_pre = p.add_run(bold_prefix + ": ")
        r_pre.bold = True
        r_pre.font.name = "Calibri"
        r_pre.font.size = Pt(8.0)
        r_pre.font.color.rgb = COLOR_PRIMARY
    r_body = p.add_run(text)
    r_body.font.name = "Calibri"
    r_body.font.size = Pt(8.0)
    r_body.font.color.rgb = COLOR_DARK
    return p


def add_flow_box(doc, steps):
    tbl = doc.add_table(rows=1, cols=len(steps) * 2 - 1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    col_idx = 0
    for i, step in enumerate(steps):
        cell = tbl.cell(0, col_idx)
        cell.text = step
        set_cell_shading(cell, HEX_PRIMARY)
        set_cell_margins(cell, top=30, bottom=30, left=45, right=45)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        r = p.runs[0]
        r.font.name = "Calibri"
        r.font.size = Pt(7.0)
        r.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)
        
        tcPr = cell._tc.get_or_add_tcPr()
        bdr = parse_xml(f'<w:tcBorders {nsdecls("w")}><w:top w:val="none"/><w:left w:val="none"/><w:right w:val="none"/><w:bottom w:val="none"/></w:tcBorders>')
        tcPr.append(bdr)
        
        col_idx += 1
        if i < len(steps) - 1:
            arr_cell = tbl.cell(0, col_idx)
            arr_cell.text = "➔"
            set_cell_shading(arr_cell, "FFFFFF")
            set_cell_margins(arr_cell, top=30, bottom=30, left=15, right=15)
            p_a = arr_cell.paragraphs[0]
            p_a.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_a.paragraph_format.space_before = Pt(0)
            p_a.paragraph_format.space_after = Pt(0)
            r_a = p_a.runs[0]
            r_a.font.name = "Calibri"
            r_a.font.size = Pt(7.5)
            r_a.bold = True
            r_a.font.color.rgb = COLOR_SECONDARY
            
            tcPr_a = arr_cell._tc.get_or_add_tcPr()
            bdr_a = parse_xml(f'<w:tcBorders {nsdecls("w")}><w:top w:val="none"/><w:left w:val="none"/><w:right w:val="none"/><w:bottom w:val="none"/></w:tcBorders>')
            tcPr_a.append(bdr_a)
            col_idx += 1
            
    p_sp = doc.add_paragraph()
    p_sp.paragraph_format.space_before = Pt(0)
    p_sp.paragraph_format.space_after = Pt(1.5)


def add_callout(doc, title, text):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_shading(cell, HEX_LIGHT_BG)
    set_cell_margins(cell, top=45, bottom=45, left=80, right=80)
    
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = parse_xml(f'<w:tcBorders {nsdecls("w")}><w:left w:val="single" w:sz="18" w:space="0" w:color="{HEX_SECONDARY}"/><w:top w:val="none"/><w:right w:val="none"/><w:bottom w:val="none"/></w:tcBorders>')
    tcPr.append(tcBorders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(1)
    r_t = p.add_run(f"★ {title}\n")
    r_t.font.name = "Calibri"
    r_t.font.size = Pt(8.5)
    r_t.bold = True
    r_t.font.color.rgb = COLOR_PRIMARY
    
    r_c = p.add_run(text)
    r_c.font.name = "Calibri"
    r_c.font.size = Pt(7.5)
    r_c.italic = True
    r_c.font.color.rgb = COLOR_DARK
    
    p_sp = doc.add_paragraph()
    p_sp.paragraph_format.space_before = Pt(0)
    p_sp.paragraph_format.space_after = Pt(1.5)


def style_table(table, col_widths, headers, data, font_size=7.5):
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr_cells = table.rows[0].cells
    for i, title in enumerate(headers):
        hdr_cells[i].text = title
        set_cell_shading(hdr_cells[i], HEX_PRIMARY)
        set_cell_margins(hdr_cells[i], top=40, bottom=40, left=50, right=50)
        p = hdr_cells[i].paragraphs[0]
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        for r in p.runs:
            r.font.name = "Calibri"
            r.font.size = Pt(font_size + 0.5)
            r.bold = True
            r.font.color.rgb = RGBColor(255, 255, 255)
            
    for r_idx, row_data in enumerate(data):
        row_cells = table.rows[r_idx + 1].cells
        bg_hex = HEX_ZEBRA if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, cell_value in enumerate(row_data):
            row_cells[c_idx].text = str(cell_value)
            set_cell_shading(row_cells[c_idx], bg_hex)
            set_cell_margins(row_cells[c_idx], top=30, bottom=30, left=50, right=50)
            p = row_cells[c_idx].paragraphs[0]
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            for r in p.runs:
                r.font.name = "Calibri"
                r.font.size = Pt(font_size)
                r.font.color.rgb = COLOR_DARK

    for row in table.rows:
        for idx, width in enumerate(col_widths):
            row.cells[idx].width = width
            tcPr = row.cells[idx]._tc.get_or_add_tcPr()
            tcBorders = parse_xml(f'<w:tcBorders {nsdecls("w")}><w:top w:val="single" w:sz="4" w:space="0" w:color="{HEX_BORDER}"/><w:bottom w:val="single" w:sz="4" w:space="0" w:color="{HEX_BORDER}"/><w:left w:val="none"/><w:right w:val="none"/></w:tcBorders>')
            tcPr.append(tcBorders)


def add_figure_img(doc, img_name, caption, width_in=4.6):
    img_path = os.path.join(ASSETS_DIR, img_name)
    if os.path.exists(img_path):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(3)
        p_img.paragraph_format.space_after = Pt(1)
        p_img.paragraph_format.keep_with_next = True
        run_img = p_img.add_run()
        run_img.add_picture(img_path, width=Inches(width_in))
        
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_before = Pt(1)
        p_cap.paragraph_format.space_after = Pt(3)
        run_cap = p_cap.add_run(caption)
        run_cap.font.name = "Calibri"
        run_cap.font.size = Pt(7.5)
        run_cap.bold = True
        run_cap.font.color.rgb = COLOR_PRIMARY


def build_full_project_dossier():
    print("Building exact 20-page full-fidelity project dossier matching 1.pdf structure...")
    doc = Document()

    # Standard A4 Setup with tight margins for 20-page fit
    for section in doc.sections:
        section.page_width = Inches(8.27)
        section.page_height = Inches(11.69)
        section.top_margin = Inches(0.60)
        section.bottom_margin = Inches(0.60)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)
        section.header.is_linked_to_previous = False
        section.footer.is_linked_to_previous = False
        
        # Running Header matching 1.pdf
        p_hdr = section.header.paragraphs[0]
        p_hdr.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        r_hdr = p_hdr.add_run("IRIS-AIOS | PROJECT DOCUMENTATION")
        r_hdr.font.name = "Calibri"
        r_hdr.font.size = Pt(8.0)
        r_hdr.font.color.rgb = COLOR_MUTED
        
        # Footer
        p_ftr = section.footer.paragraphs[0]
        p_ftr.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_ftr = p_ftr.add_run("A Multimodal Windows Desktop AI Assistant  •  Project Specification Dossier  •  2026")
        r_ftr.font.name = "Calibri"
        r_ftr.font.size = Pt(8.0)
        r_ftr.font.color.rgb = COLOR_MUTED

    # =========================================================================
    # PAGE 1: TITLE & COVER PAGE (MATCHING 1.PDF + ALL 10 MEMBERS)
    # =========================================================================
    p_t1 = doc.add_paragraph()
    p_t1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t1.paragraph_format.space_before = Pt(8)
    p_t1.paragraph_format.space_after = Pt(2)
    r_t1 = p_t1.add_run("IRIS-AIOS")
    r_t1.font.name = "Calibri"
    r_t1.font.size = Pt(26)
    r_t1.bold = True
    r_t1.font.color.rgb = COLOR_PRIMARY

    p_t2 = doc.add_paragraph()
    p_t2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t2.paragraph_format.space_after = Pt(2)
    r_t2 = p_t2.add_run("INTEGRATED REACTIVE INTELLIGENT SYSTEM")
    r_t2.font.name = "Calibri"
    r_t2.font.size = Pt(12)
    r_t2.bold = True
    r_t2.font.color.rgb = COLOR_SECONDARY

    p_t3 = doc.add_paragraph()
    p_t3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t3.paragraph_format.space_after = Pt(3)
    r_t3 = p_t3.add_run("PROJECT DOCUMENTATION\nA Multimodal Windows Desktop AI Assistant")
    r_t3.font.name = "Calibri"
    r_t3.font.size = Pt(10.5)
    r_t3.bold = True
    r_t3.font.color.rgb = COLOR_DARK

    p_t4 = doc.add_paragraph()
    p_t4.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_t4.paragraph_format.space_after = Pt(6)
    r_t4 = p_t4.add_run("Natural Language   •   Cognitive Reasoning   •   Memory   •   Voice   •   Vision   •   Desktop Automation")
    r_t4.font.name = "Calibri"
    r_t4.font.size = Pt(8.0)
    r_t4.font.color.rgb = COLOR_MUTED

    # Presentation Team Table (All 10 members)
    p_th = doc.add_paragraph()
    p_th.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_th.paragraph_format.space_after = Pt(2)
    r_th = p_th.add_run("PROJECT PRESENTATION TEAM & SPECIALIZED TECHNICAL ROLES")
    r_th.bold = True
    r_th.font.size = Pt(9.0)
    r_th.font.color.rgb = COLOR_PRIMARY

    members_data = [
        ["1", "Jude Livingston", "Project Introduction & System Scope", "Chapter 1: Problem, Objectives & OS Boundaries"],
        ["2", "Karunya", "UI/UX & Cybernetic HUD Design", "React 18 + Vite 5.4 HUD, Hologram Ring & Panels"],
        ["3", "Bhaskar", "Installation, setup.bat & System Setup", "Automated venv, Port Binding 5743 & Health Checks"],
        ["4", "Rishit", "Core Engine & API Keys Integration", "IrisBrain, 52 Intent Regexes & 20-Slot APIKeyManager"],
        ["5", "Aruna", "Language & Multimodal Emotion Intelligence", "Devanagari Unicode Shielding & Voice/Vision Emotion Fusion"],
        ["6", "VARUN SANDESH", "Computer Vision & Spatial Gaze Perception", "YuNet ONNX 30fps, dev_x Gaze Tracking & Screen OCR"],
        ["7", "Dhanush Dathu", "Hands OS Automation & Autonomous Synthesis", "Win32 WindowManager, WhatsApp, Games & CodeRunner"],
        ["8", "lokesh chandhra", "3-Tier Hierarchical Memory Architecture", "TempLayer (48h), LongTemp (18d) & SQLite DeepLayer"],
        ["9", "Mohanhemanth", "Biometric Security & Privacy Governance", "SFace PBKDF2 AES-256 Vault & Terminal Safe Mode"],
        ["10", "Bhuvana kruthi", "Results, Conclusion & Future Vision", "Chapter 5: Latency Benchmarks, Siri/Copilot Comparison"]
    ]
    t_m = doc.add_table(rows=len(members_data) + 1, cols=4)
    style_table(t_m, [Inches(0.4), Inches(1.8), Inches(2.7), Inches(1.8)],
                ["Seq", "Member Name", "Assigned Technical Role", "Documentation Focus"], members_data, font_size=7.5)

    p_yr = doc.add_paragraph()
    p_yr.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_yr.paragraph_format.space_before = Pt(6)
    p_yr.paragraph_format.space_after = Pt(0)
    r_yr = p_yr.add_run("Project Codebase: IRIS-AI  •  Environment: Windows 11 64-bit  •  FastAPI + React 18  •  Academic Year 2026")
    r_yr.font.size = Pt(8.0)
    r_yr.font.color.rgb = COLOR_MUTED

    # PAGE 1 END -> BREAK TO PAGE 2
    doc.add_page_break()

    # =========================================================================
    # PAGE 2: ABSTRACT AND PROJECT OVERVIEW (MATCHING 1.PDF PAGE 2)
    # =========================================================================
    add_custom_heading(doc, "ABSTRACT AND PROJECT OVERVIEW", level=1)
    
    add_body_p(doc, 
        "IRIS-AIOS is an autonomous multimodal Windows desktop artificial intelligence agent engineered to unify natural-language "
        "dialogue, hybrid local/cloud cognitive reasoning, 3-tier episodic memory, real-time computer vision, dual-pipeline speech synthesis, "
        "and native operating-system automation into a single cohesive runtime. Built upon Python 3.12, FastAPI, and a React 18 + Vite cybernetic "
        "heads-up display (HUD), IRIS-AIOS operates as an proactive, privacy-preserving desktop companion."
    )
    add_body_p(doc, 
        "The architecture enforces strict decoupling between understanding, decision-making, and execution. The Cognitive Core (IrisBrain) "
        "resolves user instructions across 52 compiled intent regular expressions with sub-millisecond typo normalization; the Model Router "
        "dynamically negotiates inference between quantized local LLMs (Ollama Llama 3.2 3B / Qwen 2.5 3B) and high-throughput cloud endpoints "
        "(Groq Qwen 27B); the Hands layer executes low-level Win32 ctypes window calls, coordinates automated WhatsApp navigation, and writes "
        "targeted code directly to disk without directory pollution; and the Vision engine monitors user presence and pupil gaze deviation."
    )
    
    add_figure_img(doc, "flowchart_1_architecture.png", "Figure 2.1 Conceptual IRIS-AIOS project overview (illustrative system view).", width_in=4.7)
    
    add_body_p(doc, 
        "Project Scope: Direct Win32 desktop interaction with controlled automation, multimodal audio-visual telemetry, persistent contextual memory, "
        "and secure credential governance. Experimental evaluations across 14 automation subsystems confirm sub-110ms intent dispatch, 100% voice "
        "synthesis resilience via Windows native SAPI5 fallback, zero-subfolder workspace integrity, and robust stranger lockout protection."
    )

    # PAGE 2 END -> BREAK TO PAGE 3
    doc.add_page_break()

    # =========================================================================
    # PAGE 3: TABLE OF CONTENTS (MATCHING 1.PDF PAGE 3)
    # =========================================================================
    add_custom_heading(doc, "TABLE OF CONTENTS", level=1)
    
    toc_data = [
        ["Abstract and Project Overview", "2"],
        ["Chapter 1 – Introduction", "4"],
        ["Chapter 2 – Literature Survey", "5"],
        ["Chapter 3 – Proposed System and Methodology", "6"],
        ["System Architecture and Data Flow", "7"],
        ["Core and Cognitive Pipeline", "8"],
        ["Language and Emotional Handling", "9"],
        ["Memory and Context Continuity", "10"],
        ["Automation / Hands Layer", "11"],
        ["Model Router and API Key Connection", "12"],
        ["UI/UX Development – IRIS", "13"],
        ["Security, Privacy and Spatial Vision", "14"],
        ["Chapter 4 – Hardware and Software Requirements", "15"],
        ["Algorithms / Models / Methods Used", "16"],
        ["System Design, Setup and Voice Integration", "17"],
        ["Functional Implementation, Testing and Validation", "18"],
        ["Deployment, Results and Comparative Discussion", "19"],
        ["Chapter 5 – Conclusion, Future Vision and Team Sequence", "20"]
    ]
    t_toc = doc.add_table(rows=len(toc_data) + 1, cols=2)
    style_table(t_toc, [Inches(5.4), Inches(1.3)], ["Section / Topic Title", "Page"], toc_data, font_size=7.5)
    
    add_body_p(doc, 
        "Documentation structure follows the project flow: introduction → research → methodology → implementation → validation → results → conclusion. "
        "Every chapter reflects concrete engineering artifacts, classes, and benchmarks from the IRIS-AI codebase.",
        bold_prefix="Documentation Note:"
    )

    # PAGE 3 END -> BREAK TO PAGE 4
    doc.add_page_break()

    # =========================================================================
    # PAGE 4: CHAPTER 1 – INTRODUCTION (MATCHING 1.PDF PAGE 4)
    # =========================================================================
    add_custom_heading(doc, "CHAPTER 1 – INTRODUCTION", level=1, presenter="Presenter: Jude Livingston  •  Role: Project Introduction & System Scope")
    
    add_custom_heading(doc, "1.1 Problem Definition", level=2)
    add_body_p(doc, 
        "Modern computer workflows require developers and office professionals to juggle dozens of heterogeneous applications, terminal "
        "sessions, web tabs, and file trees simultaneously. Traditional interaction models rely exclusively on manual keyboard shortcuts and "
        "rigid mouse navigation. When multi-step tasks are executed (e.g., launching an IDE, configuring a local server, writing a boilerplate script, "
        "and messaging a team contact), the user must execute each step sequentially, creating severe operational friction."
    )
    add_body_p(doc, 
        "Commercial virtual assistants (Apple Siri, Amazon Alexa, Microsoft Cortana) fail in developer workspaces because they operate inside "
        "sandboxed user-mode containers. They lack low-level Win32 operating-system hooks to enumerate desktop windows, focus background editors, "
        "or manipulate local filesystems. Conversely, generative LLM agents (such as AutoGPT) suffer from catastrophic loop failures, high latency "
        "(15-45s), and zero offline voice/vision integration. IRIS-AIOS solves this bottleneck through native ctypes hooks and hybrid reasoning."
    )
    
    add_flow_box(doc, ["USER INPUT", "UNDERSTAND", "REASON", "DECIDE", "EXECUTE", "FEEDBACK"])
    
    add_custom_heading(doc, "1.2 Objectives", level=2)
    add_bullet(doc, "Deliver natural conversational dialogue in Hindi and English, eliminating rigid CLI command syntax across 52 task categories.")
    add_bullet(doc, "Implement high-precision intent classification with negative lookaheads and sub-1ms typo normalization (TypoCorrector).")
    add_bullet(doc, "Maintain multi-turn session context without context amnesia or token explosion via 3-tier memory (Temp, LongTemp, DeepLayer).")
    add_bullet(doc, "Ensure 100% speech synthesis uptime through dual-pipeline Edge-TTS SwaraNeural/AriaNeural and native Windows SAPI5 fallback.")
    add_bullet(doc, "Execute native Win32 window management, WhatsApp automation, and zero-subfolder code synthesis directly via TaskExecutor.")
    add_bullet(doc, "Provide a real-time cybernetic React 18 HUD with dynamic audio-reactive hologram rings and live vision telemetry.")
    add_bullet(doc, "Implement single-owner biometric vaulting using SFace embeddings and PBKDF2 AES-256 encryption for absolute privacy.")

    add_custom_heading(doc, "1.3 Limitations", level=2)
    add_bullet(doc, "Native OS Hands are specifically architected for Windows 11 64-bit user32.dll, shell32, and DWM ctypes interfaces.")
    add_bullet(doc, "Webcam presence, biometric face matching, and gaze tracking require adequate ambient lighting and minimum 15 fps video capture.")
    add_bullet(doc, "Local LLM reasoning via Ollama requires a modern multi-core processor and at least 8 GB of available physical RAM.")

    # PAGE 4 END -> BREAK TO PAGE 5
    doc.add_page_break()

    # =========================================================================
    # PAGE 5: CHAPTER 2 – LITERATURE SURVEY (MATCHING 1.PDF PAGE 5)
    # =========================================================================
    add_custom_heading(doc, "CHAPTER 2 – LITERATURE SURVEY", level=1)
    
    add_custom_heading(doc, "2.1 Existing Systems and Context", level=2)
    add_body_p(doc, 
        "Virtual assistant architectures have transitioned from static rule-based IVR grammars to cloud-hosted Large Language Models. "
        "However, existing systems fail to deliver unified desktop capability: AutoGPT suffers from infinite looping and token depletion; "
        "OpenInterpreter provides terminal execution but lacks proactive visual presence, voice cloning, and Win32 window snapping; and Microsoft "
        "Copilot acts as a read-only browser sidecar unable to perform deep OS automation or offline voice synthesis."
    )
    
    add_custom_heading(doc, "2.2 Related Technical Areas", level=2)
    add_bullet(doc, "Natural Language Processing: Rule-based regex intent parsers combined with zero-shot transformer prompt routing.")
    add_bullet(doc, "Local Edge Transformers: GGUF 4-bit quantized LLM weights executed locally via Ollama to ensure complete data sovereignty.")
    add_bullet(doc, "Speech Synthesis & Watchdogs: Neural multi-speaker voice synthesis backed by native COM SpVoice engines and active buffer watchdogs.")
    add_bullet(doc, "Computer Vision: Edge ONNX neural inference (YuNet, SFace) for sub-40ms facial landmarking and 128-D biometric identification.")
    add_bullet(doc, "Desktop Automation: Low-level Win32 API window hooking, EnumWindows enumeration, and GlobalAlloc clipboard injections.")

    add_custom_heading(doc, "2.3 Technologies Relevant to IRIS", level=2)
    tech_data = [
        ["Frontend HUD", "React 18 / Vite 5.4", "Cybernetic HUD, StatusBar, VisionPanel, TodoPanel, and Emotion Hologram Ring"],
        ["Backend Server", "FastAPI / Uvicorn", "Asynchronous REST gateway, WebSocket streaming, and health endpoints on port 5743"],
        ["Local AI Runtime", "Ollama (Llama 3.2 / Qwen 2.5)", "100% offline, privacy-preserving conversational reasoning and code generation"],
        ["Cloud Failover", "Groq Cloud (Qwen 27B)", "Sub-second cloud LLM inference for deep code synthesis and complex planning"],
        ["Episodic Memory", "SQLite / In-Memory Cache", "3-tier memory: TempLayer (48h TTL), LongTemp (18d TTL), and DeepLayer (SQLite)"],
        ["Speech Input", "SpeechRecognition + Watchdog", "Voice ingestion with 1000ms active heartbeat watchdog to eliminate audio lockups"],
        ["Speech Output", "Edge-TTS + Windows SAPI5", "Dual-pipeline TTS: Hindi SwaraNeural & English AriaNeural with SAPI5 offline fallback"],
        ["Vision Stack", "OpenCV 4.10 + ONNX Runtime", "YuNet (0.35 MB) face detection, pupil gaze tracking, and SFace (37.5 MB) biometrics"],
        ["Desktop Hands", "Win32 ctypes / Shell32", "Direct user32 window orchestration, snap layouts, WhatsApp messaging, and clean CodeRunner"]
    ]
    t_tech = doc.add_table(rows=len(tech_data) + 1, cols=3)
    style_table(t_tech, [Inches(1.2), Inches(2.3), Inches(3.2)], ["Architecture Domain", "Configured Technology", "Concrete Role in IRIS-AI Codebase"], tech_data, font_size=7.0)

    add_custom_heading(doc, "2.4 Research Gap / Project Motivation", level=2)
    add_body_p(doc, 
        "Existing systems force users into a false dichotomy: choose either cloud-dependent conversational assistants that lack OS control, "
        "or brittle terminal scripts that lack conversational intelligence, vision, and voice. IRIS-AIOS resolves this gap by integrating "
        "sub-110ms intent classification, dual-pipeline offline voice resilience, deep Win32 hands, and camera gaze tracking into one runtime."
    )

    # PAGE 5 END -> BREAK TO PAGE 6
    doc.add_page_break()

    # =========================================================================
    # PAGE 6: CHAPTER 3 – PROPOSED SYSTEM AND METHODOLOGY (MATCHING 1.PDF PAGE 6)
    # =========================================================================
    add_custom_heading(doc, "CHAPTER 3 – PROPOSED SYSTEM AND METHODOLOGY", level=1)
    
    add_custom_heading(doc, "3.1 Proposed Idea", level=2)
    add_body_p(doc, 
        "IRIS-AIOS operates on a Unified Multimodal Cognitive Loop: an autonomous agent that continuously perceives user input (via voice, "
        "camera frames, screen capture, and keyboard), normalizes input through high-speed fuzzy engines, resolves intent via prioritized regex "
        "matrices, queries a 3-tier memory hierarchy, reasons over actions via local/cloud LLMs, and acts upon Windows 11 via native Win32 hands."
    )
    
    add_custom_heading(doc, "3.2 Methodology Pipeline", level=2)
    add_flow_box(doc, ["INPUT", "NORMALIZE", "UNDERSTAND", "CONTEXT", "REASON", "DECIDE", "EXECUTE / RESPOND"])
    
    add_body_p(doc, 
        "1. Ingestion: Accepts voice audio via Web Speech API or microphone, or typed text via the React HUD on port 3001.\n"
        "2. Normalization: TypoCorrector resolves spelling errors (<1ms) and shields Devanagari Unicode sequences ([ऀ-ॿ]).\n"
        "3. Understanding: IntentDetector matches 52 regex patterns with negative lookaheads, categorizing intent and extracting parameters.\n"
        "4. Context Retrieval: MemoryOrchestrator pulls recent turns from TempLayer and persistent preferences from SQLite DeepLayer.\n"
        "5. Reasoning: Decider checks if the request is a direct system action (<25ms fast-path) or routes to Ollama/Groq for LLM synthesis.\n"
        "6. Decision & Execution: TaskExecutor dispatches window manipulation, file synthesis, or WhatsApp messages, feeding results to TTS."
    )
    
    add_custom_heading(doc, "3.3 Major Functional Modules", level=2)
    add_bullet(doc, "IrisBrain (backend/core/brain.py): Central orchestrator coordinating intent, memory injection, model routing, and plan dispatch.")
    add_bullet(doc, "IntentDetector (backend/core/intent.py): Compiles 52 regex patterns with negative lookaheads and precedence guards.")
    add_bullet(doc, "TypoCorrector (backend/core/typo_corrector.py): High-speed rule-based dictionary correcting command verbs and app aliases in <1ms.")
    add_bullet(doc, "TaskExecutor (backend/hands/task_executor.py): Master hands actuator dispatching window, code, game, and social actions.")
    add_bullet(doc, "WindowManager (backend/hands/window_manager.py): Direct Win32 ctypes window enumeration, snap layouts, and focus stealing.")
    add_bullet(doc, "PresenceEmotionEngine (backend/vision/presence_emotion_engine.py): 8-chapter vision daemon running YuNet and SFace at 30 fps.")
    add_bullet(doc, "MemoryOrchestrator (backend/memory/memory_orchestrator.py): 3-tier memory coordinator (TempLayer, LongTemp, DeepLayer).")
    add_bullet(doc, "APIKeyManager (backend/core/api_keys.py): Enterprise key pool rotating 20 model slots with automatic 429 backoff.")

    add_custom_heading(doc, "3.4 Design Principle", level=2)
    add_body_p(doc, 
        "Separation of Responsibilities: AI reasoning never directly mutates Windows state without passing through the Decider safety gate, "
        "and the frontend React interface never executes raw commands, ensuring rock-solid stability and zero unvetted desktop operations."
    )

    # PAGE 6 END -> BREAK TO PAGE 7
    doc.add_page_break()

    # =========================================================================
    # PAGE 7: SYSTEM ARCHITECTURE AND DATA FLOW (MATCHING 1.PDF PAGES 7 & 8)
    # =========================================================================
    add_custom_heading(doc, "SYSTEM ARCHITECTURE AND DATA FLOW", level=1)
    
    add_custom_heading(doc, "3.5 Overall System Architecture", level=2)
    add_body_p(doc, 
        "The system architecture strictly partitions the client-facing presentation layer from the Python backend and OS execution subsystems. "
        "Communication is maintained over high-throughput REST and asynchronous polling streams on FastAPI port 5743."
    )
    
    add_flow_box(doc, ["USER", "REACT HUD (3001)", "FASTAPI (5743)", "IRISBRAIN", "DECIDER", "ROUTER/HANDS", "WIN32", "TTS/HUD"])
    
    add_figure_img(doc, "flowchart_2_brain_decision.png", "Figure 3.1 Cognitive Intent Decision & Planning Pipeline.", width_in=4.6)

    add_custom_heading(doc, "3.6 Request Processing Flow", level=2)
    add_flow_box(doc, ["REQUEST", "TYPO FILTER", "INTENT MATCH", "MEMORY RECALL", "DECIDER ROUTE", "ACTION DISPATCH", "AUDIO FEEDBACK"])
    add_body_p(doc, 
        "Every incoming payload is timestamped and evaluated. Fast-path actions bypass LLM inference entirely: commands like 'minimize all tabs' "
        "or 'mute sound' execute via ctypes user32 calls in under 22ms. Complex multi-step instructions (e.g., 'open VS Code and write a python "
        "stopwatch script on desktop') generate an ordered TaskPlan with parameter validation, executing sequentially with live telemetry."
    )

    add_custom_heading(doc, "3.7 Feedback Path and Safety Boundary", level=2)
    add_body_p(doc, 
        "Subsystem status streams back through FastAPI to the HUD's StatusBar and chat stream. Destructive operations (format disk, delete files, "
        "kill critical processes) hit an explicit Confirmation Gate in decider.py, halting execution until the user gives explicit verbal or click consent."
    )

    # PAGE 7 END -> BREAK TO PAGE 8
    doc.add_page_break()

    # =========================================================================
    # PAGE 8: CORE AND COGNITIVE PIPELINE (MATCHING 1.PDF PAGE 9)
    # =========================================================================
    add_custom_heading(doc, "CORE AND COGNITIVE PIPELINE", level=1, presenter="Presenter: Rishit  •  Role: Core Engine & Cognitive Orchestration")
    
    add_custom_heading(doc, "3.6 Core of IRIS (IrisBrain & IntentDetector)", level=2)
    add_body_p(doc, 
        "IrisBrain (backend/core/brain.py) is the master cognitive conductor. It orchestrates user perception, intent extraction, memory recall, "
        "and multi-model routing. In backend/core/intent.py, Rishit designed the IntentDetector class, which compiles 52 prioritized regular expression "
        "patterns equipped with negative lookaheads to prevent category collision (e.g., distinguishing 'write code' from 'create folder')."
    )
    
    add_custom_heading(doc, "Cognitive Processing Flow", level=3)
    add_flow_box(doc, ["RECEIVE", "ANALYZE", "CONTEXTUALIZE", "REASON", "DECIDE", "ACT", "RESPOND"])
    
    add_custom_heading(doc, "Fast-Path Processing for System Actions", level=3)
    add_flow_box(doc, ["REQUEST", "SYSTEM INTENT?", "DIRECT HANDLER", "WIN32 EXECUTION", "RESULT"])
    add_body_p(doc, 
        "When an intent maps to a deterministic OS operation (window management, app launch, volume toggle, screenshot), IrisBrain bypasses "
        "the LLM and dispatches directly to the corresponding Hands controller. This reduces execution latency from 3-5 seconds down to 21-45 milliseconds."
    )

    add_callout(doc, "Real-World Multi-Step Execution Trace", 
        "User Instruction: 'Write code in python on desktop for stopwatch and open Chrome'\n"
        "• Stage 1 (Analyze): IntentDetector extracts intent='create' (subtype=code) and intent='launch' (app=chrome).\n"
        "• Stage 2 (Typo Filter): TypoCorrector validates language='python' and path='desktop'.\n"
        "• Stage 3 (Contextualize): MemoryOrchestrator pulls active desktop path 'C:\\Users\\...\\Desktop'.\n"
        "• Stage 4 (Hands Dispatch): CodeRunner applies zero-subfolder guard, synthesizes 'stopwatch.py' directly to Desktop in 3.09s, "
        "and WindowManager launches Chrome via ShellExecuteW.\n"
        "• Stage 5 (Voice Feedback): VoiceEngine formats response and speaks confirmation via AriaNeural in 0.10s."
    )

    # PAGE 8 END -> BREAK TO PAGE 9
    doc.add_page_break()

    # =========================================================================
    # PAGE 9: LANGUAGE AND EMOTIONAL HANDLING (MATCHING 1.PDF PAGE 10)
    # =========================================================================
    add_custom_heading(doc, "LANGUAGE AND EMOTIONAL HANDLING", level=1, presenter="Presenter: Aruna  •  Role: Language & Multimodal Emotion Intelligence")
    
    add_custom_heading(doc, "3.7 Natural-Language Processing & Devanagari Shielding", level=2)
    add_body_p(doc, 
        "Aruna architected the bilingual language processing pipeline. In backend/core/typo_corrector.py, incoming text is normalized against "
        "action typos ('opn'➔'open', 'lonch'➔'launch') and application aliases. Crucially, Aruna implemented Unicode Devanagari Shielding ([ऀ-ॿ]): "
        "when Hindi speech or Devanagari script is detected, the engine bypasses destructive English character stripping, preserving Hindi grammar "
        "and automatically routing vocal responses to the authentic hi-IN-SwaraNeural voice model."
    )
    
    add_flow_box(doc, ["VOICE / TEXT", "NORMALIZE", "INTENT + ENTITIES", "CONTEXT", "REASONING", "RESPONSE / ACTION"])

    add_custom_heading(doc, "Multimodal Emotion Recognition (Camera + Voice Fusion)", level=2)
    add_callout(doc, "Core Architectural Principle", 
        "\"This system is created by combining of language and vision system.\" — Aruna\n"
        "Emotion is not evaluated in isolation. Facial landmark geometry from the camera (lip corner elevation, eyebrow furrowing, eye aspect ratio) "
        "is fused in real-time with acoustic prosody from the microphone (pitch variance, volume energy, speaking rate)."
    )
    
    add_figure_img(doc, "flowchart_7_emotion_vision_voice.png", "Figure 3.2 Multimodal Emotion Recognition Combining Vision & Voice.", width_in=4.6)

    add_custom_heading(doc, "Emotion-to-Voice Parameter Modulation (EmotionMapper)", level=3)
    add_bullet(doc, "Happy / Excited: Pitch +0.15 to +0.25, Speed 1.1x–1.2x, Tone bright, energetic delivery.")
    add_bullet(doc, "Sad / Frustrated: Pitch -0.20, Speed 0.75x, Volume 0.8x, Tone soft, empathetic and soothing pacing.")
    add_bullet(doc, "Angry / Tense: Pitch -0.10, Speed 1.2x, Volume 1.15x, Tone sharp, concise and direct responses.")

    # PAGE 9 END -> BREAK TO PAGE 10
    doc.add_page_break()

    # =========================================================================
    # PAGE 10: MEMORY AND CONTEXT CONTINUITY (MATCHING 1.PDF PAGE 11)
    # =========================================================================
    add_custom_heading(doc, "MEMORY AND CONTEXT CONTINUITY", level=1, presenter="Presenter: lokesh chandhra  •  Role: 3-Tier Hierarchical Memory Architecture")
    
    add_custom_heading(doc, "3.8 Purpose of Memory & Architecture", level=2)
    add_body_p(doc, 
        "Conversational AI systems suffer from acute amnesia when context is wiped, or experience severe token bloat when history is unbounded. "
        "To solve this, lokesh chandhra engineered a 3-Tier Hierarchical Memory Architecture (backend/memory/db.py, temp_layer.py, long_temp_layer.py, "
        "and deep_layer.py) backed by an embedded SQLite database (memory.db) with automatic promotion mechanics."
    )
    
    add_custom_heading(doc, "3-Tier Layered Specifications", level=2)
    add_bullet(doc, "TempLayer (Short-Term Working Memory): In-memory cache storing active conversational turns with a 48-hour TTL (48 * 3600s). "
                    "Features Auto-Reinforcement: if a topic is mentioned >= 2 times within 48h, it is automatically promoted to LongTempLayer.")
    add_bullet(doc, "LongTempLayer (Medium-Term Session Continuity): 18-day TTL (18 * 24 * 3600s). Compresses multi-turn sessions into rolling semantic "
                    "synopses. If reinforced >= 3 times (REINFORCEMENT_THRESHOLD = 3), it is promoted to DeepLayer.")
    add_bullet(doc, "DeepLayer (Permanent SQLite Memory): Zero TTL expiration. Persists core facts, custom project paths, enrolled owner biometric "
                    "embeddings, and personal user preferences across system restarts.")

    add_flow_box(doc, ["USER INPUT", "UNDERSTAND", "RECALL RELEVANT", "REASON", "DECIDE", "RESPOND", "UPDATE MEMORY"])

    add_custom_heading(doc, "MemoryOrchestrator Semantic Prompt Injection", level=2)
    add_body_p(doc, 
        "In backend/memory/memory_orchestrator.py, lokesh chandhra implemented contextual filtering: before an LLM call is dispatched, the orchestrator "
        "retrieves the top-5 relevant facts and injects them into the system prompt. This gives IRIS full conversational continuity without "
        "polluting context windows or leaking irrelevant historical data."
    )

    # PAGE 10 END -> BREAK TO PAGE 11
    doc.add_page_break()

    # =========================================================================
    # PAGE 11: AUTOMATION / HANDS LAYER (MATCHING 1.PDF PAGE 12)
    # =========================================================================
    add_custom_heading(doc, "AUTOMATION / HANDS LAYER", level=1, presenter="Presenter: Dhanush Dathu  •  Role: Native OS Hands Automation & Autonomous Synthesis")
    
    add_custom_heading(doc, "3.9 Role of Automation (TaskExecutor Subsystem)", level=2)
    add_body_p(doc, 
        "Dhanush Dathu engineered the physical execution layer of IRIS AI—the 'Hands' (backend/hands/task_executor.py). Unlike chatbots that only "
        "generate text advice, TaskExecutor translates decisions into concrete Windows 11 API actions via user32.dll, shell32.dll, and ctypes."
    )
    
    add_flow_box(doc, ["HUMAN INSTRUCTION", "AI UNDERSTANDING", "DECISION", "COMPUTER ACTION"])
    
    add_custom_heading(doc, "Key Hands Subsystems", level=2)
    add_bullet(doc, "Win32 WindowManager: Uses EnumWindows, GetWindowText, and AttachThreadInput to snap windows to screen halves (SWP_SHOWWINDOW), "
                    "minimize all windows to desktop, and bring background applications to the foreground without focus-stealing crashes.")
    add_bullet(doc, "WhatsApp & Social Controller: Desktop automation using 64-bit GlobalAlloc clipboard buffers, OpenInputDesktop thread attachment, "
                    "Ctrl+N new chat invocation, 0.9s UI wait, and automated message dispatch with phonetic typo correction ('chart'➔'chat').")
    add_bullet(doc, "Targeted Zero-Subfolder CodeRunner: Enforces the FORBIDDEN_SUBFOLDERS blacklist (blocking 'python', 'code', 'script' folders), "
                    "writing clean scripts directly to the target workspace or Desktop in 3.09s, with run=False for interactive scripts.")
    add_bullet(doc, "Autonomous HTML5 Game & Website Builder: hands/game_builder.py synthesizes complete playable Canvas games (Chess minimax, "
                    "Ludo turn engine, Carrom 2D collision physics, Stickman fighter, Car Racing), while website_builder.py creates responsive sites.")

    add_figure_img(doc, "flowchart_3_hands_automation.png", "Figure 3.3 Hands OS Automation Subsystem Architecture.", width_in=4.6)

    # PAGE 11 END -> BREAK TO PAGE 12
    doc.add_page_break()

    # =========================================================================
    # PAGE 12: MODEL ROUTER AND API KEY CONNECTION (MATCHING 1.PDF PAGE 13)
    # =========================================================================
    add_custom_heading(doc, "MODEL ROUTER AND API KEY CONNECTION", level=1, presenter="Presenter: Rishit  •  Role: Model Router & API Key Management")
    
    add_custom_heading(doc, "3.10 Core and Model Router (Dynamic Token Allocation)", level=2)
    add_body_p(doc, 
        "The cognitive engine avoids single-vendor lock-in through the ModelRouter (backend/core/model_router.py). Rishit implemented keyword-driven "
        "verbosity detection (detect_verbosity): requests containing DETAIL_PHRASES ('in detail', 'elaborate', 'step by step') receive DETAIL_MAX_TOKENS = 1024, "
        "while BRIEF_PHRASES ('briefly', 'in short', 'quick answer') allocate BRIEF_MAX_TOKENS = 64 (default: 512, fast: 150), optimizing cost and speed."
    )
    
    add_flow_box(doc, ["IRIS CORE", "MODEL ROUTER", "LOCAL OLLAMA / CLOUD GROQ / FALLBACK"])

    add_custom_heading(doc, "APIKeyManager 20-Slot Credential Architecture", level=2)
    add_body_p(doc, 
        "In backend/core/api_keys.py, Rishit designed the APIKeyManager. It reads credentials securely from .env without embedding keys in code. "
        "The manager configures up to 20 numbered model slots (MODEL_API_KEY_0 through MODEL_API_KEY_19). When rate limits (HTTP 429) or connection "
        "timeouts are detected on an active key, the manager automatically rotates to the next available key slot in under 5ms."
    )
    
    add_flow_box(doc, ["CORE", "MODEL ROUTER", "API KEY MANAGER", "INFERENCE ENGINE", "PROVIDER API", "AI MODEL"])

    add_custom_heading(doc, "Local and Cloud Inference Routing", level=2)
    add_bullet(doc, "Local Path (Ollama): Routes to local Llama 3.2 3B or Qwen 2.5 3B for offline privacy-preserving conversations.")
    add_bullet(doc, "Cloud Path (Groq / OpenAI): High-throughput cloud API for complex generative coding, website synthesis, and multi-step planning.")
    add_bullet(doc, "Graceful Degradation: If cloud connectivity drops, ModelRouter automatically falls back to local Ollama with zero server crash.")

    # PAGE 12 END -> BREAK TO PAGE 13
    doc.add_page_break()

    # =========================================================================
    # PAGE 13: UI/UX DEVELOPMENT – IRIS (MATCHING 1.PDF PAGE 14)
    # =========================================================================
    add_custom_heading(doc, "UI/UX DEVELOPMENT – IRIS", level=1, presenter="Presenter: Karunya  •  Role: UI/UX & Cybernetic HUD Design")
    
    add_custom_heading(doc, "3.11 Role of UI/UX & Cybernetic HUD Design System", level=2)
    add_body_p(doc, 
        "Karunya engineered the frontend user interface: a cybernetic, futuristic Heads-Up Display (HUD) built with React 18 and Vite 5.4. "
        "Operating at a smooth 60 frames per second on port 3001, the HUD communicates with the FastAPI backend on port 5743 via REST and WebSocket event "
        "streams. CSS custom properties establish a sleek dark palette: #0A0F1D deep midnight slate, #00F0FF cyan telemetry, and #10B981 emerald status."
    )
    
    add_flow_box(doc, ["USER", "REACT 18 HUD (3001)", "FASTAPI GATEWAY (5743)", "IRISBRAIN", "DECISION / HANDS", "HUD STATE UPDATE"])

    add_custom_heading(doc, "Core UI Component Layout", level=2)
    ui_comp_data = [
        ["StatusBar", "Header telemetry bar: server online/offline ping, memory token count, active LLM model tag, volume meter."],
        ["AI ChatBox", "Conversational stream: syntax-highlighted code blocks, one-click copy buttons, Markdown tables, audio badges."],
        ["ChatInput", "Dual-input controller: keyboard command input, voice mic toggle, silence toggle button, real-time waveform visualizer."],
        ["VisionPanel", "Collapsible camera telemetry drawer: 30fps webcam preview snapshot, detected face bounding boxes, emotion ratings."],
        ["TodoPanel", "Persistent task management drawer: tracks active user todos across conversations, backed by backend SQLite tables."],
        ["Emotion Hologram Ring", "Central cybernetic ring: pulses cyan on idle, modulates frequency on user speech, shifts violet on inattention."]
    ]
    t_ui = doc.add_table(rows=len(ui_comp_data) + 1, cols=2)
    style_table(t_ui, [Inches(1.8), Inches(4.7)], ["HUD Component", "Technical Purpose and Interaction Mechanics"], ui_comp_data, font_size=7.2)

    add_custom_heading(doc, "Responsive Layout & Safe Confirmation Gates", level=2)
    add_body_p(doc, 
        "The interface automatically adapts across 1080p and 4K displays. When sensitive operations (such as deleting files or formatting) are "
        "triggered, Karunya's UI displays an attention-grabbing modal confirmation window with verbal consent bypass options."
    )

    # PAGE 13 END -> BREAK TO PAGE 14
    doc.add_page_break()

    # =========================================================================
    # PAGE 14: SECURITY, PRIVACY & SPATIAL VISION (MATCHING 1.PDF PAGE 15)
    # =========================================================================
    add_custom_heading(doc, "SECURITY, PRIVACY AND SPATIAL VISION", level=1, presenter="Presenters: Mohanhemanth (Security) & VARUN SANDESH (Vision)")
    
    add_custom_heading(doc, "3.12 Security & Encrypted Single-Owner Biometric Vault", level=2)
    add_body_p(doc, 
        "Because IRIS AI executes direct native commands upon the host operating system, Mohanhemanth designed the Biometric Single-Owner Security "
        "Vault (BiometricVault). The owner's 128-dimensional facial embedding is extracted via SFace and encrypted using PBKDF2 key derivation "
        "(100,000 SHA-256 iterations) with AES-256 (Fernet) into owner_profile.enc. When an unrecognized face appears, stranger lockout engages."
    )
    
    add_flow_box(doc, ["REQUEST", "INTENT", "SENSITIVE?", "BIOMETRIC VAULT", "OWNER VERIFIED?", "HANDS EXECUTION"])

    add_custom_heading(doc, "Computer Vision Perception & Gaze Tracking (VARUN SANDESH)", level=2)
    add_body_p(doc, 
        "VARUN SANDESH engineered the spatial perception daemon (backend/vision/presence_emotion_engine.py). Using OpenCV VideoCapture(0) at 30 fps, "
        "faces are detected using the ultra-lightweight YuNet ONNX model (0.35 MB). Gaze displacement is computed from pupil and nose landmarks: "
        "dev_x = (x_pupil - x_nose) / face_w. If dev_x exceeds 0.25 (user looking away) for >7 seconds, IRIS playfully prompts their attention back."
    )
    
    add_figure_img(doc, "flowchart_5_vision_attention.png", "Figure 3.4 Vision Perception & Gaze Deviation State Machine.", width_in=4.6)

    add_custom_heading(doc, "TerminalExecutor Safe Mode & Offline Privacy", level=3)
    add_bullet(doc, "Safe Mode Whitelist: TerminalExecutor blocks destructive commands (rmdir /s /q, format, reg delete, del /f /s C:\\) by default.")
    add_bullet(doc, "Local Privacy Guarantee: When running in local mode, zero video frames, audio buffers, or code files are transmitted externally.")

    # PAGE 14 END -> BREAK TO PAGE 15
    doc.add_page_break()

    # =========================================================================
    # PAGE 15: CHAPTER 4 – HARDWARE AND SOFTWARE REQUIREMENTS (MATCHING 1.PDF PAGE 16)
    # =========================================================================
    add_custom_heading(doc, "CHAPTER 4 – HARDWARE AND SOFTWARE REQUIREMENTS", level=1)
    
    add_custom_heading(doc, "4.1 Hardware Requirements Specification", level=2)
    hw_data = [
        ["Processor (CPU)", "Intel Core i5 / AMD Ryzen 5 (4 Cores)", "Intel Core i7 / AMD Ryzen 7 (8+ Cores, 16 Threads)", "Backend, UI, and ONNX inference"],
        ["System Memory (RAM)", "8 GB DDR4", "16 GB DDR4/DDR5", "Ollama local LLM, browser HUD, SQLite db"],
        ["Storage Space", "10 GB free SSD storage", "25 GB free NVMe SSD", "Local model weights, project dependencies"],
        ["Audio Microphone", "Standard integrated microphone", "Noise-cancelling USB array microphone", "Real-time speech-to-text input"],
        ["Audio Speaker", "Standard stereo speakers", "Dedicated desktop speakers / headphones", "Neural and SAPI5 speech synthesis"],
        ["Webcam (Vision)", "720p HD webcam at 15 fps", "1080p Full HD webcam at 30 fps", "YuNet face detection & gaze tracking"],
        ["Display Monitor", "1366x768 resolution", "1920x1080 Full HD or 4K display", "Cybernetic React HUD & window management"]
    ]
    t_hw = doc.add_table(rows=len(hw_data) + 1, cols=4)
    style_table(t_hw, [Inches(1.2), Inches(1.8), Inches(2.2), Inches(1.5)], ["Component", "Minimum Requirement", "Recommended Spec", "Project Operational Purpose"], hw_data, font_size=7.0)

    add_custom_heading(doc, "4.2 Software Requirements Specification", level=2)
    sw_data = [
        ["Operating System", "Windows 11 64-bit (Build 22631+)", "Primary target environment with native Win32 ctypes & Shell32 support"],
        ["Python Runtime", "Python 3.12 64-bit", "Backend orchestration, intent classification, hands actuators, and memory"],
        ["Backend Gateway", "FastAPI + Uvicorn 0.30+", "Asynchronous REST API, event streaming, and WebSocket bus on port 5743"],
        ["Node Environment", "Node.js v20.x LTS + npm 10+", "Frontend build tools and development server runtime"],
        ["Frontend UI", "React 18 + Vite 5.4.21", "Cybernetic heads-up display and interactive telemetry on port 3001"],
        ["Local AI Runtime", "Ollama v0.3+", "Local quantized LLM inference runtime (Llama 3.2 3B / Qwen 2.5 3B)"],
        ["Speech Stack", "Edge-TTS + SAPI5 + SpeechRecognition", "Bilingual neural speech with 100% offline fallback and 1000ms watchdog"],
        ["Computer Vision", "OpenCV 4.10 + ONNX Runtime", "YuNet face detection (0.35 MB) and SFace biometric identification (37.5 MB)"]
    ]
    t_sw = doc.add_table(rows=len(sw_data) + 1, cols=3)
    style_table(t_sw, [Inches(1.2), Inches(2.3), Inches(3.2)], ["Software Technology", "Configured Version", "Role in IRIS-AI Architecture"], sw_data, font_size=7.0)

    add_custom_heading(doc, "4.3 Environment Overview & Port Configuration", level=2)
    add_body_p(doc, 
        "The project operates as an integrated dual-daemon system on Windows 11: the FastAPI backend runs on http://127.0.0.1:5743, while the Vite "
        "React HUD is served on http://localhost:3001. Cross-Origin Resource Sharing (CORS) is enabled to allow smooth bi-directional communication."
    )

    # PAGE 15 END -> BREAK TO PAGE 16
    doc.add_page_break()

    # =========================================================================
    # PAGE 16: ALGORITHMS / MODELS / METHODS USED (MATCHING 1.PDF PAGE 17)
    # =========================================================================
    add_custom_heading(doc, "ALGORITHMS / MODELS / METHODS USED", level=1)
    
    add_custom_heading(doc, "4.1.1 Algorithms Used", level=2)
    add_bullet(doc, "Weighted Multi-Pattern Intent Matching: Evaluates user prompts across 52 compiled regular expressions with negative lookaheads.")
    add_bullet(doc, "Sub-Millisecond Fuzzy Typo Normalization: In TypoCorrector, rule-based dictionary maps action verbs ('opn'➔'open') in <1ms.")
    add_bullet(doc, "Cosine Biometric Distance: Computes 128-D Euclidean feature distances for owner verification (distance threshold: 0.363).")
    add_bullet(doc, "Horizontal Gaze Vector Deviation (dev_x): Calculates pupil landmark displacement: dev_x = (x_pupil - x_nose) / face_width.")
    add_bullet(doc, "Recursive HWND Window Enumeration: Uses EnumWindows to filter visible desktop applications from background helper windows.")

    add_custom_heading(doc, "4.1.2 Models Used", level=2)
    models_data = [
        ["YuNet ONNX", "Face & Landmark Detector", "0.35 MB", "Real-time edge facial detection and 5-point landmark localization at 30 fps"],
        ["SFace ONNX", "Deep Biometric Extractor", "37.5 MB", "Extracts 128-D facial embeddings for biometric single-owner authentication"],
        ["Qwen 2.5 3B / Llama 3.2", "Local Transformer (Ollama)", "3.2 Billion", "Privacy-preserving local conversational reasoning and classification"],
        ["Qwen 27B / Cloud LLM", "High-Throughput Cloud", "27 Billion", "Deep code synthesis, website generation, and complex multi-step planning"],
        ["SwaraNeural & AriaNeural", "Neural Cloud TTS (Edge)", "Cloud API", "Fluent Hindi (Swara) and English (Aria) text-to-speech synthesis"],
        ["SAPI5 SpVoice", "Windows Native TTS", "Local Win32", "100% offline speech fallback, guaranteeing zero voice muting"]
    ]
    t_mod = doc.add_table(rows=len(models_data) + 1, cols=4)
    style_table(t_mod, [Inches(1.4), Inches(1.5), Inches(0.9), Inches(2.9)], ["Model Name", "Model Type", "Size / Params", "Operational Role in IRIS-AI"], models_data, font_size=7.0)

    add_custom_heading(doc, "4.1.3 Methods Used", level=2)
    add_bullet(doc, "Decoupled Layered Architecture: Clean boundaries between React HUD, cognitive brain, and Win32 execution hands.")
    add_bullet(doc, "Zero-Subfolder Guard: Blacklists programming language names from folder generation to ensure clean code placement.")
    add_bullet(doc, "Speech Heartbeat Watchdog: Active 1000ms background thread resetting recognition buffers to eliminate audio lockups.")

    add_custom_heading(doc, "4.1.4 Decision Processing Flow", level=2)
    add_flow_box(doc, ["USER REQUEST", "CLASSIFY INTENT", "RETRIEVE CONTEXT", "DIRECT HANDLER?", "MODEL REASONING", "SAFETY CHECK", "EXECUTE / RESPOND"])

    # PAGE 16 END -> BREAK TO PAGE 17
    doc.add_page_break()

    # =========================================================================
    # PAGE 17: SYSTEM DESIGN, SETUP & VOICE INTEGRATION (MATCHING 1.PDF PAGES 18 & 19)
    # =========================================================================
    add_custom_heading(doc, "SYSTEM DESIGN, SETUP AND VOICE INTEGRATION", level=1, presenter="Presenter: Bhaskar  •  Role: System Installation, setup.bat & System Activation")
    
    add_custom_heading(doc, "4.2.1 System Setup Procedure (Automated Launcher)", level=2)
    setup_steps = [
        ["1", "Clone or extract the IRIS-AI repository into the target directory (e.g., C:\\Users\\...\\Desktop\\IRIS-AI)."],
        ["2", "Run setup.bat as Administrator: verifies Python 3.12 64-bit and creates virtual environment (.venv) if missing."],
        ["3", "Automated pip install reads requirements.txt (FastAPI, uvicorn, opencv-python, pywin32, edge-tts, sounddevice)."],
        ["4", "setup.bat checks Node.js v20+ and runs npm install inside the frontend directory."],
        ["5", "Verifies local weights: face_detection_yunet_2023mar.onnx and face_recognition_sface_2021dec.onnx."],
        ["6", "Validates .env configuration: Groq API key slots, Ollama endpoints, audio voice presets, and debug flags."],
        ["7", "Execute start_all.bat: launches FastAPI server (port 5743) and Vite dev server (port 3001) in parallel."],
        ["8", "System initializes audio watchdog, camera capture daemon, and SQLite memory tables with automated health check ping."]
    ]
    t_set = doc.add_table(rows=len(setup_steps) + 1, cols=2)
    style_table(t_set, [Inches(0.4), Inches(6.3)], ["Step", "Installation & Activation Action in Codebase"], setup_steps, font_size=7.2)

    add_custom_heading(doc, "4.2.2 Dual-Pipeline Voice Integration & Resilience", level=2)
    add_body_p(doc, 
        "Voice failures are catastrophic for virtual assistants. Bhaskar and Aruna engineered a dual-pipeline speech synthesis architecture. "
        "Under online conditions, text routes to high-fidelity Edge-TTS neural models (SwaraNeural for Hindi, AriaNeural for English). "
        "If internet connectivity fails or times out, the engine seamlessly fails over to Windows native SAPI5 SpVoice in under 0.18s, guaranteeing 100% speech availability."
    )
    
    add_figure_img(doc, "flowchart_4_voice_resilience.png", "Figure 4.1 Dual-Pipeline Voice Engine & Speech Watchdog Architecture.", width_in=4.6)

    add_custom_heading(doc, "Active Voice Profiles in IRIS-AI", level=3)
    add_bullet(doc, "english (primary): en-US-AriaNeural (+15% rate, confident articulate female companion persona).")
    add_bullet(doc, "hindi (primary): hi-IN-SwaraNeural (+4% rate, +3Hz pitch, authentic warm Hindi female voice).")
    add_bullet(doc, "offline_fallback: SAPI.SpVoice (Hazel/Zira, 100% local Windows native synthesis, 0.18s failover).")

    # PAGE 17 END -> BREAK TO PAGE 18
    doc.add_page_break()

    # =========================================================================
    # PAGE 18: FUNCTIONAL IMPLEMENTATION & TESTING (MATCHING 1.PDF PAGES 20 & 21)
    # =========================================================================
    add_custom_heading(doc, "FUNCTIONAL IMPLEMENTATION, TESTING AND VALIDATION", level=1)
    
    add_custom_heading(doc, "4.2.3 Core Functions & Measured Execution Latencies", level=2)
    lat_data = [
        ["Playable Chess Game", "Synthesizes complete HTML5/Canvas chess with AI minimax", "'create a chess game to play'", "0.101s", "Success"],
        ["Instant Carrom Game", "HTML5 canvas game with 2D elastic collision & friction physics", "'create a carrom game to play'", "0.043s", "Success"],
        ["Responsive Website Builder", "Single-page modern responsive gym/portfolio site synthesis", "'create a website for a gym'", "8.342s", "Success"],
        ["Targeted Clean Code Writing", "Synthesizes code to target directory with zero extra subfolders", "'write python code on desktop for stopwatch'", "3.097s", "Success"],
        ["Win32 Window Minimization", "Direct Shell desktop reveal via user32.dll ctypes", "'minimize all the tabs'", "0.021s", "Success"],
        ["Offline Speech Fallback", "Switches from Edge-TTS to native SAPI5 upon network drop", "Simulated network disconnect", "0.184s", "Success"],
        ["Biometric Face Match", "YuNet face detection + SFace embedding comparison", "Webcam frame owner authentication", "0.038s", "Success"]
    ]
    t_lat = doc.add_table(rows=len(lat_data) + 1, cols=5)
    style_table(t_lat, [Inches(1.5), Inches(1.8), Inches(1.7), Inches(0.7), Inches(0.8)], ["Function Area", "Operation Details", "Query Example", "Time", "Status"], lat_data, font_size=7.0)

    add_custom_heading(doc, "4.3 Testing and Validation Suite", level=2)
    add_body_p(doc, 
        "The complete architecture was validated using three comprehensive automated test suites: (1) test_four_new_capabilities.py "
        "validating SAPI5 offline fallback, 6 game generators, 4 website templates, and zero-subfolder code writing; (2) test_hands_system.py "
        "verifying 14/14 automation subsystems; and (3) test_all_7_issues.py confirming operational fixes across WhatsApp navigation, terminal execution, "
        "and window snapping. All test suites achieved a 100% pass rate."
    )

    add_custom_heading(doc, "4.3.3 Error Handling & Controlled Fallback Flow", level=2)
    add_flow_box(doc, ["ERROR DETECTED", "CLASSIFY FAILURE", "CONTROLLED FEEDBACK", "FALLBACK / SAFE STOP", "USER INFORMED"])

    # PAGE 18 END -> BREAK TO PAGE 19
    doc.add_page_break()

    # =========================================================================
    # PAGE 19: DEPLOYMENT, RESULTS & DISCUSSION (MATCHING 1.PDF PAGES 22 & 23)
    # =========================================================================
    add_custom_heading(doc, "DEPLOYMENT, RESULTS AND COMPARATIVE DISCUSSION", level=1)
    
    add_custom_heading(doc, "4.4 Deployment Overview & Checklist", level=2)
    add_flow_box(doc, ["PROJECT SOURCE", "INSTALL DEPENDENCIES", "CONFIGURE .ENV", "START BACKEND", "START FRONTEND", "VERIFY AI / VOICE", "RUN IRIS"])
    add_body_p(doc, 
        "Deployment checklist: (1) Windows 11 64-bit verification; (2) Port binding check (ports 5743 & 3001 clear); (3) .env configuration with key rotation; "
        "(4) Webcam & microphone device permission verification; (5) Local Ollama model pull (Qwen 2.5 3B); (6) Automated health check ping."
    )

    add_custom_heading(doc, "5.1 Comparative Analysis with Existing Virtual Assistants", level=2)
    comp_data = [
        ["Native Win32 Window Control", "No", "No", "Limited Sidecar", "No", "Yes (EnumWindows, Snap, Focus)"],
        ["Offline Speech Synthesis", "No", "No", "No", "No", "Yes (Native SAPI5 Fallback)"],
        ["Zero-Freeze STT Watchdog", "No", "No", "No", "No", "Yes (1000ms Heartbeat Thread)"],
        ["Targeted Clean Code Writing", "No", "No", "No", "Subfolder Pollution", "Yes (Zero-Subfolder Guard)"],
        ["Instant HTML5 Game Builder", "No", "No", "No", "Code Only", "Yes (Canvas Games + Auto Launch)"],
        ["Responsive Website Builder", "No", "No", "No", "Code Only", "Yes (Modern Single-Page Sites)"],
        ["Social Messaging (WhatsApp)", "No", "No", "No", "No", "Yes (Direct Desktop Navigation)"],
        ["Proactive Gaze Attraction", "No", "No", "No", "No", "Yes (YuNet dev_x Deviation Tracking)"],
        ["Bilingual Hindi / English", "Basic", "Basic", "Cloud Only", "English Only", "Yes (Swara / Aria Neural Clones)"]
    ]
    t_comp = doc.add_table(rows=len(comp_data) + 1, cols=6)
    style_table(t_comp, [Inches(1.6), Inches(0.8), Inches(0.8), Inches(0.9), Inches(0.9), Inches(1.7)], 
                ["Capability Dimension", "Apple Siri", "Amazon Alexa", "MS Copilot", "AutoGPT", "IRIS-AIOS (Proposed)"], comp_data, font_size=6.8)

    add_custom_heading(doc, "5.2 Technical Discussion", level=2)
    add_body_p(doc, 
        "The comparative analysis demonstrates that IRIS-AIOS is not merely a conversational wrapper. By unifying cognitive intent reasoning "
        "with native Win32 execution hands, offline speech resilience, and edge vision, IRIS-AIOS overcomes the passivity and sandboxed "
        "limitations of existing virtual assistants."
    )

    # PAGE 19 END -> BREAK TO PAGE 20
    doc.add_page_break()

    # =========================================================================
    # PAGE 20: CONCLUSION, FUTURE VISION & TEAM SEQUENCE (MATCHING 1.PDF PAGES 24 & 25)
    # =========================================================================
    add_custom_heading(doc, "CHAPTER 5 – CONCLUSION, FUTURE VISION AND TEAM SEQUENCE", level=1, presenter="Presenter: Bhuvana kruthi  •  Role: Results, Conclusion & Future Vision")
    
    add_custom_heading(doc, "5.1 Conclusion", level=2)
    add_body_p(doc, 
        "IRIS-AIOS establishes a new benchmark for multimodal desktop AI companions. By integrating a 52-pattern cognitive brain, hybrid local/cloud "
        "model routing, dual-pipeline speech synthesis with SAPI5 offline fallback, 3-tier memory (Temp, LongTemp, DeepLayer), edge vision with gaze "
        "tracking, and low-level Win32 ctypes hands automation, IRIS-AIOS overcomes the passivity of cloud chatbots. Experimental evaluations "
        "demonstrate sub-110ms execution, 100% voice stability, clean code synthesis without subfolder pollution, and robust biometric privacy."
    )
    
    add_custom_heading(doc, "5.2 Future Vision & Engineering Roadmap", level=2)
    add_bullet(doc, "Cross-Platform Portability: Porting the Hands automation layer to X11/Wayland on Linux and macOS Accessibility APIs.")
    add_bullet(doc, "NPU Hardware Acceleration: Offloading local LLMs and vision ONNX models to integrated NPUs via DirectML.")
    add_bullet(doc, "3D Mesh Gaze Tracking: Implementing dense facial mesh landmarking for multi-monitor pupil gaze tracking.")

    add_flow_box(doc, ["UNDERSTAND", "REMEMBER", "REASON", "DECIDE", "ACT SAFELY", "RESPOND"])

    add_custom_heading(doc, "Team Members and Topic Sequence (Final Presentation Sequence)", level=2)
    seq_data = [
        ["1", "Jude Livingston", "Project Introduction & System Scope", "Chapter 1 – Introduction"],
        ["2", "Aruna", "Language & Multimodal Emotion Intelligence", "Language & Emotion Handling"],
        ["3", "lokesh chandhra", "3-Tier Hierarchical Memory Architecture", "Memory and Context Continuity"],
        ["4", "Dhanush Dathu", "Native OS Hands Automation & Synthesis", "Automation / Hands Layer"],
        ["5", "Karunya", "UI/UX Development & Cybernetic HUD", "UI/UX Development – IRIS"],
        ["6", "Mohanhemanth", "Biometric Security & Privacy Governance", "Security, Privacy & Spatial Vision"],
        ["7", "Bhaskar", "System Installation, setup.bat & Activation", "System Design, Setup & Voice"],
        ["8", "VARUN SANDESH", "Computer Vision & Spatial Gaze Perception", "Vision, Presence & Gaze Tracking"],
        ["9", "Rishit", "Core Engine & API Keys Integration", "Core, Cognitive Pipeline & Model Router"],
        ["10", "Bhuvana kruthi", "Results, Conclusion & Future Vision", "Chapter 5 – Conclusion & Roadmap"]
    ]
    t_seq = doc.add_table(rows=len(seq_data) + 1, cols=4)
    style_table(t_seq, [Inches(0.4), Inches(1.8), Inches(2.5), Inches(2.0)], ["Seq", "Member Name", "Assigned Topic Role", "Documentation Section"], seq_data, font_size=7.0)

    add_custom_heading(doc, "Selected Academic References", level=3)
    refs_text = (
        "[1] Schick et al. (2023). Toolformer. NeurIPS.  "
        "[2] Wang et al. (2023). Voyager. arXiv:2305.16291.  "
        "[3] Zhang et al. (2023). YuNet Face Detection. ICCV.  "
        "[4] Microsoft Corp. (2026). Win32 API Reference: MSDN.  "
        "[5] OpenCV Team. (2024). SFace Biometric Recognition.  "
        "[6] Qwen Team. (2024). Qwen2.5 Technical Report.  "
        "[7] FastAPI Team. (2024). FastAPI High Performance Framework.  "
        "[8] W3C Speech API Community Group. (2023). Web Speech API Specification."
    )
    p_ref = doc.add_paragraph()
    p_ref.paragraph_format.space_before = Pt(2)
    p_ref.paragraph_format.space_after = Pt(0)
    r_rf = p_ref.add_run(refs_text)
    r_rf.font.name = "Calibri"
    r_rf.font.size = Pt(7.0)
    r_rf.font.color.rgb = COLOR_MUTED

    # SAVE DOCUMENT
    doc.save(OUTPUT_DOCX_1)
    print(f"Report successfully saved to project workspace: {OUTPUT_DOCX_1}")
    try:
        doc.save(OUTPUT_DOCX_2)
        print(f"Report successfully saved to Desktop: {OUTPUT_DOCX_2}")
    except Exception as e:
        print(f"Could not save to Desktop directly: {e}")


if __name__ == "__main__":
    build_full_project_dossier()
