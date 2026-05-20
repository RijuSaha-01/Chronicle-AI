# Chronicle AI 🎬

**Transform your daily diary entries into cinematic episodic stories with AI-powered narratives.**

Chronicle AI bridges the gap between habit tracking and storytelling. By framing your daily actions as part of a narrative, you gain a fresh perspective on your choices, celebrate wins as "hero moments," and recognize patterns in your life story.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📖 Table of Contents

- [Features](#-features)
- [Core Concepts](#-core-concepts)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [CLI Usage](#-cli-usage)
- [API Endpoints](#-api-endpoints)
- [Web UI](#-web-ui)
- [Ollama Setup](#-ollama-setup)
- [Deployment](#-deployment)
- [Contributing](#-contributing)

---

## ✨ Features

### MVP Features (v0.1.0)
- **📝 Diary Entries** – Add quick entries or use guided mode with structured questions
- **🤖 AI Narratives** – Transform raw diary text into cinematic third-person narratives
- **🎬 Episode Titles** – Auto-generate catchy episode titles for each entry
- **📊 Entry Management** – View, list, and search your diary entries
- **📥 Markdown Export** – Export daily entries or weekly summaries to Markdown
- **🌐 Web UI** – Beautiful, responsive web interface
- **⚡ REST API** – Full-featured FastAPI backend
- **💻 CLI Tool** – Complete command-line interface

### Planned Features
- 🎭 Hero & Villain habit tracking
- 📈 Character arc visualization
- 🎥 Weekly "episode" summaries
- 📜 Screenplay export format

---

## 🎯 Core Concepts

| Concept | Description |
|---------|-------------|
| **Entry** | A single diary record with date and raw text |
| **Narrative** | AI-generated cinematic prose from your entry |
| **Episode Title** | A catchy 3-7 word title for each entry |
| **Export** | Markdown files for daily or weekly summaries |

---

## 🏗️ Architecture

```
Chronicle AI
├── CLI (scripts/diary_cli.py)      # Command-line interface
├── API (src/chronicle_ai/api.py)   # FastAPI REST endpoints
├── Web UI (static/)                # Minimal HTML/CSS/JS frontend
├── LLM Client (llm_client.py)      # Ollama Llama 3.2 integration
├── Repository (repository.py)      # SQLite storage layer
└── Exports (exports.py)            # Markdown export functions
```

**Tech Stack:**
- Python 3.8+
- FastAPI + Uvicorn
- SQLite (embedded database)
- Local Ollama with Llama 3.2

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/RijuSaha-01/Chronicle-AI.git
cd Chronicle-AI

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Set Up Ollama (Optional but Recommended)

```bash
# Install Ollama from https://ollama.ai
# Then pull the Llama 3.2 model:
ollama pull llama3.2

# Start Ollama (usually runs automatically)
ollama serve
```

### 3. Run the Application

**Option A: CLI**
```bash
python scripts/diary_cli.py add "Today was amazing!"
python scripts/diary_cli.py list
```

**Option B: Web Server**
```bash
# Start the FastAPI server
uvicorn chronicle_ai.api:app --reload --port 8000

# Open http://localhost:8000 in your browser
```

---

## 💻 CLI Usage

The CLI provides full access to all Chronicle AI features:

```bash
# Add a quick entry
python scripts/diary_cli.py add "Had a productive morning, wrote some code"

# Add with specific date
python scripts/diary_cli.py add "Great day!" --date 2024-01-15

# Guided mode (interactive questions)
python scripts/diary_cli.py guided

# List recent entries
python scripts/diary_cli.py list --limit 5

# View a specific entry
python scripts/diary_cli.py view 1

# Export to Markdown
python scripts/diary_cli.py export --weekly       # Weekly summary
python scripts/diary_cli.py export --date 2024-01-15  # Specific date
python scripts/diary_cli.py export --id 1         # Specific entry

# Regenerate AI content
python scripts/diary_cli.py regenerate 1

# Check system status
python scripts/diary_cli.py status

# Batch process episodes (generate missing narratives, titles, etc.)
python scripts/diary_cli.py process --from 2024-01-01 --to 2024-03-31
```

### Guided Mode Questions

When using `guided` mode, you'll be asked:
1. 🌅 How was your morning?
2. ☀️ What happened in the afternoon?
3. 🌙 How did your day end?
4. 💭 Any notable thoughts or reflections?
5. 😊 How was your overall mood today?

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Web UI homepage |
| `GET` | `/health` | Health check with status info |
| `POST` | `/entries` | Create a new entry |
| `POST` | `/entries/guided` | Create entry via guided mode |
| `GET` | `/entries` | List entries (with `limit`, `start_date`, `end_date`) |
| `GET` | `/entries/{id}` | Get a single entry |
| `POST` | `/entries/{id}/regenerate` | Regenerate AI content |
| `DELETE` | `/entries/{id}` | Delete an entry |
| `POST` | `/export/weekly` | Export weekly summary |
| `POST` | `/export/{id}` | Export single entry |

### Example API Calls

```bash
# Create entry
curl -X POST http://localhost:8000/entries \
  -H "Content-Type: application/json" \
  -d '{"raw_text": "Today was productive!", "date": "2024-01-15"}'

# List entries
curl http://localhost:8000/entries?limit=5

# Get health status
curl http://localhost:8000/health
```

**API Documentation:** Visit `/docs` (Swagger UI) or `/redoc` when the server is running.

---

## 🎨 Web UI

The web interface provides a beautiful, responsive experience:

- **Quick Mode** – Fast single-field entry
- **Guided Mode** – Structured Q&A for detailed entries
- **Episodes List** – Browse your diary entries
- **Entry Details** – View full narrative and original text
- **Export & Regenerate** – One-click actions

Access at `http://localhost:8000` when the server is running.

---

## 🤖 Ollama Setup

Chronicle AI uses local Ollama with Llama 3.2 for AI generation.

### Installation

1. **Download Ollama**: https://ollama.ai/download
2. **Pull the model**:
   ```bash
   ollama pull llama3.2
   ```
3. **Verify it's running**:
   ```bash
   curl http://localhost:11434/api/tags
   ```

### Configuration

Set environment variables to customize:

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3.2` | Model to use |
| `OLLAMA_TIMEOUT` | `60` | Request timeout (seconds) |

**Example:**
```bash
export OLLAMA_BASE_URL=http://192.168.1.100:11434
export OLLAMA_MODEL=llama3.2:7b
```

### Offline Mode

Chronicle AI works without Ollama! If the AI server is unavailable:
- Entries are saved with raw text only
- Fallback titles/narratives are generated
- You can regenerate AI content later when Ollama is available

---

## 🚢 Deployment & Containerization (Docker)

Chronicle AI is fully containerized, allowing you to run the entire system—including the FastAPI backend, ChromaDB vector search, Ollama LLM, and optional Stable Diffusion (ComfyUI) image generation engine—using a single command.

### ⚡ Quick Start with Docker Compose

To start all services on any machine (even a fresh machine with no Python or Ollama installed):

```bash
docker-compose up -d
```

This single command will:
1. Build the optimized, multi-stage `chronicle-app` container (incorporating all dependencies, `ffmpeg` for audio conversion, and SQLite+ChromaDB support).
2. Start the local `ollama` service.
3. Automatically download and prepare the `llama3.2` model using the built-in `ollama-model-puller` sidecar.
4. Launch the optional `stable-diffusion` (ComfyUI) service for beautiful cinematic episode cover generation.

Once ready, visit **http://localhost:8000** in your browser!

### 📁 Volumes & Persistence

The Docker setup maps stateful assets to ensure full data persistence across container restarts:

* `/data` (mapped to `chronicle-data` volume) – Persists the SQLite database (`chronicle_ai.db`), ChromaDB vector embeddings (`/data/chroma`), generated episode images (`/data/images`), and audios (`/data/audio`).
* `/config` (mapped to local `./config` folder) – Allows overriding bundled settings like custom cinematic styles (`style_config.json`).
* `/root/.ollama` (mapped to `ollama-data` volume) – Persists downloaded LLM checkpoints (such as Llama 3.2).

### ⚙️ Environment Configuration

You can customize runtime settings through variables in `docker-compose.yml`:

| Environment Variable | Description | Default |
|----------------------|-------------|---------|
| `OLLAMA_BASE_URL` | Ollama connection endpoint | `http://ollama:11434` |
| `OLLAMA_MODEL` | LLM model for story/title generation | `llama3.2` |
| `STABLE_DIFFUSION_URL`| Stable Diffusion API endpoint | `http://stable-diffusion:8188` |
| `STABLE_DIFFUSION_BACKEND`| API backend type (`comfyui` or `automatic1111`) | `comfyui` |
| `CHRONICLE_DATA_DIR` | Base directory for persistent data | `/data` |

### 🚀 Enabling GPU Acceleration (NVIDIA)

To leverage local GPU power for near-instantaneous story analysis and high-quality cover generation:
1. Open `docker-compose.yml`.
2. Uncomment the `deploy:` reservation blocks in both the `ollama` and `stable-diffusion` services.
3. Restart using `docker-compose up -d`.

---

## 📁 Project Structure

```
Chronicle-AI/
├── src/chronicle_ai/       # Main package
│   ├── __init__.py         # Package init + exports
│   ├── models.py           # Entry dataclass
│   ├── repository.py       # SQLite storage
│   ├── llm_client.py       # Ollama integration
│   ├── exports.py          # Markdown export
│   ├── cli.py              # CLI implementation
│   └── api.py              # FastAPI app
├── static/                 # Web UI files
│   ├── index.html
│   ├── style.css
│   └── app.js
├── scripts/
│   └── diary_cli.py        # CLI entry point
├── exports/                # Generated exports
│   ├── daily/
│   └── weekly/
├── tests/                  # Test files
├── docs/                   # Documentation
├── requirements.txt        # Python dependencies
├── pyproject.toml          # Package configuration
├── Dockerfile              # Container build
├── README.md               # This file
└── CHANGELOG.md            # Version history
```

---

## 🤝 Contributing

Contributions are welcome! Whether it's feature ideas, bug fixes, or documentation improvements.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai) for local LLM inference
- [FastAPI](https://fastapi.tiangolo.com) for the excellent API framework
- [Llama 3.2](https://ai.meta.com/llama/) by Meta AI

---

**Chronicle AI** – *Your Life, Your Story, Your Episodes* 🎬
**Feedback**-*Open to FeedBacks and improvements*
