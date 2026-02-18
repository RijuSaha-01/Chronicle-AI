# 🎙️ Chronicle AI - TTS Setup Guide

Chronicle AI supports local Text-to-Speech (TTS) for generating high-quality audiobook narration of your life episodes. This guide explains how to set up the TTS engine on different operating systems.

## 🚀 Quick Start (All Platforms)

1. **Install TTS Package**:
   ```bash
   pip install TTS
   ```

2. **Verify Installation**:
   ```bash
   python scripts/test_tts.py
   ```

---

## 🪟 Windows Setup (Recommended)

Windows users should ideally have an NVIDIA GPU for faster narration, though it works on CPU as well.

1. **Python Environment**: Ensure you are using Python 3.9 - 3.11 (TTS may have issues with 3.12+ currently).
2. **Build Tools**: You may need "Visual Studio C++ Build Tools" installed.
3. **GPU Support (Optional but Recommended)**:
   - Install [CUDA Toolkit](https://developer.nvidia.com/cuda-downloads).
   - Install PyTorch with CUDA:
     ```bash
     pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
     ```
4. **FFmpeg**: Required for audio processing.
   - Install via [Chocolatey](https://chocolatey.org/): `choco install ffmpeg`
   - Or download manually and add to PATH.

---

## 🍎 macOS Setup

1. **FFmpeg**: Required for audio processing.
   - Install via Homebrew: `brew install ffmpeg`
2. **Dependencies**:
   ```bash
   pip install TTS
   ```
3. **M1/M2/M3 (Silicon) Support**:
   Coqui TTS will use the CPU by default. MPS (Metal) acceleration is sometimes buggy with XTTS, so CPU is recommended for stability.

---

## 🐧 Linux Setup

1. **System Dependencies**:
   ```bash
   sudo apt update
   sudo apt install ffmpeg espeak-ng-data
   ```
2. **Pip Install**:
   ```bash
   pip install TTS
   ```

---

## 🛠️ Troubleshooting

### "COQUI_TOS_AGREED" Error
Chronicle AI automatically sets `os.environ["COQUI_TOS_AGREED"] = "1"` in the code. If you get a prompt in the terminal, you can also set it manually in your shell:
- **Windows (PowerShell)**: `$env:COQUI_TOS_AGREED = "1"`
- **Linux/Mac**: `export COQUI_TOS_AGREED=1`

### Model Download
The first time you run `chronicle narrate`, it will download the **XTTS v2** model (approx. 2GB). This only happens once.

### Performance
- **XTTS v2** (Quality) takes about 5-10 seconds per sentence on a decent CPU, or sub-second on a GPU.
- **Piper** (Speed) is near-instant but slightly more robotic. (Support coming soon).

## 🎙️ Available Narrative Voices

| Voice Key | Voice Name | Style |
|-----------|------------|-------|
| `storyteller` | Abrahan Mack | Warm, engaging, perfect for chronicles |
| `dramatic` | Baldur Valur | Deep, resonant, for high-tension moments |
| `calm` | Asya Arafat | Soft, steady, for peaceful reflections |

**Usage**:
```bash
chronicle narrate --episode 1 --voice dramatic
```
