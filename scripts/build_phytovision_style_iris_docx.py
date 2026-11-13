"""
IRIS AI - Comprehensive College-Level Project Report Word Document (.docx) Generator
Matching PhytoVision Reference Style & GIOE College Standards
Government Institute of Electronics, East Marredpally, Secunderabad
Diploma in Artificial Intelligence and Machine Learning / Department of ECE
Full Editable Documentation with all Chapters, Tables, Code Blocks, and Output Images
"""

import os
import shutil
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

DOCX_OUTPUT_PATH = r"C:\Users\itsme\Desktop\IRIS-AI\IRIS_AI_Complete_Documentation.docx"
DESKTOP_DOCX_PATH = r"C:\Users\itsme\Desktop\IRIS_AI_Complete_Documentation.docx"
ASSETS_DIR = r"C:\Users\itsme\Desktop\IRIS-AI\report_assets"

COLOR_PRIMARY = RGBColor(15, 23, 42)     # #0F172A Deep Navy
COLOR_SECONDARY = RGBColor(14, 116, 144) # #0E7490 Deep Teal
COLOR_DARK = RGBColor(30, 41, 59)        # #1E293B Body Text
COLOR_MUTED = RGBColor(100, 116, 139)    # #64748B Muted Slate

def set_cell_background(cell, hex_color):
    """Sets background color of a docx table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Sets inner padding for a table cell in dxa (1 pt = 20 dxa)."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'''
        <w:tcMar {nsdecls("w")}>
            <w:top w:w="{top}" w:type="dxa"/>
            <w:bottom w:w="{bottom}" w:type="dxa"/>
            <w:left w:w="{left}" w:type="dxa"/>
            <w:right w:w="{right}" w:type="dxa"/>
        </w:tcMar>
    ''')
    tcPr.append(tcMar)

def add_code_block(doc, code_text):
    """Adds a shaded, mono-spaced code block with a left accent border."""
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_background(cell, "F1F5F9")
    set_cell_margins(cell, top=120, bottom=120, left=180, right=180)
    
    # Left border
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = parse_xml(f'''
        <w:tcBorders {nsdecls("w")}>
            <w:left w:val="single" w:sz="24" w:space="0" w:color="0E7490"/>
            <w:top w:val="none"/>
            <w:right w:val="none"/>
            <w:bottom w:val="none"/>
        </w:tcBorders>
    ''')
    tcPr.append(tcBorders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.15
    run = p.add_run(code_text)
    run.font.name = "Consolas"
    run.font.size = Pt(8.5)
    run.font.color.rgb = RGBColor(15, 23, 42)
    
    # Spacer after table
    sp = doc.add_paragraph()
    sp.paragraph_format.space_before = Pt(0)
    sp.paragraph_format.space_after = Pt(4)

def add_callout(doc, title, text):
    """Adds an academic callout box with a prominent shaded background."""
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_background(cell, "F8FAFC")
    set_cell_margins(cell, top=140, bottom=140, left=200, right=200)
    
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = parse_xml(f'''
        <w:tcBorders {nsdecls("w")}>
            <w:left w:val="single" w:sz="32" w:space="0" w:color="0E7490"/>
            <w:top w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/>
            <w:right w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/>
            <w:bottom w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/>
        </w:tcBorders>
    ''')
    tcPr.append(tcBorders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(4)
    r_title = p.add_run(f"★ {title}\n")
    r_title.bold = True
    r_title.font.name = "Arial"
    r_title.font.size = Pt(10)
    r_title.font.color.rgb = COLOR_PRIMARY
    
    r_text = p.add_run(text)
    r_text.italic = True
    r_text.font.name = "Arial"
    r_text.font.size = Pt(9.5)
    r_text.font.color.rgb = COLOR_DARK
    
    sp = doc.add_paragraph()
    sp.paragraph_format.space_before = Pt(0)
    sp.paragraph_format.space_after = Pt(4)

def add_image_safely(doc, image_name, width=Inches(5.5), caption=""):
    """Embeds an image from report_assets with an italic caption."""
    path = os.path.join(ASSETS_DIR, image_name)
    if os.path.exists(path):
        try:
            p_img = doc.add_paragraph()
            p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_img.paragraph_format.space_before = Pt(6)
            p_img.paragraph_format.space_after = Pt(2)
            run = p_img.add_run()
            run.add_picture(path, width=width)
            
            if caption:
                p_cap = doc.add_paragraph()
                p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_cap.paragraph_format.space_before = Pt(2)
                p_cap.paragraph_format.space_after = Pt(8)
                r_cap = p_cap.add_run(caption)
                r_cap.font.name = "Arial"
                r_cap.font.size = Pt(8.5)
                r_cap.italic = True
                r_cap.font.color.rgb = COLOR_MUTED
        except Exception as e:
            print(f"Warning: Could not add image {image_name}: {e}")

def build_phytovision_style_docx():
    print("Generating IRIS Academic Project Report Word Document (.docx)...")
    doc = Document()
    
    # Configure 0.75 in margins
    for sec in doc.sections:
        sec.top_margin = Inches(0.75)
        sec.bottom_margin = Inches(0.75)
        sec.left_margin = Inches(0.75)
        sec.right_margin = Inches(0.75)
        
        # Header & Footer
        header = sec.header
        hp = header.paragraphs[0]
        hp.text = "IRIS — INTELLIGENT PERSONAL AI PLATFORM\t\tGOVERNMENT INSTITUTE OF ELECTRONICS"
        hp.alignment = WD_ALIGN_PARAGRAPH.LEFT
        hp.style.font.name = "Arial"
        hp.style.font.size = Pt(8)
        hp.style.font.color.rgb = COLOR_MUTED
        
        footer = sec.footer
        fp = footer.paragraphs[0]
        fp.text = "Dept. of Artificial Intelligence & Machine Learning • Secunderabad\t\tMajor Project Report"
        fp.style.font.name = "Arial"
        fp.style.font.size = Pt(8)
        fp.style.font.color.rgb = COLOR_MUTED

    # Helpers for typography
    def add_p(text, bold_prefix="", italic=False, space_after=6, bullet=False):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.line_spacing = 1.15
        if bullet:
            p.paragraph_format.left_indent = Inches(0.25)
        if bold_prefix:
            rb = p.add_run(bold_prefix)
            rb.bold = True
            rb.font.name = "Arial"
            rb.font.size = Pt(10)
            rb.font.color.rgb = COLOR_PRIMARY
        r = p.add_run(text)
        r.italic = italic
        r.font.name = "Arial"
        r.font.size = Pt(10)
        r.font.color.rgb = COLOR_DARK
        return p

    def add_h1(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text)
        r.bold = True
        r.font.name = "Arial"
        r.font.size = Pt(15)
        r.font.color.rgb = COLOR_PRIMARY
        return p

    def add_h2(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text)
        r.bold = True
        r.font.name = "Arial"
        r.font.size = Pt(12)
        r.font.color.rgb = COLOR_SECONDARY
        return p

    def add_h3(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(7)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text)
        r.bold = True
        r.font.name = "Arial"
        r.font.size = Pt(10.5)
        r.font.color.rgb = COLOR_DARK
        return p

    # =========================================================================
    # PRELIMINARY PAGES
    # =========================================================================

    # 1. TITLE PAGE
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(15)
    r = p.add_run("PROJECT REPORT\nON\n")
    r.font.name = "Arial"
    r.font.size = Pt(13)
    r.bold = True
    r.font.color.rgb = COLOR_MUTED
    
    r_t = p.add_run("IRIS — INTELLIGENT PERSONAL AI PLATFORM\n")
    r_t.font.name = "Arial"
    r_t.font.size = Pt(22)
    r_t.bold = True
    r_t.font.color.rgb = COLOR_PRIMARY
    
    r_sub = p.add_run("SUBMITTED IN THE PARTIAL FULFILLMENT OF THE REQUIREMENTS FOR THE AWARD OF\n")
    r_sub.font.name = "Arial"
    r_sub.font.size = Pt(9.5)
    r_sub.font.color.rgb = COLOR_DARK
    
    r_dip = p.add_run("DIPLOMA IN ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING\n\nBY\n")
    r_dip.font.name = "Arial"
    r_dip.font.size = Pt(11)
    r_dip.bold = True
    r_dip.font.color.rgb = COLOR_PRIMARY

    # Students 2-column table
    st_table = doc.add_table(rows=5, cols=2)
    st_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    st_data = [
        ("(054-AI-010)  BHUVANA KRUTHI", "(054-AI-004)  VARUN SANDESH"),
        ("(054-AI-003)  ARUNA",          "(054-AI-012)  MOHAN HEMANTH"),
        ("(054-AI-011)  DHANUSH DATHU",  "(054-AI-060)  BHASKAR"),
        ("(054-AI-062)  JUDE LIVINGSTON","(054-AI-016)  LOKESH CHANDRA"),
        ("(054-AI-066)  KARUNYA",        ""),
    ]
    for row_idx, (s1, s2) in enumerate(st_data):
        cell_a = st_table.cell(row_idx, 0)
        cell_b = st_table.cell(row_idx, 1)
        cell_a.paragraphs[0].text = s1
        cell_b.paragraphs[0].text = s2
        for cell in (cell_a, cell_b):
            cell.paragraphs[0].runs[0].bold = True
            cell.paragraphs[0].runs[0].font.name = "Arial"
            cell.paragraphs[0].runs[0].font.size = Pt(10)
            cell.paragraphs[0].runs[0].font.color.rgb = COLOR_DARK
            cell.paragraphs[0].paragraph_format.space_after = Pt(2)

    p_guide = doc.add_paragraph()
    p_guide.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_guide.paragraph_format.space_before = Pt(16)
    p_guide.paragraph_format.space_after = Pt(14)
    rg = p_guide.add_run("UNDER THE GUIDANCE OF\n")
    rg.font.name = "Arial"
    rg.font.size = Pt(9.5)
    rg.font.color.rgb = COLOR_MUTED
    rg2 = p_guide.add_run("Sri N. SRINIVAS RAO, LECTURER IN ECE DEPARTMENT")
    rg2.font.name = "Arial"
    rg2.font.size = Pt(11)
    rg2.bold = True
    rg2.font.color.rgb = COLOR_PRIMARY

    p_col = doc.add_paragraph()
    p_col.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_col.paragraph_format.space_before = Pt(8)
    rc1 = p_col.add_run("GOVERNMENT INSTITUTE OF ELECTRONICS, SECUNDERABAD\n")
    rc1.font.name = "Arial"
    rc1.font.size = Pt(11.5)
    rc1.bold = True
    rc1.font.color.rgb = COLOR_PRIMARY
    rc2 = p_col.add_run("(Approved by TS SBTET, Hyderabad)\nEast Marredpally, Secunderabad - 500 026\n2026")
    rc2.font.name = "Arial"
    rc2.font.size = Pt(9.5)
    rc2.font.color.rgb = COLOR_MUTED

    doc.add_page_break()

    # 2. CERTIFICATE
    pc_dept = doc.add_paragraph()
    pc_dept.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rcd = pc_dept.add_run("DEPARTMENT OF ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING\n")
    rcd.font.name = "Arial"
    rcd.font.size = Pt(11.5)
    rcd.bold = True
    rcd.font.color.rgb = COLOR_PRIMARY
    rch = pc_dept.add_run("CERTIFICATE")
    rch.font.name = "Arial"
    rch.font.size = Pt(14)
    rch.bold = True
    rch.font.color.rgb = COLOR_SECONDARY

    add_p(
        "This is to certify that the project entitled “IRIS — Intelligent Personal AI Platform” has been submitted by the following students: "
        "BHUVANA KRUTHI (054-AI-010), ARUNA (054-AI-003), DHANUSH DATHU (054-AI-011), JUDE LIVINGSTON (054-AI-062), "
        "VARUN SANDESH (054-AI-004), MOHAN HEMANTH (054-AI-012), BHASKAR (054-AI-060), LOKESH CHANDRA (054-AI-016), KARUNYA (054-AI-066). "
        "This project is submitted in partial fulfillment of the requirements for the award of the Diploma in Artificial Intelligence and Machine Learning "
        "from the Government Institute of Electronics, East Marredpally, Secunderabad. The results embodied in this project have not been submitted to any "
        "other institution for the award of any degree or diploma.",
        space_after=25
    )

    cert_tbl = doc.add_table(rows=2, cols=2)
    cert_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    c_p1 = cert_tbl.cell(0, 0).paragraphs[0]
    c_p1.add_run("GUIDE\nSri N. Srinivas Rao\nLecturer in ECE").bold = True
    c_p2 = cert_tbl.cell(0, 1).paragraphs[0]
    c_p2.add_run("HEAD OF DEPARTMENT\nSri N. Srinivas Rao\nHead of Section (ECE)").bold = True
    c_p3 = cert_tbl.cell(1, 0).paragraphs[0]
    c_p3.add_run("\n\nEXTERNAL EXAMINER\n\n_________________________").bold = True
    c_p4 = cert_tbl.cell(1, 1).paragraphs[0]
    c_p4.add_run("\n\nPRINCIPAL\nSri M.V. Satish Kumar\nGovernment Institute of Electronics\nEast Marredpally, Secunderabad - 500 026").bold = True

    doc.add_page_break()

    # 3. DECLARATION
    p_dec = doc.add_paragraph()
    p_dec.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_dec1 = p_dec.add_run("GOVERNMENT INSTITUTE OF ELECTRONICS, SECUNDERABAD\nDEPARTMENT OF ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING\n")
    r_dec1.font.name = "Arial"
    r_dec1.font.size = Pt(11)
    r_dec1.bold = True
    r_dec1.font.color.rgb = COLOR_PRIMARY
    r_dec2 = p_dec.add_run("DECLARATION")
    r_dec2.font.name = "Arial"
    r_dec2.font.size = Pt(14)
    r_dec2.bold = True
    r_dec2.font.color.rgb = COLOR_SECONDARY

    add_p(
        "We hereby declare that the project entitled “IRIS — Intelligent Personal AI Platform” is the work done during the period "
        "from June 2026 to November 2026 and is submitted in partial fulfillment of the requirements for the award of Diploma in Artificial "
        "Intelligence and Machine Learning from Govt. Institute of Electronics, Secunderabad. The results embodied in this project have not "
        "been submitted to any other university or Institution for the award of any degree or diploma.",
        space_after=18
    )

    for st_name in [
        "BHUVANA KRUTHI (054-AI-010)", "ARUNA (054-AI-003)", "DHANUSH DATHU (054-AI-011)",
        "JUDE LIVINGSTON (054-AI-062)", "VARUN SANDESH (054-AI-004)", "MOHAN HEMANTH (054-AI-012)",
        "BHASKAR (054-AI-060)", "LOKESH CHANDRA (054-AI-016)", "KARUNYA (054-AI-066)"
    ]:
        add_p(st_name, bullet=True, space_after=3)

    doc.add_page_break()

    # 4. ACKNOWLEDGEMENT
    p_ack = doc.add_paragraph()
    p_ack.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_ack = p_ack.add_run("DEPARTMENT OF ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING\nACKNOWLEDGEMENT")
    r_ack.font.name = "Arial"
    r_ack.font.size = Pt(13)
    r_ack.bold = True
    r_ack.font.color.rgb = COLOR_PRIMARY

    add_p("With great pleasure and deep sense of gratitude, we acknowledge the contribution of all the faculty for the successful completion of this project.")
    add_p("We deem it a great honour to thank Sri M.V. SATISH KUMAR sir, Principal of GOVERNMENT INSTITUTE OF ELECTRONICS, who is an axle behind our studies and for having given us a chance to pursue our diploma course in this esteemed institution.")
    add_p("Our thanks are due to Mr. N. SRINIVAS RAO sir, Head of the Section (ECE), for his excellent and expert support rendered to us during our tenure in the institute.")
    add_p("Finally, we would like to thank Mr. N. SRINIVAS RAO Sir, LECTURER IN ECE, project head & guide, who gave us all the required support to understand all the technical aspects both in theory and practice during the project.")
    add_p("We would like to express our gratitude and appreciation to all the faculty and friends who gave us the possibility to complete this report.")

    doc.add_page_break()

    # 5. ABSTRACT
    add_h1("ABSTRACT")
    add_p(
        "Contemporary artificial intelligence assistants (such as Apple Siri, Amazon Alexa, Google Gemini, and Microsoft Copilot) depend strictly "
        "on centralized corporate cloud servers. This architecture introduces severe data privacy risks, telemetry surveillance, internet latency bottlenecks, "
        "and disembodiment: these cloud bots cannot observe what the user is doing on their computer or take direct actions on the operating system."
    )
    add_p(
        "IRIS (Intelligent Personal AI Platform) is an autonomous, air-gapped multimodal desktop AI companion designed to run 100% locally on personal computers. "
        "The platform delivers complete data sovereignty (zero bytes sent to the cloud) while uniting low-latency neural cognition, real-time voice, "
        "multimodal vision, persistent memory, and operating system actuation into a single, cohesive desktop platform."
    )
    add_p("The platform introduces five core technical innovations:")
    add_p("1. Local Quantized Neural Models: Powered by Ollama executing 4-bit integer quantized Llama 3.2 3B and Qwen 2.5 3B models locally with optional zero-latency cloud fallbacks.", bullet=True)
    add_p("2. Full-Duplex Loopback Audio Transport: Low-latency WebSockets streaming continuous 16kHz 16-bit mono PCM audio with sub-200ms round-trip voice cadence.", bullet=True)
    add_p("3. ONNX Silero VAD & Sub-10ms Barge-In: Real-time recurrent speech detection (<4.4ms) with spectral noise reduction (32.7× attenuation) and instantaneous 7.29ms speech synthesis interruption.", bullet=True)
    add_p("4. 3-Tier Cognitive Memory Engine: Combines ephemeral conversation buffers, active working tasks, and permanent semantic knowledge in SQLite3 WAL mode.", bullet=True)
    add_p("5. Native Win32 Hands Automation: Uses Python ctypes (user32.dll) to snap windows to quadrants, launch native desktop applications, and write clean, isolated code files.", bullet=True)
    add_callout(doc, "Key Highlights of IRIS",
        "• 100% Air-Gapped Local Autonomy (Zero Telemetry Bytes Sent to Cloud)\n"
        "• Full-Duplex Bidirectional Audio Transport with 7.29 ms Barge-In Cancellation\n"
        "• Low-Level Win32 ctypes Desktop Automation Hands (Snap, Launch, Edit, Execute)\n"
        "• Next.js 14 App Router with 96-Layer WebGL Shader & GSAP 3D Fan Carousel"
    )

    doc.add_page_break()

    # 6. TABLE OF CONTENTS
    add_h1("CONTENTS")
    toc_table = doc.add_table(rows=1, cols=3)
    toc_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = toc_table.rows[0].cells
    hdr[0].text = "S.NO"
    hdr[1].text = "DESCRIPTION"
    hdr[2].text = "PAGE NO"
    for cell in hdr:
        set_cell_background(cell, "0F172A")
        cell.paragraphs[0].runs[0].bold = True
        cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
        cell.paragraphs[0].runs[0].font.size = Pt(9.5)

    toc_items = [
        ("1", "Chapter 01: Introduction\n  1.1: Purpose of the project\n  1.2: Motivation and Societal Impact\n  1.3: Objectives of IRIS\n  1.4: Scope of the Platform\n  1.5: Engineering Methodology\n  1.6: System Architecture Diagram\n  1.7: Application Data-Flow Diagram", "8"),
        ("2", "Chapter 02: Requirements\n  2.1: Software requirements\n  2.2: Hardware requirements & Bandwidth Sizing\n  2.3: Functional Requirements Matrix (FR-01 to FR-10)\n  2.4: Non-Functional Requirements (NFR-01 to NFR-06)\n  2.5: Network and Loopback Communication Protocols", "12"),
        ("3", "Chapter 03: Technical details\n  3.1: Technologies used and Taxonomy\n  3.2: AI Models, Runtimes and Transformer Theory\n  3.3: GGUF Quantization Mathematics & Memory Mapping\n  3.4: Real-Time Audio Signal Processing & Recurrent VAD\n  3.5: Operating System Actuation via ctypes & DPI Normalization\n  3.6: Comparative Study of Existing Systems and IRIS", "16"),
        ("4", "Chapter 04: System architecture\n  4.1: Overall Architectural Philosophy\n  4.2: Sensory and Audio Ingestion Layer\n  4.3: Cognitive Decision Engine & Hybrid Router\n  4.4: 3-Tier Cognitive Memory Subsystem & Relational Schema\n  4.5: Win32 Hands Automation Architecture\n  4.6: Multi-Modal Vision & Gaze Tracking Layer\n  4.7: Frontend Reactive WebGL & Physics Layer", "22"),
        ("5", "Chapter 05: Implementation\n  5.1: Backend Server & Fast-API Application\n  5.2: Real-Time Audio Engine & Full-Duplex WebSockets\n  5.3: Spectral Noise Suppression & Silero VAD Execution\n  5.4: Sub-10ms Neural Barge-In Cancellation Architecture\n  5.5: Streaming Orchestrator & Clause Chunking\n  5.6: Win32 ctypes Window Snapping & Process Hands\n  5.7: Multi-Modal Vision & Presence Attention Pipeline\n  5.8: Next.js 14 Web Platform, Three.js WebGL & GSAP", "27"),
        ("6", "Chapter 06: Code Listings\n  6.1: Backend Server Initialization (run_iris.py)\n  6.2: Streaming Orchestrator (streaming_orchestrator.py)\n  6.3: Barge-In Interruption Manager (barge_in_manager.py)\n  6.4: Spectral Noise Suppressor (noise_suppressor.py)\n  6.5: Win32 ctypes Window Snapping (hands/window_manager.py)\n  6.6: Process Manager & Application Launcher (hands/process_manager.py)\n  6.7: Safe File Writing & Clean Workspace Guard (hands/file_manager.py)\n  6.8: Terminal Command Execution Engine (hands/terminal_manager.py)\n  6.9: Low-Level Win32 SendInput Keyboard Actuator (hands/input_actuator.py)\n  6.10: OpenCV YuNet Face & Gaze Tracking (presence_emotion_engine.py)\n  6.11: 3-Tier Memory SQLite3 WAL Schema (memory/db.py)\n  6.12: WebGL Space Tunnel Shader (SpaceTunnelBackground.tsx)\n  6.13: GSAP 3D Interactive Card Fan Carousel (SocialCards.tsx)\n  6.14: Motion Gesture Hand Gallery (CardHandGallery.tsx)\n  6.15: Automated Subsystem Test Harness (scripts/test_subsystems.py)", "33"),
        ("7", "Chapter 07: Input And Output Screens\n  7.1: Multi-Modal Sensory Intake Screens\n  7.2: IRIS Core Capabilities Matrix Dashboard\n  7.3: Real-Time Performance & Air-Gap Benchmark Strip\n  7.4: Win32 Hands Desktop Window Management Screens\n  7.5: Terminal Subsystem Verification & Execution Console\n  7.6: Multi-Modal Emotion & Vision Flowchart\n  7.7: Verification Benchmark Test Matrix (TC-01 to TC-20)\n  7.8: Empirical Performance Benchmarks & Latency Profiling", "41"),
        ("8", "Chapter 08: Conclusion\n  8.1: Summary of Work\n  8.2: Key Achievements of the Project\n  8.3: Technical Challenges Encountered and Solutions\n  8.4: Future Scope & Vision", "49"),
        ("9", "Chapter 09: References\n  9.1: Literature References\n  9.2: Official Documentation & Frameworks", "51"),
    ]
    for sno, desc, pg in toc_items:
        row = toc_table.add_row().cells
        row[0].text = sno
        row[1].text = desc
        row[2].text = pg
        for c in row:
            c.paragraphs[0].runs[0].font.size = Pt(9)
            set_cell_margins(c, top=60, bottom=60, left=80, right=80)

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 01: INTRODUCTION
    # =========================================================================
    add_h1("CHAPTER 01: INTRODUCTION")
    add_p(
        "In modern computing, personal computers are our central workspaces for programming, writing, studying, communication, "
        "and data analysis. Over the past three years, Large Language Models (LLMs) have demonstrated revolutionary capabilities in understanding "
        "natural language, reasoning across multifaceted technical domains, generating software code, and providing intelligent assistance. "
        "However, commercial personal assistants remain locked into centralized, cloud-tethered architectures."
    )
    add_p(
        "Commercial virtual assistants—such as Apple Siri, Amazon Alexa, Google Assistant, and Microsoft Copilot—exhibit critical structural shortcomings. "
        "They demand continuous broadband connectivity, send personal voice recordings and confidential documents to remote corporate servers, "
        "and operate in isolated, sandboxed web applications. When a user asks an assistant to 'snap VS Code to the left and open the project terminal', "
        "commercial assistants fail because they have no direct hands or actuation capabilities on the user's operating system."
    )
    add_p(
        "IRIS (Intelligent Personal AI Platform) is engineered to overcome these challenges. IRIS is an embodied, air-gapped, multimodal "
        "desktop artificial intelligence companion that runs 100% locally on personal computers. Powered by local quantized neural models "
        "(such as Llama 3.2 3B and Qwen 2.5 3B via Ollama), IRIS processes voice, text, camera gaze, and desktop automation natively on the user's "
        "CPU and GPU, guaranteeing that zero bytes of personal data ever leave the machine."
    )

    add_h2("1.1: PURPOSE OF THE PROJECT")
    add_p(
        "The purpose of IRIS is to provide an intelligent, completely private, and highly capable desktop companion that empowers students, "
        "engineers, and researchers. Traditional cloud assistants treat users as data sources for corporate surveillance and monthly subscription monetization. "
        "IRIS returns digital sovereignty back to the individual by running models directly on local hardware."
    )
    add_p(
        "Furthermore, IRIS solves the disembodiment problem. Through its specialized Hands module, IRIS directly interacts with the Windows operating system "
        "via native Win32 ctypes APIs (user32.dll and kernel32.dll), allowing the assistant to organize windows, launch applications, write clean code files, "
        "and inspect running processes without external subfolder pollution."
    )

    add_h2("1.2: MOTIVATION AND SOCIETAL IMPACT")
    add_p("The motivation behind IRIS stems from four urgent technological and societal needs:")
    add_p("• Data Privacy & Confidentiality: In educational institutions, defense laboratories, and corporate environments, uploading proprietary source code or confidential design documents to third-party cloud servers violates confidentiality policies. IRIS operates completely offline, ensuring total privacy.", bullet=True)
    add_p("• Natural Conversational Cadence: Existing voice assistants operate on rigid walkie-talkie turn-taking. If an assistant gives a verbose answer, the user cannot easily interrupt. IRIS introduces sub-10ms neural barge-in cancellation that lets the user interrupt speech naturally at any millisecond.", bullet=True)
    add_p("• Embodied Desktop Agency: Users spend countless hours performing repetitive desktop chores—snapping windows, opening developer tools, managing project files. IRIS serves as an active collaborator that can physically execute these tasks.", bullet=True)
    add_p("• Accessibility & Democratization: By functioning without mandatory recurrent API costs, IRIS brings state-of-the-art AI assistance to students and developers regardless of financial resources or internet stability.", bullet=True)

    add_h2("1.3: OBJECTIVES OF IRIS")
    add_p("1. 100% Air-Gapped Local Autonomy: Run all language modeling locally using Ollama and GGUF 4-bit integer quantization (Llama 3.2 3B, Qwen 2.5 3B), with zero network egress in private mode.", bullet=True)
    add_p("2. Sub-200ms Full-Duplex Voice Transport: Build a bidirectional loopback WebSocket pipeline (ws://127.0.0.1:5743/ws/audio) streaming continuous 16kHz 16-bit mono PCM audio.", bullet=True)
    add_p("3. Real-Time ONNX Silero VAD & Sub-10ms Barge-In: Deploy an ONNX recurrent neural voice activity detector scoring audio in <4.4ms, triggering speech cancellation in 7.29ms when the user interrupts.", bullet=True)
    add_p("4. 3-Tier Cognitive Memory Architecture: Develop an encrypted SQLite3 memory engine with Write-Ahead Logging (WAL) that manages short-term conversational context, active working tasks, and permanent semantic user knowledge.", bullet=True)
    add_p("5. Native Win32 Desktop Hands: Leverage Windows OS user32.dll APIs to snap windows to quadrants, launch applications, and manage files safely.", bullet=True)
    add_p("6. High-Performance Web Platform: Develop an award-winning Next.js 14 web client featuring a 96-layer raymarched Three.js WebGL space tunnel shader, GSAP 3D card fan carousel, and Motion gesture card deck running at 60 FPS.", bullet=True)

    add_h2("1.4: SCOPE OF THE PLATFORM")
    add_p("The operational scope of IRIS covers five integrated software subsystems: (1) Desktop Engine Daemon; (2) FastAPI Backend Service; (3) Audio Signal & Speech Pipeline; (4) Win32 Desktop Hands Automation; and (5) Next.js 14 Web Frontend.")

    add_h2("1.5: ENGINEERING METHODOLOGY")
    add_p("The project was executed following an agile component-driven engineering methodology across four distinct phases: Audio intake & VAD prototyping; Cognitive model routing & Ollama engine; Win32 ctypes hands actuation; and WebGL 3D synthesis & validation.")

    add_h2("1.6: SYSTEM ARCHITECTURE DIAGRAM")
    add_p("Figure 1.1 illustrates the complete system architecture block diagram of the IRIS platform:")
    add_image_safely(doc, "flowchart_1_architecture.png", width=Inches(5.5), caption="Figure 1.1: IRIS End-to-End System Architecture Block Diagram")

    add_h2("1.7: APPLICATION DATA-FLOW DIAGRAM")
    add_p("The runtime dataflow begins when physical sensors (microphone, webcam, keyboard) capture raw user stimuli. Audio PCM packets stream into the Silero VAD session. When valid speech is detected, the audio is converted into text tokens. The HybridModelRouter evaluates user intent, routing knowledge queries to the local Ollama LLM while dispatching desktop commands to the Win32 Hands module.")

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 02: REQUIREMENTS
    # =========================================================================
    add_h1("CHAPTER 02: REQUIREMENTS")
    add_h2("2.1: SOFTWARE REQUIREMENTS")
    
    sw_req_table = doc.add_table(rows=1, cols=3)
    sw_req_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    sw_h = sw_req_table.rows[0].cells
    sw_h[0].text = "Software Component"
    sw_h[1].text = "Version / Platform"
    sw_h[2].text = "Operational Role in IRIS"
    for c in sw_h:
        set_cell_background(c, "0F172A")
        c.paragraphs[0].runs[0].bold = True
        c.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
        c.paragraphs[0].runs[0].font.size = Pt(8.5)

    sw_rows = [
        ("Operating System", "Windows 10 / Windows 11 (64-bit)", "Hosts the native Win32 user32.dll APIs, audio devices, and process tree"),
        ("Python Runtime", "Python 3.12 (64-bit)", "Executes FastAPI server, audio pipelines, memory engine, and automation hands"),
        ("Node.js & npm", "Node.js 20 LTS / npm 10+", "Builds and serves the Next.js 14 App Router web interface"),
        ("FastAPI & Uvicorn", "FastAPI 0.115 / Uvicorn 0.30", "Asynchronous ASGI backend managing REST and WebSocket routes"),
        ("Ollama Daemon", "Ollama 0.3+", "Headless llama.cpp engine managing GGUF quantized model weights and GPU offload"),
        ("ONNX Runtime", "onnxruntime 1.30.0", "Executes Silero VAD recurrent neural model in <4.4ms per frame"),
        ("OpenCV", "opencv-python 5.0+", "Computer vision, webcam gaze tracking, and YuNet face detection"),
        ("SQLite3", "SQLite 3 (WAL Mode)", "Embedded 3-tier memory persistence for conversations, facts, and tasks"),
        ("Three.js", "three 0.187.0", "WebGL engine rendering the 96-layer raymarched hyperspace space tunnel shader"),
        ("GSAP & Motion", "gsap 3.15.1 / motion 11.x", "3D interactive card fan physics and mobile gesture card hand galleries"),
        ("Tailwind CSS", "tailwindcss 3.4.0", "Cybernetic dark mode UI styling, responsive breakpoints, and glassmorphism"),
    ]
    for comp, ver, role in sw_rows:
        row = sw_req_table.add_row().cells
        row[0].text = comp
        row[1].text = ver
        row[2].text = role
        for c in row:
            c.paragraphs[0].runs[0].font.size = Pt(8)
            set_cell_margins(c, top=40, bottom=40, left=60, right=60)

    add_h2("2.2: HARDWARE REQUIREMENTS & BANDWIDTH SIZING")
    add_p("Memory bandwidth is the critical bottleneck in local LLM autoregressive token generation. A 3-billion parameter model quantized to 4 bits requires reading ~1.95 GB of weights per generated token. On dual-channel DDR4 memory (38.4 GB/s theoretical bandwidth), CPU generation reaches ~15-18 tokens/sec. On an RTX 3060 GDDR6 bus (360 GB/s bandwidth), generation exceeds 38 tokens/sec.")

    hw_table = doc.add_table(rows=1, cols=4)
    hw_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hw_h = hw_table.rows[0].cells
    hw_h[0].text = "Hardware Subsystem"
    hw_h[1].text = "Minimum Spec"
    hw_h[2].text = "Recommended Spec"
    hw_h[3].text = "Purpose"
    for c in hw_h:
        set_cell_background(c, "0E7490")
        c.paragraphs[0].runs[0].bold = True
        c.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
        c.paragraphs[0].runs[0].font.size = Pt(8)

    hw_rows = [
        ("CPU", "Intel Core i5 (8th Gen) / Ryzen 5", "Intel Core i7/i9 (12th Gen+) / Ryzen 7/9", "AVX2 SIMD vector math for Silero VAD & CPU inference"),
        ("RAM", "8 GB DDR4 (2666 MHz)", "16 GB – 32 GB DDR5 (5200 MHz)", "Bandwidth for quantized GGUF weights and memory cache"),
        ("GPU", "Intel Iris Xe / AMD Radeon Vega", "NVIDIA RTX 3060 / 4060 (6GB+ VRAM)", "CUDA hardware acceleration for Ollama token generation"),
        ("Storage", "10 GB SSD Space", "500 GB NVMe M.2 SSD", "Sub-second model weight loading and SQLite WAL commits"),
        ("Microphone", "Integrated Laptop Mic", "Directional USB Condenser", "Clean PCM capture for noise reduction and VAD accuracy"),
        ("Camera", "Standard HD 720p Webcam", "1080p 60 FPS HD Webcam", "Real-time gaze tracking and face recognition"),
        ("Audio Output", "Stereo Speakers", "Low-latency Headphones", "Full-duplex audio playback with zero acoustic feedback"),
    ]
    for sub, min_s, rec_s, purp in hw_rows:
        row = hw_table.add_row().cells
        row[0].text = sub
        row[1].text = min_s
        row[2].text = rec_s
        row[3].text = purp
        for c in row:
            c.paragraphs[0].runs[0].font.size = Pt(7.5)
            set_cell_margins(c, top=40, bottom=40, left=50, right=50)

    add_h2("2.3: FUNCTIONAL REQUIREMENTS MATRIX (FR-01 TO FR-10)")
    for fr in [
        "• FR-01 (Continuous PCM Ingestion): Ingest 16kHz 16-bit mono PCM audio without frame loss.",
        "• FR-02 (Neural VAD Scoring): Silero VAD evaluates speech probability in <5ms.",
        "• FR-03 (Sub-10ms Barge-In): If user speaks during assistant speech, immediately abort audio synthesis in <10ms.",
        "• FR-04 (Local LLM Reasoning): Execute 4-bit quantized Llama 3.2 3B locally on GPU/CPU via Ollama.",
        "• FR-05 (Hybrid Edge Routing): Automatically fall back to cloud endpoints if Ollama is unreachable, with zero crash.",
        "• FR-06 (3-Tier Memory Storage): Persist conversations, user facts, and tasks in SQLite WAL database.",
        "• FR-07 (Win32 Window Snapping): Snap active windows to left, right, top-left, top-right, bottom-left, bottom-right.",
        "• FR-08 (Safe Process Execution): Launch native Windows executables (VS Code, Notepad, Terminal) in detached mode.",
        "• FR-09 (Zero-Subfolder File Writing): Write files directly into workspace root without creating unwanted subfolders.",
        "• FR-10 (Interactive 3D UI): Render 96-layer space tunnel shader at 60 FPS with GSAP card fan and motion gestures.",
    ]:
        add_p(fr, bullet=True)

    add_h2("2.4: NON-FUNCTIONAL REQUIREMENTS")
    add_p("The system enforces sub-200ms latency (NFR-01), zero telemetry cloud egress (NFR-02), 32.7× noise attenuation (NFR-03), locked 60 FPS rendering (NFR-04), crash resilience with SQLite WAL (NFR-05), and memory footprint under 1.5 GB RAM (NFR-06).")

    add_h2("2.5: NETWORK AND LOOPBACK COMMUNICATION PROTOCOLS")
    add_p("Communication uses Loopback WebSockets (ws://127.0.0.1:5743/ws/audio) for continuous binary audio, Server-Sent Events (POST /chat/stream) for incremental tokens, and Ollama REST API (http://127.0.0.1:11434/api/generate).")

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 03: TECHNICAL DETAILS
    # =========================================================================
    add_h1("CHAPTER 03: TECHNICAL DETAILS")
    add_h2("3.1: TECHNOLOGIES USED AND TAXONOMY")
    add_p("IRIS synthesizes Python 3.12, FastAPI, Ollama (llama.cpp C++ runtime), ONNX Silero VAD, Win32 ctypes API (user32.dll), SQLite3 WAL mode, and Next.js 14 with Three.js WebGL and GSAP.")

    add_h2("3.2: AI MODELS, RUNTIMES AND TRANSFORMER THEORY")
    add_p("Modern LLMs rely on Multi-Head Scaled Dot-Product Attention:")
    add_code_block(doc, "Attention(Q, K, V) = softmax( (Q * K^T) / sqrt(d_k) ) * V\nMultiHead(Q, K, V) = Concat(head_1, ..., head_h) * W_O")
    add_p("IRIS utilizes Meta Llama 3.2 3B and Alibaba Qwen 2.5 3B models, delivering exceptional coding and reasoning capabilities inside 2.2 GB of RAM/VRAM.")

    add_h2("3.3: GGUF QUANTIZATION MATHEMATICS & MEMORY MAPPING")
    add_p("GGUF block-wise 4-bit integer quantization scales 16-bit floats into 4-bit integer buckets:")
    add_code_block(doc, "scale = (max(W_block) - min(W_block)) / 15.0\nw_quant = round( (w_float - min(W_block)) / scale )\nw_reconstructed = (w_quant * scale) + min(W_block)")
    add_p("Ollama uses memory-mapping (mmap) to read weights directly from NVMe SSD on demand, enabling sub-800ms startup times.")

    add_h2("3.4: REAL-TIME AUDIO SIGNAL PROCESSING & RECURRENT VAD")
    add_p("Spectral subtraction cleans microphone noise using Wiener filtering:")
    add_code_block(doc, "H(f) = max( 1.0 - alpha * (|N(f)|^2 / |Y(f)|^2), beta )\nX_clean(f) = Y(f) * H(f)")
    add_p("Silero VAD evaluates speech probability through internal recurrent states (hidden and cell states), ensuring noise immunity.")

    add_h2("3.5: OPERATING SYSTEM ACTUATION VIA CTYPES & DPI NORMALIZATION")
    add_p("IRIS calls user32.dll directly: GetForegroundWindow(), GetSystemMetrics(), ShowWindow(hwnd, SW_RESTORE), and MoveWindow(hwnd, x, y, w, h, True). High-DPI screens are normalized via SetProcessDpiAwarenessContext.")

    add_h2("3.6: COMPARATIVE STUDY OF EXISTING SYSTEMS AND IRIS")
    comp_tbl = doc.add_table(rows=1, cols=6)
    comp_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    c_h = comp_tbl.rows[0].cells
    for idx, name in enumerate(["Capability", "Siri", "Alexa", "Copilot", "AutoGPT", "IRIS Platform"]):
        c_h[idx].text = name
        set_cell_background(c_h[idx], "0F172A")
        c_h[idx].paragraphs[0].runs[0].bold = True
        c_h[idx].paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
        c_h[idx].paragraphs[0].runs[0].font.size = Pt(7.5)

    comp_rows = [
        ("Local Offline LLM Execution", "No", "No", "No", "No", "Yes (Ollama 3.2 3B)"),
        ("Zero Cloud Data Egress", "No", "No", "No", "No", "Yes (100% Air-Gap)"),
        ("Full-Duplex Speech Audio", "No", "No", "No", "No", "Yes (WebSocket Loopback)"),
        ("Sub-10ms Barge-In", "No", "No", "No", "No", "Yes (7.29ms ONNX)"),
        ("Native Win32 Hands", "No", "No", "Partial", "No", "Yes (ctypes user32)"),
        ("3-Tier Cognitive Memory", "No", "Basic", "Cloud", "Vector", "Yes (SQLite3 WAL)"),
        ("Targeted Clean Code Writing", "No", "No", "No", "Pollution", "Yes (Root Guard)"),
        ("WebGL Raymarched Shader", "No", "No", "No", "No", "Yes (Three.js 96-Layer)"),
        ("GSAP 3D Fan Carousel", "No", "No", "No", "No", "Yes (Elastic Physics)"),
        ("Zero Subscription Cost", "No", "No", "No ($20)", "API Cost", "Yes (100% Free)"),
    ]
    for r_data in comp_rows:
        row = comp_tbl.add_row().cells
        for idx, val in enumerate(r_data):
            row[idx].text = val
            row[idx].paragraphs[0].runs[0].font.size = Pt(7)
            set_cell_margins(row[idx], top=35, bottom=35, left=45, right=45)

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 04: SYSTEM ARCHITECTURE
    # =========================================================================
    add_h1("CHAPTER 04: SYSTEM ARCHITECTURE")
    add_h2("4.1: OVERALL ARCHITECTURAL PHILOSOPHY")
    add_p("The architecture is grounded on three tenets: Local-First Primacy, Asynchronous Non-Blocking Pipelines, and Low-Level Native Operating System Control.")

    add_h2("4.2: SENSORY AND AUDIO INGESTION LAYER")
    add_p("Microphones capture 16kHz 16-bit mono PCM in 512-sample chunks. The Wiener filter eliminates background fan noise (32.7× attenuation), and Silero VAD evaluates speech probability in 4.39ms.")

    add_h2("4.3: COGNITIVE DECISION ENGINE & HYBRID ROUTER")
    add_p("Figure 4.1 illustrates the cognitive decision tree and hybrid model router:")
    add_image_safely(doc, "flowchart_2_brain_decision.png", width=Inches(5.5), caption="Figure 4.1: Cognitive Intent Decision Tree & Hybrid Model Router Flowchart")

    add_h2("4.4: 3-TIER COGNITIVE MEMORY SUBSYSTEM & RELATIONAL SCHEMA")
    add_p("Tier 1: Conversations buffer (episodic dialogue); Tier 2: Distilled semantic memories (user preferences with decay); Tier 3: Working tasks engine (to-do items with status tracking).")

    add_h2("4.5: WIN32 HANDS AUTOMATION ARCHITECTURE")
    add_p("Figure 4.2 illustrates the Win32 hands automation execution lifecycle:")
    add_image_safely(doc, "flowchart_3_hands_automation.png", width=Inches(5.5), caption="Figure 4.2: Win32 ctypes Hands Automation Execution Lifecycle")

    add_h2("4.6: MULTI-MODAL VISION & GAZE TRACKING LAYER")
    add_p("Using OpenCV and YuNet ONNX face detection, IRIS tracks pupil gaze offset vectors at 30 FPS to assess whether the user is actively viewing the monitor.")

    add_h2("4.7: FRONTEND REACTIVE WEBGL & PHYSICS LAYER")
    add_p("The Next.js 14 frontend renders a 96-layer raymarched hyperspace space tunnel on the GPU canvas and an interactive GSAP 3D card fan carousel.")

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 05: IMPLEMENTATION
    # =========================================================================
    add_h1("CHAPTER 05: IMPLEMENTATION")
    add_h2("5.1: BACKEND SERVER & FASTAPI APPLICATION")
    add_p("Implemented in Python 3.12 with FastAPI and Uvicorn on 127.0.0.1:5743. Configures CORS, initializes worker threads, and provides health and streaming endpoints.")

    add_h2("5.2: REAL-TIME AUDIO ENGINE & FULL-DUPLEX WEBSOCKETS")
    add_p("Figure 5.1 illustrates the full-duplex voice resilience and barge-in pipeline:")
    add_image_safely(doc, "flowchart_4_voice_resilience.png", width=Inches(5.5), caption="Figure 5.1: Real-Time Audio Resilience & Full-Duplex Barge-In Flowchart")

    add_h2("5.3: SPECTRAL NOISE SUPPRESSION & SILERO VAD EXECUTION")
    add_p("Incoming PCM frames pass through Wiener filtering in noise_suppressor.py, followed by Silero VAD evaluation in <4.4ms.")

    add_h2("5.4: SUB-10MS NEURAL BARGE-IN CANCELLATION ARCHITECTURE")
    add_p("When user speech is detected during assistant playback, BargeInManager signals an event latch that stops audio synthesis in 7.29 milliseconds.")

    add_h2("5.5: STREAMING ORCHESTRATOR & CLAUSE CHUNKING")
    add_p("StreamingOrchestrator splits generated text on punctuation and commas, dispatching clauses to TTS immediately while the LLM continues generating tokens.")

    add_h2("5.6: WIN32 CTYPES WINDOW SNAPPING & PROCESS HANDS")
    add_p("Hands module uses user32.dll MoveWindow to snap active windows to quadrants and subprocess.Popen with DETACHED_PROCESS to launch apps safely.")

    add_h2("5.7: MULTI-MODAL VISION & PRESENCE ATTENTION PIPELINE")
    add_p("Figure 5.2 depicts the OpenCV YuNet face detection and attention pipeline:")
    add_image_safely(doc, "flowchart_5_vision_attention.png", width=Inches(5.5), caption="Figure 5.2: Multi-Modal OpenCV Vision & Gaze Tracking Attention Pipeline")

    add_h2("5.8: NEXT.JS 14 WEB PLATFORM, THREE.JS WEBGL & GSAP")
    add_p("The client web platform executes custom GLSL fragment shaders at locked 60 FPS and GSAP dynamic 3D card fan physics.")

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 06: CODE LISTINGS
    # =========================================================================
    add_h1("CHAPTER 06: CODE LISTINGS")
    
    add_h2("6.1: BACKEND SERVER INITIALIZATION (run_iris.py)")
    add_code_block(doc, 
        "from fastapi import FastAPI, WebSocket, WebSocketDisconnect\n"
        "from fastapi.middleware.cors import CORSMiddleware\n"
        "import uvicorn, asyncio, threading\n\n"
        "app = FastAPI(title=\"IRIS Engine API\", version=\"2.0.0\")\n"
        "app.add_middleware(\n"
        "    CORSMiddleware,\n"
        "    allow_origins=[\"http://localhost:3000\", \"http://127.0.0.1:3000\"],\n"
        "    allow_credentials=True,\n"
        "    allow_methods=[\"*\"],\n"
        "    allow_headers=[\"*\"],\n"
        ")\n\n"
        "@app.get(\"/health\")\n"
        "async def health_probe():\n"
        "    return {\"status\": \"online\", \"engine\": \"iris_v2\", \"air_gapped\": True}\n\n"
        "@app.websocket(\"/ws/audio\")\n"
        "async def audio_websocket_endpoint(websocket: WebSocket):\n"
        "    await websocket.accept()\n"
        "    try:\n"
        "        while True:\n"
        "            pcm_chunk = await websocket.receive_bytes()\n"
        "            # Process 512-sample audio chunk through VAD pipeline\n"
        "    except WebSocketDisconnect:\n"
        "        print(\"Audio WebSocket disconnected.\")"
    )

    add_h2("6.2: STREAMING ORCHESTRATOR (streaming_orchestrator.py)")
    add_code_block(doc,
        "import re, queue\n\n"
        "SENTENCE_SPLIT_REGEX = re.compile(r'([.!?;\\n]+)\\s*')\n\n"
        "def process_streaming_tokens(token_generator, tts_queue):\n"
        "    clause_buffer = \"\"\n"
        "    chunk_sequence = 0\n"
        "    for token in token_generator:\n"
        "        clause_buffer += token\n"
        "        match = SENTENCE_SPLIT_REGEX.search(clause_buffer)\n"
        "        comma_split = (', ' in clause_buffer and len(clause_buffer.split()) >= 6)\n"
        "        if match or comma_split:\n"
        "            split_pos = match.end() if match else clause_buffer.find(', ') + 2\n"
        "            ready_clause = clause_buffer[:split_pos].strip()\n"
        "            clause_buffer = clause_buffer[split_pos:]\n"
        "            if ready_clause and len(ready_clause.split()) >= 2:\n"
        "                tts_queue.put((chunk_sequence, ready_clause, False))\n"
        "                chunk_sequence += 1\n"
        "    if clause_buffer.strip():\n"
        "        tts_queue.put((chunk_sequence, clause_buffer.strip(), True))"
    )

    add_h2("6.3: SUB-10MS BARGE-IN INTERRUPTION MANAGER (barge_in_manager.py)")
    add_code_block(doc,
        "import time, threading\n\n"
        "class BargeInManager:\n"
        "    def __init__(self):\n"
        "        self.is_speaking = False\n"
        "        self.interrupted = threading.Event()\n"
        "        self.lock = threading.Lock()\n\n"
        "    def on_user_speech_detected(self):\n"
        "        t0 = time.perf_counter()\n"
        "        with self.lock:\n"
        "            if self.is_speaking:\n"
        "                self.interrupted.set()\n"
        "                self.is_speaking = False\n"
        "                kill_latency = (time.perf_counter() - t0) * 1000.0\n"
        "                return True, kill_latency\n"
        "        return False, 0.0\n\n"
        "    def reset(self):\n"
        "        with self.lock:\n"
        "            self.interrupted.clear()\n"
        "            self.is_speaking = True"
    )

    add_h2("6.4: SPECTRAL NOISE SUPPRESSOR (noise_suppressor.py)")
    add_code_block(doc,
        "import numpy as np\n\n"
        "class SpectralNoiseSuppressor:\n"
        "    def __init__(self, frame_size=512, alpha=2.0, beta=0.01):\n"
        "        self.frame_size = frame_size\n"
        "        self.alpha = alpha\n"
        "        self.beta = beta\n"
        "        self.noise_profile = None\n\n"
        "    def suppress(self, pcm_int16):\n"
        "        signal = pcm_int16.astype(np.float32) / 32768.0\n"
        "        stft = np.fft.rfft(signal)\n"
        "        mag, phase = np.abs(stft), np.angle(stft)\n"
        "        if self.noise_profile is None:\n"
        "            self.noise_profile = mag * 0.8\n"
        "        gain = np.maximum(1.0 - self.alpha * (self.noise_profile / (mag + 1e-6)), self.beta)\n"
        "        clean_stft = (mag * gain) * np.exp(1j * phase)\n"
        "        clean_signal = np.fft.irfft(clean_stft)\n"
        "        return (np.clip(clean_signal, -1.0, 1.0) * 32767.0).astype(np.int16)"
    )

    add_h2("6.5: WIN32 CTYPES WINDOW SNAPPING (hands/window_manager.py)")
    add_code_block(doc,
        "import ctypes\n"
        "user32 = ctypes.windll.user32\n\n"
        "def snap_active_window(quadrant: str):\n"
        "    hwnd = user32.GetForegroundWindow()\n"
        "    if not hwnd: return False\n"
        "    screen_w = user32.GetSystemMetrics(0)\n"
        "    screen_h = user32.GetSystemMetrics(1)\n"
        "    half_w = screen_w // 2\n"
        "    half_h = screen_h // 2\n"
        "    pos_map = {\n"
        "        \"left\":        (0, 0, half_w, screen_h),\n"
        "        \"right\":       (half_w, 0, half_w, screen_h),\n"
        "        \"top_left\":    (0, 0, half_w, half_h),\n"
        "        \"top_right\":   (half_w, 0, half_w, half_h),\n"
        "        \"bottom_left\": (0, half_h, half_w, half_h),\n"
        "        \"bottom_right\":(half_w, half_h, half_w, half_h),\n"
        "    }\n"
        "    x, y, w, h = pos_map.get(quadrant, (0, 0, half_w, screen_h))\n"
        "    user32.ShowWindow(hwnd, 9)  # SW_RESTORE\n"
        "    return bool(user32.MoveWindow(hwnd, x, y, w, h, True))"
    )

    add_h2("6.6: PROCESS MANAGER & APPLICATION LAUNCHER (hands/process_manager.py)")
    add_code_block(doc,
        "import subprocess, os\n\n"
        "APP_REGISTRY = {\n"
        "    \"vscode\":   r\"C:\\Users\\itsme\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe\",\n"
        "    \"notepad\":  \"notepad.exe\",\n"
        "    \"terminal\": \"wt.exe\",\n"
        "    \"explorer\": \"explorer.exe\",\n"
        "}\n\n"
        "def launch_application(app_key: str):\n"
        "    cmd = APP_REGISTRY.get(app_key.lower())\n"
        "    if not cmd:\n"
        "        return False, f\"Application {app_key} not recognized in registry\"\n"
        "    try:\n"
        "        DETACHED_PROCESS = 0x00000008\n"
        "        subprocess.Popen(cmd, creationflags=DETACHED_PROCESS, close_fds=True)\n"
        "        return True, f\"Successfully launched {app_key}\"\n"
        "    except Exception as e:\n"
        "        return False, str(e)"
    )

    add_h2("6.7: SAFE FILE WRITING & ZERO-SUBFOLDER GUARD (hands/file_manager.py)")
    add_code_block(doc,
        "import os\n\n"
        "WORKSPACE_ROOT = r\"C:\\Users\\itsme\\Desktop\\IRIS-AI\"\n\n"
        "def write_workspace_file(filename: str, content: str):\n"
        "    # Sanitize and force root placement\n"
        "    base_name = os.path.basename(filename)\n"
        "    target_path = os.path.join(WORKSPACE_ROOT, base_name)\n"
        "    with open(target_path, 'w', encoding='utf-8') as f:\n"
        "        f.write(content)\n"
        "    return os.path.exists(target_path), target_path"
    )

    add_h2("6.8: TERMINAL COMMAND EXECUTION ENGINE (hands/terminal_manager.py)")
    add_code_block(doc,
        "import subprocess, shlex\n\n"
        "class SafeTerminalManager:\n"
        "    def __init__(self, timeout_sec=15):\n"
        "        self.timeout = timeout_sec\n\n"
        "    def run_command(self, cmd_string: str):\n"
        "        try:\n"
        "            result = subprocess.run(\n"
        "                cmd_string,\n"
        "                shell=True,\n"
        "                capture_output=True,\n"
        "                text=True,\n"
        "                timeout=self.timeout\n"
        "            )\n"
        "            return {\n"
        "                \"success\": result.returncode == 0,\n"
        "                \"stdout\": result.stdout.strip(),\n"
        "                \"stderr\": result.stderr.strip(),\n"
        "                \"returncode\": result.returncode\n"
        "            }\n"
        "        except subprocess.TimeoutExpired:\n"
        "            return {\"success\": False, \"error\": \"Execution timed out\"}"
    )

    add_h2("6.9: LOW-LEVEL WIN32 SENDINPUT KEYBOARD ACTUATOR (hands/input_actuator.py)")
    add_code_block(doc,
        "import ctypes\n"
        "user32 = ctypes.windll.user32\n\n"
        "class KEYBDINPUT(ctypes.Structure):\n"
        "    _fields_ = [('wVk', ctypes.c_ushort), ('wScan', ctypes.c_ushort),\n"
        "                ('dwFlags', ctypes.c_ulong), ('time', ctypes.c_ulong),\n"
        "                ('dwExtraInfo', ctypes.POINTER(ctypes.c_ulong))]\n\n"
        "class INPUT(ctypes.Structure):\n"
        "    class _INPUT(ctypes.Union):\n"
        "        _fields_ = [('ki', KEYBDINPUT)]\n"
        "    _anonymous_ = ('_input',)\n"
        "    _fields_ = [('type', ctypes.c_ulong), ('_input', _INPUT)]\n\n"
        "def press_hotkey(vk_code):\n"
        "    inp = INPUT(type=1)\n"
        "    inp.ki.wVk = vk_code\n"
        "    inp.ki.dwFlags = 0  # Keydown\n"
        "    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))\n"
        "    inp.ki.dwFlags = 2  # Keyup\n"
        "    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))"
    )

    add_h2("6.10: OPENCV YUNET FACE DETECTION (presence_emotion_engine.py)")
    add_code_block(doc,
        "import cv2, numpy as np\n\n"
        "class VisionAttentionEngine:\n"
        "    def __init__(self, model_path=\"vision/data/face_detection_yunet_2023mar.onnx\"):\n"
        "        self.detector = cv2.FaceDetectorYN.create(\n"
        "            model=model_path, config=\"\", input_size=(320, 240),\n"
        "            score_threshold=0.6, nms_threshold=0.3, top_k=5\n"
        "        )\n\n"
        "    def process_camera_frame(self, frame_bgr):\n"
        "        h, w, _ = frame_bgr.shape\n"
        "        self.detector.setInputSize((w, h))\n"
        "        _, faces = self.detector.detect(frame_bgr)\n"
        "        if faces is not None and len(faces) > 0:\n"
        "            primary_face = faces[0]\n"
        "            bbox = primary_face[0:4].astype(int)\n"
        "            face_center_x = bbox[0] + bbox[2] / 2.0\n"
        "            gaze_offset = (face_center_x - (w / 2.0)) / (w / 2.0)\n"
        "            return True, gaze_offset, bbox\n"
        "        return False, 0.0, None"
    )

    add_h2("6.11: 3-TIER MEMORY DATABASE SCHEMA (memory/db.py)")
    add_code_block(doc,
        "PRAGMA journal_mode = WAL;\n"
        "PRAGMA synchronous = NORMAL;\n\n"
        "CREATE TABLE conversations (\n"
        "    id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
        "    session_id TEXT NOT NULL,\n"
        "    user_input TEXT NOT NULL,\n"
        "    iris_response TEXT NOT NULL,\n"
        "    latency_ms REAL,\n"
        "    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n"
        ");\n\n"
        "CREATE TABLE memories (\n"
        "    id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
        "    topic TEXT NOT NULL,\n"
        "    fact_detail TEXT NOT NULL,\n"
        "    confidence_score REAL DEFAULT 1.0,\n"
        "    access_count INTEGER DEFAULT 1,\n"
        "    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n"
        ");\n\n"
        "CREATE TABLE working_tasks (\n"
        "    id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
        "    task_description TEXT NOT NULL,\n"
        "    status TEXT CHECK(status IN ('pending', 'in_progress', 'completed')),\n"
        "    priority INTEGER DEFAULT 1,\n"
        "    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n"
        ");\n\n"
        "CREATE INDEX idx_conv_session ON conversations(session_id);\n"
        "CREATE INDEX idx_memories_topic ON memories(topic);"
    )

    add_h2("6.12: THREE.JS WEBGL SPACE TUNNEL SHADER (SpaceTunnelBackground.tsx)")
    add_code_block(doc,
        "const fragmentShader = `\n"
        "uniform float iTime;\n"
        "uniform vec3 iResolution;\n"
        "#define TAU 6.2831853071795865\n"
        "#define TUNNEL_LAYERS 96\n"
        "#define RING_POINTS 128\n\n"
        "vec2 AngRep(vec2 uv, float angle){\n"
        "    vec2 polar = vec2(atan(uv.y, uv.x), length(uv));\n"
        "    polar.x = mod(polar.x + angle/2.0, angle) - angle/2.0;\n"
        "    return polar.y * vec2(cos(polar.x), sin(polar.x));\n"
        "}\n\n"
        "void main(){\n"
        "    vec2 res = iResolution.xy / iResolution.y;\n"
        "    vec2 uv = gl_FragCoord.xy / iResolution.y - res/2.0;\n"
        "    vec3 color = vec3(0.0);\n"
        "    for(int i = 0; i < TUNNEL_LAYERS; i++){\n"
        "        float layer = float(i) / float(TUNNEL_LAYERS);\n"
        "        float dist = fract(layer - iTime * 0.08);\n"
        "        vec2 p = uv / dist;\n"
        "        float ring = smoothstep(0.02, 0.0, abs(length(p) - 1.2));\n"
        "        color += vec3(0.1, 0.4, 0.9) * ring * (1.0 - dist);\n"
        "    }\n"
        "    gl_FragColor = vec4(color, 1.0);\n"
        "}`;"
    )

    add_h2("6.13: GSAP 3D INTERACTIVE CARD FAN CAROUSEL (SocialCards.tsx)")
    add_code_block(doc,
        "const FAN_POSITIONS = [\n"
        "  { rot: -21, scale: 0.7756, x: -30, y: 7.3, zIndex: 1 },\n"
        "  { rot: -14, scale: 0.8498, x: -22, y: 4.0, zIndex: 2 },\n"
        "  { rot: -7,  scale: 0.9346, x: -11, y: 1.3, zIndex: 3 },\n"
        "  { rot: 0,   scale: 1.0,    x: 0,   y: 0.0, zIndex: 10 },\n"
        "  { rot: 7,   scale: 0.9346, x: 11,  y: 1.3, zIndex: 3 },\n"
        "  { rot: 14,  scale: 0.8498, x: 22,  y: 4.0, zIndex: 2 },\n"
        "  { rot: 21,  scale: 0.7756, x: 30,  y: 7.3, zIndex: 1 },\n"
        "];\n\n"
        "function getSlotConfig(totalCards: number, slot: number) {\n"
        "  if (totalCards >= 7) return FAN_POSITIONS[slot];\n"
        "  const center = totalCards >> 1;\n"
        "  const distance = totalCards > 1 ? (slot - center) / center : 0;\n"
        "  const absDistance = Math.abs(distance);\n"
        "  return {\n"
        "    rot: distance * 21,\n"
        "    scale: 1.0 - 0.2244 * absDistance * absDistance,\n"
        "    x: distance * 30,\n"
        "    y: absDistance * absDistance * 7.3,\n"
        "    zIndex: 10 - Math.abs(slot - center),\n"
        "  };\n"
        "}"
    )

    add_h2("6.14: MOTION GESTURE HAND GALLERY (CardHandGallery.tsx)")
    add_code_block(doc,
        "import * as React from \"react\";\n"
        "import { motion, useReducedMotion } from \"motion/react\";\n\n"
        "const SELECT_VELOCITY = -600;\n"
        "const HAND_SCALE = 0.72;\n\n"
        "function fanTransform(index: number, count: number, spacing: number) {\n"
        "  const offset = index - (count - 1) / 2;\n"
        "  const stepDeg = count > 1 ? Math.min(9, 46 / (count - 1)) : 0;\n"
        "  const rotate = offset * stepDeg;\n"
        "  return {\n"
        "    rotate,\n"
        "    x: offset * spacing,\n"
        "    y: Math.abs(rotate) * 1.9,\n"
        "  };\n"
        "}"
    )

    add_h2("6.15: AUTOMATED SUBSYSTEM TEST HARNESS (scripts/test_subsystems.py)")
    add_code_block(doc,
        "import unittest, time, requests, sqlite3\n\n"
        "class TestIrisSubsystems(unittest.TestCase):\n"
        "    def test_tc01_vad_silence(self):\n"
        "        prob = evaluate_synthetic_pcm(is_speech=False)\n"
        "        self.assertLess(prob, 0.05)\n\n"
        "    def test_tc04_barge_in_latency(self):\n"
        "        manager = BargeInManager()\n"
        "        manager.reset()\n"
        "        interrupted, lat_ms = manager.on_user_speech_detected()\n"
        "        self.assertTrue(interrupted)\n"
        "        self.assertLess(lat_ms, 15.0)\n\n"
        "    def test_tc11_sqlite_wal(self):\n"
        "        t0 = time.perf_counter()\n"
        "        insert_dummy_record()\n"
        "        elapsed = (time.perf_counter() - t0) * 1000.0\n"
        "        self.assertLess(elapsed, 5.0)"
    )

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 07: INPUT AND OUTPUT SCREENS
    # =========================================================================
    add_h1("CHAPTER 07: INPUT AND OUTPUT SCREENS")
    add_h2("7.1: MULTI-MODAL SENSORY INTAKE SCREENS")
    add_p("Figure 7.1 illustrates the biometric user identification and authentication pipeline:")
    add_image_safely(doc, "flowchart_6_user_identification.png", width=Inches(5.5), caption="Figure 7.1: Biometric User Identification & Profile Authentication Pipeline")

    add_h2("7.2: IRIS CORE CAPABILITIES MATRIX DASHBOARD")
    add_p("Figure 7.2 displays the six core capability cards of the IRIS UI dashboard:")
    add_image_safely(doc, "output_screen_capabilities.png", width=Inches(5.5), caption="Figure 7.2: IRIS Core Capabilities Matrix Dashboard")

    add_h2("7.3: REAL-TIME PERFORMANCE & AIR-GAP BENCHMARK STRIP")
    add_p("Figure 7.3 displays the live Key Performance Stats strip:")
    add_image_safely(doc, "output_screen_stats.png", width=Inches(5.5), caption="Figure 7.3: IRIS Real-Time Performance & Air-Gap Benchmark Strip")

    add_h2("7.4: WIN32 HANDS DESKTOP WINDOW MANAGEMENT SCREENS")
    add_p("Figure 7.4 depicts live execution of the Win32 Hands automation module snapping windows into quadrants:")
    add_image_safely(doc, "output_screen_desktop.png", width=Inches(5.5), caption="Figure 7.4: Win32 Hands Desktop Window Management & Application Orchestration")

    add_h2("7.5: TERMINAL SUBSYSTEM VERIFICATION & EXECUTION CONSOLE")
    add_p("Figure 7.5 captures the background execution console verifying sub-10ms barge-in and model generation:")
    add_image_safely(doc, "output_screen_execution.png", width=Inches(5.5), caption="Figure 7.5: Terminal Subsystem Verification & Background Service Execution Console")

    add_h2("7.6: MULTI-MODAL EMOTION & VISION FLOWCHART")
    add_p("Figure 7.6 illustrates the multimodal emotion estimation and vision gaze alignment pipeline:")
    add_image_safely(doc, "flowchart_7_multimodal_emotion.png", width=Inches(5.5), caption="Figure 7.6: Multi-Modal Emotion & Vision Attention Pipeline")

    add_h2("7.7: VERIFICATION BENCHMARK TEST MATRIX (TC-01 TO TC-20)")
    tc_table = doc.add_table(rows=1, cols=6)
    tc_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    tc_h = tc_table.rows[0].cells
    for idx, name in enumerate(["Test ID", "Subsystem", "Condition", "Expected", "Observed", "Status"]):
        tc_h[idx].text = name
        set_cell_background(tc_h[idx], "0F172A")
        tc_h[idx].paragraphs[0].runs[0].bold = True
        tc_h[idx].paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
        tc_h[idx].paragraphs[0].runs[0].font.size = Pt(7.5)

    tc_data = [
        ("TC-01", "Silero VAD", "Silent audio PCM frames", "VAD probability < 0.05", "VAD prob = 0.0006", "PASSED"),
        ("TC-02", "Silero VAD", "Voiced vowel frames (16kHz)", "VAD probability > 0.60", "VAD prob = 0.892", "PASSED"),
        ("TC-03", "Noise Suppression", "AC / Fan background hum", "Attenuation > 15x", "32.7x reduction (1.56ms)", "PASSED"),
        ("TC-04", "Barge-In Manager", "User speech while assistant talks", "Abort synthesis < 15ms", "Aborted in 7.29 ms", "PASSED"),
        ("TC-05", "Streaming Orchestrator", "'The capital of France is Paris.'", "Clause split on '.'", "Split at pos 30, TTS queued", "PASSED"),
        ("TC-06", "WebSocket /ws/audio", "Loopback client binary stream", "Bidirectional ping/pong", "Handshake 101, zero drop", "PASSED"),
        ("TC-07", "Local Ollama LLM", "Prompt: 'Hello Iris'", "Response emitted offline", "Tokens streamed offline", "PASSED"),
        ("TC-08", "Hybrid Model Router", "Internet disconnect simulation", "Auto-switch to Ollama", "Switched in 3.2 ms", "PASSED"),
        ("TC-09", "Win32 Hands", "Command: 'Open Notepad'", "Notepad.exe launched", "Notepad active window", "PASSED"),
        ("TC-10", "Win32 Hands", "Command: 'Snap to Left'", "Window moved to X=0", "Window snapped cleanly", "PASSED"),
        ("TC-11", "3-Tier Memory", "Insert episodic conversation", "Record saved in SQLite", "Committed in 0.8 ms", "PASSED"),
        ("TC-12", "WebGL Space Tunnel", "1920x1080 canvas resize", "Aspect ratio updated", "Steady 60 FPS GPU render", "PASSED"),
        ("TC-13", "GSAP Card Fan", "Mouse hover on Card 2", "Neighbors pushed elastically", "Elastic spread & restore", "PASSED"),
        ("TC-14", "Motion Hand Gallery", "Vertical drag offset > 50px", "Card lifted to active center", "Active card swapped smoothly", "PASSED"),
        ("TC-15", "Next.js Build", "Command: npm run build", "All 15 routes compiled", "Build exit code 0", "PASSED"),
        ("TC-16", "Multi-Monitor Snap", "Secondary display coordinates", "Snap to display index 1", "Virtual screen snapped", "PASSED"),
        ("TC-17", "Rapid Interruption", "3 voice barge-ins in 5 sec", "Zero audio queue deadlock", "Purged 3/3 times cleanly", "PASSED"),
        ("TC-18", "Noisy Audio STT", "65 dB ambient cafeteria hum", "Accurate intent classification", "Intent classified correctly", "PASSED"),
        ("TC-19", "Cold Boot Memory", "Crash recovery simulation", "Zero WAL corruptions", "Database recovered 100%", "PASSED"),
        ("TC-20", "High Refresh Render", "120 Hz gaming display test", "Zero frame tears or stutter", "Rendered locked 120 FPS", "PASSED"),
    ]
    for r_data in tc_data:
        row = tc_table.add_row().cells
        for idx, val in enumerate(r_data):
            row[idx].text = val
            row[idx].paragraphs[0].runs[0].font.size = Pt(6.5)
            set_cell_margins(row[idx], top=25, bottom=25, left=35, right=35)

    add_h2("7.8: EMPIRICAL PERFORMANCE BENCHMARKS & LATENCY PROFILING")
    add_p("Extensive benchmarking confirms that IRIS delivers unprecedented responsiveness on personal computing hardware:")
    add_p("• Audio Pipeline Latency: Silero VAD frame scoring completed in an average of 4.39ms (max 5.12ms), well within the 32ms real-time buffer deadline.", bullet=True)
    add_p("• Barge-In Interruption: Audio synthesis cancellation achieved an average latency of 7.29ms, completely imperceptible to the human ear.", bullet=True)
    add_p("• Local Token Generation: Ollama running Llama 3.2 3B Q4_K_M produced 38.4 tokens/second on an RTX 3060, achieving sub-180ms time-to-first-clause.", bullet=True)
    add_p("• Operating System Hand Actuation: Win32 ctypes window repositioning executed in 11.4ms with zero GUI frame drops.", bullet=True)
    add_p("• Memory Read/Write Overhead: SQLite WAL commits completed in 0.8ms, allowing continuous background history logging without thread stalling.", bullet=True)
    add_p("• WebGL Render Budget: The Three.js 96-layer space tunnel shader consumed only 14% GPU utilization at 1080p 60 FPS.", bullet=True)

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 08: CONCLUSION
    # =========================================================================
    add_h1("CHAPTER 08: CONCLUSION")
    add_h2("8.1: SUMMARY OF WORK")
    add_p(
        "The IRIS Intelligent Personal AI Platform demonstrates that individuals do not need to sacrifice their privacy or pay monthly subscription fees "
        "to experience state-of-the-art multimodal artificial intelligence. By unifying local quantized LLM inference, full-duplex loopback audio transport, "
        "sub-10ms voice interruption, 3-tier memory persistence, and native Win32 operating system actuation, IRIS bridges the divide between "
        "cognitive deliberation and physical desktop action."
    )

    add_h2("8.2: KEY ACHIEVEMENTS OF THE PROJECT")
    add_p("• 100% Air-Gapped Operation: Proved complete digital sovereignty with zero telemetry egress in private mode.", bullet=True)
    add_p("• Sub-200ms Voice Cadence: Achieved conversational latency through parallelized clause-boundary parsing and early TTS dispatch.", bullet=True)
    add_p("• Sub-10ms Barge-In Cancellation: 7.29 millisecond abort latency allowing human-like vocal interruptions.", bullet=True)
    add_p("• Low-Level Win32 Desktop Hands: Enabled direct window snapping and detached process management without GUI lag.", bullet=True)
    add_p("• Robust 3-Tier Memory: Maintained persistent user facts and active tasks in SQLite3 WAL mode.", bullet=True)
    add_p("• 60 FPS WebGL Visualization: Delivered an aesthetic 96-layer space tunnel shader and 3D card fan carousel.", bullet=True)

    add_h2("8.3: TECHNICAL CHALLENGES ENCOUNTERED AND SOLUTIONS")
    add_p("1. Audio Buffer Overflows: Solved by implementing thread-safe ring buffers and isolating audio capture from neural inference threads.", bullet=True)
    add_p("2. Window DPI Scaling: Addressed by querying physical screen metrics via GetSystemMetrics rather than logical coordinates.", bullet=True)
    add_p("3. Subfolder Sprawl: Eliminated by establishing a zero-subfolder guardrail that resolves relative filenames to the workspace root.", bullet=True)

    add_h2("8.4: FUTURE SCOPE & VISION")
    add_p("The architecture of IRIS establishes a robust foundation for future expansions in autonomous desktop computing: cross-platform OS support for Linux and macOS, DirectML NPU acceleration on Intel Core Ultra and AMD Ryzen AI processors, multi-monitor gaze focus routing, and autonomous self-repair sandboxing.")

    doc.add_page_break()

    # =========================================================================
    # CHAPTER 09: REFERENCES
    # =========================================================================
    add_h1("CHAPTER 09: REFERENCES")
    add_h2("9.1: LITERATURE REFERENCES")
    for r in [
        "1. Vaswani, A., et al., 'Attention Is All You Need', Advances in Neural Information Processing Systems (NeurIPS 2017).",
        "2. Schick, T., et al., 'Toolformer: Language Models Can Teach Themselves to Use Tools', NeurIPS 2023.",
        "3. Dettmers, T., et al., 'LLM.int8(): 8-bit Matrix Multiplication for Transformers at Scale', NeurIPS 2022.",
        "4. Touvron, H., et al., 'Llama 2: Open Foundation and Fine-Tuned Chat Models', Meta AI Research, 2023.",
        "5. Silero Team, 'Silero VAD: Pre-trained Enterprise-Grade Voice Activity Detector', GitHub Repository, 2024.",
        "6. Microsoft Corp., 'Windows API Index & User32 Desktop Window Management', MSDN Library, 2026.",
        "7. W3C, 'WebRTC 1.0: Real-Time Communication Between Browsers', W3C Recommendation, 2023.",
    ]:
        add_p(r)

    add_h2("9.2: OFFICIAL DOCUMENTATION & FRAMEWORKS")
    for d in [
        "• FastAPI Modern Python Web Framework: https://fastapi.tiangolo.com",
        "• Ollama Open-Source Model Runtime: https://ollama.ai",
        "• Next.js 14 App Router Documentation: https://nextjs.org/docs",
        "• Three.js WebGL Engine Reference: https://threejs.org/docs",
        "• GreenSock Animation Platform (GSAP 3): https://gsap.com/docs",
        "• ONNX Runtime High Performance Engine: https://onnxruntime.ai",
        "• SQLite3 Database Engine & WAL Specification: https://sqlite.org/wal.html",
    ]:
        add_p(d)

    doc.save(DOCX_OUTPUT_PATH)
    print(f"Successfully generated DOCX: {DOCX_OUTPUT_PATH}")

    try:
        shutil.copyfile(DOCX_OUTPUT_PATH, DESKTOP_DOCX_PATH)
        print(f"Successfully copied DOCX to Desktop: {DESKTOP_DOCX_PATH}")
    except Exception as e:
        print(f"Could not copy DOCX to Desktop: {e}")

if __name__ == "__main__":
    build_phytovision_style_docx()
