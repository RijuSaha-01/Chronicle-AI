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

## 🚢 Deployment

### Docker

```bash
# Build the image
docker build -t chronicle-ai .

# Run the container
docker run -p 8000:8000 -v $(pwd)/data:/app/data chronicle-ai
```

### Render / Railway

1. Connect your GitHub repository
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `uvicorn chronicle_ai.api:app --host 0.0.0.0 --port $PORT`
4. Add environment variables if needed

### Environment Variables for Production

```bash
OLLAMA_BASE_URL=https://your-ollama-endpoint.com  # If using remote Ollama
CHRONICLE_EXPORTS_DIR=/data/exports
```

**Note:** For cloud deployment without Ollama, the app will work in "offline mode" with stub narratives.

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
