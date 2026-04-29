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
from .clustering import memory_clusterer
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
    logline: Optional[str] = None
    synopsis: Optional[str] = None
    keywords: List[str] = []
    conflict_data: Optional[dict] = None
    season_id: Optional[int] = None
    cover_art_path: Optional[str] = None
    image_variants: dict = {}
    mood: Optional[str] = None
    style: Optional[str] = None
    characters: List[str] = []
    locations: List[str] = []
    audio_path: Optional[str] = None
    audio_duration: Optional[float] = None
    
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


class SearchResultResponse(BaseModel):
    """Response schema for a single search result."""
    episode_id: str
    section: str
    text_snippet: str
    highlighted_text: str
    similarity_score: float
    date: str
    mood: Optional[str] = None
    metadata: dict


class SearchListResponse(BaseModel):
    """Response schema for search results."""
    query: str
    results: List[SearchResultResponse]
    limit: int


class ExportResponse(BaseModel):
    """Response schema for export operations."""
    success: bool
    filepath: Optional[str] = None
    message: str


class SeasonResponse(BaseModel):
    """Response schema for a season."""
    id: int
    title: str
    start_date: str
    end_date: str
    episode_count: int
    dominant_themes: List[str] = []
    description: Optional[str] = None
    poster_path: Optional[str] = None
    
    class Config:
        from_attributes = True


class SeasonListResponse(BaseModel):
    """Response schema for season list."""
    seasons: List[SeasonResponse]


class MemoryChatQuestion(BaseModel):
    """Request body for memory chat."""
    question: str


class MemoryChatResponse(BaseModel):
    """Response schema for memory chat."""
    answer: str
    sources: List[SearchResultResponse]


class ArcMilestoneResponse(BaseModel):
    """Response schema for a single arc milestone."""
    episode_id: int
    date: str
    title: str
    description: str


class ArcSummaryResponse(BaseModel):
    """Response schema for a full topic story arc."""
    topic: str
    time_range: str
    narrative: str
    milestones: List[ArcMilestoneResponse]
    progression_score: float


class SimilarityResponse(BaseModel):
    """Response schema for a similar episode."""
    episode_id: int
    title: str
    similarity_score: float
    date: str
    themes: str
    explanation: Optional[str] = None


class EpisodeSimilarityListResponse(BaseModel):
    """Response schema for list of similar/opposite episodes."""
    reference_id: int
    mode: str
    results: List[SimilarityResponse]


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

# Serve data files (images)
data_path = Path(__file__).parent.parent.parent / "data"
if data_path.exists():
    app.mount("/data", StaticFiles(directory=str(data_path)), name="data")

# Serve exports (audio)
exports_path = Path(__file__).parent.parent.parent / "exports"
if exports_path.exists():
    app.mount("/exports", StaticFiles(directory=str(exports_path)), name="exports")


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
        title=entry.title,
        logline=entry.logline,
        synopsis=entry.synopsis,
        keywords=entry.keywords,
        characters=entry.characters,
        locations=entry.locations,
        cover_art_path=entry.cover_art_path,
        image_variants=entry.image_variants,
        mood=entry.mood,
        audio_path=entry.audio_path,
        audio_duration=entry.audio_duration
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
        title=entry.title,
        logline=entry.logline,
        synopsis=entry.synopsis,
        keywords=entry.keywords,
        characters=entry.characters,
        locations=entry.locations,
        cover_art_path=entry.cover_art_path,
        image_variants=entry.image_variants,
        mood=entry.mood,
        audio_path=entry.audio_path,
        audio_duration=entry.audio_duration
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
                logline=e.logline,
                synopsis=e.synopsis,
                keywords=e.keywords,
                characters=e.characters,
                locations=e.locations,
                conflict_data=e.conflict_data.to_dict() if e.conflict_data else None,
                cover_art_path=e.cover_art_path,
                image_variants=e.image_variants,
                mood=e.mood,
                audio_path=e.audio_path,
                audio_duration=e.audio_duration
            )
            for e in entries
        ],
        total=len(entries)
    )


@app.get("/search", response_model=SearchListResponse)
async def search_episodes(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=50),
    season: Optional[int] = Query(None),
    mood: Optional[str] = Query(None),
    themes: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """
    Perform semantic search across all episodes.
    
    Supports filtering by season, mood, themes, and date range.
    """
    from .semantic_search import get_semantic_search
    
    search_engine = get_semantic_search()
    
    filters = {}
    if start_date or end_date:
        filters["date_range"] = [start_date, end_date]
    if season is not None:
        filters["season"] = season
    if mood:
        filters["mood"] = mood
    if themes:
        filters["themes"] = themes
        
    results = search_engine.search(q, limit=limit, filters=filters)
    
    return SearchListResponse(
        query=q,
        results=[SearchResultResponse(**res) for res in results],
        limit=limit
    )

@app.post("/ask", response_model=MemoryChatResponse)
async def ask_memory(body: MemoryChatQuestion):
    """
    Ask a natural language question about the user's history.
    """
    from .memory_chat import get_memory_chat
    
    chat = get_memory_chat()
    response = chat.ask(body.question)
    
    formatted_sources = []
    for src in response.sources:
        formatted_sources.append(SearchResultResponse(**src))
        
    return MemoryChatResponse(
        answer=response.answer,
        sources=formatted_sources
    )


@app.get("/arc", response_model=ArcSummaryResponse)
async def get_story_arc(
    topic: str = Query(..., description="The topic to analyze (e.g., 'career', 'fitness')"),
    time_range: str = Query("all time", description="Time period for analysis")
):
    """
    Generate a narrative arc analysis for a specific topic across records.
    
    Identifies progression, milestones, and provides a synthesized narrative.
    """
    from .arc_analyzer import get_story_arc_analyzer
    
    analyzer = get_story_arc_analyzer()
    arc = analyzer.get_arc(topic, time_range)
    
    return ArcSummaryResponse(
        topic=arc.topic,
        time_range=arc.time_range,
        narrative=arc.narrative,
        milestones=[ArcMilestoneResponse(**m.to_dict()) for m in arc.milestones],
        progression_score=arc.progression_score
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
        title=entry.title,
        logline=entry.logline,
        synopsis=entry.synopsis,
        keywords=entry.keywords,
        characters=entry.characters,
        locations=entry.locations,
        cover_art_path=entry.cover_art_path,
        image_variants=entry.image_variants,
        mood=entry.mood,
        audio_path=entry.audio_path,
        audio_duration=entry.audio_duration
    )


@app.get("/entries/{entry_id}/connections")
async def get_entry_connections(entry_id: int):
    """
    Find internal connections for an episode (recurring characters, locations, etc).
    """
    connections = connection_finder.find_connections(entry_id)
    return {"episode_id": entry_id, "connections": connections}


@app.get("/episodes/{episode_id}/similar", response_model=EpisodeSimilarityListResponse)
async def get_similar_episodes(
    episode_id: int,
    limit: int = Query(5, ge=1, le=10),
    mode: str = Query("similar", regex="^(similar|opposite)$"),
    explain: bool = Query(True, description="Generate thematic explanation for matches")
):
    """
    Find episodes similar or opposite to a selected one.
    
    Excludes episodes from the same week to avoid temporal similarity bias.
    """
    from .semantic_search import get_semantic_search
    from .llm_client import explain_similarity
    
    repo = get_repository()
    ref_episode = repo.get_entry_by_id(episode_id)
    if not ref_episode:
        raise HTTPException(status_code=404, detail=f"Episode {episode_id} not found")
        
    search_engine = get_semantic_search()
    
    if mode == "similar":
        results = search_engine.find_similar_episodes(episode_id, limit=limit)
    else:
        results = search_engine.find_opposite_episodes(episode_id, limit=limit)
        
    # Generate explanations if requested and it's 'similar' mode
    final_results = []
    for res in results:
        explanation = None
        if explain and mode == "similar":
            match_ep = repo.get_entry_by_id(res["episode_id"])
            if match_ep:
                explanation = explain_similarity(ref_episode, match_ep)
        
        final_results.append(SimilarityResponse(
            episode_id=res["episode_id"],
            title=res["title"],
            similarity_score=res["similarity_score"],
            date=res["date"],
            themes=res["themes"],
            explanation=explanation
        ))
        
    return EpisodeSimilarityListResponse(
        reference_id=episode_id,
        mode=mode,
        results=final_results
    )


@app.get("/clusters/map")
async def get_cluster_map():
    """Get the text-based cluster map data."""
    return memory_clusterer.get_cluster_map()


@app.get("/clusters/view/{cluster_name}")
async def get_cluster_episodes(cluster_name: str):
    """Get all episodes in a specific cluster."""
    repo = get_repository()
    all_entries = repo.list_entries()
    filtered = [e for e in all_entries if e.cluster_label and e.cluster_label.lower() == cluster_name.lower()]
    return filtered


@app.post("/clusters/refresh")
async def refresh_clusters(k: int = Query(12)):
    """Re-run the clustering algorithm and update all entries."""
    if not is_ollama_available():
        raise HTTPException(status_code=503, detail="Ollama is not available for cluster naming")
    clusters = memory_clusterer.cluster_episodes(k=k)
    return {"status": "success", "cluster_count": len(clusters)}


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
    entry.characters = []
    entry.locations = []
    process_entry(entry)
    
    repo.update_entry(entry)
    
    return EntryResponse(
        id=entry.id,
        date=entry.date,
        raw_text=entry.raw_text,
        narrative_text=entry.narrative_text,
        title=entry.title,
        logline=entry.logline,
        synopsis=entry.synopsis,
        keywords=entry.keywords,
        characters=entry.characters,
        locations=entry.locations,
        cover_art_path=entry.cover_art_path,
        image_variants=entry.image_variants,
        mood=entry.mood,
        audio_path=entry.audio_path,
        audio_duration=entry.audio_duration
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


@app.get("/gallery", response_model=EntryListResponse)
async def get_gallery(
    season: Optional[int] = Query(None, description="Filter by season ID"),
    mood: Optional[str] = Query(None, description="Filter by mood"),
    style: Optional[str] = Query(None, description="Filter by style"),
    start_date: Optional[str] = Query(None, description="Filter: start date"),
    end_date: Optional[str] = Query(None, description="Filter: end date"),
    sort_by: str = Query("date", description="Sort by: date, mood, generation_date"),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Get image gallery with filters and sorting.
    """
    repo = get_repository()
    entries = repo.search_gallery(
        season_id=season,
        mood=mood,
        style=style,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        limit=limit
    )
    
    return EntryListResponse(
        entries=[
            EntryResponse(
                id=e.id,
                date=e.date,
                raw_text=e.raw_text,
                narrative_text=e.narrative_text,
                title=e.title,
                logline=e.logline,
                synopsis=e.synopsis,
                keywords=e.keywords,
                characters=e.characters,
                locations=e.locations,
                season_id=e.season_id,
                cover_art_path=e.cover_art_path,
                image_variants=e.image_variants,
                mood=e.mood,
                style=e.style,
                audio_path=e.audio_path,
                audio_duration=e.audio_duration
            )
            for e in entries
        ],
        total=len(entries)
    )


@app.get("/gallery/{season_id}", response_model=EntryListResponse)
async def get_season_gallery(season_id: int, limit: int = 50):
    """
    Get image gallery for a specific season.
    """
    repo = get_repository()
    entries = repo.search_gallery(season_id=season_id, limit=limit)
    
    return EntryListResponse(
        entries=[
            EntryResponse(
                id=e.id,
                date=e.date,
                raw_text=e.raw_text,
                narrative_text=e.narrative_text,
                title=e.title,
                logline=e.logline,
                synopsis=e.synopsis,
                keywords=e.keywords,
                characters=e.characters,
                locations=e.locations,
                season_id=e.season_id,
                cover_art_path=e.cover_art_path,
                image_variants=e.image_variants,
                mood=e.mood,
                style=e.style,
                audio_path=e.audio_path,
                audio_duration=e.audio_duration
            )
            for e in entries
        ],
        total=len(entries)
    )


@app.get("/seasons", response_model=SeasonListResponse)
async def list_seasons():
    """
    List all seasons.
    """
    repo = get_repository()
    seasons = repo.list_seasons()
    
    return SeasonListResponse(
        seasons=[
            SeasonResponse(
                id=s.id,
                title=s.title,
                start_date=s.start_date,
                end_date=s.end_date,
                episode_count=s.episode_count,
                dominant_themes=s.dominant_themes,
                description=s.description,
                poster_path=s.poster_path
            )
            for s in seasons
        ]
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
