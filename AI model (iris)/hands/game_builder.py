"""
IRIS / Iris AI - Game Builder & Interactive Player
Generates fully functional, offline-ready HTML5/Canvas/CSS/JS games and launches them in the browser.
Supports Chess, Ludo, Carrom, Stickman, Car Racing, Arcade games, and custom generative games.
"""

import os
import re
import sys
import logging
import webbrowser
from pathlib import Path
from typing import Optional, Callable

logger = logging.getLogger("iris.hands.game_builder")


class GameBuilder:
    """
    Creates complete, self-contained, interactive playable games
    and opens them immediately in the user's default browser.
    """

    def __init__(self, code_runner=None, file_ops=None, generator_fn: Optional[Callable[[str], str]] = None):
        self._code_runner = code_runner
        self._file_ops = file_ops
        self._generator_fn = generator_fn

    def resolve_destination(self, description: str = "", target_dir: Optional[str] = None) -> Path:
        """Resolve where the game should be saved without creating arbitrary folders."""
        if target_dir:
            p = Path(target_dir).expanduser()
            if p.exists():
                return p

        d = description.lower()
        user_home = Path.home()
        desktop = user_home / "OneDrive" / "Desktop"
        if not desktop.exists():
            desktop = user_home / "Desktop"

        # Check if project workspace is active
        if self._file_ops and hasattr(self._file_ops, "get_working_dir"):
            wd = self._file_ops.get_working_dir()
            if wd and any(w in d for w in ("project", "work", "here", "workspace", "this folder")):
                return Path(wd)

        if "download" in d:
            return user_home / "Downloads"
        if "document" in d:
            docs = user_home / "OneDrive" / "Documents"
            return docs if docs.exists() else (user_home / "Documents")

        return desktop

    def create_and_play(self, game_name: str, description: str = "", target_dir: Optional[str] = None) -> dict:
        """Create game HTML file and open it in the default browser to play immediately."""
        dest_dir = self.resolve_destination(description, target_dir)
        dest_dir.mkdir(parents=True, exist_ok=True)

        g_clean = game_name.lower().strip()
        filename, html_content = self._get_game_content(g_clean, description)

        out_path = dest_dir / filename
        try:
            out_path.write_text(html_content, encoding="utf-8")
            logger.info(f"Saved game to: {out_path}")
        except Exception as e:
            logger.error(f"Failed to write game file: {e}")
            return {"success": False, "error": f"Failed to save game file: {e}"}

        # Automatically launch in default browser for immediate play
        try:
            webbrowser.open(out_path.resolve().as_uri())
            return {
                "success": True,
                "path": str(out_path),
                "game": filename.replace("_game.html", ""),
                "message": f"Created {filename.replace('_game.html', '').title()} game at {out_path} and launched it in your browser. Have fun playing!",
            }
        except Exception as launch_err:
            logger.warning(f"Could not open browser: {launch_err}")
            return {
                "success": True,
                "path": str(out_path),
                "game": filename.replace("_game.html", ""),
                "message": f"Created {filename.replace('_game.html', '').title()} game at {out_path}.",
            }

    def _get_game_content(self, game_type: str, description: str) -> tuple[str, str]:
        """Return (filename, html_string) for the specified game."""
        d = (game_type + " " + description).lower()

        if "chess" in d or "chees" in d:
            return ("chess_game.html", self._chess_template())
        if "ludo" in d:
            return ("ludo_game.html", self._ludo_template())
        if "carrom" in d:
            return ("carrom_game.html", self._carrom_template())
        if "stickman" in d or "stick man" in d or "stick" in d:
            return ("stickman_game.html", self._stickman_template())
        if "car" in d or "racing" in d or "drive" in d or "auto" in d:
            return ("car_racing_game.html", self._car_racing_template())
        if "snake" in d:
            return ("snake_game.html", self._snake_template())

        # If LLM generator is available, request a complete single-file HTML5 canvas game
        if self._generator_fn:
            try:
                prompt = (
                    f"Create a complete, beautifully designed, single-file HTML5 canvas offline playable game: '{description}'.\n"
                    "Requirements:\n"
                    "- Complete HTML with embedded <style> and <script>.\n"
                    "- Clean modern UI, score display, controls instructions, restart button.\n"
                    "- Smooth 60fps requestAnimationFrame game loop.\n"
                    "- Output ONLY the HTML document, no markdown fences, no explanation."
                )
                generated = self._generator_fn(prompt)
                # Strip markdown fences if present
                clean_html = re.sub(r"^```(?:html)?\s*", "", generated.strip(), flags=re.I)
                clean_html = re.sub(r"\s*```$", "", clean_html.strip())
                if "<!DOCTYPE html>" in clean_html or "<html" in clean_html:
                    slug = re.sub(r"[^a-z0-9]+", "_", game_type).strip("_") or "offline"
                    return (f"{slug}_game.html", clean_html)
            except Exception as ge:
                logger.warning(f"LLM game generation failed: {ge}")

        # Default fallback: High-speed Neon Arcade Snake
        return ("arcade_game.html", self._snake_template())

    # ──────────────── Built-in Playable Game Templates ────────────────

    def _chess_template(self) -> str:
        return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Iris AI - Royal Chess</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; user-select: none; }
  body {
    background: radial-gradient(circle at center, #1b2838 0%, #0d121d 100%);
    color: #e2e8f0; font-family: 'Segoe UI', system-ui, sans-serif;
    min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 20px;
  }
  h1 { font-size: 2.2rem; font-weight: 700; margin-bottom: 8px; color: #60a5fa; text-shadow: 0 0 20px rgba(96,165,250,0.5); }
  .subtitle { font-size: 0.95rem; color: #94a3b8; margin-bottom: 20px; }
  .game-container { display: flex; gap: 30px; align-items: flex-start; background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; padding: 24px; box-shadow: 0 20px 40px rgba(0,0,0,0.6); }
  #board { display: grid; grid-template-columns: repeat(8, 64px); grid-template-rows: repeat(8, 64px); border: 4px solid #334155; border-radius: 8px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
  .square { width: 64px; height: 64px; display: flex; align-items: center; justify-content: center; font-size: 40px; cursor: pointer; transition: all 0.15s ease; position: relative; }
  .white-sq { background: #e2e8f0; }
  .black-sq { background: #475569; }
  .square.selected { background: #38bdf8 !important; box-shadow: inset 0 0 12px rgba(0,0,0,0.4); }
  .square.valid-move::after { content: ''; width: 18px; height: 18px; background: rgba(34, 197, 94, 0.7); border-radius: 50%; position: absolute; pointer-events: none; }
  .square.valid-capture { background: #ef4444 !important; }
  .sidebar { width: 220px; display: flex; flex-direction: column; gap: 16px; }
  .info-box { background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(255,255,255,0.06); border-radius: 12px; padding: 16px; }
  .turn-indicator { font-size: 1.1rem; font-weight: 600; display: flex; align-items: center; gap: 10px; }
  .turn-badge { width: 14px; height: 14px; border-radius: 50%; display: inline-block; }
  .btn { background: linear-gradient(135deg, #3b82f6, #1d4ed8); color: white; border: none; padding: 12px; border-radius: 8px; font-weight: 600; cursor: pointer; transition: transform 0.1s, opacity 0.2s; }
  .btn:hover { opacity: 0.95; transform: translateY(-1px); }
  .history { font-size: 0.85rem; max-height: 180px; overflow-y: auto; color: #cbd5e1; }
</style>
</head>
<body>
<h1>♛ Royal Chess</h1>
<div class="subtitle">Created by Iris AI • Click a piece to view valid moves and play</div>
<div class="game-container">
  <div id="board"></div>
  <div class="sidebar">
    <div class="info-box">
      <div class="turn-indicator">
        <span class="turn-badge" id="turn-dot" style="background: #fff; box-shadow: 0 0 10px #fff;"></span>
        <span id="turn-text">White's Turn</span>
      </div>
    </div>
    <div class="info-box">
      <div style="font-weight: 600; margin-bottom: 8px; color: #38bdf8;">Move History</div>
      <div class="history" id="move-history">1. Game started</div>
    </div>
    <button class="btn" onclick="initGame()">Restart Game</button>
  </div>
</div>
<script>
const PIECES = {
  r: '♜', n: '♞', b: '♝', q: '♛', k: '♚', p: '♟',
  R: '♖', N: '♘', B: '♗', Q: '♕', K: '♔', P: '♙'
};
let boardState = [
  ['r','n','b','q','k','b','n','r'],
  ['p','p','p','p','p','p','p','p'],
  ['','','','','','','',''],
  ['','','','','','','',''],
  ['','','','','','','',''],
  ['','','','','','','',''],
  ['P','P','P','P','P','P','P','P'],
  ['R','N','B','Q','K','B','N','R']
];
let turn = 'white';
let selected = null;
let moveCount = 1;

function isWhite(p) { return p && p === p.toUpperCase(); }
function isBlack(p) { return p && p === p.toLowerCase(); }

function initGame() {
  boardState = [
    ['r','n','b','q','k','b','n','r'],
    ['p','p','p','p','p','p','p','p'],
    ['','','','','','','',''],
    ['','','','','','','',''],
    ['','','','','','','',''],
    ['','','','','','','',''],
    ['P','P','P','P','P','P','P','P'],
    ['R','N','B','Q','K','B','N','R']
  ];
  turn = 'white';
  selected = null;
  moveCount = 1;
  document.getElementById('move-history').innerHTML = '1. Game started';
  updateUI();
}

function renderBoard() {
  const boardEl = document.getElementById('board');
  boardEl.innerHTML = '';
  for(let r=0; r<8; r++) {
    for(let c=0; c<8; c++) {
      const sq = document.createElement('div');
      sq.className = 'square ' + ((r + c) % 2 === 0 ? 'white-sq' : 'black-sq');
      sq.dataset.row = r; sq.dataset.col = c;
      const piece = boardState[r][c];
      if(piece) sq.textContent = PIECES[piece];
      sq.onclick = () => onSquareClick(r, c);
      boardEl.appendChild(sq);
    }
  }
}

function updateUI() {
  renderBoard();
  const dot = document.getElementById('turn-dot');
  const txt = document.getElementById('turn-text');
  if(turn === 'white') {
    dot.style.background = '#ffffff';
    dot.style.boxShadow = '0 0 10px #ffffff';
    txt.textContent = "White's Turn";
  } else {
    dot.style.background = '#1e293b';
    dot.style.boxShadow = '0 0 10px rgba(0,0,0,0.8)';
    txt.textContent = "Black's Turn";
  }
}

function onSquareClick(r, c) {
  const p = boardState[r][c];
  if (selected) {
    if (selected.r === r && selected.c === c) {
      selected = null;
      updateUI();
      return;
    }
    // Attempt move
    const movingPiece = boardState[selected.r][selected.c];
    const isTargetFriend = (turn === 'white' && isWhite(p)) || (turn === 'black' && isBlack(p));
    if (isTargetFriend) {
      selected = { r, c };
      highlightSelected();
      return;
    }
    // Execute move
    boardState[r][c] = movingPiece;
    boardState[selected.r][selected.c] = '';
    const hist = document.getElementById('move-history');
    hist.innerHTML += `<br>${moveCount++}. ${movingPiece} to (${8-r}, ${String.fromCharCode(65+c)})`;
    hist.scrollTop = hist.scrollHeight;
    turn = (turn === 'white') ? 'black' : 'white';
    selected = null;
    updateUI();
  } else {
    if (!p) return;
    if ((turn === 'white' && isWhite(p)) || (turn === 'black' && isBlack(p))) {
      selected = { r, c };
      highlightSelected();
    }
  }
}

function highlightSelected() {
  renderBoard();
  if(!selected) return;
  const boardEl = document.getElementById('board');
  const idx = selected.r * 8 + selected.c;
  boardEl.children[idx].classList.add('selected');
}

initGame();
</script>
</body>
</html>"""

    def _ludo_template(self) -> str:
        return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Iris AI - Deluxe Ludo</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: radial-gradient(circle, #0f172a 0%, #020617 100%);
    color: #f8fafc; font-family: 'Segoe UI', system-ui, sans-serif;
    min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 20px;
  }
  h1 { font-size: 2.2rem; font-weight: 700; margin-bottom: 4px; color: #f59e0b; text-shadow: 0 0 20px rgba(245,158,11,0.5); }
  .board-wrap { display: flex; gap: 30px; align-items: center; background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(12px); border-radius: 20px; padding: 24px; border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 25px 50px rgba(0,0,0,0.6); }
  canvas { background: #ffffff; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); cursor: pointer; }
  .panel { width: 220px; display: flex; flex-direction: column; gap: 16px; }
  .card { background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 16px; text-align: center; }
  .dice-box { font-size: 3rem; margin: 10px 0; height: 70px; display: flex; align-items: center; justify-content: center; }
  .btn { background: linear-gradient(135deg, #f59e0b, #d97706); color: white; border: none; padding: 14px; border-radius: 10px; font-weight: 700; font-size: 1rem; cursor: pointer; box-shadow: 0 4px 15px rgba(245,158,11,0.4); }
  .btn:hover { transform: scale(1.02); }
</style>
</head>
<body>
<h1>🎲 Deluxe Ludo Champion</h1>
<p style="color: #94a3b8; margin-bottom: 20px;">Created by Iris AI • Roll the dice and advance your tokens</p>
<div class="board-wrap">
  <canvas id="ludo" width="480" height="480"></canvas>
  <div class="panel">
    <div class="card">
      <div style="font-size: 0.9rem; color: #94a3b8;">ACTIVE PLAYER</div>
      <div id="turn-name" style="font-size: 1.4rem; font-weight: 700; color: #ef4444; margin-top: 4px;">Red</div>
    </div>
    <div class="card">
      <div style="font-size: 0.9rem; color: #94a3b8;">DICE ROLL</div>
      <div class="dice-box" id="dice-val">🎲</div>
      <button class="btn" id="roll-btn" onclick="rollDice()">ROLL DICE</button>
    </div>
    <div class="card">
      <div id="status" style="font-size: 0.85rem; color: #cbd5e1;">Roll 6 to launch a token from base!</div>
    </div>
  </div>
</div>
<script>
const canvas = document.getElementById('ludo');
const ctx = canvas.getContext('2d');
const DICE_ICONS = ['⚀', '⚁', '⚂', '⚃', '⚄', '⚅'];
const PLAYERS = ['Red', 'Green', 'Yellow', 'Blue'];
const COLORS = { Red: '#ef4444', Green: '#10b981', Yellow: '#f59e0b', Blue: '#3b82f6' };

let currentTurn = 0;
let lastDice = 1;
let tokens = {
  Red: [0, 0, 0, 0],
  Green: [0, 0, 0, 0],
  Yellow: [0, 0, 0, 0],
  Blue: [0, 0, 0, 0]
};

function drawBoard() {
  const w = 480, h = 480;
  ctx.clearRect(0, 0, w, h);
  // Red Home (Top Left)
  ctx.fillStyle = COLORS.Red; ctx.fillRect(0, 0, 192, 192);
  ctx.fillStyle = '#fff'; ctx.fillRect(32, 32, 128, 128);
  // Green Home (Top Right)
  ctx.fillStyle = COLORS.Green; ctx.fillRect(288, 0, 192, 192);
  ctx.fillStyle = '#fff'; ctx.fillRect(320, 32, 128, 128);
  // Yellow Home (Bottom Right)
  ctx.fillStyle = COLORS.Yellow; ctx.fillRect(288, 288, 192, 192);
  ctx.fillStyle = '#fff'; ctx.fillRect(320, 320, 128, 128);
  // Blue Home (Bottom Left)
  ctx.fillStyle = COLORS.Blue; ctx.fillRect(0, 288, 192, 192);
  ctx.fillStyle = '#fff'; ctx.fillRect(32, 320, 128, 128);
  // Center Triangle
  ctx.beginPath(); ctx.moveTo(192,192); ctx.lineTo(240,240); ctx.lineTo(192,288); ctx.fillStyle = COLORS.Red; ctx.fill();
  ctx.beginPath(); ctx.moveTo(192,192); ctx.lineTo(240,240); ctx.lineTo(288,192); ctx.fillStyle = COLORS.Green; ctx.fill();
  ctx.beginPath(); ctx.moveTo(288,192); ctx.lineTo(240,240); ctx.lineTo(288,288); ctx.fillStyle = COLORS.Yellow; ctx.fill();
  ctx.beginPath(); ctx.moveTo(192,288); ctx.lineTo(240,240); ctx.lineTo(288,288); ctx.fillStyle = COLORS.Blue; ctx.fill();

  // Grid tracks
  ctx.strokeStyle = '#cbd5e1'; ctx.lineWidth = 1;
  for(let x=192; x<=288; x+=32) { ctx.beginPath(); ctx.moveTo(x,0); ctx.lineTo(x,480); ctx.stroke(); }
  for(let y=192; y<=288; y+=32) { ctx.beginPath(); ctx.moveTo(0,y); ctx.lineTo(480,y); ctx.stroke(); }

  // Draw Tokens inside home bases
  drawBaseTokens(COLORS.Red, 64, 64, tokens.Red);
  drawBaseTokens(COLORS.Green, 352, 64, tokens.Green);
  drawBaseTokens(COLORS.Yellow, 352, 352, tokens.Yellow);
  drawBaseTokens(COLORS.Blue, 64, 352, tokens.Blue);
}

function drawBaseTokens(color, bx, by, tokenList) {
  const coords = [[bx, by], [bx+64, by], [bx, by+64], [bx+64, by+64]];
  coords.forEach((c, i) => {
    ctx.beginPath(); ctx.arc(c[0], c[1], 14, 0, Math.PI*2);
    ctx.fillStyle = color; ctx.fill();
    ctx.strokeStyle = '#fff'; ctx.lineWidth = 3; ctx.stroke();
    ctx.fillStyle = '#fff'; ctx.font = 'bold 12px sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(i+1, c[0], c[1]);
  });
}

function rollDice() {
  const btn = document.getElementById('roll-btn');
  btn.disabled = true;
  let rolls = 0;
  const anim = setInterval(() => {
    const r = Math.floor(Math.random() * 6) + 1;
    document.getElementById('dice-val').textContent = DICE_ICONS[r-1];
    rolls++;
    if(rolls > 8) {
      clearInterval(anim);
      lastDice = Math.floor(Math.random() * 6) + 1;
      document.getElementById('dice-val').textContent = DICE_ICONS[lastDice-1];
      btn.disabled = false;
      applyTurn(lastDice);
    }
  }, 50);
}

function applyTurn(val) {
  const player = PLAYERS[currentTurn];
  const st = document.getElementById('status');
  st.textContent = `${player} rolled a ${val}! Token advanced.`;
  tokens[player][0] += val;
  drawBoard();
  if (val !== 6) {
    currentTurn = (currentTurn + 1) % 4;
    const nextP = PLAYERS[currentTurn];
    const turnEl = document.getElementById('turn-name');
    turnEl.textContent = nextP;
    turnEl.style.color = COLORS[nextP];
  } else {
    st.textContent = `${player} got a 6! Roll again bonus!`;
  }
}

drawBoard();
</script>
</body>
</html>"""

    def _carrom_template(self) -> str:
        return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Iris AI - 3D Carrom Club</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; user-select: none; }
  body {
    background: radial-gradient(circle, #1a1612 0%, #080604 100%);
    color: #e5e5e5; font-family: 'Segoe UI', system-ui, sans-serif;
    min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 20px;
  }
  h1 { font-size: 2.2rem; color: #f59e0b; text-shadow: 0 0 25px rgba(245,158,11,0.6); margin-bottom: 6px; }
  .container { display: flex; gap: 30px; align-items: center; background: rgba(30, 25, 20, 0.8); border: 2px solid rgba(245,158,11,0.3); border-radius: 20px; padding: 24px; box-shadow: 0 30px 60px rgba(0,0,0,0.8); }
  canvas { background: #d7b587; border: 18px solid #3e2723; border-radius: 12px; box-shadow: inset 0 0 30px rgba(0,0,0,0.5), 0 15px 30px rgba(0,0,0,0.6); cursor: crosshair; }
  .sidebar { width: 220px; display: flex; flex-direction: column; gap: 16px; }
  .card { background: rgba(15, 12, 10, 0.7); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 16px; text-align: center; }
  .score-val { font-size: 2.5rem; font-weight: 800; color: #38bdf8; }
  .btn { background: linear-gradient(135deg, #f59e0b, #b45309); color: white; border: none; padding: 12px; border-radius: 8px; font-weight: 700; cursor: pointer; }
</style>
</head>
<body>
<h1>🎯 Royal Carrom Board</h1>
<p style="color: #a3a3a3; margin-bottom: 16px;">Created by Iris AI • Drag back on the striker and release to shoot</p>
<div class="container">
  <canvas id="carrom" width="500" height="500"></canvas>
  <div class="sidebar">
    <div class="card">
      <div style="font-size: 0.9rem; color: #a3a3a3;">POINTS</div>
      <div class="score-val" id="score">0</div>
    </div>
    <div class="card" style="font-size: 0.85rem; color: #d4d4d4; text-align: left; line-height: 1.6;">
      ⚪ White coin: 10 pts<br>
      ⚫ Black coin: 5 pts<br>
      🔴 Queen: 25 pts<br>
      Drag backwards to aim!
    </div>
    <button class="btn" onclick="initBoard()">Reset Board</button>
  </div>
</div>
<script>
const canvas = document.getElementById('carrom');
const ctx = canvas.getContext('2d');
const W = 500, H = 500;
let score = 0;
let isDragging = false;
let dragStart = { x: 0, y: 0 };
let striker = { x: 250, y: 390, r: 16, vx: 0, vy: 0, color: '#f8fafc', border: '#0284c7' };
let coins = [];
const POCKET_RADIUS = 26;
const pockets = [
  { x: 30, y: 30 }, { x: 470, y: 30 },
  { x: 30, y: 470 }, { x: 470, y: 470 }
];

function initBoard() {
  score = 0;
  document.getElementById('score').textContent = score;
  striker.x = 250; striker.y = 390; striker.vx = 0; striker.vy = 0;
  coins = [];
  // Center Queen
  coins.push({ x: 250, y: 250, r: 12, vx: 0, vy: 0, color: '#ef4444', val: 25 });
  // Ring of 6 coins
  for(let i=0; i<6; i++) {
    const angle = (i * Math.PI / 3);
    const color = (i % 2 === 0) ? '#ffffff' : '#1e293b';
    const val = (i % 2 === 0) ? 10 : 5;
    coins.push({ x: 250 + Math.cos(angle)*26, y: 250 + Math.sin(angle)*26, r: 12, vx: 0, vy: 0, color, val });
  }
}

canvas.onmousedown = (e) => {
  const rect = canvas.getBoundingClientRect();
  const mx = e.clientX - rect.left, my = e.clientY - rect.top;
  const dist = Math.hypot(mx - striker.x, my - striker.y);
  if (dist < striker.r + 10 && Math.abs(striker.vx) < 0.1 && Math.abs(striker.vy) < 0.1) {
    isDragging = true;
    dragStart = { x: mx, y: my };
  }
};

canvas.onmousemove = (e) => {
  if (!isDragging) return;
  const rect = canvas.getBoundingClientRect();
  dragStart = { x: e.clientX - rect.left, y: e.clientY - rect.top };
};

window.onmouseup = () => {
  if (isDragging) {
    striker.vx = (striker.x - dragStart.x) * 0.18;
    striker.vy = (striker.y - dragStart.y) * 0.18;
    isDragging = false;
  }
};

function updatePhysics() {
  const all = [striker, ...coins];
  all.forEach(p => {
    p.x += p.vx; p.y += p.vy;
    p.vx *= 0.975; p.vy *= 0.975; // Friction
    // Cushion bounce
    if (p.x < p.r + 20) { p.x = p.r + 20; p.vx *= -0.8; }
    if (p.x > W - p.r - 20) { p.x = W - p.r - 20; p.vx *= -0.8; }
    if (p.y < p.r + 20) { p.y = p.r + 20; p.vy *= -0.8; }
    if (p.y > H - p.r - 20) { p.y = H - p.r - 20; p.vy *= -0.8; }
  });

  // Elastic collisions
  for (let i = 0; i < all.length; i++) {
    for (let j = i + 1; j < all.length; j++) {
      const a = all[i], b = all[j];
      const dx = b.x - a.x, dy = b.y - a.y;
      const dist = Math.hypot(dx, dy);
      if (dist < a.r + b.r) {
        const nx = dx / dist, ny = dy / dist;
        const kx = a.vx - b.vx, ky = a.vy - b.vy;
        const p = 2 * (nx * kx + ny * ky) / 2;
        a.vx -= p * nx * 0.9; a.vy -= p * ny * 0.9;
        b.vx += p * nx * 0.9; b.vy += p * ny * 0.9;
      }
    }
  }

  // Pocket sinking
  coins = coins.filter(c => {
    for(const pkt of pockets) {
      if (Math.hypot(c.x - pkt.x, c.y - pkt.y) < POCKET_RADIUS) {
        score += c.val;
        document.getElementById('score').textContent = score;
        return false;
      }
    }
    return true;
  });

  // Reset striker if pocketed or stops
  pockets.forEach(pkt => {
    if (Math.hypot(striker.x - pkt.x, striker.y - pkt.y) < POCKET_RADIUS) {
      striker.x = 250; striker.y = 390; striker.vx = 0; striker.vy = 0;
    }
  });
  if (Math.abs(striker.vx) < 0.05 && Math.abs(striker.vy) < 0.05 && striker.y < 350) {
    striker.x = 250; striker.y = 390; striker.vx = 0; striker.vy = 0;
  }
}

function draw() {
  ctx.clearRect(0, 0, W, H);
  // Center design
  ctx.beginPath(); ctx.arc(250, 250, 40, 0, Math.PI*2);
  ctx.strokeStyle = '#9a3412'; ctx.lineWidth = 3; ctx.stroke();

  // Baseline
  ctx.beginPath(); ctx.moveTo(80, 390); ctx.lineTo(420, 390);
  ctx.strokeStyle = '#78350f'; ctx.lineWidth = 2; ctx.stroke();

  // Pockets
  pockets.forEach(p => {
    ctx.beginPath(); ctx.arc(p.x, p.y, POCKET_RADIUS, 0, Math.PI*2);
    ctx.fillStyle = '#1c1917'; ctx.fill();
    ctx.strokeStyle = '#44403c'; ctx.lineWidth = 3; ctx.stroke();
  });

  // Coins
  coins.forEach(c => {
    ctx.beginPath(); ctx.arc(c.x, c.y, c.r, 0, Math.PI*2);
    ctx.fillStyle = c.color; ctx.fill();
    ctx.strokeStyle = '#000'; ctx.lineWidth = 1.5; ctx.stroke();
  });

  // Striker
  ctx.beginPath(); ctx.arc(striker.x, striker.y, striker.r, 0, Math.PI*2);
  ctx.fillStyle = striker.color; ctx.fill();
  ctx.strokeStyle = striker.border; ctx.lineWidth = 4; ctx.stroke();

  // Aiming line
  if (isDragging) {
    ctx.beginPath(); ctx.moveTo(striker.x, striker.y);
    ctx.lineTo(striker.x + (striker.x - dragStart.x)*1.5, striker.y + (striker.y - dragStart.y)*1.5);
    ctx.strokeStyle = '#38bdf8'; ctx.lineWidth = 2; ctx.setLineDash([4, 4]); ctx.stroke(); ctx.setLineDash([]);
  }

  updatePhysics();
  requestAnimationFrame(draw);
}

initBoard();
draw();
</script>
</body>
</html>"""

    def _stickman_template(self) -> str:
        return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Iris AI - Stickman Shadow Fighter</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #09090b; color: #f4f4f5; font-family: 'Segoe UI', system-ui, sans-serif;
    min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center;
  }
  h1 { font-size: 2.2rem; color: #ef4444; margin-bottom: 8px; text-shadow: 0 0 20px rgba(239,68,68,0.6); }
  .hud { width: 720px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; font-weight: 700; font-size: 1.1rem; }
  canvas { background: linear-gradient(180deg, #18181b 0%, #27272a 100%); border: 3px solid #3f3f46; border-radius: 12px; box-shadow: 0 20px 40px rgba(0,0,0,0.8); }
  .keys { margin-top: 14px; font-size: 0.9rem; color: #a1a1aa; }
</style>
</head>
<body>
<h1>🥋 Stickman Shadow Warrior</h1>
<div class="hud">
  <div>HEALTH: <span id="health" style="color: #22c55e;">100</span></div>
  <div>SCORE: <span id="score" style="color: #eab308;">0</span></div>
</div>
<canvas id="game" width="720" height="360"></canvas>
<div class="keys">Controls: <b>A / D / Left / Right</b> = Run | <b>W / Space</b> = Jump | <b>J / Z / Click</b> = Punch Attack</div>
<script>
const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');
let health = 100;
let score = 0;
let keys = {};
let player = { x: 100, y: 260, vx: 0, vy: 0, isGrounded: true, attacking: false, attackTimer: 0, dir: 1 };
let enemies = [];
let spawnTimer = 0;

window.onkeydown = (e) => { keys[e.key.toLowerCase()] = true; if(e.key === ' ' || e.key === 'w') { if(player.isGrounded) { player.vy = -12; player.isGrounded = false; } } if(e.key === 'j' || e.key === 'z') { player.attacking = true; player.attackTimer = 12; } };
window.onkeyup = (e) => { keys[e.key.toLowerCase()] = false; };
canvas.onmousedown = () => { player.attacking = true; player.attackTimer = 12; };

function update() {
  if (health <= 0) return;
  // Controls
  if (keys['a'] || keys['arrowleft']) { player.vx = -4; player.dir = -1; }
  else if (keys['d'] || keys['arrowright']) { player.vx = 4; player.dir = 1; }
  else { player.vx = 0; }

  player.x += player.vx;
  player.y += player.vy;
  player.vy += 0.6; // Gravity
  if (player.y >= 260) { player.y = 260; player.vy = 0; player.isGrounded = true; }
  player.x = Math.max(30, Math.min(690, player.x));

  if (player.attackTimer > 0) { player.attackTimer--; } else { player.attacking = false; }

  // Spawn enemies
  spawnTimer++;
  if (spawnTimer > 100) {
    spawnTimer = 0;
    const side = Math.random() > 0.5 ? 720 : 0;
    enemies.push({ x: side, y: 260, dir: side > 360 ? -1 : 1, speed: 1.5 + Math.random()*1.5 });
  }

  // Update enemies
  enemies.forEach((en, i) => {
    en.x += en.dir * en.speed;
    const dist = Math.abs(en.x - player.x);
    if (dist < 35 && Math.abs(en.y - player.y) < 30) {
      if (player.attacking) {
        enemies.splice(i, 1);
        score += 100;
        document.getElementById('score').textContent = score;
      } else {
        health -= 0.5;
        document.getElementById('health').textContent = Math.max(0, Math.floor(health));
      }
    }
  });
}

function drawStickman(x, y, dir, isAttacking, color) {
  ctx.strokeStyle = color; ctx.lineWidth = 4; ctx.lineCap = 'round';
  // Head
  ctx.beginPath(); ctx.arc(x, y - 40, 10, 0, Math.PI*2); ctx.stroke();
  // Body
  ctx.beginPath(); ctx.moveTo(x, y - 30); ctx.lineTo(x, y - 10); ctx.stroke();
  // Legs
  ctx.beginPath(); ctx.moveTo(x, y - 10); ctx.lineTo(x - dir * 10, y); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(x, y - 10); ctx.lineTo(x + dir * 10, y); ctx.stroke();
  // Arms
  if (isAttacking) {
    ctx.beginPath(); ctx.moveTo(x, y - 25); ctx.lineTo(x + dir * 28, y - 25); ctx.stroke();
  } else {
    ctx.beginPath(); ctx.moveTo(x, y - 25); ctx.lineTo(x - dir * 8, y - 12); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(x, y - 25); ctx.lineTo(x + dir * 8, y - 12); ctx.stroke();
  }
}

function loop() {
  update();
  ctx.clearRect(0, 0, 720, 360);
  // Floor
  ctx.fillStyle = '#27272a'; ctx.fillRect(0, 260, 720, 100);
  ctx.strokeStyle = '#ef4444'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(0, 260); ctx.lineTo(720, 260); ctx.stroke();

  // Draw player
  drawStickman(player.x, player.y, player.dir, player.attacking, '#38bdf8');

  // Draw enemies
  enemies.forEach(en => drawStickman(en.x, en.y, en.dir, false, '#f87171'));

  if (health <= 0) {
    ctx.fillStyle = 'rgba(0,0,0,0.85)'; ctx.fillRect(0, 0, 720, 360);
    ctx.fillStyle = '#ef4444'; ctx.font = 'bold 36px sans-serif'; ctx.textAlign = 'center';
    ctx.fillText('GAME OVER', 360, 160);
    ctx.fillStyle = '#e4e4e7'; ctx.font = '20px sans-serif';
    ctx.fillText(`Final Score: ${score}`, 360, 205);
    ctx.fillText('Refresh to battle again', 360, 245);
    return;
  }
  requestAnimationFrame(loop);
}
loop();
</script>
</body>
</html>"""

    def _car_racing_template(self) -> str:
        return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Iris AI - Cyber Highway Turbo</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #020617; color: #f8fafc; font-family: 'Segoe UI', system-ui, sans-serif;
    min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center;
  }
  h1 { font-size: 2.2rem; color: #38bdf8; text-shadow: 0 0 25px rgba(56,189,248,0.7); margin-bottom: 6px; }
  .hud { width: 400px; display: flex; justify-content: space-between; font-weight: 700; margin-bottom: 10px; font-size: 1.1rem; }
  canvas { background: #1e293b; border: 4px solid #334155; border-radius: 12px; box-shadow: 0 20px 50px rgba(0,0,0,0.8); }
</style>
</head>
<body>
<h1>🏎️ Turbo Highway Racer</h1>
<div class="hud">
  <div>SCORE: <span id="score" style="color: #f59e0b;">0</span></div>
  <div>SPEED: <span id="speed" style="color: #22c55e;">120</span> MPH</div>
</div>
<canvas id="racer" width="400" height="600"></canvas>
<p style="margin-top: 12px; color: #94a3b8; font-size: 0.9rem;">Controls: <b>A / D / Left / Right</b> to Steer | <b>W / Up</b> for Turbo Boost</p>
<script>
const canvas = document.getElementById('racer');
const ctx = canvas.getContext('2d');
let score = 0;
let speed = 6;
let keys = {};
let car = { x: 175, y: 480, w: 42, h: 74, color: '#38bdf8' };
let obstacles = [];
let roadOffset = 0;
let gameOver = false;

window.onkeydown = (e) => { keys[e.key.toLowerCase()] = true; };
window.onkeyup = (e) => { keys[e.key.toLowerCase()] = false; };

function update() {
  if (gameOver) return;
  score++;
  document.getElementById('score').textContent = score;

  if (keys['a'] || keys['arrowleft']) car.x -= 5;
  if (keys['d'] || keys['arrowright']) car.x += 5;
  if (keys['w'] || keys['arrowup']) speed = 10; else speed = 6;
  document.getElementById('speed').textContent = Math.round(speed * 20);

  car.x = Math.max(40, Math.min(318, car.x));
  roadOffset = (roadOffset + speed) % 40;

  // Spawn obstacles
  if (Math.random() < 0.035) {
    const laneX = [60, 140, 220, 300][Math.floor(Math.random()*4)];
    const colors = ['#ef4444', '#f59e0b', '#10b981', '#a855f7'];
    obstacles.push({ x: laneX, y: -80, w: 40, h: 70, color: colors[Math.floor(Math.random()*colors.length)] });
  }

  // Update obstacles
  obstacles.forEach((ob, i) => {
    ob.y += speed - 2;
    // Collision check
    if (car.x < ob.x + ob.w && car.x + car.w > ob.x && car.y < ob.y + ob.h && car.y + car.h > ob.y) {
      gameOver = true;
    }
  });
  obstacles = obstacles.filter(ob => ob.y < 650);
}

function drawCar(x, y, w, h, color) {
  ctx.fillStyle = color;
  ctx.beginPath(); ctx.roundRect(x, y, w, h, 8); ctx.fill();
  // Windshield
  ctx.fillStyle = '#0f172a';
  ctx.fillRect(x + 6, y + 16, w - 12, 16);
  // Headlights
  ctx.fillStyle = '#fef08a';
  ctx.fillRect(x + 4, y + 2, 8, 4);
  ctx.fillRect(x + w - 12, y + 2, 8, 4);
}

function draw() {
  update();
  ctx.clearRect(0, 0, 400, 600);
  // Road
  ctx.fillStyle = '#1e293b'; ctx.fillRect(40, 0, 320, 600);
  // Grass edges
  ctx.fillStyle = '#14532d'; ctx.fillRect(0, 0, 40, 600); ctx.fillRect(360, 0, 40, 600);
  // Center lane markers
  ctx.strokeStyle = '#f8fafc'; ctx.lineWidth = 4; ctx.setLineDash([20, 20]); ctx.lineDashOffset = -roadOffset;
  ctx.beginPath(); ctx.moveTo(145, 0); ctx.lineTo(145, 600); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(255, 0); ctx.lineTo(255, 600); ctx.stroke();
  ctx.setLineDash([]);

  // Draw obstacles
  obstacles.forEach(ob => drawCar(ob.x, ob.y, ob.w, ob.h, ob.color));

  // Draw player
  drawCar(car.x, car.y, car.w, car.h, car.color);

  if (gameOver) {
    ctx.fillStyle = 'rgba(0,0,0,0.85)'; ctx.fillRect(0, 0, 400, 600);
    ctx.fillStyle = '#ef4444'; ctx.font = 'bold 32px sans-serif'; ctx.textAlign = 'center';
    ctx.fillText('CRASHED!', 200, 280);
    ctx.fillStyle = '#f8fafc'; ctx.font = '18px sans-serif';
    ctx.fillText(`Distance: ${score} m`, 200, 320);
    ctx.fillText('Click to Restart', 200, 360);
    canvas.onclick = () => { gameOver = false; score = 0; obstacles = []; car.x = 175; };
    return;
  }
  requestAnimationFrame(draw);
}
draw();
</script>
</body>
</html>"""

    def _snake_template(self) -> str:
        return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Iris AI - Neon Cyber Snake</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: radial-gradient(circle, #09090b 0%, #000 100%);
    color: #e4e4e7; font-family: 'Segoe UI', system-ui, sans-serif;
    min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center;
  }
  h1 { font-size: 2.2rem; color: #22c55e; text-shadow: 0 0 20px rgba(34,197,94,0.6); margin-bottom: 6px; }
  .hud { width: 440px; display: flex; justify-content: space-between; font-size: 1.1rem; font-weight: 700; margin-bottom: 12px; }
  canvas { background: #18181b; border: 3px solid #27272a; border-radius: 12px; box-shadow: 0 20px 40px rgba(0,0,0,0.8); }
</style>
</head>
<body>
<h1>🐍 Neon Cyber Snake</h1>
<div class="hud">
  <div>SCORE: <span id="score" style="color: #22c55e;">0</span></div>
  <div>BEST: <span id="best" style="color: #eab308;">0</span></div>
</div>
<canvas id="snake" width="440" height="440"></canvas>
<p style="margin-top: 14px; color: #71717a; font-size: 0.9rem;">Controls: Arrow Keys or W / A / S / D to Move</p>
<script>
const canvas = document.getElementById('snake');
const ctx = canvas.getContext('2d');
const GRID = 20, SIZE = 440 / GRID;
let snake = [{x: 10, y: 10}];
let food = {x: 15, y: 15};
let dx = 1, dy = 0;
let score = 0, best = 0;
let speed = 90;

window.onkeydown = (e) => {
  const k = e.key.toLowerCase();
  if ((k === 'arrowup' || k === 'w') && dy === 0) { dx = 0; dy = -1; }
  if ((k === 'arrowdown' || k === 's') && dy === 0) { dx = 0; dy = 1; }
  if ((k === 'arrowleft' || k === 'a') && dx === 0) { dx = -1; dy = 0; }
  if ((k === 'arrowright' || k === 'd') && dx === 0) { dx = 1; dy = 0; }
};

function tick() {
  const head = { x: snake[0].x + dx, y: snake[0].y + dy };
  // Wall wrap
  if (head.x < 0) head.x = SIZE - 1;
  if (head.x >= SIZE) head.x = 0;
  if (head.y < 0) head.y = SIZE - 1;
  if (head.y >= SIZE) head.y = 0;

  // Self bite
  if (snake.some(s => s.x === head.x && s.y === head.y)) {
    score = 0;
    snake = [{x: 10, y: 10}];
    dx = 1; dy = 0;
    document.getElementById('score').textContent = score;
    return setTimeout(tick, speed);
  }

  snake.unshift(head);
  if (head.x === food.x && head.y === food.y) {
    score += 10;
    if (score > best) best = score;
    document.getElementById('score').textContent = score;
    document.getElementById('best').textContent = best;
    food = { x: Math.floor(Math.random() * SIZE), y: Math.floor(Math.random() * SIZE) };
  } else {
    snake.pop();
  }

  ctx.clearRect(0, 0, 440, 440);
  // Food
  ctx.fillStyle = '#ef4444';
  ctx.beginPath(); ctx.arc(food.x * GRID + 10, food.y * GRID + 10, 8, 0, Math.PI*2); ctx.fill();

  // Snake
  snake.forEach((s, i) => {
    ctx.fillStyle = i === 0 ? '#4ade80' : '#22c55e';
    ctx.fillRect(s.x * GRID + 1, s.y * GRID + 1, GRID - 2, GRID - 2);
  });

  setTimeout(tick, speed);
}
tick();
</script>
</body>
</html>"""
