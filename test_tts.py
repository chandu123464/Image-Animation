"""
test_tts.py — Run this FIRST to verify Edge TTS is working correctly.
Usage:  python test_tts.py
"""
import asyncio
import os
import sys

print("=" * 60)
print("  TTS Voice Test")
print("=" * 60)

# ── Test 1: Check edge-tts is installed ──────────────────────────
try:
    import edge_tts
    print("[OK] edge-tts is installed:", edge_tts.__version__ if hasattr(edge_tts, '__version__') else "found")
except ImportError:
    print("[FAIL] edge-tts NOT installed!")
    print("       Run:  pip install edge-tts")
    sys.exit(1)

# ── Test 2: Generate Kannada Male voice ──────────────────────────
async def test_voice(text, voice_name, out_file):
    try:
        communicate = edge_tts.Communicate(text, voice_name, rate="+0%")
        await communicate.save(out_file)
        size = os.path.getsize(out_file)
        print(f"[OK] Generated: {out_file}  ({size} bytes)")
        return True
    except Exception as e:
        print(f"[FAIL] {voice_name}: {e}")
        return False

async def run_all_tests():
    tests = [
        ("ನಮಸ್ಕಾರ, ನಾನು ಕನ್ನಡದಲ್ಲಿ ಮಾತನಾಡುತ್ತಿದ್ದೇನೆ",  "kn-IN-GaganNeural",   "test_kannada_male.mp3"),
        ("ನಮಸ್ಕಾರ, ನಾನು ಕನ್ನಡದಲ್ಲಿ ಮಾತನಾಡುತ್ತಿದ್ದೇನೆ",  "kn-IN-SapnaNeural",   "test_kannada_female.mp3"),
        ("నమస్కారం, నేను తెలుగులో మాట్లాడుతున్నాను",       "te-IN-MohanNeural",   "test_telugu_male.mp3"),
        ("నమస్కారం, నేను తెలుగులో మాట్లాడుతున్నాను",       "te-IN-ShrutiNeural",  "test_telugu_female.mp3"),
        ("नमस्ते, मैं हिंदी में बोल रहा हूं",              "hi-IN-MadhurNeural",  "test_hindi_male.mp3"),
        ("Hello, I am speaking in English",                  "en-US-GuyNeural",     "test_english_male.mp3"),
    ]

    print("\nGenerating test audio files...")
    print("-" * 60)
    for text, voice, outfile in tests:
        await test_voice(text, voice, outfile)

    print("\n" + "=" * 60)
    print("Listen to the generated .mp3 files to verify voices.")
    print("If all show [OK] with file size > 0, Edge TTS is working!")
    print("=" * 60)

asyncio.run(run_all_tests())
