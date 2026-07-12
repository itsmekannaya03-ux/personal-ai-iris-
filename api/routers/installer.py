import uuid
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..models.clone import Clone
from ..schemas.clone import InstallerResponse

router = APIRouter(tags=["installer"])


def _generate_windows_script(token: str, base_url: str) -> str:
    return f'''@echo off
setlocal enabledelayedexpansion
title IGRIS AI Installer

echo.
echo ╭──────────────────────────────────────╮
echo │        Installing IGRIS AI...        │
echo ╰──────────────────────────────────────╯
echo.

set "IGRIS_DIR=%USERPROFILE%\\.igris"
set "ENGINE_DIR=%IGRIS_DIR%\\engine"

:: 1. Check Ollama
where ollama >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo → Installing Ollama...
    echo   Downloading from ollama.com...
    curl -fsSL -o "%TEMP%\\ollama_setup.exe" "https://ollama.com/download/OllamaSetup.exe"
    start /wait "" "%TEMP%\\ollama_setup.exe" /silent
)

:: 2. Create directories
if not exist "%IGRIS_DIR%" mkdir "%IGRIS_DIR%"
if not exist "%IGRIS_DIR%\\chroma" mkdir "%IGRIS_DIR%\\chroma"
if not exist "%IGRIS_DIR%\\logs" mkdir "%IGRIS_DIR%\\logs"

:: 3. Pull AI model
echo → Pulling AI model (llama3.2:3b)...
ollama pull llama3.2:3b 2>nul
echo   Model ready!

:: 4. Fetch profile
echo → Fetching your profile...
curl -fsSL "{base_url}/installer/{token}" -o "%IGRIS_DIR%\\profile.json"
echo   Profile loaded!

:: 5. Clone engine
echo → Downloading IGRIS engine...
if exist "%ENGINE_DIR%" rmdir /s /q "%ENGINE_DIR%"
git clone --depth 1 https://github.com/igris-ai/igris-engine "%ENGINE_DIR%" 2>nul
if %ERRORLEVEL% neq 0 (
    echo   Could not clone engine. Creating local setup...
    if not exist "%ENGINE_DIR%" mkdir "%ENGINE_DIR%"
)

:: 6. Install Python dependencies
echo → Installing Python dependencies...
pip install -r "%ENGINE_DIR%\\requirements.txt" 2>nul

:: 7. Create startup alias
echo @echo off > "%IGRIS_DIR%\\start.bat"
echo python "%ENGINE_DIR%\\server.py" >> "%IGRIS_DIR%\\start.bat"

:: 8. Add to PATH
for /f "skip=2 tokens=3*" %%A in ('reg query HKCU\\Environment /v Path 2^>nul') do set "userPath=%%A %%B"
if "!userPath!"=="!userPath:%IGRIS_DIR%=!" (
    reg add HKCU\\Environment /v Path /t REG_EXPAND_SZ /d "!userPath!;%IGRIS_DIR%" /f
)

echo.
echo ╭──────────────────────────────────────╮
echo │  IGRIS AI installed successfully!    │
echo │                                      │
echo │  Open dashboard: http://localhost:5743│
echo │  Or type: ai "your message"          │
echo ╰──────────────────────────────────────╯
echo.
echo → Starting IGRIS...
start python "%ENGINE_DIR%\\server.py"
'''


def _generate_unix_script(token: str, base_url: str, os_type: str) -> str:
    return f'''#!/bin/bash
# IGRIS AI Installer — {"macOS" if os_type == "mac" else "Linux"}
set -e

IGRIS_DIR="$HOME/.igris"
ENGINE_DIR="$IGRIS_DIR/engine"
BASE_URL="{base_url}"
TOKEN="{token}"

echo ""
echo "╭──────────────────────────────────────╮"
echo "│        Installing IGRIS AI...        │"
echo "╰──────────────────────────────────────╯"
echo ""

# 1. Check / Install Ollama
if ! command -v ollama &> /dev/null; then
    echo "→ Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
fi

# 2. Create directories
mkdir -p "$IGRIS_DIR/chroma" "$IGRIS_DIR/logs" "$ENGINE_DIR"

# 3. Pull model
echo "→ Pulling AI model (llama3.2:3b)..."
ollama pull llama3.2:3b 2>/dev/null
echo "  Model ready!"

# 4. Fetch profile
echo "→ Fetching your profile..."
curl -fsSL "$BASE_URL/installer/$TOKEN" -o "$IGRIS_DIR/profile.json"
echo "  Profile loaded!"

# 5. Clone engine
echo "→ Downloading IGRIS engine..."
if [ -d "$ENGINE_DIR" ]; then
    rm -rf "$ENGINE_DIR"
fi
git clone --depth 1 https://github.com/igris-ai/igris-engine "$ENGINE_DIR" 2>/dev/null || mkdir -p "$ENGINE_DIR"

# 6. Install dependencies
echo "→ Installing Python dependencies..."
pip3 install -r "$ENGINE_DIR/requirements.txt" 2>/dev/null || pip install -r "$ENGINE_DIR/requirements.txt" 2>/dev/null

# 7. Create alias
echo "alias ai='python3 $ENGINE_DIR/cli.py'" >> "$HOME/.bashrc" 2>/dev/null || true
echo "alias ai='python3 $ENGINE_DIR/cli.py'" >> "$HOME/.zshrc" 2>/dev/null || true

echo ""
echo "╭──────────────────────────────────────╮"
echo "│  IGRIS AI installed successfully!    │"
echo "│                                      │"
echo "│  Open dashboard: http://localhost:5743│"
echo "│  Or type: ai 'your message'          │"
echo "╰──────────────────────────────────────╯"
echo ""
echo "→ Starting IGRIS..."
python3 "$ENGINE_DIR/server.py" &
sleep 2
echo "  IGRIS is running!"
'''


@router.get("/download/{os_type}")
async def generate_installer(
    os_type: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if os_type not in ("windows", "mac", "linux"):
        raise HTTPException(status_code=400, detail="Unsupported OS. Use: windows, mac, or linux")

    token = str(uuid.uuid4())
    profile_snapshot = json.dumps({
        "name": user.name,
        "age": user.age,
        "job": user.job,
        "interests": user.interests,
        "location": user.location,
        "goals": user.goals,
        "ai_name": user.ai_name,
        "ai_personality": user.ai_personality,
        "theme": user.theme,
        "wake_word": user.wake_word,
    })

    clone = Clone(
        user_id=user.id,
        installer_token=token,
        os_type=os_type,
        profile_snapshot=profile_snapshot,
    )
    db.add(clone)
    await db.commit()

    base_url = "https://igris.ai/api"
    if os_type == "windows":
        script = _generate_windows_script(token, base_url)
        return PlainTextResponse(
            content=script,
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename=install-igris.bat"},
        )
    script = _generate_unix_script(token, base_url, os_type)
    return PlainTextResponse(
        content=script,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename=install-igris.sh"},
    )


@router.get("/install/script/{os_type}/{token}")
async def download_installer_script(
    os_type: str,
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """Public endpoint — serves the installer script with token embedded.
    Used by the one-liner install command shown on the website."""
    if os_type not in ("windows", "mac", "linux"):
        raise HTTPException(status_code=400, detail="Unsupported OS")

    result = await db.execute(
        select(Clone).where(Clone.installer_token == token)
    )
    clone = result.scalar_one_or_none()
    if not clone:
        raise HTTPException(status_code=404, detail="Invalid or expired token")

    base_url = "https://igris.ai/api"
    if os_type == "windows":
        script = _generate_windows_script(token, base_url)
        return PlainTextResponse(
            content=script,
            media_type="text/plain",
        )
    script = _generate_unix_script(token, base_url, os_type)
    return PlainTextResponse(
        content=script,
        media_type="text/plain",
    )


@router.get("/installer/{token}", response_model=InstallerResponse)
async def validate_installer(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Clone).where(Clone.installer_token == token)
    )
    clone = result.scalar_one_or_none()
    if not clone:
        raise HTTPException(status_code=404, detail="Invalid or expired installer token")

    user_result = await db.execute(select(User).where(User.id == clone.user_id))
    user = user_result.scalar_one_or_none()

    profile = json.loads(clone.profile_snapshot)

    return InstallerResponse(
        profile=profile,
        model=clone.base_model_version,
        ai_name=user.ai_name if user else "IGRIS",
        theme=user.theme if user else "blob",
        wake_word=user.wake_word if user else "hey igris",
    )
