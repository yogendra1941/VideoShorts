# VideoShorts 🎬⚡
### Open-Source AI Video Clipping & Vertical Reframing Engine

Turn long videos, podcasts, and streams into viral 9:16 Shorts, TikToks, and Reels with automatic face tracking, word-level karaoke subtitles, and narrative synthesis.

---

## 🌟 Key Features

- **🎬 Ingest Anything**: Drop a local MP4 file or paste any YouTube URL via `yt-dlp`.
- **⚡ RTX GPU Hardware Accelerated**:
  - `faster-whisper` for word-level speech transcription with automatic CPU fallback on VRAM exhaustion.
  - FFmpeg `h264_nvenc` for fast, crisp 1080x1920 video encoding.
- **🧵 Deep Clips (Story Synthesis)**:
  - Fuses non-adjacent moments from long interviews (e.g. question at min 8 + payoff at min 52) into a cohesive 60s short while preserving speaker context and honesty.
- **🧐 3-Pass Statistical AI Critic**:
  - Evaluates candidate moments through 3 randomized blind evaluation runs with anonymized tokens, filtering out weak openings, rambling fluff, and abrupt endings.
- **🎯 Smart 9:16 Reframing**:
  - `TRACK`: Centers solo speaker's face.
  - `SPLIT`: Stacks two conversing speakers (top and bottom) with captions placed on the seam.
  - `GENERAL`: Blurred letterbox background for widescreen graphics.
- **✨ Animated Karaoke Subtitles**:
  - Generates TikTok / Alex Hormozi style burned ASS captions highlighting the active spoken word in gold/yellow with dark contrast outlines.
- **🔊 Broadcast Audio Polish**:
  - Two-pass EBU R128 `loudnorm` filter for consistent loudness across platforms.
- **🔒 100% Offline & Private**:
  - Powered by local **Ollama** (`llama3.2`) with optional cloud fallback to Google Gemini.

---

## 🚀 Quick Start

### 1. Requirements
- **Python 3.10+**
- **FFmpeg** on system PATH
- **Ollama** running locally (`ollama run llama3.2`)

### 2. Setup
```bash
# Clone or navigate to the repository
cd VideoShorts

# Activate virtual environment
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Generate Shorts
```bash
# Generate 3 viral shorts from a YouTube link
python main.py "https://www.youtube.com/watch?v=VIDEO_ID" --clips 3

# Process a local MP4 file
python main.py "C:\path\to\podcast.mp4" --clips 5

# Force a specific layout (e.g. dual speaker stack)
python main.py "C:\path\to\interview.mp4" --layout SPLIT
```

Rendered shorts will be saved directly into `VideoShorts/output/`.

---

## ⚙️ Configuration (`.env`)

```ini
# LLM Provider ('ollama', 'gemini', or 'openai')
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# Hardware Acceleration
ASR_DEVICE=cuda
ASR_MODEL_SIZE=small
ASR_COMPUTE_TYPE=float16
ASR_CPU_FALLBACK=true
```
