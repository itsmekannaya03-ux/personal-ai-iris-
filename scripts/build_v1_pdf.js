/**
 * build_v1_pdf.js
 * Generates v.1.pdf - The Official Visual System Dossier of IRIS AI
 * Containing ALL Input and Output images organized strictly topic by topic:
 * - Double line running header rule
 * - Professional Cover Page matching reference PDF
 * - Visual Contents Index
 * - Full-page high-resolution showcase for every input and output image
 * - System, component, and operational metadata box for each figure
 */

const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');
const { pathToFileURL } = require('url');

const WORKSPACE = path.resolve('c:/Users/itsme/Desktop/IRIS-AI');
const ASSETS_DIR = path.join(WORKSPACE, 'report_assets');
const OUTPUT_HTML = path.join(WORKSPACE, 'iris_v1_print.html');
const OUTPUT_PDF = path.join(WORKSPACE, 'v.1.pdf');
const OUTPUT_PDF_ALT = path.join(WORKSPACE, 'v1.pdf');

function imgUrl(filename) {
  const filePath = path.join(ASSETS_DIR, filename);
  if (!fs.existsSync(filePath)) {
    console.warn('Image not found:', filePath);
    return '';
  }
  return pathToFileURL(filePath).href;
}

const logo = imgUrl('college_logo.jpg');

const images = [
  // -------------------------------------------------------------
  // TOPIC 1: LANDING EXPERIENCE & BOTANICAL COMPUTING ETHOS
  // -------------------------------------------------------------
  {
    topic: 'TOPIC 01 : 3D BOTANICAL LANDING EXPERIENCE',
    subsystem: 'website/components/ui/FlowerValley.tsx',
    type: 'OUTPUT SCREEN',
    badgeClass: 'badge-output',
    title: 'Figure 1.1 : "Flower Valley" 3D Experience (Ethos: "Grown, Not Built")',
    file: imgUrl('iris_landing_flower_valley.jpg'),
    desc: 'The official landing canvas of IRIS AI rendered with real-time procedural WebGL flora. Features interactive 3D depth navigation, ambient bioluminescent petals, and the foundational design ethos: "Grown, not built. Rooted in nature. Built for what\'s next."'
  },

  // -------------------------------------------------------------
  // TOPIC 2: DASHBOARD CONTROLS & SYSTEM TELEMETRY
  // -------------------------------------------------------------
  {
    topic: 'TOPIC 02 : DASHBOARD CONTROLS & TELEMETRY GAUGES',
    subsystem: 'website/app/dashboard/page.tsx',
    type: 'INPUT SCREEN',
    badgeClass: 'badge-input',
    title: 'Figure 2.1 : Dashboard Mode Toggles & System Control Strip',
    file: imgUrl('iris_dashboard_overview.png'),
    desc: 'The authenticated operator dashboard overview screen. Displays workstation status gauges, 3-tier memory indicator, offline neural engine connection status, and one-click launch cards for Local Chat, Theme Customizer, and System Rules.'
  },
  {
    topic: 'TOPIC 02 : DASHBOARD CONTROLS & TELEMETRY GAUGES',
    subsystem: 'website/components/ui/IrisFlowerBackground.tsx',
    type: 'INPUT SCREEN',
    badgeClass: 'badge-input',
    title: 'Figure 2.2 : 3D Iris Live Parameter Adjustment Bar',
    file: imgUrl('input_3d_adjustments_bar.jpg'),
    desc: 'Real-time parameter controls for the procedural 3D Iris Flower HUD. Allows interactive adjustment of Screen Scale (65%), Perspective Tilt Angle (-17° to -20°), Orbital Self-Rotation Period (70s), Bioluminescent Glow (Intensity: 4), and Active Atmosphere.'
  },
  {
    topic: 'TOPIC 02 : DASHBOARD CONTROLS & TELEMETRY GAUGES',
    subsystem: 'website/app/dashboard/page.tsx',
    type: 'OUTPUT SCREEN',
    badgeClass: 'badge-output',
    title: 'Figure 2.3 : System Engine Telemetry & Subscription Status Strip',
    file: imgUrl('output_status_strip.png'),
    desc: 'Top-level status gauge strip showing hardware engine connection health, 3-tier memory cache residency (RAM / Session / SQLite), offline sovereignty status, and license tier tiering.'
  },
  {
    topic: 'TOPIC 02 : DASHBOARD CONTROLS & TELEMETRY GAUGES',
    subsystem: 'website/app/dashboard/page.tsx',
    type: 'OUTPUT SCREEN',
    badgeClass: 'badge-output',
    title: 'Figure 2.4 : Primary Desktop Subsystem Feature Navigation Cards',
    file: imgUrl('output_feature_cards.png'),
    desc: 'Interactive holographic navigation cards for the three primary functional modes: Local AI Chat (offline neural assistant), Theme Customizer (6 visual overlay modes), and Skills & System Rules (autonomous action triggers).'
  },
  {
    topic: 'TOPIC 02 : DASHBOARD CONTROLS & TELEMETRY GAUGES',
    subsystem: 'AI model (iris)/hands/system_monitor.py',
    type: 'OUTPUT SCREEN',
    badgeClass: 'badge-output',
    title: 'Figure 2.5 : Live Telemetry Gauges, Token Ratios & Resource Graphs',
    file: imgUrl('output_screen_stats.png'),
    desc: 'Real-time system telemetry output monitoring CPU load percentage, RAM memory footprint, local GPU VRAM allocation, neural token generation throughput (tps), and microphone frequency audio visualizer bins.'
  },

  // -------------------------------------------------------------
  // TOPIC 3: PROCEDURAL 3D WEBGL IRIS FLOWER & HOLOGRAPHIC HUD
  // -------------------------------------------------------------
  {
    topic: 'TOPIC 03 : PROCEDURAL 3D WEBGL IRIS FLOWER HUD',
    subsystem: 'website/components/ui/IrisFlowerBackground.tsx',
    type: 'OUTPUT SCREEN',
    badgeClass: 'badge-output',
    title: 'Figure 3.1 : Procedural 3D WebGL Iris Flower with Double-Sided Fresnel Shading',
    file: imgUrl('iris_3d_hud_rotating.jpg'),
    desc: 'The live procedural 3D Iris Flower rendered at 60 FPS in WebGL. Features 3 ruffled Falls, 3 upright domed Standards, 3 Style Crests, golden beards, 26 fan-radiating botanical veins, 62 delicate micro-veins, and smooth 360° orbital self-rotation.'
  },
  {
    topic: 'TOPIC 03 : PROCEDURAL 3D WEBGL IRIS FLOWER HUD',
    subsystem: 'website/components/ui/IrisFlowerBackground.tsx',
    type: 'INPUT SCREEN',
    badgeClass: 'badge-input',
    title: 'Figure 3.2 : Interactive 3D Upper Petal Nodes HUD Header & Expand Control',
    file: imgUrl('input_interactive_hud_bar.png'),
    desc: 'The interactive upper HUD control bar: "3D IRIS UPPER PETAL NODES • INTERACTIVE HUD — Touch any dot on the petals to unfold the indicator. Touch again to retract back" with global "Expand All" toggle.'
  },
  {
    topic: 'TOPIC 03 : PROCEDURAL 3D WEBGL IRIS FLOWER HUD',
    subsystem: 'website/components/ui/IrisFlowerBackground.tsx',
    type: 'INPUT / OUTPUT SPEC',
    badgeClass: 'badge-input',
    title: 'Figure 3.3 : Directional Indicator Arrow & Slanted Parallelogram Card Mechanical Specification',
    file: imgUrl('iris_hud_callout_spec.png'),
    desc: 'The engineering callout trajectory specification: A circle anchor dot on the petal emits a straight directional line that takes a slight turn (Southeast for Skills, Southwest for Chat, Northeast for Themes) to anchor a slanted parallelogram card (skewX -3.5°).'
  },
  {
    topic: 'TOPIC 03 : PROCEDURAL 3D WEBGL IRIS FLOWER HUD',
    subsystem: 'website/components/ui/IrisFlowerBackground.tsx',
    type: 'OUTPUT SCREEN',
    badgeClass: 'badge-output',
    title: 'Figure 3.4 : 3D Petal Node Anchors resting on Standards Petals',
    file: imgUrl('iris_hud_petal_nodes.png'),
    desc: 'Close-up perspective of the 3 Standards petal nodes (01 Chat in Cyan #0eaee8, 02 Themes in Purple #9a6eb8, 03 Skills in Green #34d399) dynamically tracked and projected onto screen coordinates at 60 FPS via project3DPoint().'
  },
  {
    topic: 'TOPIC 03 : PROCEDURAL 3D WEBGL IRIS FLOWER HUD',
    subsystem: 'website/components/ui/IrisFlowerBackground.tsx',
    type: 'OUTPUT SCREEN',
    badgeClass: 'badge-output',
    title: 'Figure 3.5 : 3D Iris Flower HUD with Projected Lateral Petal Callouts',
    file: imgUrl('output_flower_with_3dots.png'),
    desc: 'Full viewport view showing the 3D Iris Flower centered on the holographic stage with the 3 interactive petal anchor callouts projected laterally: 01 Neural Chat (Left), 02 Visual Themes (Center), and 03 System Rules (Right).'
  },
  {
    topic: 'TOPIC 03 : PROCEDURAL 3D WEBGL IRIS FLOWER HUD',
    subsystem: 'website/components/ui/IrisFlowerBackground.tsx',
    type: 'OUTPUT SCREEN',
    badgeClass: 'badge-output',
    title: 'Figure 3.6 : Full Botanical Bloom Perspective & Radiating Veining',
    file: imgUrl('output_flower_full_bloom.jpg'),
    desc: 'High-detail rendering of the botanical geometry showing ruffled margin translucency, central spine midribs, golden papillose beards, split wingtip style crests, and natural stem S-curve tapering.'
  },

  // -------------------------------------------------------------
  // TOPIC 4: COGNITIVE MIND & NEURAL CHAT SYSTEM
  // -------------------------------------------------------------
  {
    topic: 'TOPIC 04 : COGNITIVE MIND & NEURAL CHAT SYSTEM',
    subsystem: 'website/app/dashboard/chat/page.tsx',
    type: 'INPUT SCREEN',
    badgeClass: 'badge-input',
    title: 'Figure 4.1 : Neural Chat Console & Natural Language Input Interface',
    file: imgUrl('output_screen_capabilities.png'),
    desc: 'The natural language prompt console and voice command interface. Allows typing or speaking complex queries, system instructions, and multi-turn conversational goals.'
  },
  {
    topic: 'TOPIC 04 : COGNITIVE MIND & NEURAL CHAT SYSTEM',
    subsystem: 'AI model (iris)/core/brain.py',
    type: 'OUTPUT SCREEN',
    badgeClass: 'badge-output',
    title: 'Figure 4.2 : Neural AI Reasoning Stream & Fast-Path Execution Console',
    file: imgUrl('output_screen_execution.png'),
    desc: 'The execution console output displaying intent classification results, fast-path sub-50ms hardware bypass execution logs, local Ollama token stream output, and synthesized vocal responses.'
  },

  // -------------------------------------------------------------
  // TOPIC 5: OPERATING SYSTEM HANDS & DESKTOP AUTOMATION
  // -------------------------------------------------------------
  {
    topic: 'TOPIC 05 : OPERATING SYSTEM HANDS & AUTOMATION',
    subsystem: 'AI model (iris)/hands/window_manager.py',
    type: 'OUTPUT SCREEN',
    badgeClass: 'badge-output',
    title: 'Figure 5.1 : Win32 Hands Desktop Window Snapping & Workspace Orchestration',
    file: imgUrl('output_screen_desktop.png'),
    desc: 'Operating system automation output executing under the Sub-2-Second Law. Demonstrates simultaneous launching and precise geometric window snapping of Visual Studio Code, Windows Terminal, and documentation browser tabs.'
  }
];

// Generate HTML
let html = `
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>IRIS AI - VISUAL SYSTEM DOSSIER (INPUT & OUTPUT SCREENS)</title>
<style>
  @page {
    size: A4 portrait;
    margin: 18mm 18mm 18mm 18mm;
  }
  @media print {
    body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    .page { page-break-after: always; }
    .page:last-child { page-break-after: avoid; }
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    padding: 0;
    font-family: 'Times New Roman', Times, serif;
    font-size: 11pt;
    line-height: 1.45;
    color: #111;
  }
  .page {
    position: relative;
    width: 100%;
    min-height: 260mm;
    page-break-after: always;
    box-sizing: border-box;
    padding-top: 2px;
  }
  .double-line {
    border-top: 2.5px solid #000;
    border-bottom: 1px solid #000;
    height: 3px;
    margin-bottom: 8px;
  }
  .running-header {
    text-align: right;
    font-size: 8.5pt;
    font-weight: bold;
    letter-spacing: 1px;
    margin-top: -4px;
    margin-bottom: 14px;
    font-family: 'Times New Roman', serif;
  }
  .page-num {
    position: absolute;
    bottom: 0mm;
    right: 5mm;
    font-size: 10pt;
    font-weight: bold;
  }
  .topic-title {
    font-size: 11.5pt;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #1e3a8a;
    margin-bottom: 4px;
  }
  .image-wrapper {
    text-align: center;
    margin: 12px 0;
    border: 1.5px solid #000;
    border-radius: 6px;
    padding: 8px;
    background: #000;
  }
  .image-wrapper img {
    max-width: 100%;
    max-height: 145mm;
    object-fit: contain;
    border-radius: 4px;
    display: block;
    margin: 0 auto;
  }
  .badge-input {
    display: inline-block;
    background: #0284c7;
    color: #fff;
    font-size: 8pt;
    font-weight: bold;
    padding: 2px 8px;
    border-radius: 4px;
    letter-spacing: 0.5px;
  }
  .badge-output {
    display: inline-block;
    background: #16a34a;
    color: #fff;
    font-size: 8pt;
    font-weight: bold;
    padding: 2px 8px;
    border-radius: 4px;
    letter-spacing: 0.5px;
  }
  .caption-box {
    border: 1px solid #cbd5e1;
    background: #f8fafc;
    border-radius: 6px;
    padding: 10px 14px;
    margin-top: 10px;
  }
  .caption-title {
    font-size: 10.5pt;
    font-weight: bold;
    color: #0f172a;
    margin-bottom: 4px;
  }
  .caption-meta {
    font-size: 8.5pt;
    color: #475569;
    font-family: Consolas, monospace;
    margin-bottom: 6px;
  }
  .caption-desc {
    font-size: 9.5pt;
    text-align: justify;
    line-height: 1.4;
    color: #334155;
    margin: 0;
  }
</style>
</head>
<body>
`;

// PAGE 1: COVER PAGE
html += `
<div class="page" style="text-align: center; padding-top: 10px;">
  <div class="double-line"></div>
  
  <div style="font-size: 16pt; font-weight: bold; letter-spacing: 2px; margin-top: 15px; margin-bottom: 5px;">
    PROJECT REPORT
  </div>
  <div style="font-size: 13pt; font-weight: bold; margin-bottom: 8px;">
    ON
  </div>
  <div style="font-size: 26pt; font-weight: bold; letter-spacing: 3px; color: #8B0000; margin-bottom: 4px; font-family: 'Times New Roman', serif;">
    IRIS
  </div>
  <div style="font-size: 10pt; font-weight: bold; letter-spacing: 1px; color: #1e3a8a; margin-bottom: 8px;">
    (INTEGRATED REACTIVE INTELLIGENT SYSTEM / IRIS AI)
  </div>

  <div style="font-size: 12pt; font-weight: bold; letter-spacing: 1.5px; color: #047857; margin-bottom: 12px; text-transform: uppercase;">
    VOLUME 1 : VISUAL SYSTEM DOSSIER<br>
    <span style="font-size: 10pt; color: #334155;">COMPLETE INPUT AND OUTPUT SCREENS SPECIFICATION</span>
  </div>

  <div style="font-size: 8.5pt; font-weight: bold; line-height: 1.4; margin-bottom: 12px; padding: 0 30px;">
    SUBMITTED IN THE PARTIAL FULFILLMENT OF THE REQUIREMENTS FOR THE AWARD OF<br>
    DIPLOMA IN ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING
  </div>

  <div style="font-size: 11pt; font-weight: bold; color: #1e40af; margin-bottom: 10px;">
    BY
  </div>

  <div style="font-size: 9pt; font-weight: bold; line-height: 1.5; margin-bottom: 15px;">
    (054-AI-015) V. SAI SUPRAJA<br>
    (054-AI-030) G. YESHWANTH SIVA RAMA TEJA<br>
    (054-AI-031) K. SRAVANI<br>
    (054-AI-026) M. SANTOSH<br>
    (054-AI-001) V. AMULYA<br>
    (054-AI-056) B. JINTU MONI<br>
    (054-AI-035) B.A. SHAALOM<br>
    (054-AI-054) R. SIDDHU<br>
    (054-AI-067) N. MADHAV<br>
    (054-AI-059) D. TULASI
  </div>

  <div style="font-size: 8.5pt; font-weight: bold; margin-bottom: 10px;">
    UNDER THE GUIDANCE OF <u>Mr. VIKRAM CHAKRAVORTHY</u>, LECTURER IN ECE DEPARTMENT
  </div>

  <div style="margin: 10px 0;">
    <img src="${logo}" style="width: 100px; height: 100px; object-fit: contain; border-radius: 50%;">
  </div>

  <div style="font-size: 12pt; font-weight: bold; letter-spacing: 1px; margin-top: 6px;">
    GOVERNMENT INSTITUTE OF ELECTRONICS,
  </div>
  <div style="font-size: 11pt; font-weight: bold; letter-spacing: 1.5px; margin-bottom: 2px;">
    SECUNDERABAD
  </div>
  <div style="font-size: 9pt; font-style: italic; margin-bottom: 2px;">
    (Approved by TS SBTET, Hyderabad)
  </div>
  <div style="font-size: 8.5pt; margin-bottom: 6px;">
    East Marredpally, Secunderabad - 500026
  </div>
  <div style="font-size: 10pt; font-weight: bold;">
    2026
  </div>
  <div class="page-num">1</div>
</div>
`;

// PAGE 2: VISUAL CONTENTS INDEX
html += `
<div class="page">
  <div class="double-line"></div>
  <div class="running-header">IRIS &bull; VISUAL SYSTEM DOSSIER</div>
  
  <div style="text-align: center; margin-top: 15px; margin-bottom: 20px;">
    <div style="font-size: 14pt; font-weight: bold; letter-spacing: 1.5px;">
      VISUAL CONTENTS &bull; INPUT &amp; OUTPUT SCREENS INDEX
    </div>
  </div>

  <table style="width: 100%; border-collapse: collapse; font-size: 9.5pt; border: 1.5px solid #000;">
    <thead>
      <tr style="background: #f2f2f2;">
        <th style="border: 1px solid #000; padding: 6px; width: 12%; text-align: center;">FIGURE</th>
        <th style="border: 1px solid #000; padding: 6px; width: 68%;">IMAGE DESCRIPTION &amp; SYSTEM TOPIC</th>
        <th style="border: 1px solid #000; padding: 6px; width: 10%; text-align: center;">MODALITY</th>
        <th style="border: 1px solid #000; padding: 6px; width: 10%; text-align: center;">PAGE</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td style="border: 1px solid #000; padding: 5px; text-align: center; font-weight: bold;">Figure 1.1</td>
        <td style="border: 1px solid #000; padding: 5px;">"Flower Valley" 3D Experience (Ethos: "Grown, Not Built")</td>
        <td style="border: 1px solid #000; padding: 5px; text-align: center; color: #16a34a; font-weight: bold;">OUTPUT</td>
        <td style="border: 1px solid #000; padding: 5px; text-align: center; font-weight: bold;">3</td>
      </tr>
      <tr>
        <td style="border: 1px solid #000; padding: 5px; text-align: center; font-weight: bold;">Figure 2.1</td>
        <td style="border: 1px solid #000; padding: 5px;">Dashboard Mode Toggles &amp; System Control Strip</td>
        <td style="border: 1px solid #000; padding: 5px; text-align: center; color: #0284c7; font-weight: bold;">INPUT</td>
        <td style="border: 1px solid #000; padding: 5px; text-align: center; font-weight: bold;">4</td>
      </tr>
      <tr>
        <td style="border: 1px solid #000; padding: 5px; text-align: center; font-weight: bold;">Figure 2.2</td>
        <td style="border: 1px solid #000; padding: 5px;">3D Iris Live Parameter Adjustment Bar (65% Size, -17&deg; Angle, 70s Orbit)</td>
        <td style="border: 1px solid #000; padding: 5px; text-align: center; color: #0284c7; font-weight: bold;">INPUT</td>
        <td style="border: 1px solid #000; padding: 5px; text-align: center; font-weight: bold;">5</td>
      </tr>
      <tr>
        <td style="border: 1px solid #000; padding: 5px; text-align: center; font-weight: bold;">Figure 2.3</td>
        <td style="border: 1px solid #000; padding: 5px;">System Engine Telemetry &amp; Subscription Status Strip</td>
        <td style="border: 1px solid #000; padding: 5px; text-align: center; color: #16a34a; font-weight: bold;">OUTPUT</td>
        <td style="border: 1px solid #000; padding: 5px; text-align: center; font-weight: bold;">6</td>
      </tr>
      <tr>
        <td style="border: 1px solid #000; padding: 5px; text-align: center; font-weight: bold;">Figure 2.4</td>
        <td style="border: 1px solid #000; padding: 5px;">Primary Desktop Subsystem Feature Navigation Cards</td>
        <td style="border: 1px solid #000; padding: 5px; text-align: center; color: #16a34a; font-weight: bold;">OUTPUT</td>
        <td style="border: 1px solid #000; padding: 5px; text-align: center; font-weight: bold;">7</td>
      </tr>
      <tr>
        <td style="border: 1px solid #000; padding: 5px; text-align: center; font-weight: bold;">Figure 2.5</td>
        <td style="border: 1px solid #000; padding: 5px;">Live Telemetry Gauges, Token Ratios &amp; Resource Graphs</td>
        <td style="border: 1px solid #000; padding: 5px; text-align: center; color: #16a34a; font-weight: bold;">OUTPUT</td>
        <td style="border: 1px solid #000; padding: 5px; text-align: center; font-weight: bold;">8</td>
      </tr>
      <tr>
        <td style="border: 1px solid #000; padding: 5px; text-align: center; font-weight: bold;">Figure 3.1</td>
        <td style="border: 1px solid #000; padding: 5px;">Procedural 3D WebGL Iris Flower with Double-Sided Fresnel Shading</td>
        <td style="border: 1px solid #000; padding: 5px; text-align: center; color: #16a34a; font-weight: bold;">OUTPUT</td>
        <td style="border: 1px solid #000; padding: 5px; text-align: center; font-weight: bold;">9</td>
      </tr>
      <tr>
        <td style="border: 1px solid #000; padding: 5px; text-align: center; font-weight: bold;">Figure 3.2</td>
        <td style="border: 1px solid #000; padding: 5px;">Interactive 3D Upper Petal Nodes HUD Header &amp; Expand Control</td>
        <td style="border: 1px solid #000; padding: 5px; text-align: center; color: #0284c7; font-weight: bold;">INPUT</td>
        <td style="border: 1px solid #000; padding: 5px; text-align: center; font-weight: bold;">10</td>
      </tr>
      <tr>
        <td style="border: 1px solid #000; padding: 5px; text-align: center; font-weight: bold;">Figure 3.3</td>
        <td style="border: 1px solid #000; padding: 5px;">Directional Indicator Arrow &amp; Slanted Parallelogram Card Specification</td>
        <td style="border: 1px solid #000; padding: 5px; text-align: center; color: #0284c7; font-weight: bold;">SPEC</td>
        <td style="border: 1px solid #000; padding: 5px; text-align: center; font-weight: bold;">11</td>
      </tr>
      <tr>
        <td style="border: 1px solid #000; padding: 5px; text-align: center; font-weight: bold;">Figure 3.4</td>
        <td style="border: 1px solid #000; padding: 5px;">3D Petal Node Anchors resting on Standards Petals</td>
        <td style="border: 1px solid #000; padding: 5px; text-align: center; color: #16a34a; font-weight: bold;">OUTPUT</td>
        <td style="border: 1px solid #000; padding: 5px; text-align: center; font-weight: bold;">12</td>
      </tr>
      <tr>
        <td style="border: 1px solid #000; padding: 5px; text-align: center; font-weight: bold;">Figure 3.5</td>
        <td style="border: 1px solid #000; padding: 5px;">3D Iris Flower HUD with Projected Lateral Petal Callouts</td>
        <td style="border: 1px solid #000; padding: 5px; text-align: center; color: #16a34a; font-weight: bold;">OUTPUT</td>
        <td style="border: 1px solid #000; padding: 5px; text-align: center; font-weight: bold;">13</td>
      </tr>
      <tr>
        <td style="border: 1px solid #000; padding: 5px; text-align: center; font-weight: bold;">Figure 3.6</td>
        <td style="border: 1px solid #000; padding: 5px;">Full Botanical Bloom Perspective &amp; Radiating Veining</td>
        <td style="border: 1px solid #000; padding: 5px; text-align: center; color: #16a34a; font-weight: bold;">OUTPUT</td>
        <td style="border: 1px solid #000; padding: 5px; text-align: center; font-weight: bold;">14</td>
      </tr>
      <tr>
        <td style="border: 1px solid #000; padding: 5px; text-align: center; font-weight: bold;">Figure 4.1</td>
        <td style="border: 1px solid #000; padding: 5px;">Neural Chat Console &amp; Natural Language Input Interface</td>
        <td style="border: 1px solid #000; padding: 5px; text-align: center; color: #0284c7; font-weight: bold;">INPUT</td>
        <td style="border: 1px solid #000; padding: 5px; text-align: center; font-weight: bold;">15</td>
      </tr>
      <tr>
        <td style="border: 1px solid #000; padding: 5px; text-align: center; font-weight: bold;">Figure 4.2</td>
        <td style="border: 1px solid #000; padding: 5px;">Neural AI Reasoning Stream &amp; Fast-Path Execution Console</td>
        <td style="border: 1px solid #000; padding: 5px; text-align: center; color: #16a34a; font-weight: bold;">OUTPUT</td>
        <td style="border: 1px solid #000; padding: 5px; text-align: center; font-weight: bold;">16</td>
      </tr>
      <tr>
        <td style="border: 1px solid #000; padding: 5px; text-align: center; font-weight: bold;">Figure 5.1</td>
        <td style="border: 1px solid #000; padding: 5px;">Win32 Hands Desktop Window Snapping &amp; Workspace Orchestration</td>
        <td style="border: 1px solid #000; padding: 5px; text-align: center; color: #16a34a; font-weight: bold;">OUTPUT</td>
        <td style="border: 1px solid #000; padding: 5px; text-align: center; font-weight: bold;">17</td>
      </tr>
    </tbody>
  </table>
  <div class="page-num">2</div>
</div>
`;

// PAGE 3 ONWARDS: IMAGE SHOWCASE PAGES
images.forEach((item, index) => {
  const pageNum = index + 3;
  html += `
  <div class="page">
    <div class="double-line"></div>
    <div class="running-header">IRIS AI &bull; VISUAL SYSTEM DOSSIER</div>

    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
      <div class="topic-title">${item.topic}</div>
      <span class="${item.badgeClass}">${item.type}</span>
    </div>

    <div class="image-wrapper">
      <img src="${item.file}" alt="${item.title}">
    </div>

    <div class="caption-box">
      <div class="caption-title">${item.title}</div>
      <div class="caption-meta">Subsystem Component: ${item.subsystem}</div>
      <p class="caption-desc">${item.desc}</p>
    </div>

    <div class="page-num">${pageNum}</div>
  </div>
  `;
});

html += `
</body>
</html>
`;

fs.writeFileSync(OUTPUT_HTML, html, 'utf8');
console.log('HTML for v.1 generated:', OUTPUT_HTML, 'Size:', fs.statSync(OUTPUT_HTML).size);

const chromePath = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
console.log('Compiling v.1.pdf via Google Chrome...');

const res = spawnSync(chromePath, [
  '--headless',
  '--no-sandbox',
  '--disable-gpu',
  '--run-all-compositor-stages-before-draw',
  '--print-to-pdf=' + OUTPUT_PDF,
  'file:///' + OUTPUT_HTML.replace(/\\\\/g, '/')
]);

console.log('Chrome Status:', res.status);
console.log('PDF Exists:', fs.existsSync(OUTPUT_PDF));

if (fs.existsSync(OUTPUT_PDF)) {
  const size = fs.statSync(OUTPUT_PDF).size;
  console.log('v.1.pdf Size:', size, 'bytes (' + (size / (1024*1024)).toFixed(2) + ' MB)');
  fs.copyFileSync(OUTPUT_PDF, OUTPUT_PDF_ALT);
  console.log('Also created v1.pdf as mirror.');
} else {
  if (res.stderr) console.error('Stderr:', res.stderr.toString());
}

