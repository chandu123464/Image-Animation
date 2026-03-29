#!/usr/bin/env bash
# setup.sh — One-shot environment setup for AI Image Animation
# Run: bash setup.sh
set -euo pipefail

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║      AI Image Animation — Setup Script           ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# ── 1. Python virtualenv ──────────────────────────────────────────────────────
echo "[1/6] Creating virtual environment…"
python3 -m venv venv
# shellcheck disable=SC1091
source venv/bin/activate
pip install --upgrade pip --quiet

# ── 2. System deps (Ubuntu/Debian) ───────────────────────────────────────────
echo "[2/6] Installing system dependencies (needs sudo)…"
sudo apt-get update -qq
sudo apt-get install -y --no-install-recommends \
  ffmpeg cmake libboost-all-dev \
  python3-dev build-essential libssl-dev \
  libopenblas-dev liblapack-dev > /dev/null

# ── 3. Python packages ────────────────────────────────────────────────────────
echo "[3/6] Installing Python packages…"
pip install -r requirements.txt --quiet

# ── 4. Clone Wav2Lip ─────────────────────────────────────────────────────────
echo "[4/6] Setting up Wav2Lip…"
if [ ! -d "Wav2Lip" ]; then
  git clone https://github.com/Rudrabha/Wav2Lip.git --quiet
  pip install -r Wav2Lip/requirements.txt --quiet
  mkdir -p Wav2Lip/checkpoints
  echo ""
  echo "  ⚠  Download Wav2Lip checkpoint manually:"
  echo "     https://iiitaphyd-my.sharepoint.com/personal/radrabha_m_research_iiit_ac_in/_layouts/15/onedrive.aspx?id=%2Fpersonal%2Fradrabha%5Fm%5Fresearch%5Fiiit%5Fac%5Fin%2FDocuments%2FWav2Lip%5FModels%2Fwav2lip%5Fgan%2Epth"
  echo "     Save as:  Wav2Lip/checkpoints/wav2lip_gan.pth"
  echo ""
else
  echo "  Wav2Lip already present — skipping clone."
fi

# ── 5. Clone FOMM ────────────────────────────────────────────────────────────
echo "[5/6] Setting up First Order Motion Model…"
if [ ! -d "first-order-model" ]; then
  git clone https://github.com/AliaksandrSiarohin/first-order-model.git --quiet
  pip install -r first-order-model/requirements.txt --quiet 2>/dev/null || true
  mkdir -p first-order-model/checkpoints
  echo ""
  echo "  ⚠  Download FOMM checkpoint manually:"
  echo "     https://drive.google.com/drive/folders/1PyQJmkdCsAkOYwUyaj_l-l0as-iLDgeH"
  echo "     Save as:  first-order-model/checkpoints/vox-cpk.pth.tar"
  echo ""
else
  echo "  FOMM already present — skipping clone."
fi

# ── 6. Create folders ─────────────────────────────────────────────────────────
echo "[6/6] Creating upload/output directories…"
mkdir -p uploads outputs

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  Setup complete!                                 ║"
echo "║                                                  ║"
echo "║  Next steps:                                     ║"
echo "║   1. Download model checkpoints (see above)      ║"
echo "║   2. source venv/bin/activate                    ║"
echo "║   3. python app.py                               ║"
echo "║   4. Open http://localhost:5000                  ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""
