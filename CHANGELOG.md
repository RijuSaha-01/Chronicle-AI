# Changelog

All notable changes to Chronicle AI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] - 2026-01-06

### 🎉 Initial Release - Phase 1 MVP

This is the first public release of Chronicle AI, a diary-to-episodes application that transforms your daily entries into cinematic narratives.

### Added

#### Core Features
- **Entry Model** with id, date, raw_text, narrative_text, and title fields
- **SQLite Repository** with full CRUD operations and date-range queries
- **Ollama LLM Client** for narrative and title generation using Llama 3.2
- **Graceful offline mode** when Ollama is unavailable

#### CLI (Command Line Interface)
- `add` command for quick diary entries
- `guided` command with interactive Q&A mode (5 structured questions)
- `list` command with `--limit` option
- `view` command to show entry details
- `export` command for Markdown export (daily, weekly, or by ID)
- `regenerate` command to refresh AI content
- `status` command for system health check

#### API (FastAPI)
- `POST /entries` - Create new entry
- `POST /entries/guided` - Create entry via guided mode
- `GET /entries` - List entries with filters
- `GET /entries/{id}` - Get single entry
- `POST /entries/{id}/regenerate` - Regenerate AI content
- `DELETE /entries/{id}` - Delete entry
- `POST /export/weekly` - Export weekly summary
- `POST /export/{id}` - Export single entry
- `GET /health` - Health check endpoint
- Interactive API docs at `/docs` and `/redoc`

#### Web UI
- Modern, responsive design with glassmorphism effects
- Quick mode and guided mode for entry creation
- Episodes list with card view
- Entry detail modal with full content
- One-click regenerate and export actions
- Real-time Ollama status indicator

#### Markdown Export
- Daily export (`exports/daily/YYYY-MM-DD.md`)
- Weekly summary export (`exports/weekly/week-YYYY-WW.md`)
- Collapsible raw text sections
- Table of contents for weekly exports

#### Deployment
- `Dockerfile` for containerized deployment
- `requirements.txt` for pip installation
- Environment variable configuration
- Works offline (demo mode) when Ollama unavailable

### Technical Details
- Python 3.8+ compatible
- FastAPI 0.104+
- SQLite embedded database (auto-migration for schema updates)
- httpx/requests for HTTP calls
- Pydantic v2 for data validation

---

## [Unreleased]

### Planned
- Hero & Villain habit categorization
- Character arc visualization over time
- Weekly "episode" video/audio summaries
- Screenplay export format
- Multi-user support
- Cloud sync options

---

**Full documentation:** See [README.md](README.md)

**Report issues:** [GitHub Issues](https://github.com/RijuSaha-01/Chronicle-AI/issues)
