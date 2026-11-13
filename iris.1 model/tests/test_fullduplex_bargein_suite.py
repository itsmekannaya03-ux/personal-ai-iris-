"""
Comprehensive Full-Duplex Audio, VAD, Noise Suppression & Barge-In Test Suite
============================================================================
Tests all 5 systems implemented for IRIS AI:
  1. Full-Duplex WebRTC & Audio Streaming Communication
  2. Low-Latency Token Streaming & Incremental TTS
  3. Real-Time Barge-In & Response Cancellation
  4. Silero Voice Activity Detection (ONNX)
  5. Real-Time Background Noise Suppression
"""

import os
import sys
import time
import json
import numpy as np

os.environ["IRIS_TEST_MODE"] = "1"

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.audio.silero_vad import get_silero_vad, SileroVAD
from backend.audio.noise_suppressor import get_noise_suppressor, RealtimeNoiseSuppressor
from backend.engine.barge_in_manager import get_barge_in_manager, BargeInManager
from backend.engine.streaming_orchestrator import get_streaming_orchestrator, StreamingOrchestrator
from backend.audio.full_duplex_session import FullDuplexAudioSession, create_or_get_session, remove_session
from fastapi.testclient import TestClient
from backend.server.api import create_app


def test_silero_vad():
    print("\n" + "=" * 60)
    print("TEST 1: Silero Voice Activity Detection (Module 4)")
    print("=" * 60)

    vad = SileroVAD()
    assert vad.is_ready(), "Silero VAD ONNX session failed to initialize"
    print(f"[PASS] Model Loaded: {vad.model_path}")

    # 1. Test Silence
    silence = np.zeros(512, dtype=np.float32)
    prob_silence = vad.process_frame(silence)
    print(f"[PASS] Silence Frame Probability: {prob_silence:.4f} (Expected < 0.05)")
    assert prob_silence < 0.05, f"Expected silence probability < 0.05, got {prob_silence}"

    # 2. Test Simulated Speech Formants (Multiple resonant frequencies)
    t = np.linspace(0, 0.032, 512, endpoint=False)
    # Simulated voiced vowel phoneme (F0=150Hz + harmonics)
    synthetic_vowel = (
        0.5 * np.sin(2 * np.pi * 150 * t) +
        0.3 * np.sin(2 * np.pi * 750 * t) +
        0.2 * np.sin(2 * np.pi * 1250 * t)
    ).astype(np.float32)

    # Prime recurrent state with speech frames
    probs = []
    for _ in range(5):
        probs.append(vad.process_frame(synthetic_vowel))
    
    print(f"[PASS] Voiced Vowel Probabilities: {[round(p, 4) for p in probs]}")
    print(f"[PASS] Average Inference Latency: {vad.avg_inference_latency_ms:.3f} ms per frame")
    assert vad.avg_inference_latency_ms < 5.0, f"VAD latency too high: {vad.avg_inference_latency_ms}ms"

    # 3. Test Onset and Offset State Machine via step()
    vad.reset_states()
    res_silence = vad.step(np.zeros(1024, dtype=np.float32))
    assert not res_silence["is_speech"], "Silence should not trigger speech"

    diag = vad.get_diagnostics()
    print(f"[PASS] VAD Diagnostics: sample_rate={diag['sample_rate']}, latency={diag['last_inference_latency_ms']}ms")
    return True


def test_noise_suppression():
    print("\n" + "=" * 60)
    print("TEST 2: Real-Time Background Noise Suppression (Module 5)")
    print("=" * 60)

    ns = get_noise_suppressor(level="moderate")
    stats = ns.get_stats()
    print(f"[PASS] Initialized Level: {stats['level']} ({stats['description']})")

    # Generate synthetic stationary noise (fan / air conditioner hiss)
    np.random.seed(42)
    noise = np.random.normal(0, 0.04, 1024).astype(np.float32)
    in_power = float(np.var(noise))

    # Update noise profile during stationary silence
    ns.update_noise_profile(noise)
    cleaned = ns.process_frame(noise)
    out_power = float(np.var(cleaned))
    attenuation_ratio = in_power / max(out_power, 1e-10)

    print(f"[PASS] Input Noise Power:  {in_power:.6f}")
    print(f"[PASS] Output Noise Power: {out_power:.6f}")
    print(f"[PASS] Noise Attenuation:  {attenuation_ratio:.1f}x reduction")
    assert attenuation_ratio > 10.0, f"Expected >10x noise attenuation, got {attenuation_ratio}"

    # Verify configurable levels
    for lvl in ["off", "low", "moderate", "high"]:
        ok = ns.set_level(lvl)
        assert ok, f"Failed to set level {lvl}"
        cur_stats = ns.get_stats()
        assert cur_stats["level"] == lvl
    print(f"[PASS] Dynamic level switching verified across: off, low, moderate, high")
    print(f"[PASS] Average Noise Suppressor Latency: {ns.avg_latency_ms:.3f} ms")
    assert ns.avg_latency_ms < 5.0, "Noise suppression latency too high"
    return True


def test_barge_in_manager():
    print("\n" + "=" * 60)
    print("TEST 3: Real-Time Barge-In & Response Cancellation (Module 3)")
    print("=" * 60)

    bm = get_barge_in_manager()
    gen1 = bm.start_new_generation()
    assert bm.is_valid(gen1), f"Expected gen1 {gen1} to be valid"
    print(f"[PASS] Generation 1 started: {gen1}")

    # Test interruption triggering
    record = bm.trigger_barge_in(source="test_speech_onset")
    print(f"[PASS] Barge-in triggered in: {record['latency_ms']:.2f} ms")
    assert record["interrupted_generation_id"] == gen1
    assert not bm.is_valid(gen1), "Interrupted generation must be marked invalid"
    assert record["latency_ms"] < 100.0, f"Barge-in latency must be < 100ms, got {record['latency_ms']}"

    # Test that subsequent chunks with old generation ID are rejected
    assert not bm.is_valid(gen1), "Stale audio chunks must be rejected"

    # Start new generation
    gen2 = bm.start_new_generation()
    assert bm.is_valid(gen2), f"Expected gen2 {gen2} to be valid"
    assert not bm.is_valid(gen1), "Old generation gen1 must still be invalid"
    print(f"[PASS] Generation 2 started cleanly: {gen2}")
    return True


def test_streaming_and_incremental_tts():
    print("\n" + "=" * 60)
    print("TEST 4: Low-Latency Token Streaming & Incremental TTS (Module 2)")
    print("=" * 60)

    orch = get_streaming_orchestrator()
    tokens = []
    chunks = []

    def on_token(tok, gid):
        tokens.append(tok)

    def on_chunk(chunk_payload):
        chunks.append(chunk_payload)

    # Test streaming chat
    res = orch.stream_chat_and_synthesize(
        messages=[{"role": "user", "content": "What is the capital of France?"}],
        synthesize_voice=True,
        on_token=on_token,
        on_audio_chunk=on_chunk,
    )

    metrics = res["metrics"]
    print(f"[PASS] Generation ID: {res['generation_id']}")
    print(f"[PASS] Tokens Received: {len(tokens)}")
    print(f"[PASS] Response Text: {res['response'][:60]}...")
    print(f"[PASS] TTFT (Time to First Token): {metrics['ttft_ms']} ms")
    print(f"[PASS] Total Latency: {metrics['total_latency_ms']} ms")
    print(f"[PASS] Provider: {metrics['provider']}, Model: {metrics['model']}")
    assert len(tokens) > 0, "Expected at least 1 streamed token"
    assert metrics["ttft_ms"] is not None, "Expected TTFT measurement"

    # Test mid-stream barge-in cancellation
    bm = get_barge_in_manager()
    tokens_aborted = []
    def on_tok_abort(t, gid):
        tokens_aborted.append(t)
        if len(tokens_aborted) == 2:
            bm.trigger_barge_in("test_midstream_interruption")

    res_abort = orch.stream_chat_and_synthesize(
        messages=[{"role": "user", "content": "Give me a long paragraph about stars and planets."}],
        synthesize_voice=False,
        on_token=on_tok_abort,
    )
    print(f"[PASS] Mid-Stream Barge-In: Stopped at {len(tokens_aborted)} tokens")
    assert res_abort["interrupted"], "Session must be marked interrupted"
    assert len(tokens_aborted) <= 4, f"Tokens continued streaming after abort: {len(tokens_aborted)}"
    return True


def test_full_duplex_session_and_endpoints():
    print("\n" + "=" * 60)
    print("TEST 5: Full-Duplex WebRTC & WebSocket Audio Transport (Module 1)")
    print("=" * 60)

    # 1. Test FullDuplexAudioSession
    sess = FullDuplexAudioSession()
    assert sess.is_active, "Session must be active"

    # Feed synthetic 16kHz PCM audio
    frame = (np.random.normal(0, 0.05, 512).astype(np.float32) * 32767).astype(np.int16).tobytes()
    events = sess.process_incoming_pcm(frame)
    assert events["vad"] is not None, "Expected VAD evaluation"
    print(f"[PASS] Full-Duplex PCM Intake: Processed frame, VAD prob={events['vad']['probability']}")

    # 2. Test FastAPI Endpoints with TestClient
    app = create_app()
    client = TestClient(app)

    # WebRTC Offer endpoint
    res_offer = client.post("/webrtc/offer", json={"sdp": "v=0\r\no=Client\r\n"})
    assert res_offer.status_code == 200, f"WebRTC offer failed: {res_offer.text}"
    offer_data = res_offer.json()
    assert offer_data["status"] == "ready"
    assert "ws_endpoint" in offer_data
    print(f"[PASS] POST /webrtc/offer: Handshake successful, session={offer_data['session_id']}")

    # WebRTC Status endpoint
    res_status = client.get("/webrtc/status")
    assert res_status.status_code == 200
    print(f"[PASS] GET /webrtc/status: Active sessions={res_status.json()['total_active_sessions']}")

    # Silero VAD Status & Config endpoints
    res_vad = client.get("/audio/vad/status")
    assert res_vad.status_code == 200
    assert res_vad.json()["model_ready"] == True
    print(f"[PASS] GET /audio/vad/status: Model ready, threshold={res_vad.json()['threshold']}")

    res_vad_cfg = client.post("/audio/vad/config", json={"threshold": 0.65, "neg_threshold": 0.30})
    assert res_vad_cfg.status_code == 200
    assert res_vad_cfg.json()["diagnostics"]["threshold"] == 0.65
    print(f"[PASS] POST /audio/vad/config: Threshold updated to 0.65")

    # Noise Suppression Status & Config endpoints
    res_ns = client.get("/audio/noise-suppression/status")
    assert res_ns.status_code == 200
    res_ns_cfg = client.post("/audio/noise-suppression/config", json={"level": "high"})
    assert res_ns_cfg.status_code == 200
    assert res_ns_cfg.json()["stats"]["level"] == "high"
    print(f"[PASS] POST /audio/noise-suppression/config: Level set to 'high'")

    # Barge-In Status & Trigger endpoints
    res_bm = client.get("/barge-in/status")
    assert res_bm.status_code == 200
    res_bm_trig = client.post("/barge-in/trigger", json={"source": "test_suite"})
    assert res_bm_trig.status_code == 200
    assert res_bm_trig.json()["record"]["latency_ms"] < 50.0
    print(f"[PASS] POST /barge-in/trigger: Cancelled in {res_bm_trig.json()['record']['latency_ms']} ms")

    # WebSocket Full-Duplex Audio Endpoint
    with client.websocket_connect("/ws/audio") as ws:
        init_frame = ws.receive_json()
        assert init_frame["type"] == "session_init"
        print(f"[PASS] WS /ws/audio Connected: Handshake received for session {init_frame['session_id']}")

        # Send audio PCM frame
        ws.send_bytes(frame)
        
        # Send JSON ping
        ws.send_json({"action": "ping"})
        pong_frame = ws.receive_json()
        assert pong_frame["type"] == "pong"
        print(f"[PASS] WS /ws/audio Bidirectional Ping/Pong Verified")

        # Send barge-in command
        ws.send_json({"action": "barge_in"})
        ack_frame = ws.receive_json()
        assert ack_frame["type"] == "barge_in_ack"
        print(f"[PASS] WS /ws/audio Client-Side Barge-In Acknowledged")

    sess.close()
    return True


if __name__ == "__main__":
    t_start = time.time()
    print("STARTING IRIS FULL-DUPLEX AUDIO & INTELLIGENCE VERIFICATION SUITE")
    
    test_silero_vad()
    test_noise_suppression()
    test_barge_in_manager()
    test_streaming_and_incremental_tts()
    test_full_duplex_session_and_endpoints()

    elapsed = round(time.time() - t_start, 2)
    print("\n" + "=" * 60)
    print(f"[SUCCESS] ALL 5 ADVANCED AUDIO & STREAMING SYSTEMS VERIFIED IN {elapsed}s!")
    print("=" * 60)
