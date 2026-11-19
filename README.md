# VideoShorts 🎬⚡
### Open-Source AI Video Clipping & Vertical Reframing Studio
**Created & Maintained by [yogendra1941](https://github.com/yogendra1941/VideoShorts)**

Transform long videos, YouTube podcasts, and streams into viral 9:16 Shorts, TikToks, and Reels with automatic face tracking, broadcast-grade karaoke subtitles, hook headline overlays, and multi-platform social captions.

---

## 🌟 Key Features

| Feature | Description | Reference / Origin |
|---|---|---|
| **Universal Ingest** | Fetch any public video link via `yt-dlp` or upload local MP4/MOV files | VideoShorts Ingest |
| **GPU Acceleration** | `faster-whisper` CUDA with automatic int8 CPU fallback + `h264_nvenc` 1080x1920 encoder | NVIDIA RTX 3050 |
| **4D Virality Framework** | Hook $\times 3$, Payoff $\times 3$, Emotion $\times 2$, Quotability $\times 1$ evaluation | Inception Mercury-3 / Ollama |
| **Deep Clips Engine** | Topic Map $\rightarrow$ Thread Seeding $\rightarrow$ Multi-Scene Composition | Dynamic Thread Engine |
| **Honesty Gate** | Verifies transcript faithfulness, eliminating hallucinations and out-of-context quotes | Context Guard |
| **3-Pass Statistical Critic** | Randomized blind evaluation filtering weak openings and rambling fluff | AI Critic Pass |
| **Smart 9:16 Reframing** | MediaPipe Face Tracking (`TRACK`), Dual-Speaker Stack (`SPLIT`), or Letterbox (`GENERAL`) | EMA Motion Smoothing |
| **Bespoke Karaoke Styles** | 6 ASS subtitle presets (`Cyber Neon`, `Hormozi Gold`, `Podcast Split`, `Bold`, `Minimal`, `Default`) | Broadcast ASS Engine |
| **Viral Hook Headlines** | Auto-generates punchy headline overlays for the first 3-5 seconds of every short | VideoShorts Hooks |
| **Social Copy Generator** | Generates tailored captions & hashtags for TikTok, Instagram Reels, and YouTube Shorts | Multi-Platform Engine |
| **Security Hardening** | Strict SSRF guard blocking private IP/cloud metadata ranges + path traversal sanitizer | RFC 1918 / Link-Local Guard |
| **100% Free & Unlimited** | Zero subscriptions, no watermark checks, no plan gates, runs completely self-hosted | Unlocked |

---

## 🎨 6 Bespoke Subtitle Style Presets

VideoShorts includes 6 high-retention karaoke subtitle presets designed for vertical video:

1. **`cyber_neon`** (Default): Electric cyan (`#06B6D4`) with bright neon yellow (`#FACC15`) active word highlight and heavy dark shadow.
2. **`hormozi_gold`**: Alex Hormozi signature style with punchy yellow (`#FFE600`) word-pop and thick black outline.
3. **`podcast_split`**: Dual-tone speaker highlight (`#6366F1`) designed for interviews and podcasts.
4. **`bold`**: Heavy impact uppercase typography with red accent (`#EF4444`).
5. **`minimal`**: Clean aesthetic white text with translucent pill backdrop.
6. **`default`**: Balanced high-legibility studio karaoke.

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.10+** (Tested on Python 3.13)
- **Node.js 18+** (for web studio building)
- **FFmpeg** installed on your system PATH
- **NVIDIA GPU** (Optional, recommended for NVENC and CUDA Whisper)

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/yogendra1941/VideoShorts.git
cd VideoShorts

# Create and activate Python virtual environment
python -m venv venv
.\venv\Scripts\activate   # Windows
# source venv/bin/activate # Linux / macOS

# Install Python dependencies
pip install -r requirements.txt
```

---

## 🖥️ Running the Web Studio

To launch the dark Obsidian/Linear-inspired Web Studio UI:

```bash
# Activate virtual environment
.\venv\Scripts\activate

# Start the FastAPI / Uvicorn server
python -m uvicorn api.server:app --host 0.0.0.0 --port 8000
```

Open your browser at **[http://localhost:8000](http://localhost:8000)**.

### Web Studio Tabs:
- 🎬 **Clips Studio**: Paste any YouTube link or upload an MP4, select your subtitle preset, aspect ratio, and click **Generate Clips**.
- 🎨 **Subtitle Lab**: Interactive 9:16 live simulation previewing word-by-word karaoke highlights across all 6 presets.
- 📜 **Clip Vault**: Access and preview all past rendered shorts stored in `output/`.
- 🤖 **Autonomous Agent**: Workflow guide for integrating VideoShorts into automated CLI scripts.
- ⚙️ **Studio Config**: Monitor hardware acceleration status, test API health, and manage LLM fallback options.

---

## ⌨️ Command Line Usage (CLI)

You can also run the entire end-to-end pipeline directly from your terminal:

```bash
# Generate 3 shorts from a YouTube URL with Cyber Neon subtitles
python main.py "https://www.youtube.com/watch?v=VIDEO_ID" --clips 3 --brand cyber_neon

# Process a local MP4 file with Hormozi Gold subtitles
python main.py "D:\Videos\podcast.mp4" --clips 4 --brand hormozi_gold

# Force a specific 9:16 layout (e.g. SPLIT for two speakers)
python main.py "D:\Videos\interview.mp4" --clips 3 --layout SPLIT

# Disable honesty gate (for creative / loose cuts)
python main.py "D:\Videos\talk.mp4" --no-honesty
```

All rendered shorts and per-clip `.meta.json` sidecars are saved directly into `output/`.

---

## ⚙️ Environment Configuration (`.env`)

```ini
# LLM Provider ('inception', 'ollama', or 'gemini')
LLM_PROVIDER=inception
INCEPTION_API_KEY=sk_...
INCEPTION_MODEL=mercury-3

# Local Ollama Fallback
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# Hardware Acceleration
ASR_DEVICE=cuda
ASR_MODEL_SIZE=small
ASR_COMPUTE_TYPE=float16
ASR_CPU_FALLBACK=true
```

---

## 🔒 Security Architecture

1. **SSRF Guard (`core/security.py`)**: All incoming video URLs undergo DNS resolution and IP range checks. Requests to private networks (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), AWS metadata (`169.254.169.254`), or loopback (`127.0.0.1`) are immediately rejected.
2. **Path Traversal Protection**: File streaming endpoints sanitize all input filenames, stripping directory separators and null bytes.
3. **100% Client-Side Privacy**: No external analytics trackers or third-party telemetry scripts.

---

## 📜 License & Ownership

Developed & maintained by **[yogendra1941](https://github.com/yogendra1941)**.  
Released under the MIT License. 100% Free & Open Source.
