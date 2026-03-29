"""
AnimaFace — Flask Backend
Supports: translation + multi-language TTS + Wav2Lip
"""
import os, uuid, logging
from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename
from pipeline import AnimationPipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

UPLOAD_FOLDER  = "uploads"
OUTPUT_FOLDER  = "outputs"
ALLOWED_IMAGES = {"png","jpg","jpeg","webp"}
ALLOWED_AUDIO  = {"wav","mp3","ogg","m4a"}
ALLOWED_VIDEO  = {"mp4","avi","mov","mkv"}

app = Flask(__name__)
CORS(app)
app.config["UPLOAD_FOLDER"]      = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"]      = OUTPUT_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

pipeline = AnimationPipeline(upload_dir=UPLOAD_FOLDER, output_dir=OUTPUT_FOLDER)

def allowed(filename, allowed_set):
    return "." in filename and filename.rsplit(".",1)[1].lower() in allowed_set

def save_upload(file, allowed_set):
    if not file or file.filename == "": return None, "No file selected."
    if not allowed(file.filename, allowed_set): return None, f"Type not allowed: {allowed_set}"
    ext  = file.filename.rsplit(".",1)[1].lower()
    name = f"{uuid.uuid4().hex}.{ext}"
    path = os.path.join(UPLOAD_FOLDER, name)
    file.save(path)
    logger.info("Saved → %s", path)
    return path, None

@app.route("/")
def index(): return render_template("index.html")

@app.route("/translate", methods=["POST"])
def translate_text():
    """Preview translation before generating."""
    try:
        data = request.get_json()
        text     = data.get("text","").strip()
        lang     = data.get("lang","en")
        if not text:
            return jsonify({"success":False,"error":"No text provided"}), 400
        translated = pipeline.translate(text, target_lang=lang)
        return jsonify({"success":True,"translated":translated,"lang":lang})
    except Exception as e:
        logger.exception("Translation error")
        return jsonify({"success":False,"error":str(e)}), 500

@app.route("/generate", methods=["POST"])
def generate():
    try:
        mode = request.form.get("mode","").lower()
        if mode not in ("audio","video","text"):
            return jsonify({"success":False,"error":"mode must be audio|video|text"}), 400

        image_path, err = save_upload(request.files.get("image"), ALLOWED_IMAGES)
        if err: return jsonify({"success":False,"error":f"Image: {err}"}), 400

        result = None

        if mode == "audio":
            audio_path, err = save_upload(request.files.get("audio"), ALLOWED_AUDIO)
            if err: return jsonify({"success":False,"error":f"Audio: {err}"}), 400
            voice = request.form.get("voice","female").strip()
            result = pipeline.run_audio_mode(image_path, audio_path, voice=voice)

        elif mode == "video":
            video_path, err = save_upload(request.files.get("video"), ALLOWED_VIDEO)
            if err: return jsonify({"success":False,"error":f"Video: {err}"}), 400
            result = pipeline.run_video_mode(image_path, video_path)

        elif mode == "text":
            text  = request.form.get("text","").strip()
            lang  = request.form.get("lang","en").strip()
            voice = request.form.get("voice","female").strip()
            slow  = request.form.get("slow","false").strip().lower() == "true"
            if not text:
                return jsonify({"success":False,"error":"Text cannot be empty."}), 400
            logger.info("TEXT MODE → lang=%s voice=%s slow=%s", lang, voice, slow)
            result = pipeline.run_text_mode(image_path, text,
                                            lang=lang, voice=voice, slow=slow)

        if not result or not os.path.exists(result):
            return jsonify({"success":False,"error":"Generation failed. Check server logs."}), 500

        fname = os.path.basename(result)
        logger.info("Done → %s", result)
        return jsonify({"success":True,"output":f"/download/{fname}"})

    except Exception as exc:
        logger.exception("Unhandled error")
        return jsonify({"success":False,"error":str(exc)}), 500

@app.route("/download/<filename>")
def download(filename):
    path = os.path.join(OUTPUT_FOLDER, secure_filename(filename))
    if not os.path.exists(path):
        return jsonify({"error":"File not found."}), 404
    return send_file(path, as_attachment=False, mimetype="video/mp4")

@app.route("/health")
def health(): return jsonify({"status":"ok"})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)