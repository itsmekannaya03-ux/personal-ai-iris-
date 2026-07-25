"""
API Server — FastAPI REST interface for the AI.

Endpoints:
  POST /chat         — Send a message, get a response
  POST /think        — Full thinking pipeline
  GET  /status       — System status
  POST /memory/store — Store a memory
  GET  /memory/recall/:key — Recall a memory
  POST /voice/say    — Speak text
  GET  /voice/info   — Voice system info
  POST /system/*     — System commands
"""

import logging
import time
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logger = logging.getLogger("iris.api")


class ChatRequest(BaseModel):
    message: str
    voice: Optional[bool] = False
    voice_preset: Optional[str] = None


class ChatResponse(BaseModel):
    text: str
    action: str
    intent: Optional[str] = None
    processing_time: Optional[float] = None


class MemoryStoreRequest(BaseModel):
    key: str
    value: str


class MemoryRecallRequest(BaseModel):
    key: str


class VoiceSayRequest(BaseModel):
    text: str
    preset: Optional[str] = None


def create_app(brain=None):
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Jarvis AI API",
        description="Professional Jarvis-like AI assistant API",
        version="1.0.0",
    )

    @app.on_event("startup")
    async def startup():
        logger.info("Jarvis AI API server starting...")

    @app.get("/health")
    async def health():
        return {
            "status": "ok",
            "name": "Jarvis AI",
            "version": "1.0.0",
            "timestamp": time.time(),
        }

    @app.post("/chat", response_model=ChatResponse)
    async def chat(request: ChatRequest):
        if brain is None:
            raise HTTPException(status_code=503, detail="AI brain not initialized")
        start = time.time()
        result = brain.think(request.message)
        elapsed = time.time() - start

        if request.voice and brain._voice:
            brain._voice.say(result["text"], preset=request.voice_preset)

        return ChatResponse(
            text=result.get("text", ""),
            action=result.get("action", "error"),
            intent=result.get("intent"),
            processing_time=round(elapsed, 3),
        )

    @app.post("/think", response_model=ChatResponse)
    async def think(request: ChatRequest):
        return await chat(request)

    @app.get("/status")
    async def status():
        if brain is None:
            return {"status": "brain_not_initialized"}
        return {
            "brain": brain.status(),
            "personality": brain._personality.config if brain._personality else None,
            "memory": brain._memory.get_stats() if brain._memory else None,
            "voice": brain._voice.get_info() if brain._voice else None,
            "vision": brain._vision.get_status() if brain._vision else None,
            "automation": brain._automation.get_status() if brain._automation else None,
            "knowledge": brain._knowledge.get_status() if brain._knowledge else None,
        }

    @app.post("/memory/store")
    async def memory_store(request: MemoryStoreRequest):
        if brain is None or brain._memory is None:
            raise HTTPException(status_code=503, detail="Memory not available")
        brain.remember(request.key, request.value)
        return {"success": True}

    @app.get("/memory/recall/{key}")
    async def memory_recall(key: str):
        if brain is None or brain._memory is None:
            raise HTTPException(status_code=503, detail="Memory not available")
        value = brain.recall(key)
        if value is None:
            raise HTTPException(status_code=404, detail="Memory not found")
        return {"key": key, "value": value}

    @app.post("/voice/say")
    async def voice_say(request: VoiceSayRequest):
        if brain is None or brain._voice is None:
            raise HTTPException(status_code=503, detail="Voice not available")
        brain._voice.say(request.text, preset=request.preset)
        return {"success": True, "text": request.text}

    @app.get("/voice/info")
    async def voice_info():
        if brain is None or brain._voice is None:
            raise HTTPException(status_code=503, detail="Voice not available")
        return brain._voice.get_info()

    return app
