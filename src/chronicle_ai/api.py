"""
Chronicle AI - FastAPI Web Application

RESTful API and minimal web UI for the diary-to-episodes app.
"""

import os
from datetime import date
from typing import Optional, List
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, Field

from .models import Entry
from .repository import get_repository, EntryRepository
from .llm_client import process_entry, is_ollama_available
from .exports import export_entry_to_markdown, export_weekly
from . import __version__


# =============================================================================
# Pydantic Schemas
# =============================================================================

class EntryCreate(BaseModel):
    """Request body for creating a new entry."""
    raw_text: str = Field(..., min_length=1, description="The diary entry text")
    date: Optional[str] = Field(None, description="Date in YYYY-MM-DD format (default: today)")
    skip_ai: bool = Field(False, description="Skip AI narrative/title generation")


class GuidedEntryCreate(BaseModel):
    """Request body for creating an entry via guided mode."""
    morning: Optional[str] = Field(None, description="Morning response")
    afternoon: Optional[str] = Field(None, description="Afternoon response")
    evening: Optional[str] = Field(None, description="Evening response")
    thoughts: Optional[str] = Field(None, description="Thoughts/reflections")
    mood: Optional[str] = Field(None, description="Overall mood")
    date: Optional[str] = Field(None, description="Date in YYYY-MM-DD format")
    skip_ai: bool = Field(False, description="Skip AI generation")


class EntryResponse(BaseModel):
    """Response schema for an entry."""
    id: int
    date: str
    raw_text: str
    narrative_text: Optional[str] = None
    title: Optional[str] = None
    conflict_data: Optional[dict] = None
    
    class Config:
        from_attributes = True


class EntryListResponse(BaseModel):
    """Response schema for entry list."""
    entries: List[EntryResponse]
    total: int


class HealthResponse(BaseModel):
    """Response schema for health check."""
    status: str
    version: str
    ollama_available: bool
    entry_count: int


class ExportResponse(BaseModel):
    """Response schema for export operations."""
    success: bool
    filepath: Optional[str] = None
    message: str


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="Chronicle AI",
    description="🎬 Turn your daily diary into episodic stories with AI-powered narratives",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
)


# Serve static files (web UI)
static_path = Path(__file__).parent.parent.parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main web UI."""
    index_path = static_path / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    
    # Fallback if static files not found
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head><title>Chronicle AI</title></head>
    <body>
        <h1>🎬 Chronicle AI</h1>
        <p>Web UI files not found. Please ensure the <code>static/</code> directory exists.</p>
        <p>API documentation available at <a href="/docs">/docs</a></p>
    </body>
    </html>
    """)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns system status including Ollama availability and entry count.
    """
    repo = get_repository()
    entries = repo.list_entries()
    
    return HealthResponse(
        status="healthy",
        version=__version__,
        ollama_available=is_ollama_available(),
        entry_count=len(entries)
    )


@app.post("/entries", response_model=EntryResponse, status_code=201)
async def create_entry(body: EntryCreate):
    """
    Create a new diary entry.
    
    The entry will be processed by AI to generate a narrative and title
    unless skip_ai is set to True.
    """
    repo = get_repository()
    
    entry = Entry(
        date=body.date or date.today().isoformat(),
        raw_text=body.raw_text
    )
    
    if not body.skip_ai:
        process_entry(entry)
    
    repo.create_entry(entry)
    
    return EntryResponse(
        id=entry.id,
        date=entry.date,
        raw_text=entry.raw_text,
        narrative_text=entry.narrative_text,
        title=entry.title
    )


@app.post("/entries/guided", response_model=EntryResponse, status_code=201)
async def create_guided_entry(body: GuidedEntryCreate):
    """
    Create a new entry using guided mode responses.
    
    Combines responses from guided questions into a single entry
    and processes with AI.
    """
    repo = get_repository()
    
    # Combine guided responses
    parts = []
    if body.morning:
        parts.append(f"Morning: {body.morning}")
    if body.afternoon:
        parts.append(f"Afternoon: {body.afternoon}")
    if body.evening:
        parts.append(f"Evening: {body.evening}")
    if body.thoughts:
        parts.append(f"Thoughts: {body.thoughts}")
    if body.mood:
        parts.append(f"Mood: {body.mood}")
    
    if not parts:
        raise HTTPException(status_code=400, detail="At least one field must be provided")
    
    raw_text = "\n\n".join(parts)
    
    entry = Entry(
        date=body.date or date.today().isoformat(),
        raw_text=raw_text
    )
    
    if not body.skip_ai:
        process_entry(entry)
    
    repo.create_entry(entry)
    
    return EntryResponse(
        id=entry.id,
        date=entry.date,
        raw_text=entry.raw_text,
        narrative_text=entry.narrative_text,
        title=entry.title
    )


@app.get("/entries", response_model=EntryListResponse)
async def list_entries(
    limit: int = Query(10, ge=1, le=100, description="Maximum entries to return"),
    start_date: Optional[str] = Query(None, description="Filter: start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter: end date (YYYY-MM-DD)")
):
    """
    List diary entries with optional filters.
    
    Returns entries ordered by date descending (most recent first).
    """
    repo = get_repository()
    
    if start_date and end_date:
        entries = repo.list_entries_between_dates(start_date, end_date)
        entries = entries[:limit]
    else:
        entries = repo.list_recent_entries(limit)
    
    return EntryListResponse(
        entries=[
            EntryResponse(
                id=e.id,
                date=e.date,
                raw_text=e.raw_text,
                narrative_text=e.narrative_text,
                title=e.title,
                conflict_data=e.conflict_data.to_dict() if e.conflict_data else None
            )
            for e in entries
        ],
        total=len(entries)
    )


@app.get("/entries/{entry_id}", response_model=EntryResponse)
async def get_entry(entry_id: int):
    """
    Get a single entry by ID.
    """
    repo = get_repository()
    entry = repo.get_entry_by_id(entry_id)
    
    if not entry:
        raise HTTPException(status_code=404, detail=f"Entry {entry_id} not found")
    
    return EntryResponse(
        id=entry.id,
        date=entry.date,
        raw_text=entry.raw_text,
        narrative_text=entry.narrative_text,
        title=entry.title
    )


@app.post("/entries/{entry_id}/regenerate", response_model=EntryResponse)
async def regenerate_entry(entry_id: int):
    """
    Regenerate AI content (narrative and title) for an entry.
    
    Requires Ollama to be available.
    """
    repo = get_repository()
    entry = repo.get_entry_by_id(entry_id)
    
    if not entry:
        raise HTTPException(status_code=404, detail=f"Entry {entry_id} not found")
    
    if not is_ollama_available():
        raise HTTPException(status_code=503, detail="Ollama is not available")
    
    # Clear and regenerate
    entry.narrative_text = None
    entry.title = None
    process_entry(entry)
    
    repo.update_entry(entry)
    
    return EntryResponse(
        id=entry.id,
        date=entry.date,
        raw_text=entry.raw_text,
        narrative_text=entry.narrative_text,
        title=entry.title
    )


@app.delete("/entries/{entry_id}", status_code=204)
async def delete_entry(entry_id: int):
    """
    Delete an entry by ID.
    """
    repo = get_repository()
    deleted = repo.delete_entry(entry_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Entry {entry_id} not found")


@app.post("/export/weekly", response_model=ExportResponse)
async def export_weekly_summary():
    """
    Export entries from the last 7 days to a Markdown file.
    """
    filepath = export_weekly()
    
    if filepath:
        return ExportResponse(
            success=True,
            filepath=filepath,
            message="Weekly export created successfully"
        )
    
    return ExportResponse(
        success=False,
        message="No entries found for weekly export"
    )


@app.post("/export/{entry_id}", response_model=ExportResponse)
async def export_entry(entry_id: int):
    """
    Export a single entry to a Markdown file.
    """
    repo = get_repository()
    entry = repo.get_entry_by_id(entry_id)
    
    if not entry:
        raise HTTPException(status_code=404, detail=f"Entry {entry_id} not found")
    
    filepath = export_entry_to_markdown(entry)
    
    return ExportResponse(
        success=True,
        filepath=filepath,
        message="Entry exported successfully"
    )


# =============================================================================
# Run configuration
# =============================================================================

def run_dev_server(host: str = "127.0.0.1", port: int = 8000):
    """Run the development server using uvicorn."""
    import uvicorn
    uvicorn.run(
        "chronicle_ai.api:app",
        host=host,
        port=port,
        reload=True
    )


if __name__ == "__main__":
    run_dev_server()
