/* app.js — AnimaFace */
(function () {
  "use strict";

  let currentMode  = "audio";
  let currentVoice = "female";
  let imageFile = null, audioFile = null, outputUrl = null;

  const LANG_NAMES = {
    "en":"English","hi":"Hindi","te":"Telugu","ta":"Tamil","kn":"Kannada",
    "ml":"Malayalam","mr":"Marathi","bn":"Bengali","gu":"Gujarati","pa":"Punjabi",
    "ur":"Urdu","ar":"Arabic","fr":"French","de":"German","es":"Spanish",
    "it":"Italian","pt":"Portuguese","ru":"Russian","ja":"Japanese","ko":"Korean",
    "zh-CN":"Chinese (Simplified)","zh-TW":"Chinese (Traditional)","tr":"Turkish",
    "nl":"Dutch","pl":"Polish","sv":"Swedish","no":"Norwegian","fi":"Finnish",
    "da":"Danish","id":"Indonesian","ms":"Malay","th":"Thai","vi":"Vietnamese",
    "el":"Greek","cs":"Czech","hu":"Hungarian","ro":"Romanian","sk":"Slovak",
    "uk":"Ukrainian","af":"Afrikaans","sw":"Swahili"
  };

  const MODE_BADGE = {
    audio: "AUDIO MODE",
    text:  "TEXT MODE",
  };
  const MODE_INFO = {
    audio: "Wav2Lip · 16 kHz GAN lip-sync",
    text:  "Translate · Edge TTS · Wav2Lip",
  };
  const STEPS = {
    audio: ["Uploading files…","Detecting face…","Running Wav2Lip…","Encoding video…"],
    text:  ["Translating text…","Synthesising voice…","Detecting face…","Running Wav2Lip…"],
  };

  const CIRC = 2 * Math.PI * 36;   // r=36 in progress SVG
  const C = id => document.getElementById(id);

  const imageInput    = C("imageInput");
  const imageDropZone = C("imageDropZone");
  const imgPreview    = C("imgPreview");
  const imgPreviewWrap= C("imgPreviewWrap");
  const previewImg    = C("previewImg");
  const imgName       = C("imgName");
  const imgSize       = C("imgSize");
  const changeImgBtn  = C("changeImgBtn");

  const audioInput    = C("audioInput");
  const audioDropZone = C("audioDropZone");
  const audioTag      = C("audioTag");

  const videoTag      = null; // video mode removed

  const textInput     = C("textInput");
  const charCount     = C("charCount");
  const langSelect    = C("langSelect");
  const vpText        = C("vpText");
  const generateBtn   = C("generateBtn");

  const outIdle    = C("outIdle");
  const outProgress= C("outProgress");
  const outVideo   = C("outVideo");
  const outError   = C("outError");
  const outputActs = C("outputActs");
  const progCircle = C("progCircle");
  const progPct    = C("progPct");
  const progLbl    = C("progLbl");
  const errMsg     = C("errMsg");
  const dlBtn      = C("dlBtn");
  const fsBtn      = C("fsBtn");
  const modePill   = C("modePill");
  const modeInfoTxt= C("modeInfoTxt");

  // ── Tabs ──────────────────────────────────────────────────────────────────
  document.querySelectorAll(".tab").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".pane").forEach(p => p.classList.remove("active"));
      btn.classList.add("active");
      currentMode = btn.dataset.mode;
      C(`pane-${currentMode}`).classList.add("active");
      modePill.textContent    = MODE_BADGE[currentMode];
      modeInfoTxt.textContent = MODE_INFO[currentMode];
    });
  });

  // ── Image upload ──────────────────────────────────────────────────────────
  imageInput.addEventListener("change", e => handleImage(e.target.files[0]));
  changeImgBtn.addEventListener("click", e => { e.stopPropagation(); imageInput.click(); });
  setupDrop(imageDropZone, handleImage);

  function handleImage(file) {
    if (!file) return;
    imageFile = file;
    const reader = new FileReader();
    reader.onload = ev => {
      const tmp = new Image();
      tmp.onload = () => {
        previewImg.src     = ev.target.result;
        imgName.textContent = trunc(file.name, 26);
        imgSize.textContent = `${tmp.naturalWidth} × ${tmp.naturalHeight}`;
        imageDropZone.style.display = "none";
        imgPreview.style.display    = "block";
      };
      tmp.src = ev.target.result;
    };
    reader.readAsDataURL(file);
  }

  function trunc(s, max) {
    if (s.length <= max) return s;
    const d = s.lastIndexOf("."), n = d > -1 ? s.slice(0, d) : s, e = d > -1 ? s.slice(d) : "";
    return n.slice(0, max - e.length - 3) + "…" + e;
  }

  // ── Audio ─────────────────────────────────────────────────────────────────
  audioInput.addEventListener("change", e => handleAudio(e.target.files[0]));
  setupDrop(audioDropZone, handleAudio);
  function handleAudio(file) {
    if (!file) return;
    audioFile = file;
    audioTag.textContent = "✓  " + file.name;
    audioDropZone.classList.add("has-file");
  }

  // ── Text counter ──────────────────────────────────────────────────────────
  textInput.addEventListener("input", () => {
    charCount.textContent = textInput.value.length;
  });

  // ── Language / Voice ──────────────────────────────────────────────────────
  langSelect.addEventListener("change", updatePill);

  document.querySelectorAll(".vtog").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".vtog").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      currentVoice = btn.dataset.voice;
      updatePill();
    });
  });

  function updatePill() {
    const lang  = LANG_NAMES[langSelect.value] || langSelect.value;
    const voice = currentVoice === "male" ? "Male" : "Female";
    vpText.textContent = `${lang} · ${voice} Neural Voice`;
  }

  // ── Generate ──────────────────────────────────────────────────────────────
  generateBtn.addEventListener("click", generate);

  async function generate() {
    if (!imageFile)                                         return showErr("Please upload a portrait photo first.");
    if (currentMode === "audio" && !audioFile)              return showErr("Please upload an audio file.");
    if (currentMode === "text"  && !textInput.value.trim()) return showErr("Please enter text to speak.");

    const fd = new FormData();
    fd.append("image", imageFile);
    fd.append("mode",  currentMode);
    fd.append("lang",  langSelect.value);
    fd.append("voice", currentVoice);
    fd.append("slow",  "false");

    if (currentMode === "audio") fd.append("audio", audioFile);
    if (currentMode === "text")  fd.append("text",  textInput.value.trim());

    setUI("loading");

    const steps = STEPS[currentMode];
    let prog = 0;
    const timer = setInterval(() => {
      prog = Math.min(prog + Math.random() * 4 + 2, 88);
      const si = Math.min(Math.floor(prog / (100 / steps.length)), steps.length - 1);
      setProgress(prog, steps[si]);
    }, 700);

    try {
      const resp = await fetch("/generate", { method: "POST", body: fd });
      const data = await resp.json();
      clearInterval(timer);
      if (!data.success) { setUI("error", data.error || "Generation failed."); return; }
      setProgress(100, "Complete!");
      outputUrl = data.output;
      setTimeout(() => {
        outVideo.src = data.output;
        setUI("done");
        outVideo.play().catch(() => {});
      }, 400);
    } catch (err) {
      clearInterval(timer);
      setUI("error", "Network error: " + err.message);
    }
  }

  // ── Download / Fullscreen ─────────────────────────────────────────────────
  dlBtn.addEventListener("click", () => {
    if (!outputUrl) return;
    const a = document.createElement("a");
    a.href = outputUrl; a.download = "animaface_output.mp4"; a.click();
  });
  fsBtn.addEventListener("click", () => {
    if (outVideo.requestFullscreen)       outVideo.requestFullscreen();
    else if (outVideo.webkitRequestFullscreen) outVideo.webkitRequestFullscreen();
  });

  // ── UI states ─────────────────────────────────────────────────────────────
  function setUI(state, msg) {
    outIdle.style.display     = "none";
    outProgress.style.display = "none";
    outVideo.style.display    = "none";
    outError.style.display    = "none";
    outputActs.style.display  = "none";
    generateBtn.disabled      = false;
    generateBtn.textContent   = "";

    // Rebuild button content
    const icon = document.createElement("svg");
    icon.setAttribute("viewBox", "0 0 18 18");
    icon.setAttribute("fill", "currentColor");
    icon.setAttribute("width", "15"); icon.setAttribute("height", "15");
    icon.innerHTML = '<path d="M3.5 3 L15.5 9 L3.5 15 Z"/>';
    generateBtn.appendChild(icon);
    const txt = document.createElement("span");

    if (state === "loading") {
      outProgress.style.display = "flex";
      generateBtn.disabled = true;
      txt.textContent = "Generating…";
      generateBtn.appendChild(txt);
      setProgress(0, STEPS[currentMode][0]);
    } else if (state === "done") {
      outVideo.style.display   = "block";
      outputActs.style.display = "flex";
      txt.textContent = "Generate Animation";
      generateBtn.appendChild(txt);
    } else if (state === "error") {
      outError.style.display = "flex";
      errMsg.textContent = msg || "Something went wrong.";
      txt.textContent = "Generate Animation";
      generateBtn.appendChild(txt);
    } else {
      outIdle.style.display = "flex";
      txt.textContent = "Generate Animation";
      generateBtn.appendChild(txt);
    }
  }

  function setProgress(pct, lbl) {
    const offset = CIRC - (pct / 100) * CIRC;
    progCircle.style.strokeDashoffset = offset;
    progPct.textContent = Math.round(pct) + "%";
    progLbl.textContent = lbl || "";
  }

  function showErr(msg) { setUI("error", msg); }

  // ── Drag & drop ───────────────────────────────────────────────────────────
  function setupDrop(zone, handler) {
    if (!zone) return;
    zone.addEventListener("dragover",  e => { e.preventDefault(); zone.classList.add("over"); });
    zone.addEventListener("dragleave", () => zone.classList.remove("over"));
    zone.addEventListener("drop", e => {
      e.preventDefault(); zone.classList.remove("over");
      const f = e.dataTransfer.files[0]; if (f) handler(f);
    });
  }

  // ── Init ──────────────────────────────────────────────────────────────────
  modePill.textContent    = MODE_BADGE["audio"];
  modeInfoTxt.textContent = MODE_INFO["audio"];
  updatePill();

})();