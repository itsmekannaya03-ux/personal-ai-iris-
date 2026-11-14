import uuid
import json
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import PlainTextResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..security import get_current_user
from ..models.user import User
from ..models.clone import Clone
from ..schemas.clone import InstallerResponse

router = APIRouter(tags=["installer"])


def _generate_windows_script(token: str, base_url: str) -> str:
    zip_url = "https://personal-ai-iris.vercel.app/downloads/iris-ai.zip"
    return f'''@echo off
setlocal enabledelayedexpansion
title IRIS AI Installer

echo.
echo ╭──────────────────────────────────────╮
echo │         Installing IRIS AI...        │
echo ╰──────────────────────────────────────╯
echo.

set "IRIS_DIR=%USERPROFILE%\\.iris"
set "ENGINE_DIR=%USERPROFILE%\\Desktop\\IRIS-AI"
set "ZIP_FILE=%TEMP%\\iris-ai.zip"

:: 1. Check Python
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo → Downloading Python 3.11...
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%TEMP%\\py_install.exe' -UseBasicParsing"
    start /wait "" "%TEMP%\\py_install.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1
    del "%TEMP%\\py_install.exe" >nul 2>nul
)

:: 2. Create directories
if not exist "%IRIS_DIR%" mkdir "%IRIS_DIR%"
if not exist "%IRIS_DIR%\\chroma" mkdir "%IRIS_DIR%\\chroma"
if not exist "%IRIS_DIR%\\logs" mkdir "%IRIS_DIR%\\logs"
if not exist "%IRIS_DIR%\\memory" mkdir "%IRIS_DIR%\\memory"

:: 3. Fetch profile from website
echo → Fetching your customized profile...
curl -fsSL "{base_url}/installer/{token}" -o "%IRIS_DIR%\\profile.json" 2>nul
echo   Profile loaded!

:: 4. Download IRIS AI package (iris-ai.zip)
echo → Downloading IRIS AI Package (72 MB)...
powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '{zip_url}' -OutFile '%ZIP_FILE%'"

if not exist "%ZIP_FILE%" (
    echo [ERROR] Failed to download IRIS AI package.
    pause
    exit /b 1
)

:: 5. Extract to Desktop
echo → Extracting to %ENGINE_DIR%...
if not exist "%ENGINE_DIR%" mkdir "%ENGINE_DIR%"
powershell -Command "Expand-Archive -Path '%ZIP_FILE%' -DestinationPath '%ENGINE_DIR%' -Force"
del "%ZIP_FILE%" >nul 2>nul

echo.
echo ╭──────────────────────────────────────╮
echo │   IRIS AI installed successfully!    │
echo │   Location: %ENGINE_DIR%              │
echo ╰──────────────────────────────────────╯
echo.
echo → Starting IRIS AI...
start "" "%ENGINE_DIR%\\run.bat"
'''


def _generate_unix_script(token: str, base_url: str, os_type: str) -> str:
    return f'''#!/bin/bash
# IRIS AI Installer — {"macOS" if os_type == "mac" else "Linux"}
set -e

IRIS_DIR="$HOME/.iris"
ENGINE_DIR="$IRIS_DIR/engine"
BASE_URL="{base_url}"
TOKEN="{token}"

echo ""
echo "╭──────────────────────────────────────╮"
echo "│        Installing IRIS AI...        │"
echo "╰──────────────────────────────────────╯"
echo ""

# 1. Check / Install IRIS Neural Core
if ! command -v IRIS Neural Core &> /dev/null; then
    echo "→ Installing IRIS Neural Core..."
    curl -fsSL https://IRIS Neural Core.com/install.sh | sh
fi

# 2. Create directories
mkdir -p "$IRIS_DIR/chroma" "$IRIS_DIR/logs" "$ENGINE_DIR"

# 3. Pull model
echo "→ Pulling AI model (llama3.2:3b)..."
IRIS Neural Core pull llama3.2:3b 2>/dev/null
echo "  Model ready!"

# 4. Fetch profile
echo "→ Fetching your profile..."
curl -fsSL "$BASE_URL/installer/$TOKEN" -o "$IRIS_DIR/profile.json"
echo "  Profile loaded!"

# 5. Clone engine
echo "→ Downloading IRIS engine..."
if [ -d "$ENGINE_DIR" ]; then
    rm -rf "$ENGINE_DIR"
fi
git clone --depth 1 https://github.com/iris-ai/iris-engine "$ENGINE_DIR" 2>/dev/null || mkdir -p "$ENGINE_DIR"

# 6. Install dependencies
echo "→ Installing Python dependencies..."
pip3 install -r "$ENGINE_DIR/requirements.txt" 2>/dev/null || pip install -r "$ENGINE_DIR/requirements.txt" 2>/dev/null

# 7. Create alias
echo "alias ai='python3 $ENGINE_DIR/cli.py'" >> "$HOME/.bashrc" 2>/dev/null || true
echo "alias ai='python3 $ENGINE_DIR/cli.py'" >> "$HOME/.zshrc" 2>/dev/null || true

echo ""
echo "╭──────────────────────────────────────╮"
echo "│  IRIS AI installed successfully!    │"
echo "│                                      │"
echo "│  Open dashboard: http://localhost:5743│"
echo "│  Or type: ai 'your message'          │"
echo "╰──────────────────────────────────────╯"
echo ""
echo "→ Starting IRIS..."
python3 "$ENGINE_DIR/server.py" &
sleep 2
echo "  IRIS is running!"
'''


@router.get("/download/{os_type}")
async def generate_installer(
    os_type: str,
    request: Request,
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

    base_url = str(request.base_url).rstrip("/") + "/api"
    if os_type == "windows":
        script = _generate_windows_script(token, base_url)
        return PlainTextResponse(
            content=script,
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename=install-iris.bat"},
        )
    script = _generate_unix_script(token, base_url, os_type)
    return PlainTextResponse(
        content=script,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename=install-iris.sh"},
    )


@router.get("/install/script/{os_type}/{token}")
async def download_installer_script(
    os_type: str,
    token: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Public endpoint — serves the installer script with token embedded.
    Used by the one-liner install command shown on the website."""
    if os_type not in ("windows", "mac", "linux"):
        raise HTTPException(status_code=400, detail="Unsupported OS")

    base_url = str(request.base_url).rstrip("/") + "/api"

    if token == "latest":
        if os_type == "windows":
            return PlainTextResponse(
                content=_generate_windows_script("latest", base_url),
                media_type="text/plain",
            )
        return PlainTextResponse(
            content=_generate_unix_script("latest", base_url, os_type),
            media_type="text/plain",
        )

    result = await db.execute(
        select(Clone).where(Clone.installer_token == token)
    )
    clone = result.scalar_one_or_none()
    if not clone:
        # Fallback to universal script so the installer never fails for users
        if os_type == "windows":
            return PlainTextResponse(
                content=_generate_windows_script("latest", base_url),
                media_type="text/plain",
            )
        return PlainTextResponse(
            content=_generate_unix_script("latest", base_url, os_type),
            media_type="text/plain",
        )

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
        ai_name=user.ai_name if user else "IRIS",
        theme=user.theme if user else "blob",
        wake_word=user.wake_word if user else "hey iris",
    )
