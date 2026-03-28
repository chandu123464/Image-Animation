"""
pipeline.py — AnimaFace
Flow: English text → translate to selected language → Edge TTS Neural voice → Wav2Lip lip sync
"""
import os, sys, uuid, asyncio, logging, subprocess, cv2
logger = logging.getLogger(__name__)

# ── Shell helpers ─────────────────────────────────────────────────────────────
def run_cmd(cmd, cwd=None):
    logger.info("CMD: %s", " ".join(str(c) for c in cmd))
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    logger.info("STDOUT: %s", r.stdout[-2000:] if r.stdout else "")
    logger.info("STDERR: %s", r.stderr[-2000:] if r.stderr else "")
    if r.returncode != 0:
        raise RuntimeError(f"STDOUT:{r.stdout[-800:]}\nSTDERR:{r.stderr[-800:]}")

def convert_audio_to_wav(src, out_dir):
    dst = os.path.join(out_dir, f"{uuid.uuid4().hex}.wav")
    run_cmd(["ffmpeg", "-y", "-i", src, "-ar", "16000", "-ac", "1", dst])
    return dst

def convert_video_to_mp4(src, out_dir):
    dst = os.path.join(out_dir, f"{uuid.uuid4().hex}.mp4")
    run_cmd(["ffmpeg", "-y", "-i", src, "-c:v", "libx264", "-c:a", "aac", dst])
    return dst

# ── Deep translator language map ──────────────────────────────────────────────
# Maps our lang codes → deep_translator language names
TRANSLATOR_MAP = {
    "en":"english","hi":"hindi","te":"telugu","ta":"tamil","kn":"kannada",
    "ml":"malayalam","mr":"marathi","bn":"bengali","gu":"gujarati","pa":"punjabi",
    "ur":"urdu","ar":"arabic","fr":"french","de":"german","es":"spanish",
    "it":"italian","pt":"portuguese","ru":"russian","ja":"japanese","ko":"korean",
    "zh-CN":"chinese (simplified)","zh-TW":"chinese (traditional)","tr":"turkish",
    "nl":"dutch","pl":"polish","sv":"swedish","no":"norwegian","fi":"finnish",
    "da":"danish","id":"indonesian","ms":"malay","th":"thai","vi":"vietnamese",
    "el":"greek","cs":"czech","hu":"hungarian","ro":"romanian","sk":"slovak",
    "uk":"ukrainian","af":"afrikaans","sw":"swahili",
}

# ── Edge TTS voice map ────────────────────────────────────────────────────────
EDGE_VOICE_MAP = {
    "te":   {"female":"te-IN-ShrutiNeural",       "male":"te-IN-MohanNeural"},
    "kn":   {"female":"kn-IN-SapnaNeural",        "male":"kn-IN-GaganNeural"},
    "hi":   {"female":"hi-IN-SwaraNeural",        "male":"hi-IN-MadhurNeural"},
    "ta":   {"female":"ta-IN-PallaviNeural",      "male":"ta-IN-ValluvarNeural"},
    "ml":   {"female":"ml-IN-SobhanaNeural",      "male":"ml-IN-MidhunNeural"},
    "mr":   {"female":"mr-IN-AarohiNeural",       "male":"mr-IN-ManoharNeural"},
    "bn":   {"female":"bn-IN-TanishaaNeural",     "male":"bn-IN-BashkarNeural"},
    "gu":   {"female":"gu-IN-DhwaniNeural",       "male":"gu-IN-NiranjanNeural"},
    "pa":   {"female":"pa-IN-VaaniNeural",        "male":"pa-IN-OjasNeural"},
    "ur":   {"female":"ur-IN-GulNeural",          "male":"ur-IN-SalmanNeural"},
    "en":   {"female":"en-US-JennyNeural",        "male":"en-US-GuyNeural"},
    "ja":   {"female":"ja-JP-NanamiNeural",       "male":"ja-JP-KeitaNeural"},
    "ko":   {"female":"ko-KR-SunHiNeural",        "male":"ko-KR-InJoonNeural"},
    "zh-CN":{"female":"zh-CN-XiaoxiaoNeural",     "male":"zh-CN-YunxiNeural"},
    "zh-TW":{"female":"zh-TW-HsiaoChenNeural",    "male":"zh-TW-YunJheNeural"},
    "th":   {"female":"th-TH-PremwadeeNeural",    "male":"th-TH-NiwatNeural"},
    "vi":   {"female":"vi-VN-HoaiMyNeural",       "male":"vi-VN-NamMinhNeural"},
    "id":   {"female":"id-ID-GadisNeural",        "male":"id-ID-ArdiNeural"},
    "ms":   {"female":"ms-MY-YasminNeural",       "male":"ms-MY-OsmanNeural"},
    "ar":   {"female":"ar-SA-ZariyahNeural",      "male":"ar-SA-HamedNeural"},
    "tr":   {"female":"tr-TR-EmelNeural",         "male":"tr-TR-AhmetNeural"},
    "sw":   {"female":"sw-KE-ZuriNeural",         "male":"sw-KE-RafikiNeural"},
    "af":   {"female":"af-ZA-AdriNeural",         "male":"af-ZA-WillemNeural"},
    "fr":   {"female":"fr-FR-DeniseNeural",       "male":"fr-FR-HenriNeural"},
    "de":   {"female":"de-DE-KatjaNeural",        "male":"de-DE-ConradNeural"},
    "es":   {"female":"es-ES-ElviraNeural",       "male":"es-ES-AlvaroNeural"},
    "it":   {"female":"it-IT-ElsaNeural",         "male":"it-IT-DiegoNeural"},
    "pt":   {"female":"pt-BR-FranciscaNeural",    "male":"pt-BR-AntonioNeural"},
    "ru":   {"female":"ru-RU-SvetlanaNeural",     "male":"ru-RU-DmitryNeural"},
    "nl":   {"female":"nl-NL-ColetteNeural",      "male":"nl-NL-MaartenNeural"},
    "pl":   {"female":"pl-PL-ZofiaNeural",        "male":"pl-PL-MarekNeural"},
    "sv":   {"female":"sv-SE-SofieNeural",        "male":"sv-SE-MattiasNeural"},
    "no":   {"female":"nb-NO-PernilleNeural",     "male":"nb-NO-FinnNeural"},
    "fi":   {"female":"fi-FI-NooraNeural",        "male":"fi-FI-HarriNeural"},
    "da":   {"female":"da-DK-ChristelNeural",     "male":"da-DK-JeppeNeural"},
    "el":   {"female":"el-GR-AthinaNeural",       "male":"el-GR-NestorasNeural"},
    "cs":   {"female":"cs-CZ-VlastaNeural",       "male":"cs-CZ-AntoninNeural"},
    "hu":   {"female":"hu-HU-NoemiNeural",        "male":"hu-HU-TamasNeural"},
    "ro":   {"female":"ro-RO-AlinaNeural",        "male":"ro-RO-EmilNeural"},
    "sk":   {"female":"sk-SK-ViktoriaNeural",     "male":"sk-SK-LukasNeural"},
    "uk":   {"female":"uk-UA-PolinaNeural",       "male":"uk-UA-OstapNeural"},
}

def get_voice(lang, gender):
    voices = EDGE_VOICE_MAP.get(lang, EDGE_VOICE_MAP["en"])
    chosen = voices.get(gender, voices["female"])
    logger.info(">>> VOICE SELECTED: %s  (lang=%s  gender=%s)", chosen, lang, gender)
    return chosen

# ── Pipeline ──────────────────────────────────────────────────────────────────
class AnimationPipeline:
    WAV2LIP_DIR  = os.getenv("WAV2LIP_DIR",  "Wav2Lip")
    WAV2LIP_CKPT = os.getenv("WAV2LIP_CKPT", os.path.join("Wav2Lip","checkpoints","wav2lip_gan.pth"))
    FOMM_DIR     = os.getenv("FOMM_DIR",  "first-order-model")
    FOMM_CFG     = os.getenv("FOMM_CFG",  os.path.join("first-order-model","config","vox-256.yaml"))
    FOMM_CKPT    = os.getenv("FOMM_CKPT", os.path.join("first-order-model","checkpoints","vox-cpk.pth.tar"))

    def __init__(self, upload_dir="uploads", output_dir="outputs"):
        self.upload_dir = upload_dir
        self.output_dir = output_dir

    def _tmp(self, ext): return os.path.join(self.upload_dir, f"{uuid.uuid4().hex}.{ext}")
    def _out(self, ext="mp4"): return os.path.join(self.output_dir, f"{uuid.uuid4().hex}.{ext}")
    def _get_voice_name(self, lang, gender): return get_voice(lang, gender)

    # ── Step 1: Translate text ────────────────────────────────────────────────
    def translate(self, text: str, target_lang: str = "en") -> str:
        """
        Translate ANY text → target language using Google Translate (deep-translator).
        pip install deep-translator
        """
        if target_lang == "en":
            logger.info(">>> TRANSLATE: target=English, no translation needed")
            return text

        lang_name = TRANSLATOR_MAP.get(target_lang)
        if not lang_name:
            logger.warning("No translator map for '%s' — using original", target_lang)
            return text

        try:
            from deep_translator import GoogleTranslator
            translated = GoogleTranslator(source="auto", target=lang_name).translate(text)
            logger.info(">>> TRANSLATED  [auto → %s]", lang_name)
            logger.info("    Original  : %s", text)
            logger.info("    Translated: %s", translated)
            return translated
        except Exception as e:
            logger.error(">>> TRANSLATION FAILED (%s) — using original text", e)
            return text  # graceful fallback

    # ── Face detection ────────────────────────────────────────────────────────
    def preprocess_image(self, path):
        img = cv2.imread(path)
        if img is None: raise ValueError(f"Cannot read: {path}")

        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        fc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        faces = fc.detectMultiScale(gray, 1.1, 5, minSize=(30, 30))
        if len(faces) == 0:
            pc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_profileface.xml")
            faces = pc.detectMultiScale(gray, 1.1, 5, minSize=(30, 30))

        out = self._tmp("png")

        if len(faces) > 0:
            faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
            fx, fy, fw, fh = faces[0]
            logger.info("Face detected at (%d,%d,%d,%d)", fx, fy, fw, fh)

            # Keep generous context around face — DO NOT crop tight
            # Wav2Lip works better with the full upper-body/head in frame
            pad_x = int(fw * 0.6)
            pad_y_top = int(fh * 0.8)
            pad_y_bot = int(fh * 0.4)

            x1 = max(0, fx - pad_x)
            y1 = max(0, fy - pad_y_top)
            x2 = min(w, fx + fw + pad_x)
            y2 = min(h, fy + fh + pad_y_bot)

            crop = img[y1:y2, x1:x2]
        else:
            logger.warning("No face detected — using full image")
            crop = img

        # Resize to 720p-width keeping aspect ratio, min 480px tall
        ch, cw = crop.shape[:2]
        target_w = 720
        target_h = int(ch * target_w / cw)
        target_h = max(target_h, 480)

        # Make dimensions even (required by ffmpeg/Wav2Lip)
        target_w = target_w if target_w % 2 == 0 else target_w + 1
        target_h = target_h if target_h % 2 == 0 else target_h + 1

        resized = cv2.resize(crop, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4)
        cv2.imwrite(out, resized, [cv2.IMWRITE_PNG_COMPRESSION, 0])  # lossless
        logger.info("Preprocessed image: %dx%d → %dx%d", cw, ch, target_w, target_h)
        return out

    # ── Audio Mode ────────────────────────────────────────────────────────────
    def run_audio_mode(self, image_path, audio_path, voice="female"):
        logger.info("[AUDIO MODE] image=%s  voice=%s", image_path, voice)
        pi  = self.preprocess_image(image_path)
        wav = convert_audio_to_wav(audio_path, self.upload_dir)
        wav = self._apply_voice_pitch(wav, voice)

        raw_out = self._out()
        run_cmd(
            [sys.executable, "inference.py",
             "--checkpoint_path", os.path.abspath(self.WAV2LIP_CKPT),
             "--face",            os.path.abspath(pi),
             "--audio",           os.path.abspath(wav),
             "--outfile",         os.path.abspath(raw_out),
             "--resize_factor",   "1",
             "--pads",            "0", "15", "0", "0",
             "--nosmooth"],
            cwd=os.path.abspath(self.WAV2LIP_DIR)
        )

        # ── Post-process: sharpen + enhance clarity ───────────────────────────
        final_out = self._out()
        try:
            run_cmd([
                "ffmpeg", "-y", "-i", raw_out,
                "-vf",
                "unsharp=5:5:1.5:5:5:0.0,eq=contrast=1.1:brightness=0.02:saturation=1.2",
                "-c:v", "libx264", "-crf", "17",
                "-preset", "slow",
                "-c:a", "aac", "-b:a", "192k",
                final_out
            ])
            logger.info(">>> Sharpened output: %s", final_out)
            return final_out
        except Exception as e:
            logger.warning("Post-process failed (%s) — returning raw output", e)
            return raw_out

    # ── Video Mode ────────────────────────────────────────────────────────────
    def run_video_mode(self, image_path, video_path):
        logger.info("[VIDEO MODE]")
        pi  = self.preprocess_image(image_path)
        mp4 = convert_video_to_mp4(video_path, self.upload_dir)
        out = self._out()
        run_cmd(
            [sys.executable, "demo.py",
             "--config",        os.path.abspath(self.FOMM_CFG),
             "--checkpoint",    os.path.abspath(self.FOMM_CKPT),
             "--source_image",  os.path.abspath(pi),
             "--driving_video", os.path.abspath(mp4),
             "--result_video",  os.path.abspath(out),
             "--relative", "--adapt_scale"],
            cwd=os.path.abspath(self.FOMM_DIR)
        )
        return out

    # ── Text Mode: translate → TTS → Wav2Lip ─────────────────────────────────
    def run_text_mode(self, image_path, text, lang="en", voice="female", slow=False):
        logger.info("=" * 60)
        logger.info("[TEXT MODE]")
        logger.info("  Input text : %s", text)
        logger.info("  Language   : %s", lang)
        logger.info("  Voice      : %s", voice)
        logger.info("=" * 60)

        # STEP 1 ── Translate English → target language
        translated_text = self.translate(text, target_lang=lang)

        # STEP 2 ── Convert translated text → speech in target language
        mp3_path = self._tmp("mp3")
        self._tts_edge(translated_text, mp3_path, lang=lang, gender=voice)

        if not os.path.exists(mp3_path) or os.path.getsize(mp3_path) == 0:
            raise RuntimeError(
                "TTS failed — audio file is empty.\n"
                "Check your internet connection (Edge TTS requires internet)."
            )

        logger.info(">>> TTS audio ready: %d bytes", os.path.getsize(mp3_path))

        # STEP 3 ── Lip sync the face to the translated speech
        return self.run_audio_mode(image_path, mp3_path, voice=voice)

    # ── Edge TTS ──────────────────────────────────────────────────────────────
    def _tts_edge(self, text, out_path, lang="en", gender="female"):
        """
        Microsoft Edge TTS — genuine Neural voices for Telugu, Kannada, Hindi, etc.
        Requires: pip install edge-tts  +  internet connection
        """
        try:
            import edge_tts
        except ImportError:
            raise RuntimeError(
                "edge-tts not installed!\n"
                "Run: pip install edge-tts\n"
                "Then restart the server."
            )

        voice_name = get_voice(lang, gender)
        logger.info(">>> Edge TTS generating speech...")
        logger.info("    Voice : %s", voice_name)
        logger.info("    Text  : %s", text[:80])

        async def _synth():
            c = edge_tts.Communicate(text, voice_name, rate="+0%")
            await c.save(out_path)

        # Safe asyncio runner
        try:
            asyncio.run(_synth())
        except RuntimeError as e:
            if "running event loop" in str(e):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(_synth())
                finally:
                    loop.close()
            else:
                raise

        sz = os.path.getsize(out_path) if os.path.exists(out_path) else 0
        if sz == 0:
            raise RuntimeError(
                f"Edge TTS produced empty audio!\n"
                f"Voice: {voice_name}\n"
                f"Check internet connection."
            )
        logger.info(">>> Edge TTS SUCCESS: %d bytes → %s", sz, out_path)

    # ── Voice pitch adjustment ─────────────────────────────────────────────────
    def _apply_voice_pitch(self, wav_path, voice):
        """
        Male: lower pitch using ffmpeg asetrate trick (no extra deps needed).
        Female: no change.
        """
        if voice != "male":
            return wav_path
        out = os.path.join(self.upload_dir, f"{uuid.uuid4().hex}.wav")
        try:
            run_cmd([
                "ffmpeg", "-y", "-i", wav_path,
                "-af", "asetrate=16000*0.84,atempo=1.19,aresample=16000",
                "-ar", "16000", "-ac", "1", out
            ])
            logger.info(">>> Voice pitch shifted to male: %s", out)
            return out
        except Exception as e:
            logger.warning("Pitch shift failed (%s) — using original audio", e)
            return wav_path