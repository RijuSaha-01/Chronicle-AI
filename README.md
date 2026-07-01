# 🎬 Chronicle AI

**Transform your daily diary entries into cinematic episodic stories with local AI-powered narratives.**

Chronicle AI bridges the gap between daily journaling, habit tracking, and cinematic storytelling. By framing your daily life as a series of "episodes" inside structured "seasons," you gain a fresh perspective on your choices, celebrate wins as "hero moments," and analyze patterns through a narrative lens.

---

## 🖼️ Project Overview & Screenshots:-

Chronicle AI features a **Premium Dark** visual aesthetic with gold accents, deep glassmorphism panels, and a smooth, responsive single-page web interface.

*(Screenshots will appear here once local assets are generated/rendered by user interfaces)*

- **Dashboard Feed**: Displays episodes as cards with cinematic cover arts.
- **Guided Reflection Mode**: A step-by-step Q&A form with smooth micro-animations.
- **Memory RAG Chat**: Natural language interface to search and discuss your life events.
- **Audio narration**: Integrated audiobook player with waveform visuals.

---

## ✨ Feature Highlights:-

- **📝 Structured Guided Mode**: Interactive prompts split your entries into morning, afternoon, and night reflections for rich narrative context.
- **🤖 Local Cinematic Engine**: AI-generated stories, loglines, and title suggestions powered offline by Meta's Llama 3.2 via Ollama.
- **🎨 Visual Cover Art**: Dynamically generates custom poster art based on detected entry moods using Stable Diffusion (ComfyUI / Automatic1111).
- **🎙️ audiobook narration**: Converts generated stories into spoken audiobooks using Coqui TTS (XTTS v2).
- **🧠 Semantic Search & RAG Chat**: Ask natural language questions about your journal history using ChromaDB vector database.
- **📊 Narrative Analysis**: Automatic seasonal grouping, character arc tracking, recurring conflict analysis, and weekly recaps.

---

## 🚀 Quick Start (5 Minutes)

Get Chronicle AI up and running locally in three simple steps:

### 1. Clone & Set Up Environment
```bash
git clone https://github.com/RijuSaha-01/Chronicle-AI.git
cd Chronicle-AI

# Create and activate virtual environment
python -m venv venv
# On Windows (PowerShell): .\venv\Scripts\Activate.ps1
# On macOS/Linux: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Set Up Ollama
Chronicle AI uses Ollama for local LLM processing:
1. Download Ollama from [Ollama's Official Website](https://ollama.com).
2. Start the Ollama daemon and pull the default model:
   ```bash
   ollama pull llama3.2
   ```

### 3. Run the Application
You can interact with Chronicle AI via the Web UI or the terminal CLI:

- **Launch Web Interface**:
  ```bash
  uvicorn chronicle_ai.api:app --reload --port 8000
  ```
  Open **[http://localhost:8000](http://localhost:8000)** in your browser!

- **Quick CLI Entry**:
  ```bash
  python scripts/diary_cli.py add "Had a productive morning, wrote some docs, and committed changes."
  python scripts/diary_cli.py list
  ```

---

## 📚 Complete Documentation

Check the detailed documentation guides inside the `docs/` folder:

- **[Installation Guide](file:///c:/Users/hp/Desktop/Riju/Habit%20Cinematic/docs/INSTALLATION.md)**: System requirements, step-by-step native and Docker setup, GPU acceleration details, and AI configuration.
- **[Usage & API Guide](file:///c:/Users/hp/Desktop/Riju/Habit%20Cinematic/docs/USAGE.md)**: Full CLI reference table, API endpoint details, and RAG search options.
- **[Architecture & Design](file:///c:/Users/hp/Desktop/Riju/Habit%20Cinematic/docs/ARCHITECTURE.md)**: System design flowchart, database models, and component structure.
- **[TTS Setup Guide](file:///c:/Users/hp/Desktop/Riju/Habit%20Cinematic/docs/TTS_SETUP.md)**: Multi-platform voice synthesis configuration details.
