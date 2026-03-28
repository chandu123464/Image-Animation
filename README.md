# 🎬 AI Image Animation System

Upload a face photo + audio / video / text → get an animated talking-face or motion-transfer video.

---

## 📁 Project Structure

```
ai_image_animation/
├── app.py              ← Flask server (routes & file handling)
├── pipeline.py         ← Core animation pipeline (all 3 modes)
├── requirements.txt    ← Python dependencies
├── setup.sh            ← Automated setup script
├── templates/
│   └── index.html      ← Frontend UI
├── static/
│   ├── css/style.css
│   └── js/app.js
├── uploads/            ← (auto-created) temporary uploads
├── outputs/            ← (auto-created) generated videos
├── Wav2Lip/            ← (cloned by setup.sh)
└── first-order-model/  ← (cloned by setup.sh)
```

---

## ⚡ Quick Start

### 1 — Run Setup Script
```bash
bash setup.sh
```

### 2 — Download Model Checkpoints (required)

#### Wav2Lip (Audio & Text modes)
```
URL: https://iiitaphyd-my.sharepoint.com/personal/radrabha_m_research_iiit_ac_in/...
     (search "Wav2Lip GAN checkpoint" on the official GitHub)
Save to: Wav2Lip/checkpoints/wav2lip_gan.pth
```

#### First Order Motion Model (Video mode)
```
URL: https://drive.google.com/drive/folders/1PyQJmkdCsAkOYwUyaj_l-l0as-iLDgeH
File: vox-cpk.pth.tar
Save to: first-order-model/checkpoints/vox-cpk.pth.tar
```

### 3 — Start the Server
```bash
source venv/bin/activate
python app.py
```

### 4 — Open Browser
```
http://localhost:5000
```

---

## 🖥 Manual Install (without setup.sh)

```bash
# System deps (Ubuntu)
sudo apt install ffmpeg cmake libboost-all-dev

# Python env
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Clone model repos
git clone https://github.com/Rudrabha/Wav2Lip.git
git clone https://github.com/AliaksandrSiarohin/first-order-model.git

pip install -r Wav2Lip/requirements.txt
pip install -r first-order-model/requirements.txt

# Create folders
mkdir -p uploads outputs
mkdir -p Wav2Lip/checkpoints
mkdir -p first-order-model/checkpoints
```

---

## 🧠 How Each Mode Works

### 🎤 Audio Mode  (`mode=audio`)
```
Image + Audio ──► Wav2Lip ──► Talking-face MP4
```
- Converts audio to 16 kHz mono WAV
- Detects & aligns face in source image
- Runs `Wav2Lip/inference.py` with GAN checkpoint
- Output: lip-synced video

### 💃 Video Mode  (`mode=video`)
```
Image + Driving Video ──► FOMM ──► Motion-transferred MP4
```
- Re-encodes driving video to MP4
- Resizes source image to 256×256
- Runs `first-order-model/demo.py` with relative motion
- Output: face animated with driving-video motion

### ✍️ Text Mode  (`mode=text`)
```
Image + Text ──► gTTS (TTS) ──► Wav2Lip ──► Talking-face MP4
```
- gTTS converts text to MP3 speech
- Same pipeline as Audio mode from here on
- Optional: swap gTTS for Coqui TTS for better voice quality

---

## 🔧 Configuration (Environment Variables)

| Variable         | Default                                        | Description                  |
|------------------|------------------------------------------------|------------------------------|
| `WAV2LIP_DIR`    | `Wav2Lip`                                      | Path to Wav2Lip repo          |
| `WAV2LIP_CKPT`   | `Wav2Lip/checkpoints/wav2lip_gan.pth`          | Wav2Lip model checkpoint     |
| `FOMM_DIR`       | `first-order-model`                            | Path to FOMM repo             |
| `FOMM_CFG`       | `first-order-model/config/vox-256.yaml`        | FOMM config file             |
| `FOMM_CKPT`      | `first-order-model/checkpoints/vox-cpk.pth.tar`| FOMM checkpoint              |
| `SADTALKER_DIR`  | `SadTalker`                                    | (Optional) SadTalker repo    |

Example:
```bash
export WAV2LIP_CKPT=/path/to/wav2lip_gan.pth
python app.py
```

---

## 🚀 GPU Acceleration (Recommended)

Replace PyTorch CPU install with:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```
Then pass `--device cuda` in pipeline.py model calls where supported.

---

## 🔌 API Reference

### `POST /generate`
**Multipart form-data:**

| Field   | Type   | Required | Description               |
|---------|--------|----------|---------------------------|
| `image` | File   | Yes      | Face image (jpg/png/webp) |
| `mode`  | String | Yes      | `audio` / `video` / `text`|
| `audio` | File   | mode=audio | Audio file (wav/mp3)    |
| `video` | File   | mode=video | Driving video (mp4/avi) |
| `text`  | String | mode=text  | Text to speak           |

**Response:**
```json
{ "success": true, "output": "/download/abc123.mp4" }
```

### `GET /download/<filename>`
Returns the generated video.

### `GET /health`
Returns `{ "status": "ok" }`.

---

## 🎯 Optional Enhancements

### Use SadTalker (better quality than Wav2Lip)
```python
# In pipeline.py, call:
result = pipeline.run_sadtalker_mode(image_path, audio_path)
```
Clone: `git clone https://github.com/OpenTalker/SadTalker.git`

### Use Coqui TTS (better voice than gTTS)
```bash
pip install TTS
```
```python
# In pipeline.py _tts():
from TTS.api import TTS
tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC")
tts.tts_to_file(text=text, file_path=out_path)
```

---

## ⚠️ Common Issues

| Issue | Fix |
|-------|-----|
| `ffmpeg not found` | `sudo apt install ffmpeg` |
| `dlib install fails` | `sudo apt install cmake` then retry |
| `No face detected` | Use a clear front-facing photo |
| `CUDA out of memory` | Reduce image size or use CPU |
| `Wav2Lip checkpoint missing` | Download `.pth` file to correct path |
| `FOMM checkpoint missing` | Download `.pth.tar` file to correct path |

---

## 📜 License

This project is MIT licensed. The underlying models (Wav2Lip, FOMM, SadTalker) have their own licenses — please review before commercial use.
