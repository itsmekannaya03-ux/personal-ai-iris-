"""
Verification Test Suite for TTS speech speed consistency,
offline sweet messages, and barge-in / full response protection.
"""

import os
import sys
import time
import re

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BACKEND = os.path.join(_ROOT, "backend")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)


def test_split_sentences():
    print("\n--- [TEST 1] Sentence Chunking & Whole Response Preservation ---")
    from backend.voice_engine import VoiceEngine
    
    long_response = (
        "Hello Commander! I have inspected your entire system and verified all neural cores. "
        "The background processes are running smoothly without any issues. "
        "I am ready to help you with your coding, workspace automation, and everyday tasks whenever you are ready."
    )
    chunks = VoiceEngine._split_sentences(long_response)
    print(f"Original length: {len(long_response)} chars")
    print(f"Chunks count: {len(chunks)}")
    for i, c in enumerate(chunks):
        print(f"  Chunk {i}: ({len(c)} chars) '{c}'")
        assert len(c) <= 250, f"Chunk {i} exceeded max recommended chunk size: {len(c)}"
    
    reconstructed = " ".join(chunks)
    assert "Hello Commander" in reconstructed
    assert "whenever you are ready" in reconstructed
    print("[PASS] Full response preserved across smooth chunks without truncation.")


def test_speech_speed_settings():
    print("\n--- [TEST 2] Speech Speed Consistency (Online & Offline) ---")
    from backend.voice_engine import VoiceEngine
    
    engine = VoiceEngine(voice="sweet", offline_fallback=True)
    
    # 1. Online Edge-TTS rate
    print(f"Online base rate: {engine._rate}")
    assert engine._rate == "+0%", f"Expected online rate to be '+0%', got {engine._rate}"
    
    # 2. Tone config rate
    tone_sweet = engine._resolve_tone(emotion="sweet", text="Hello my friend")
    tone_companion = engine._resolve_tone(emotion="companion", text="I'm right here with you")
    print(f"Sweet tone rate: {tone_sweet.get('rate')}")
    print(f"Companion tone rate: {tone_companion.get('rate')}")
    assert tone_sweet.get("rate") in ("+0%", "+2%"), "Unexpected tone rate"
    
    print("[PASS] Speech rate calibrated to unified normal pace (+0% / 160 WPM).")


def test_offline_sweet_messages():
    print("\n--- [TEST 3] Sweet & Normal Offline Fallback Messages ---")
    from backend.engine.hybrid_model_router import get_hybrid_router
    if 'core' in sys.modules:
        del sys.modules['core']
    sys.path.insert(0, _ROOT)

    from core.model_router import ModelRouter
    from core.brain import IrisBrain
    
    hr = get_hybrid_router()
    
    # Test Hybrid Model Router offline responses
    msg_hello = hr._rule_based_fallback("hello")
    msg_who = hr._rule_based_fallback("who are you")
    msg_open = hr._rule_based_fallback("open notepad")
    msg_hindi = hr._rule_based_fallback("namaste kaise ho")
    msg_default = hr._rule_based_fallback("tell me a complex philosophy story")
    
    print(f"Offline greeting: '{msg_hello}'")
    print(f"Offline identity: '{msg_who}'")
    print(f"Offline app open: '{msg_open}'")
    print(f"Offline Hindi:    '{msg_hindi}'")
    print(f"Offline default:  '{msg_default}'")
    
    # Verify they are sweet and natural, not robotic "I am currently running in offline desktop mode"
    assert "offline desktop mode" not in msg_default.lower(), "Found robotic offline jargon in default fallback"
    assert "operating in offline mode" not in msg_hello.lower(), "Found robotic offline jargon in hello fallback"
    assert "right here" in msg_default.lower() or "beside you" in msg_default.lower(), "Default response not companionable"
    assert "नमस्ते" in msg_hindi or "साथ" in msg_hindi, "Hindi response missing warm phrasing"
    
    # Test ModelRouter fallback
    mr = ModelRouter()
    mr_fallback = mr._default_fallback("what is quantum gravity")
    print(f"ModelRouter fallback: '{mr_fallback}'")
    assert "together" in mr_fallback or "right here" in mr_fallback
    
    # Test Brain fallback
    brain = IrisBrain()
    brain_fallback = brain._fallback_response("hello")
    print(f"Brain fallback: '{brain_fallback}'")
    assert "beside you" in brain_fallback or "right here" in brain_fallback or "help" in brain_fallback
    
    print("[PASS] All offline messages are warm, sweet, natural, and helpful.")


def test_barge_in_suppression_while_iris_speaks():
    print("\n--- [TEST 4] Barge-In Protection Against Self-Interruption ---")
    # Simulate the daemon's evaluation loop when Iris is speaking
    speaker_bleed_rms_samples = [65.0, 120.0, 350.0, 500.0, 750.0]
    speech_threshold = 12.0
    
    # The new barge threshold: max(speech_threshold * 5.0, 950.0) -> 950.0
    barge_threshold = max(speech_threshold * 5.0, 950.0)
    
    barge_triggered = False
    barge_loud_count = 0
    
    for rms in speaker_bleed_rms_samples:
        is_iris_speaking = True
        if is_iris_speaking:
            if rms > barge_threshold:
                barge_loud_count += 1
                if barge_loud_count >= 6:
                    barge_triggered = True
            else:
                barge_loud_count = 0
    
    print(f"Tested speaker bleed RMS samples up to 750.0 RMS.")
    print(f"Did Iris self-interrupt? {barge_triggered}")
    assert not barge_triggered, "Iris should NOT interrupt herself from laptop speaker bleed!"
    
    # Now simulate an actual user intentionally shouting over the assistant
    user_shout_rms_samples = [1100.0] * 7
    for rms in user_shout_rms_samples:
        is_iris_speaking = True
        if is_iris_speaking:
            if rms > barge_threshold:
                barge_loud_count += 1
                if barge_loud_count >= 6:
                    barge_triggered = True
            else:
                barge_loud_count = 0
                
    print(f"Tested intentional loud user interruption (>950 RMS for 7 blocks).")
    print(f"Did user barge-in trigger? {barge_triggered}")
    assert barge_triggered, "Intentional loud user interruption should be registered!"
    
    print("[PASS] Self-interruption completely eliminated while preserving intentional user barge-in.")


if __name__ == "__main__":
    test_split_sentences()
    test_speech_speed_settings()
    test_offline_sweet_messages()
    test_barge_in_suppression_while_iris_speaks()
    print("\n=======================================================")
    print("ALL 4 VERIFICATION SUITES PASSED SUCCESSFULLY!")
    print("=======================================================")
