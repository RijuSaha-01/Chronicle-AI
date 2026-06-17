# 📖 Usage & API Reference

Welcome to the Chronicle AI Usage Guide. This document provides a complete guide to all features, the CLI tool, and the REST API.

---

## 🌟 Feature Guide

### 1. Daily Diary & Guided Mode
- **Quick Entry**: Create an entry by typing raw text.
- **Guided Mode**: Prompts you with questions for morning, afternoon, evening, reflections, and mood. This structured reflection yields rich narratives.

### 2. Cinematic Story Generation
- Turns bullet points and dry logs into a structured third-person cinematic script or story.
- Detects the tone and mood, applying camera presets, lighting guidelines, and visual styles.

### 3. Seasons & Episode Management
- Group related entries into narrative **Seasons** (e.g., based on months or life phases).
- Tracks recurring locations, characters, and key thematic connections across your life timeline.

### 4. Semantic Search & Memory Chat
- Query your journal semantically using ChromaDB vector database.
- Chat with your "journal memories" to ask questions like: *"When was the last time I coded a FastAPI app?"* or *"What did I do when I felt overwhelmed last season?"*

### 5. Media Generation (Images & Audio)
- **Covers & Posters**: Generate beautiful episode cards using Stable Diffusion.
- **Voice Narration**: Convert your stories into audiobooks with selectable voices.

---

## 💻 CLI Reference

All interactions can be performed via the CLI entrypoint [diary_cli.py](file:///c:/Users/hp/Desktop/Riju/Habit%20Cinematic/scripts/diary_cli.py).

### Core Commands

| Command | Arguments | Description | Example |
| :--- | :--- | :--- | :--- |
| `add` | `"<text>"` | Add a quick entry | `python scripts/diary_cli.py add "Worked on documentation all night" --date 2026-06-17` |
| `guided` | None | Interactive structured reflection | `python scripts/diary_cli.py guided` |
| `list` | `--limit N` | List recent entries | `python scripts/diary_cli.py list --limit 5` |
| `view` | `<id>` | View details of an entry (with analysis) | `python scripts/diary_cli.py view 1` |
| `status` | None | Check services (Ollama, SD, TTS) and database status | `python scripts/diary_cli.py status` |
| `regenerate`| `<id>` | Clear and recreate LLM narrative/title | `python scripts/diary_cli.py regenerate 1` |

### Narrative & Theme Analysis

| Command | Arguments | Description | Example |
| :--- | :--- | :--- | :--- |
| `recap` | `--days N` | Generate a "Previously on Chronicle..." recap | `python scripts/diary_cli.py recap --days 7` |
| `retitle` | `--episode ID --pick` | Pick alternative title options for an episode | `python scripts/diary_cli.py retitle --episode 1 --pick` |
| `seasons` | Various options | Manage and view seasons | `python scripts/diary_cli.py seasons --list` |
| `clusters` | `--show`, `--refresh` | Group episodes into cluster themes | `python scripts/diary_cli.py clusters --show` |
| `similar` | `--episode ID` | Find semantically similar/opposite episodes | `python scripts/diary_cli.py similar --episode 1` |
| `arc` | `<topic>` | Analyze character development for a theme | `python scripts/diary_cli.py arc career` |
| `insights` | `--period [week\|month]` | Generate periodic life pattern insights | `python scripts/diary_cli.py insights --period week` |

### Image & Audio Generation

| Command | Arguments | Description | Example |
| :--- | :--- | :--- | :--- |
| `regen-cover`| `--episode ID` | Generate a new cover using Stable Diffusion | `python scripts/diary_cli.py regen-cover --episode 1 --style cinematic` |
| `covers` | `--episode ID --history` | View cover history and choose variants | `python scripts/diary_cli.py covers --episode 1 --history` |
| `generate-poster`| `--season ID` | Generate seasonal poster graphics | `python scripts/diary_cli.py generate-poster --season 1` |
| `narrate` | `--episode ID` | Generate audiobook narration file via TTS | `python scripts/diary_cli.py narrate --episode 1 --voice dramatic` |
| `play` | `--episode ID` | Play generated audiobook narration | `python scripts/diary_cli.py play --episode 1` |
| `embed` | `--batch` | Generate ChromaDB vector embeddings | `python scripts/diary_cli.py embed --batch` |

---

## ⚡ API Reference

FastAPI serves the backend and API endpoints. When the server is running, visit `http://localhost:8000/docs` for the interactive Swagger UI.

### 1. Diary Entries

#### `POST /entries`
Create a new journal entry.
- **Request Body**:
  ```json
  {
    "raw_text": "Completed the documentation changes and pushed to github.",
    "date": "2026-06-17",
    "skip_ai": false
  }
  ```

#### `POST /entries/guided`
Submit an entry structured by guided prompts.
- **Request Body**:
  ```json
  {
    "morning": "Morning run and coffee.",
    "afternoon": "Fixed high priority bugs.",
    "evening": "Celebrated with team.",
    "thoughts": "Need to write more docs.",
    "mood": "Excellent",
    "date": "2026-06-17"
  }
  ```

#### `GET /entries`
List saved entries.
- **Query Params**: `limit` (default: 50), `start_date`, `end_date`.

#### `GET /entries/{entry_id}`
Fetch detailed entry record including mood, conflict data, characters, locations, and media paths.

#### `POST /entries/{entry_id}/regenerate`
Force Ollama to regenerate the title and cinematic narrative for the entry.

#### `DELETE /entries/{entry_id}`
Remove an entry.

---

### 2. Semantic Memory & RAG Chat

#### `GET /search`
Perform semantic search across journal history.
- **Query Params**: `q` (query text), `limit`, `season`, `mood`, `themes`, `start_date`, `end_date`.

#### `POST /ask`
Submit a question to the Memory Chat system (returns answer + RAG sources).
- **Request Body**:
  ```json
  {
    "question": "What patterns do you notice in my productivity?",
    "session_id": null
  }
  ```

#### `GET /chat/sessions`
Get list of previous chat sessions.

---

### 3. Seasons & Story Arcs

#### `GET /seasons`
Get all season records with dates, episode counts, and poster links.

#### `GET /arc`
Retrieve story arc analysis on a specific topic.
- **Query Params**: `topic` (e.g. `career`, `health`), `time_range`.

#### `GET /episodes/{episode_id}/similar`
Find similar or opposite episodes.

#### `GET /recommendations/homepage`
Fetch personalized homepage layout categories (Continue listening, On this day, Theme journeys, etc.).
