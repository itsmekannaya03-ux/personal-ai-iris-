"""
IGRIS AI — Local Engine Server

Runs on localhost:5743, serves the dashboard UI and local API.

New endpoints exposed in this version:
  GET /runtime/status  — engine name, active model, PIE status, model assignments
  GET /runtime/models  — all installed models + task routing
  POST /pie/explain    — explain privacy routing for a message
"""

import json
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Ensure engine package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core_matrix import CoreMatrix
from engine.neural_core import AIEngine, VoiceEngine
from engine.pie.router import HybridRouter
from engine.pie.classifier import PrivacyClassifier

app = FastAPI(title="IGRIS AI Local Engine", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Layer 5: Core Matrix — central coordinator
matrix = CoreMatrix()

# Layer 6: AI Orchestrator — routes requests through 7-stage pipeline
engine = AIEngine(matrix)

# Layer 4: Neural Core — the mind (used via Core Matrix)
matrix.register_module("neural_core", engine, name="Neural Core", version="1.0.0")

# Layer 3: Runtime services
router = HybridRouter()
pie    = PrivacyClassifier()

# Start health monitoring
matrix.start_health_monitor()


class ChatRequest(BaseModel):
    message: str


class CommandRequest(BaseModel):
    command: str


class PIERequest(BaseModel):
    message: str


class SessionRequest(BaseModel):
    keep_summary: bool = True


class MaxTokensRequest(BaseModel):
    max_tokens: int = 4096


# ── Original Endpoints (backward compatible) ───────────────────────────────

@app.get("/status")
async def get_status():
    return {
        "status": "running",
        "version": "1.0.0",
        "engine": engine.engine_name,
        "model": engine.model,
        "ai_name": engine.profile.get("ai_name", "IGRIS"),
        "memory": engine.memory.get_stats(),
        "mode": engine.mode,
        "online": True,
        "matrix": {
            "modules": matrix.registry.module_count if hasattr(matrix.registry, 'module_count') else len(matrix.registry._modules),
            "healthy": matrix.health.get_status_summary().get("healthy", 0),
        },
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


# ── New: Runtime Endpoints ─────────────────────────────────────────────────

@app.get("/runtime/status")
async def runtime_status():
    """IGRIS Runtime status — engine, models, PIE, task routing."""
    try:
        available_models = engine._inference.list_models()
    except Exception:
        available_models = []

    pie_suggestions = engine._model_manager.get_upgrade_path()
    memory_backend = getattr(engine, 'memory_backend', None)
    voice_backend = getattr(engine, 'voice_backend', None)

    return {
        "engine": engine.engine_name,
        "available_models": available_models,
        "task_assignments": engine._model_manager.list_task_assignments(),
        "model_upgrades": pie_suggestions,
        "pie": {
            "active": True,
            "mode": engine.privacy_profile.privacy_mode,
            "cloud_enabled": engine.privacy_profile.is_cloud_enabled(),
            "cloud_provider": engine.privacy_profile.cloud_provider,
            "anonymization": engine.privacy_profile.anonymization_level,
            "learner_corrections": engine.privacy_learner.get_stats()["total_corrections"],
        },
        "cloud_routing": engine.pie_router._cloud_available,
        "memory_backend": memory_backend.backend_name if memory_backend else "default",
        "voice_backend": voice_backend.backend_name if voice_backend else "default",
        "memory_encrypted": (Path.home() / ".igris" / "deep_memory.enc").exists(),
        "privacy": engine.privacy_profile.to_dict(),
    }


@app.get("/runtime/models")
async def runtime_models():
    """Lists all installed models with their task assignments."""
    try:
        available = engine._inference.list_models()
    except Exception:
        available = []

    models_info = []
    for model_id in available:
        cfg = engine._model_manager.get_model_info(model_id)
        models_info.append({
            "id": model_id,
            "display_name": cfg.display_name if cfg else model_id,
            "task_types": cfg.task_types if cfg else [],
            "description": cfg.description if cfg else "",
        })

    missing = engine._model_manager.get_missing_models()
    return {
        "installed": models_info,
        "task_assignments": engine._model_manager.list_task_assignments(),
        "suggested_upgrades": [
            {
                "model_id": m.model_id,
                "display_name": m.display_name,
                "task_types": m.task_types,
                "description": m.description,
                "download_command": f"ollama pull {m.model_id}",
            }
            for m in missing
        ],
    }


# ── New: PIE Endpoints ─────────────────────────────────────────────────────

@app.post("/pie/explain")
async def pie_explain(req: PIERequest):
    """Returns the PIE routing explanation for a given message."""
    route_result = engine.pie_router.route(req.message)
    return {
        "privacy_level": route_result.privacy_result.level.value,
        "categories": route_result.privacy_result.categories,
        "confidence": route_result.privacy_result.confidence,
        "routing": route_result.decision.value,
        "can_cloud": route_result.privacy_result.can_cloud,
        "explanation": route_result.reason,
        "flagged_patterns": route_result.privacy_result.flagged_patterns,
    }


@app.get("/pie/status")
async def pie_status():
    return {
        "active": True,
        "privacy_mode": engine.privacy_profile.privacy_mode,
        "cloud_enabled": engine.privacy_profile.is_cloud_enabled(),
        "cloud_provider": engine.privacy_profile.cloud_provider,
        "anonymization_level": engine.privacy_profile.anonymization_level,
        "learner": engine.privacy_learner.get_stats(),
        "always_local_categories": engine.privacy_profile.always_local_categories,
    }


@app.post("/pie/correct")
async def pie_correct(req: PIERequest):
    """Record a PIE correction for adaptive learning."""
    route_result = engine.pie_router.route(req.message)
    for pattern in route_result.privacy_result.flagged_patterns:
        engine.privacy_learner.record_correction(
            pattern_name=pattern,
            original_level=route_result.privacy_result.level.value,
            corrected_level="low",
            text=req.message,
        )
    return {
        "recorded": True,
        "patterns_corrected": route_result.privacy_result.flagged_patterns,
        "learner_stats": engine.privacy_learner.get_stats(),
    }


@app.post("/pie/classify")
async def pie_classify(req: PIERequest):
    """Raw PIE classification result for a message."""
    result = engine.pie_router.route(req.message)
    return {
        "level": result.privacy_result.level.value,
        "categories": result.privacy_result.categories,
        "confidence": result.privacy_result.confidence,
        "routing": result.decision.value,
        "can_cloud": result.privacy_result.can_cloud,
        "requires_anonymization": result.privacy_result.requires_anonymization if hasattr(result.privacy_result, 'requires_anonymization') else False,
        "flagged_patterns": result.privacy_result.flagged_patterns,
        "explanation": result.reason,
    }


# ── Core Matrix Endpoint ──────────────────────────────────────────────────

@app.get("/matrix/status")
async def matrix_status():
    return matrix.get_status()


# ── Conversation / Session Management Endpoints ────────────────────────────

@app.get("/conversation/status")
async def conversation_status():
    return engine.conversation_status()


@app.post("/conversation/new-session")
async def new_session(req: SessionRequest = SessionRequest()):
    return engine.new_session(keep_summary=req.keep_summary)


@app.get("/conversation/summary")
async def conversation_summary():
    summary = engine._summarize_conversation()
    return {"summary": summary}


@app.post("/conversation/max-tokens")
async def set_max_tokens(req: MaxTokensRequest):
    engine.set_max_tokens(req.max_tokens)
    return {"max_tokens": req.max_tokens, "status": "updated"}


# ── Server Entry Point ─────────────────────────────────────────────────────

def main():
    cloud_status = "enabled" if engine.privacy_profile.is_cloud_enabled() else "disabled"
    matrix_status = matrix.get_status()
    print("  +" + "-" * 48 + "+")
    print("  |  IGRIS AI OS — Engine v1.0.0               |")
    print("  |  Runtime: " + engine.engine_name.ljust(36) + "|")
    print("  |  PIE: Active | Cloud: " + cloud_status.ljust(27) + "|")
    print("  |  Matrix: " + str(matrix_status['module_count']) + " modules | " + str(matrix_status['health']['healthy']) + "/" + str(matrix_status['health']['total']) + " healthy".ljust(22) + "|")
    print("  |  Dashboard: http://localhost:5743           |")
    print("  +" + "-" * 48 + "+")
    uvicorn.run(app, host="127.0.0.1", port=5743)


if __name__ == "__main__":
    main()

