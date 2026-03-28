"""
debug_test.py — Run this to find exactly what's going wrong
Usage: python debug_test.py
"""
import asyncio, os, sys

print("=" * 60)
print("  FULL PIPELINE DEBUG TEST")
print("=" * 60)

# ── Test 1: deep-translator ───────────────────────────────────────────────────
print("\n[TEST 1] Translation...")
try:
    from deep_translator import GoogleTranslator
    text = "Hello my name is Chandu I am from Hyderabad"
    result = GoogleTranslator(source="auto", target="kannada").translate(text)
    print(f"  English : {text}")
    print(f"  Kannada : {result}")
    if result == text:
        print("  WARNING: Translation returned SAME text - may be failing silently!")
    else:
        print("  Translation OK ✓")
except ImportError:
    print("  FAIL: deep-translator not installed! Run: pip install deep-translator")
    sys.exit(1)
except Exception as e:
    print(f"  FAIL: {e}")

# ── Test 2: edge-tts with Kannada voice ──────────────────────────────────────
print("\n[TEST 2] Edge TTS - Kannada Male voice...")
try:
    import edge_tts

    # Use the TRANSLATED text from test 1
    kannada_text = result  # from test 1

    async def test_tts():
        voice = "kn-IN-GaganNeural"
        print(f"  Voice     : {voice}")
        print(f"  Text      : {kannada_text}")
        c = edge_tts.Communicate(kannada_text, voice, rate="+0%")
        await c.save("debug_kannada_output.mp3")
        size = os.path.getsize("debug_kannada_output.mp3")
        print(f"  File size : {size} bytes")
        if size > 1000:
            print("  Edge TTS OK ✓")
        else:
            print("  WARN: File very small - may be silent!")

    asyncio.run(test_tts())
except ImportError:
    print("  FAIL: edge-tts not installed! Run: pip install edge-tts")
except Exception as e:
    print(f"  FAIL: {e}")

# ── Test 3: Check which pipeline.py is actually loaded ───────────────────────
print("\n[TEST 3] Pipeline version check...")
try:
    import pipeline
    import inspect
    src = inspect.getsource(pipeline.AnimationPipeline.run_text_mode)
    if "translate" in src and "edge_tts" in src:
        print("  Pipeline has translation + Edge TTS ✓")
    elif "translate" in src:
        print("  WARNING: Pipeline has translate but NO edge_tts!")
    else:
        print("  CRITICAL: Pipeline is OLD VERSION - no translation, no Edge TTS!")
        print("  You need to replace pipeline.py with the new version!")
    print(f"  Pipeline file: {pipeline.__file__}")
except Exception as e:
    print(f"  Error loading pipeline: {e}")

# ── Test 4: Check app.py passes lang+voice ────────────────────────────────────
print("\n[TEST 4] app.py check...")
try:
    with open("app.py") as f:
        app_src = f.read()
    if "lang" in app_src and "voice" in app_src and "run_text_mode" in app_src:
        if "lang=lang" in app_src:
            print("  app.py passes lang+voice to pipeline ✓")
        else:
            print("  WARNING: app.py may not be passing lang/voice correctly!")
    else:
        print("  CRITICAL: app.py missing lang/voice parameters!")
except Exception as e:
    print(f"  Error: {e}")

print("\n" + "=" * 60)
print("  Done! Play debug_kannada_output.mp3 to hear the voice.")
print("=" * 60)
