"""
IGRIS AI — Local Server
Runs on localhost:5743, serves the dashboard UI and API.
"""

import json
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from core import AIEngine, VoiceEngine

app = FastAPI(title="IGRIS AI Local Engine", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = AIEngine()


class ChatRequest(BaseModel):
    message: str


class CommandRequest(BaseModel):
    command: str


@app.get("/status")
async def get_status():
    return {
        "status": "running",
        "model": engine.model,
        "ai_name": engine.profile.get("ai_name", "IGRIS"),
        "memory": engine.memory.get_stats(),
        "mode": engine.mode,
        "online": True,
    }


@app.post("/chat")
async def chat(req: ChatRequest):
    if req.message.startswith("/"):
        response = engine.handle_command(req.message)
    else:
        response = engine.chat(req.message)
    return {"response": response}


@app.get("/memory")
async def get_memory():
    return {
        "short_term": engine.memory.short_term[-10:],
        "long_term": engine.memory.get_long_term_summary(),
        "deep": engine.memory.get_deep_memories(),
        "stats": engine.memory.get_stats(),
    }


@app.get("/profile")
async def get_profile():
    return engine.profile


@app.post("/profile")
async def update_profile(data: dict):
    profile_path = Path.home() / ".igris" / "profile.json"
    engine.profile.update(data)
    profile_path.write_text(json.dumps(engine.profile, indent=2))
    engine._init_system_prompt()
    return {"status": "updated", "profile": engine.profile}


@app.post("/system")
async def system_control(req: CommandRequest):
    result = engine.pc.execute(req.command)
    return {"result": result}


def main():
    print("  " + "+" + "-" * 40 + "+")
    print("  |  IGRIS AI Engine — Running           |")
    print("  |  Dashboard: http://localhost:5743    |")
    print("  " + "+" + "-" * 40 + "+")
    uvicorn.run(app, host="127.0.0.1", port=5743)


if __name__ == "__main__":
    main()
