# 📥 Installation Guide

This guide provides step-by-step instructions for setting up Chronicle AI. You can install it either directly on your local system or containerized using Docker.

---

## 💻 System Requirements

### Minimum Requirements
- **OS**: Windows 10/11, macOS Big Sur+, or Linux (Ubuntu 20.04+)
- **Python**: 3.9 – 3.11 (Required for local TTS package dependencies)
- **RAM**: 8 GB
- **Disk**: 5 GB free space (mostly for local AI models)

### Recommended (for local GPU acceleration)
- **GPU**: NVIDIA GPU with 6GB+ VRAM (CUDA support)
- **RAM**: 16 GB
- **Disk**: 15 GB free space (SSD recommended)

---

## 🛠️ Step-by-Step Setup

### Option A: Without Docker (Local Development Setup)

Follow these steps to set up Chronicle AI natively on your machine:

#### 1. Clone the Repository
```bash
git clone https://github.com/RijuSaha-01/Chronicle-AI.git
cd Chronicle-AI
```

#### 2. Create and Activate a Virtual Environment
We recommend using Python 3.10:
```bash
# Create virtual environment
python -m venv venv

# Activate on Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Activate on macOS/Linux
source venv/bin/activate
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Verify Local Installation
```bash
python scripts/diary_cli.py status
```

---

### Option B: With Docker (Recommended & Containerized)

Docker Compose allows you to spin up the entire stack—including ChromaDB, local Ollama, and ComfyUI for cover art—using a single command.

#### 1. Start Services
Run the following command in the root directory:
```bash
docker-compose up -d
```

This starts:
1. `chronicle-app`: The FastAPI backend and Web UI.
2. `ollama`: The local LLM inference engine.
3. `ollama-model-puller`: An automated sidecar that downloads `llama3.2` and exit.
4. `stable-diffusion`: ComfyUI backend for cover art.

#### 2. Verify Services
Visit [http://localhost:8000](http://localhost:8000) in your browser.

#### 3. NVIDIA GPU Acceleration (Optional)
To enable GPU support in Docker, uncomment the `deploy` blocks under `ollama` and `stable-diffusion` services inside the [docker-compose.yml](file:///c:/Users/hp/Desktop/Riju/Habit%20Cinematic/docker-compose.yml) file, then run:
```bash
docker-compose up -d --force-recreate
```

---

## ⚙️ Configuring AI Engines

Chronicle AI relies on three local AI capabilities: **Large Language Models (Ollama)**, **Stable Diffusion (SD)**, and **Text-to-Speech (TTS)**.

### 1. Configuring Ollama (LLM)
Ollama runs Llama 3.2 locally to turn journal entries into structured stories.

- **Download**: Install from [Ollama's Official Website](https://ollama.com).
- **Start Service**: Make sure the daemon is running.
- **Download Model**:
  ```bash
  ollama pull llama3.2
  ```
- **Environment Variables**:
  - `OLLAMA_BASE_URL`: Default is `http://localhost:11434` (or `http://ollama:11434` in Docker).
  - `OLLAMA_MODEL`: Default is `llama3.2`.

---

### 2. Configuring Stable Diffusion (SD Cover Art)
Used for generating custom cinematic episode covers. Supported backends: **ComfyUI** (default) and **Automatic1111**.

#### Using ComfyUI (Recommended)
- **Start ComfyUI** on port `8188`.
- Set environment variables:
  - `STABLE_DIFFUSION_BACKEND=comfyui`
  - `STABLE_DIFFUSION_URL=http://localhost:8188`
- Put your checkpoint (e.g., `sd_xl_base_1.0.safetensors` or similar) in your ComfyUI models directory.

#### Using Automatic1111
- Start Automatic1111 with `--api` enabled on port `7860`.
- Set environment variables:
  - `STABLE_DIFFUSION_BACKEND=automatic1111`
  - `STABLE_DIFFUSION_URL=http://localhost:7860`

---

### 3. Configuring Text-to-Speech (TTS Audiobooks)
Generate realistic audiobook narrations using Coqui TTS (XTTS v2).

1. Install TTS:
   ```bash
   pip install TTS
   ```
2. Install system-wide audio processors:
   - **Windows**: Install `ffmpeg` using Chocolatey: `choco install ffmpeg`
   - **macOS**: Install `ffmpeg` using Homebrew: `brew install ffmpeg`
   - **Linux**: Install via apt: `sudo apt install ffmpeg espeak-ng-data`
3. Accept Coqui TOS:
   The app will automatically agree, but you can set this manually:
   - Windows: `$env:COQUI_TOS_AGREED = "1"`
   - macOS/Linux: `export COQUI_TOS_AGREED=1`
4. Test TTS:
   ```bash
   python scripts/test_tts.py
   ```
   *Note: On first run, a ~2GB model checkpoint (XTTS v2) will download automatically.*
