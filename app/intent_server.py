from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import importlib.util

spec = importlib.util.spec_from_file_location("intent", "core/intent.py")
intent_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(intent_mod)
detector = intent_mod.detector

app = FastAPI(title="IGRIS Intent Detector")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class Message(BaseModel):
    text: str

@app.post("/detect")
def detect_intent(req: Message):
    result = detector.detect(req.text)
    return {
        "message": req.text,
        "intent": result.intent,
        "confidence": result.confidence,
        "entities": result.entities,
    }

@app.get("/")
def root():
    return {"status": "running", "endpoints": ["POST /detect"]}

if __name__ == "__main__":
    print("IGRIS Intent Detector — http://localhost:8001")
    uvicorn.run(app, host="127.0.0.1", port=8001)
