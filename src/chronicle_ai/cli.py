"""
Chronicle AI - Command Line Interface

Full-featured CLI for diary management with guided input, AI processing, and exports.
"""

import argparse
import sys
from datetime import date

from .models import Entry
from .repository import get_repository
from .llm_client import process_entry, is_ollama_available
from .recap import RecapGenerator
from .exports import export_entry_to_markdown, export_weekly, export_daily
from .season_manager import SeasonManager
from .director import director_engine
from .cover_gen import cover_generator
from .poster_gen import poster_generator

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn


# Guided mode questions
GUIDED_QUESTIONS = [
    ("🌅 How was your morning?", "morning"),
    ("☀️ What happened in the afternoon?", "afternoon"),
    ("🌙 How did your day end?", "evening"),
    ("💭 Any notable thoughts or reflections?", "thoughts"),
    ("😊 How was your overall mood today?", "mood"),
]


def cmd_add(args):
    """Handle the 'add' command - create a quick entry."""
    repo = get_repository()
    
    entry_date = args.date or date.today().isoformat()
    entry = Entry(
        date=entry_date,
        raw_text=args.text
    )
    
    print(f"✨ Creating entry for {entry_date}...")
    
    if not args.skip_ai:
        print("🤖 Generating narrative and title with Ollama...")
        if is_ollama_available():
            # If recap is requested, generate it first
            if getattr(args, 'with_recap', False):
                print("📺 Generating 'Previously on Chronicle...' recap...")
                generator = RecapGenerator(repo)
                recap = generator.get_recap_for_days(args.recap_days or 7)
                repo.create_recap(recap)
                entry.recap_id = recap.id
                print(f"🎬 Recap generated: {recap.id}")
                
                # Prepend recap to narrative (this will be handled after process_entry if we want it preserved)
                # Or we can pass it to process_entry?
            
            process_entry(entry)
            
            # Prepend recap content if it exists
            if entry.recap_id:
                recap = repo.get_recap_by_id(entry.recap_id)
                if recap and recap.content:
                    entry.narrative_text = f"{recap.content}\n\n{entry.narrative_text}"
            
            print(f"📝 Title: {entry.title}")
        else:
            print("⚠️  Ollama not available, saving raw text only")
    
    repo.create_entry(entry)
    print(f"✅ Entry saved successfully! (ID: {entry.id})")


def cmd_guided(args):
    """Handle the 'guided' command - interactive Q&A entry."""
    repo = get_repository()
    entry_date = args.date or date.today().isoformat()
    
    print(f"\n🎬 Chronicle AI - Guided Entry for {entry_date}")
    print("=" * 50)
    print("Answer the following questions about your day.")
    print("Press Enter to skip any question.\n")
    
    responses = []
    
    for question, key in GUIDED_QUESTIONS:
        try:
            answer = input(f"{question}\n> ").strip()
            if answer:
                responses.append(f"{key.title()}: {answer}")
        except (EOFError, KeyboardInterrupt):
            print("\n\n❌ Entry cancelled.")
            return
    
    if not responses:
        print("\n⚠️  No responses provided. Entry not saved.")
        return
    
    # Combine responses into raw text
    raw_text = "\n\n".join(responses)
    
    print("\n" + "=" * 50)
    print("📋 Your entry preview:\n")
    print(raw_text)
    print("\n" + "=" * 50)
    
    try:
        confirm = input("\n💾 Save this entry? (Y/n): ").strip().lower()
        if confirm == 'n':
            print("❌ Entry not saved.")
            return
    except (EOFError, KeyboardInterrupt):
        print("\n❌ Entry cancelled.")
        return
    
    entry = Entry(
        date=entry_date,
        raw_text=raw_text
    )
    
    if not args.skip_ai:
        print("\n🤖 Generating narrative and title with Ollama...")
        if is_ollama_available():
            # If recap is requested, generate it first
            if args.with_recap:
                print("📺 Generating 'Previously on Chronicle...' recap...")
                generator = RecapGenerator(repo)
                recap = generator.get_recap_for_days(args.recap_days or 7)
                repo.create_recap(recap)
                entry.recap_id = recap.id
            
            process_entry(entry)
            
            # Prepend recap content if it exists
            if entry.recap_id:
                recap = repo.get_recap_by_id(entry.recap_id)
                if recap and recap.content:
                    entry.narrative_text = f"{recap.content}\n\n{entry.narrative_text}"
            
            print(f"\n📖 Generated Narrative:\n{entry.narrative_text}\n")
            print(f"🎬 Episode Title: {entry.title}")
        else:
            print("⚠️  Ollama not available, saving raw text only")
    
    repo.create_entry(entry)
    print(f"\n✅ Entry saved successfully! (ID: {entry.id})")


def cmd_list(args):
    """Handle the 'list' command - show recent entries."""
    repo = get_repository()
    
    limit = args.limit or 10
    entries = repo.list_recent_entries(limit)
    
    if not entries:
        print("📭 No entries found.")
        return
    
    print(f"\n🎬 Chronicle AI - Recent Episodes ({len(entries)} entries)")
    print("=" * 60)
    
    for entry in entries:
        title = entry.display_title()
        snippet = entry.snippet(80)
        
        print(f"\n📅 [{entry.date}] ID: {entry.id}")
        if entry.is_placeholder:
            print(f"   🖼️  [bold yellow][PLACEHOLDER IMAGE][/bold yellow]")
        print(f"   🎬 {title}")
        if entry.logline:
            print(f"   💡 {entry.logline}")
        if entry.keywords:
            print(f"   🏷️  {', '.join(entry.keywords)}")
        print(f"   📝 {snippet}")
    
    print("\n" + "=" * 60)


def cmd_view(args):
    """Handle the 'view' command - show a single entry."""
    repo = get_repository()
    
    entry = repo.get_entry_by_id(args.id)
    
    if not entry:
        print(f"❌ Entry with ID {args.id} not found.")
        return
    
    pattern = "N/A"
    if entry.title_options and entry.title:
        for opt in entry.title_options:
            if opt.get('title') == entry.title:
                pattern = opt.get('pattern', 'N/A')
                break

    print(f"\n🎬 {entry.display_title()}")
    print(f"🎭 Pattern: {pattern}")
    print("=" * 60)
    print(f"📅 Date: {entry.date}")
    print(f"🆔 ID: {entry.id}")
    print()
    
    if entry.narrative_text:
        print("📖 Narrative:")
        print("-" * 40)
        print(entry.narrative_text)
        print()
    
    if entry.logline:
        print(f"💡 Logline: {entry.logline}")
    if entry.keywords:
        print(f"🏷️ Keywords: {', '.join(entry.keywords)}")
    if entry.synopsis:
        print(f"\n📝 Synopsis:\n{entry.synopsis}")
        print()
    
    if entry.conflict_data:
        print("⚡ Conflict Analysis:")
        print("-" * 40)
        cd = entry.conflict_data
        print(f"   🏆 Central: {cd.central_conflict}")
        print(f"   🎭 Archetype: {cd.archetype}")
        print(f"   📈 Tension: {'🔥' * cd.tension_level} ({cd.tension_level}/10)")
        if cd.internal_conflicts:
            print(f"   🧠 Internal: {', '.join(cd.internal_conflicts)}")
        if cd.external_conflicts:
            print(f"   🌍 External: {', '.join(cd.external_conflicts)}")
        print()
    
    print("📝 Original Entry:")
    print("-" * 40)
    print(entry.raw_text)
    print("\n" + "=" * 60)


def cmd_export(args):
    """Handle the 'export' command - generate Markdown files."""
    if args.weekly:
        print("📚 Exporting weekly summary...")
        filepath = export_weekly()
        if filepath:
            print(f"✅ Weekly export saved to: {filepath}")
        else:
            print("⚠️  No entries found for weekly export.")
    elif args.date:
        print(f"📝 Exporting entry for {args.date}...")
        filepath = export_daily(args.date)
        if filepath:
            print(f"✅ Daily export saved to: {filepath}")
        else:
            print(f"⚠️  No entries found for {args.date}.")
    elif args.id:
        repo = get_repository()
        entry = repo.get_entry_by_id(args.id)
        if entry:
            filepath = export_entry_to_markdown(entry)
            print(f"✅ Entry exported to: {filepath}")
        else:
            print(f"❌ Entry with ID {args.id} not found.")
    else:
        print("📚 Exporting all entries...")
        from .exports import export_all_entries
        files = export_all_entries()
        print(f"✅ Exported {len(files)} entries.")


    print(f"\n✅ Entry updated successfully!")


def cmd_regenerate(args):
    """Handle the 'regenerate' command - re-generate AI content for an entry."""
    repo = get_repository()
    
    entry = repo.get_entry_by_id(args.id)
    if not entry:
        print(f"❌ Entry with ID {args.id} not found.")
        return
    
    print(f"🔄 Regenerating AI content for entry {args.id}...")
    
    if not is_ollama_available():
        print("❌ Ollama is not available. Cannot regenerate.")
        return
    
    # Clear existing and regenerate
    entry.narrative_text = None
    entry.title = None
    process_entry(entry)
    
    repo.update_entry(entry)
    
    print(f"\n🎬 New Title: {entry.title}")
    print(f"\n📖 New Narrative:\n{entry.narrative_text}")
    print(f"\n✅ Entry updated successfully!")


def cmd_recap(args):
    """Handle the 'recap' command - generate a standalone recap."""
    repo = get_repository()
    generator = RecapGenerator(repo)
    
    days = args.days or 7
    print(f"📺 Generating 'Previously on Chronicle...' recap for the last {days} days...")
    
    if not is_ollama_available():
        print("❌ Ollama is not available. Cannot generate recap.")
        return
    
    recap = generator.get_recap_for_days(days)
    repo.create_recap(recap)
    
    print("\n" + "=" * 60)
    print(recap.content)
    print("=" * 60)
    print(f"✅ Recap generated and saved! (ID: {recap.id})")
    print(f"🔗 Linked to {len(recap.entry_ids)} episodes from the last {days} days.")


def cmd_retitle(args):
    """Handle the 'retitle' command - explore and pick new titles."""
    repo = get_repository()
    entry = repo.get_entry_by_id(args.episode)
    
    if not entry:
        print(f"❌ Episode {args.episode} not found.")
        return
    
    print(f"🎬 Retitling Episode {args.episode}: {entry.display_title()}")
    
    if not entry.title_options:
        print("🤖 No existing options found. Generating 5 new options...")
        if not is_ollama_available():
            print("❌ Ollama not available.")
            return
        from .llm_client import generate_title_options
        entry.title_options = generate_title_options(entry.narrative_text or entry.raw_text)
        repo.update_entry(entry)
    
    options = entry.title_options
    
    if args.pick:
        print("\nChoose a new title for this episode:")
        for idx, opt in enumerate(options, 1):
            pattern = opt.get('pattern', 'N/A')
            score = opt.get('score', 0)
            print(f"{idx}. {opt['title']} [{pattern}] (Score: {score:.2f})")
        
        try:
            choice = input(f"\nSelect option (1-{len(options)}) or 'q' to quit: ").strip().lower()
            if choice == 'q':
                return
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                entry.title = options[idx]['title']
                repo.update_entry(entry)
                print(f"✅ Title updated to: {entry.title}")
            else:
                print("❌ Invalid selection.")
        except (ValueError, IndexError, EOFError, KeyboardInterrupt):
            print("\n❌ Cancelled or invalid input.")
    else:
        print("\nAvailable Title Options:")
        for opt in options:
            pattern = opt.get('pattern', 'N/A')
            score = opt.get('score', 0)
            print(f"- {opt['title']} [{pattern}] (Score: {score:.2f})")


def cmd_visual_prompt(args):
    """Handle the 'visual-prompt' command - generate SD prompts for an episode."""
    repo = get_repository()
    entry = repo.get_entry_by_id(args.id)
    
    if not entry:
        print(f"❌ Entry with ID {args.id} not found.")
        return
    
    print(f"🎨 Generating Visual Prompt for Episode {args.id}...")
    
    from .visual_prompts import mood_to_visual
    style = repo.get_setting("visual_style", "cinematic")
    positive, negative, preset = mood_to_visual.generate_cover_prompt(entry, style_name=style)
    
    print("\n" + "=" * 60)
    print(f"🎬 Title: {entry.display_title()}")
    print("=" * 60)
    print("\n✅ Positive Prompt (SD-Optimized):")
    print("-" * 40)
    print(positive)
    print("\n❌ Negative Prompt:")
    print("-" * 40)
    print(negative)
    print(f"\n⚙️  Style Settings ({preset['name']}):")
    print(f"   Sampler: {preset['sampler']}")
    print(f"   Steps: {preset['steps']}")
    print("\n" + "=" * 60)
            
            
def cmd_regen_cover(args):
    """Handle the 'regen-cover' command."""
    from rich.console import Console
    console = Console()
    repo = get_repository()
    
    style = getattr(args, "style", None)
    variations = getattr(args, "variations", 1)
    prompt_override = getattr(args, "prompt", None)
    
    episode_ids = []
    if getattr(args, "season", None):
        season = repo.get_season_by_id(args.season)
        if not season:
            console.print(f"[bold red]❌ Season {args.season} not found.[/bold red]")
            return
        entries = repo.list_entries_between_dates(season.start_date, season.end_date)
        episode_ids = [e.id for e in entries if e.season_id == args.season]
        console.print(f"[cyan]🎬 Found {len(episode_ids)} episodes in Season {args.season}. Regenerating covers...[/cyan]")
    elif getattr(args, "episode", None):
        episode_ids = [args.episode]
    else:
        console.print("[bold red]❌ Either --episode or --season is required.[/bold red]")
        return

    for ep_id in episode_ids:
        console.print(f"\n[bold cyan]🎨 Regenerating Cover for Episode {ep_id}[/bold cyan]")
        if style: console.print(f"   🎭 Style: {style}")
        if variations > 1: console.print(f"   🔢 Variations: {variations}")
        if prompt_override: console.print(f"   ✍️  Prompt: {prompt_override}")
        
        paths = cover_generator.generate_cover(
            ep_id, 
            regenerate=True, 
            style_name=style, 
            prompt_override=prompt_override,
            variations=variations
        )
        
        if paths:
            console.print(f"   [bold green]✅ Success![/bold green] Generated {len(paths)} variants.")
            for p in paths:
                console.print(f"      📍 {p}")
        else:
            console.print(f"   [bold red]❌ Failed for episode {ep_id}[/bold red]")

def cmd_covers(args):
    """Handle the 'covers' command - view history and select."""
    from rich.console import Console
    from rich.table import Table
    console = Console()
    repo = get_repository()
    
    episode_id = args.episode
    episode = repo.get_entry_by_id(episode_id)
    
    if not episode:
        console.print(f"[bold red]❌ Episode {episode_id} not found.[/bold red]")
        return

    if args.history:
        if not episode.cover_history:
            console.print(f"[yellow]📭 No cover history for Episode {episode_id}.[/yellow]")
        else:
            console.print(f"\n[bold cyan]🖼️  Cover History for Episode {episode_id}: {episode.display_title()}[/bold cyan]")
            
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Idx", style="dim", width=4)
            table.add_column("Date", width=20)
            table.add_column("Style", width=12)
            table.add_column("Prompt Snippet")
            
            # Show current first (not in history list usually, or at top)
            table.add_row("ACT", "CURRENT", repo.get_setting("visual_style", "cinematic"), episode.image_variants.get("prompt", "N/A")[:50] + "...")
            
            for i, h in enumerate(episode.cover_history):
                prompt = h.get("prompt", "N/A")
                if len(prompt) > 50: prompt = prompt[:47] + "..."
                table.add_row(str(i), h.get("date", "N/A"), h.get("style", "N/A"), prompt)
            
            console.print(table)
            
            console.print("\n[dim]To select a version: chronicle covers --episode ID --select INDEX[/dim]")

    if args.select is not None:
        idx = args.select
        console.print(f"🔄 Selecting cover variant {idx} for Episode {episode_id}...")
        if cover_generator.select_cover(episode_id, idx):
            console.print("[bold green]✅ Cover updated successfully![/bold green]")
        else:
            console.print(f"[bold red]❌ Failed to select variant {idx}. Check index.[/bold red]")

def cmd_generate_cover(args):
    """Bridge to regen-cover for backward compatibility or direct use."""
    cmd_regen_cover(args)


def cmd_generate_poster(args):
    """Handle the 'generate-poster' command."""
    from rich.console import Console
    console = Console()
    repo = get_repository()
    
    regenerate = getattr(args, "regenerate", False)
    variants = ["dramatic", "minimalist", "artistic"]
    
    if args.season:
        # Generate for a specific season
        season_ids = [args.season]
    else:
        # Generate for all existing seasons
        seasons = repo.list_seasons()
        season_ids = [s.id for s in seasons]
        console.print(f"[cyan]🎬 Found {len(season_ids)} existing seasons. Generating posters...[/cyan]")

    for season_id in season_ids:
        season = repo.get_season_by_id(season_id)
        if not season:
            console.print(f"[red]❌ Season {season_id} not found.[/red]")
            continue
            
        console.print(f"\n[bold cyan]🖼️  Generating Season Posters for: {season.title} (ID: {season_id})[/bold cyan]")
        
        for variant in variants:
            console.print(f"🎨 Variant: [bold]{variant}[/bold]...")
            path = poster_generator.generate_poster(season_id, variant=variant, regenerate=regenerate)
            if path:
                console.print(f"   [green]✅ Saved to: {path}[/green]")
            else:
                console.print(f"   [red]❌ Failed to generate {variant} poster.[/red]")

    console.print(f"\n[bold green]✅ Poster generation complete![/bold green]")


def cmd_batch_synopsis(args):
    """Handle 'batch-synopsis' command - generate missing synopsis for all episodes."""
    repo = get_repository()
    entries = repo.list_entries()
    console = Console()
    
    to_process = [e for e in entries if not e.logline or not e.synopsis]
    
    if not to_process:
        console.print("[green]✅ All episodes already have synopsis metadata.[/green]")
        return
        
    console.print(f"[cyan]🤖 Found {len(to_process)} episodes missing synopsis metadata.[/cyan]")
    console.print(f"🔄 Starting batch generation (this may take a while)...")
    
    if not is_ollama_available():
        console.print("[red]❌ Ollama not available.[/red]")
        return

    from .llm_client import ensure_synopsis
    
    success_count = 0
    for i, entry in enumerate(to_process, 1):
        console.print(f"[[bold cyan]{i}/{len(to_process)}[/bold cyan]] Processing Episode {entry.id}: {entry.display_title()}...")
        try:
            ensure_synopsis(entry)
            repo.update_entry(entry)
            success_count += 1
        except Exception as e:
            console.print(f"  [red]❌ Failed: {e}[/red]")
            
    console.print(f"\n[bold green]✅ Batch processing complete! {success_count}/{len(to_process)} episodes updated.[/bold green]")


def cmd_process(args):
    """Handle the 'process' command - batch generate content for a date range."""
    repo = get_repository()
    console = Console()
    
    if not is_ollama_available():
        console.print("[bold red]❌ Ollama is not available. Please start Ollama to process entries.[/bold red]")
        return

    console.print(f"[bold cyan]🎬 Chronicle AI - Batch Processing[/bold cyan]")
    console.print(f"📅 Range: {args.from_date} to {args.to_date}")
    
    # Get entries in range
    entries = repo.list_entries_between_dates(args.from_date, args.to_date)
    
    if not entries:
        console.print("[yellow]📭 No entries found in the specified date range.[/yellow]")
        return

    processed = 0
    failed = 0
    skipped = 0
    
    # Filter entries if not --force (Resume support)
    to_process = []
    for entry in entries:
        # Check if fully processed (has narrative, title, synopsis, and conflict data)
        is_processed = (entry.narrative_text and entry.title and 
                        entry.synopsis and entry.conflict_data)
        
        if is_processed and not args.force:
            skipped += 1
        else:
            to_process.append(entry)
            
    if not to_process:
        console.print(f"[green]✅ All {len(entries)} entries in range are already processed.[/green]")
        console.print(f"📊 Summary: {processed} processed, {failed} failed, {skipped} skipped.")
        return

    console.print(f"🔄 Processing {len(to_process)} entries ({skipped} already processed/skipped)...")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("Generating episodes...", total=len(to_process))
        
        for entry in to_process:
            progress.update(task, description=f"Processing {entry.date} (ID: {entry.id})...")
            try:
                # Fully process narrative, title, synopsis, and conflict
                # This uses the existing logic in llm_client
                process_entry(entry, force=args.force)
                repo.update_entry(entry)
                processed += 1
            except Exception as e:
                console.print(f"[red]❌ Error processing {entry.date} (ID {entry.id}): {str(e)}[/red]")
                failed += 1
            
            progress.advance(task)

    console.print("\n[bold green]🏁 Batch Processing Complete![/bold green]")
    console.print(f"📊 Summary: [bold white]{processed}[/bold white] processed, [bold red]{failed}[/bold red] failed, [bold yellow]{skipped}[/bold yellow] skipped.")


def cmd_seasons(args):
    """Handle the 'seasons' command - list and create seasons."""
    repo = get_repository()
    manager = SeasonManager(repo)
    
    if args.create:
        if args.mode == "manual":
            if not args.start or not args.end or not args.title:
                print("❌ Manual mode requires --start, --end, and --title.")
                return
            print(f"🎬 Creating manual season: {args.title}...")
            manager.create_manual_season(args.title, args.start, args.end)
            print("✅ Season created and episodes linked!")
        else:
            mode = args.mode or "default"
            print(f"🎬 Organizing episodes into seasons (Mode: {mode})...")
            print("🤖 This will analyze narratives and themes to create life chapters.")
            
            manager.organize_seasons(mode=mode, clear_existing=True)
            print("✅ Seasons created and episodes linked successfully!")
        
        # Now list them
        seasons = repo.list_seasons()
    elif args.analyze:
        from .arc_analyzer import SeasonArcAnalyzer
        print(f"🧠 Analyzing season {args.analyze}...")
        print("🤖 Identifying storylines, character growth, and themes...")
        
        analyzer = SeasonArcAnalyzer(repo)
        try:
            arc = analyzer.analyze_season(args.analyze)
            
            print("\n" + "=" * 80)
            print(f"🎬 SEASON SUMMARY: {arc.summary}")
            print("=" * 80)
            
            print(f"\n📈 STORYLINES:")
            for s_type, s_desc in arc.storylines.items():
                print(f"   🏆 {s_type.title()}: {s_desc}")
            
            print(f"\n🌱 CHARACTER GROWTH:")
            print(f"   {arc.character_growth}")
            
            if arc.climax_episode_id:
                climax = repo.get_entry_by_id(arc.climax_episode_id)
                climax_title = climax.display_title() if climax else "Unknown"
                print(f"\n🔥 SEASON CLIMAX: Episode {arc.climax_episode_id} ({climax_title})")
            
            print(f"\n🏷️  MOTIFS & THEMES:")
            print(f"   {', '.join(arc.motifs)}")
            
            if arc.finale_worthy_episodes:
                print(f"\n🎬 FINALE-WORTHY EPISODES:")
                for ep_id in arc.finale_worthy_episodes:
                    ep = repo.get_entry_by_id(ep_id)
                    ep_title = ep.display_title() if ep else f"Episode {ep_id}"
                    print(f"   📺 ID {ep_id}: {ep_title}")
            
            print("\n" + "=" * 80)
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
        return
    elif args.list:
        seasons = repo.list_seasons()
    else:
        # Fallback to list if nothing specified
        seasons = repo.list_seasons()

    if not seasons:
        if args.list:
            print("📭 No seasons found. Run 'chronicle seasons --create' to organize episodes.")
        return

    print(f"\n🎬 Chronicle AI - Life Seasons ({len(seasons)})")
    print("=" * 80)
    
    # Reverse seasons to show chronological order (or descending as per repo.list_seasons which is DESC)
    # Actually repo.list_seasons() returns DESC by start_date.
    for s in seasons:
        print(f"\n🏆 {s.title}")
        print(f"   📅 {s.start_date} to {s.end_date} ({s.episode_count} episodes)")
        if s.description:
            print(f"   📝 {s.description}")
        if s.dominant_themes:
            print(f"   🏷️  Themes: {', '.join(s.dominant_themes)}")
    
    print("\n" + "=" * 80)


def cmd_status(args):
    """Handle the 'status' command - show system status."""
    repo = get_repository()
    entries = repo.list_entries()
    
    print("\n🎬 Chronicle AI Status")
    print("=" * 40)
    print(f"📊 Total entries: {len(entries)}")
    
    # Count entries with AI content
    with_narrative = sum(1 for e in entries if e.narrative_text)
    with_title = sum(1 for e in entries if e.title)
    
    print(f"📖 With narrative: {with_narrative}")
    print(f"🎬 With title: {with_title}")
    print()
    
    # Count placeholders
    placeholders = sum(1 for e in entries if e.is_placeholder)
    needs_retry = sum(1 for e in entries if e.needs_image_retry)
    
    print(f"🖼️  Placeholder images: {placeholders}")
    if needs_retry > 0:
        print(f"🔄 Needing retry: {needs_retry}")
    print()
    
    # Ollama status
    if is_ollama_available():
        print("✅ Ollama: Connected")
    else:
        print("⚠️  Ollama: Not available")
        
    # SD status
    if cover_generator.image_gen.check_health():
        print("✅ Stable Diffusion: Connected")
    else:
        print("⚠️  Stable Diffusion: Not available (using placeholders)")
    
    print("=" * 40)


def cmd_config(args):
    """Handle the 'config' command - manage user settings."""
    repo = get_repository()
    
    if args.style:
        style = args.style.lower()
        from .visual_prompts import VisualStylePresets
        if style in VisualStylePresets.PRESETS:
            repo.set_setting("visual_style", style)
            print(f"✅ Visual style updated to: [bold cyan]{style.upper()}[/bold cyan]")
            print(f"📝 Description: {VisualStylePresets.PRESETS[style]['description']}")
        else:
            print(f"❌ Invalid style: {style}")
            print(f"💡 Available styles: {', '.join(VisualStylePresets.PRESETS.keys())}")
    else:
        # Show current config
        style = repo.get_setting("visual_style", "cinematic")
        print("\n🎬 Chronicle AI Configuration")
        print("=" * 40)
        print(f"🎨 Active Visual Style: {style.upper()}")
        print("=" * 40)


def cmd_gallery(args):
    """Handle the 'gallery' command - view or export image gallery."""
    repo = get_repository()
    console = Console()
    
    # Search for entries with images
    entries = repo.search_gallery(
        season_id=args.season,
        mood=args.mood,
        style=args.style,
        start_date=args.start,
        end_date=args.end,
        sort_by=args.sort,
        limit=args.limit or 50
    )
    
    if not entries:
        console.print("[yellow]📭 No images found matching the filters.[/yellow]")
        return

    if args.export:
        from .exports import export_gallery_html
        console.print(f"🎨 Exporting gallery to [bold]{args.export}[/bold]...")
        filepath = export_gallery_html(entries, output_path=args.export)
        console.print(f"✅ Gallery exported successfully to: [green]{filepath}[/green]")
        return


def cmd_retry_images(args):
    """Handle the 'retry-images' command - regenerate all placeholders."""
    repo = get_repository()
    console = Console()
    
    entries = repo.list_entries()
    to_retry = [e for e in entries if e.needs_image_retry]
    
    if not to_retry:
        console.print("[green]✅ No images need retry (no placeholder images found with retry flag).[/green]")
        return
        
    console.print(f"[cyan]🔄 Found {len(to_retry)} episodes with placeholder images to regenerate.[/cyan]")
    
    # Check if SD is available before starting
    if not cover_generator.image_gen.check_health():
        console.print("[bold red]❌ Stable Diffusion is still unavailable. Please start it before retrying.[/bold red]")
        return

    success_count = 0
    for i, entry in enumerate(to_retry, 1):
        console.print(f"[[bold cyan]{i}/{len(to_retry)}[/bold cyan]] Regenerating Episode {entry.id}: {entry.display_title()}...")
        try:
            paths = cover_generator.generate_cover(entry.id, regenerate=True)
            # Fetch fresh state to check if it's still a placeholder
            updated_entry = repo.get_entry_by_id(entry.id)
            if paths and not updated_entry.is_placeholder:
                success_count += 1
                console.print(f"  [green]✅ Success![/green]")
            else:
                console.print(f"  [yellow]⚠️  Generated another placeholder.[/yellow]")
        except Exception as e:
            console.print(f"  [red]❌ Failed: {e}[/red]")
            
    console.print(f"\n[bold green]✅ Retry complete! {success_count}/{len(to_retry)} episodes successfully upgraded from placeholders.[/bold green]")

    # CLI View
    console.print(f"\n[bold cyan]🖼️  Chronicle Image Gallery ({len(entries)} items)[/bold cyan]")
    console.print("=" * 80)
    
    from rich.table import Table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Date", width=12)
    table.add_column("Title", width=30)
    table.add_column("Mood", width=12)
    table.add_column("Style", width=12)
    table.add_column("Image Path")
    
    for e in entries:
        table.add_row(
            e.date,
            e.title or "Untitled",
            e.mood or "N/A",
            e.style or "N/A",
            e.cover_art_path or "N/A"
        )
    
    console.print(table)
    console.print("\n[dim]Tip: Use --export gallery.html for a beautiful standalone page.[/dim]")
    console.print("=" * 80)


def cmd_benchmark(args):
    """Handle the 'benchmark' command - run a full pipeline benchmark."""
    repo = get_repository()
    console = Console()
    
    console.print(f"\n[bold cyan]🎬 Chronicle AI - Director Engine Benchmark[/bold cyan]")
    console.print("=" * 60)
    
    # 1. Prepare sample entries
    console.print("🧪 Preparing 10 sample entries...")
    samples = []
    
    # Try to grab 10 recent entries
    recent = repo.list_recent_entries(10)
    if len(recent) < 10:
        console.print(f"⚠️  Only found {len(recent)} entries in database. Creating dummy entries for benchmark...")
        # Create some dummy entries for testing if needed, or just use what we have
        samples = recent
        for i in range(10 - len(recent)):
            samples.append(Entry(
                date=f"2024-01-{i+1:02d}",
                raw_text=f"Benchmark entry {i+1}: Today was a productive day. I worked on the new benchmark suite and optimized the LLM client. It felt good to see the performance improvements."
            ))
    else:
        samples = recent[:10]
        
    # 2. Run benchmark
    console.print(f"🚀 Processing {len(samples)} entries...")
    
    if not is_ollama_available():
        console.print("[bold red]❌ Ollama is not available. Benchmark results will reflect fallback performance.[/bold red]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("Running benchmark...", total=len(samples))
        
        results = director_engine.run_benchmark(samples)
        progress.update(task, completed=len(samples))

    # 3. Report metrics
    console.print("\n[bold green]📊 Benchmark Report[/bold green]")
    console.print("-" * 30)
    console.print(f"Total Duration: {results['total_duration']:.2f}s")
    console.print(f"Average per Episode: {results['avg_duration']:.2f}s")
    console.print("-" * 30)
    
    console.print("\n[bold]Component Breakdown:[/bold]")
    for comp, stats in results['stats'].items():
        console.print(f"  🔹 {comp}:")
        console.print(f"     Average: {stats['avg']:.2f}s")
        console.print(f"     Max:     {stats['max']:.2f}s")
        console.print(f"     Count:   {stats['count']}")

    console.print("\n[bold]Quality Checks:[/bold]")
    valid_count = sum(1 for r in results['results'] if r['quality']['valid'])
    console.print(f"  ✅ Pass Rate: {valid_count}/{len(samples)} ({valid_count/len(samples)*100:.0f}%)")
    
    issues = []
    for r in results['results']:
        if not r['quality']['valid']:
            issues.extend(r['quality']['issues'])
    
    if issues:
        console.print(f"  ❌ Major Issues: {', '.join(set(issues))}")

    console.print("\n[bold cyan]Done![/bold cyan]")


def cmd_storage(args):
    """Handle the 'storage' command."""
    from .storage import storage_manager
    from rich.console import Console
    console = Console()
    
    if args.images:
        usage = storage_manager.get_storage_usage()
        console.print(f"\n[bold cyan]🖼️  Image Storage Usage[/bold cyan]")
        console.print(f"   📍 Base Path: [dim]{usage['base_path']}[/dim]")
        console.print(f"   📂 File Count: {usage['file_count']}")
        console.print(f"   💾 Total Size: [bold green]{usage['total_size_mb']} MB[/bold green]")
        
    elif args.cleanup:
        console.print("[yellow]🔍 Searching for orphaned images...[/yellow]")
        deleted = storage_manager.cleanup_orphaned_images()
        if deleted:
            console.print(f"[bold green]✅ Cleaned up {len(deleted)} orphaned directories:[/bold green]")
            for p in deleted:
                console.print(f"   🗑️  {p}")
        else:
            console.print("[green]✅ No orphaned images found.[/green]")
            
    elif args.backup:
        console.print("[cyan]📦 Creating image backup...[/cyan]")
        path = storage_manager.backup_images(args.export_path)
        console.print(f"[bold green]✅ Backup complete! Saved to: {path}[/bold green]")
    else:
        # Default to usage
        usage = storage_manager.get_storage_usage()
        console.print(f"\n[bold cyan]🖼️  Image Storage Overview[/bold cyan]")
        console.print(f"   📂 Files: {usage['file_count']}")
        console.print(f"   💾 Size: {usage['total_size_mb']} MB")


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="chronicle-ai",
        description="🎬 Chronicle AI - Turn your daily diary into episodic stories",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  chronicle-ai add "Had a productive morning, wrote some code"
  chronicle-ai guided
  chronicle-ai list --limit 5
  chronicle-ai view 1
  chronicle-ai export --weekly
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Add command
    add_parser = subparsers.add_parser("add", help="Add a quick diary entry")
    add_parser.add_argument("text", type=str, help="The diary entry text")
    add_parser.add_argument("--date", type=str, help="Date in YYYY-MM-DD format (default: today)")
    add_parser.add_argument("--skip-ai", action="store_true", help="Skip AI narrative/title generation")
    add_parser.add_argument("--with-recap", action="store_true", help="Prepend a 'Previously on' recap to the narrative")
    add_parser.add_argument("--recap-days", type=int, default=7, help="Number of days to include in recap (default: 7)")
    
    # Guided command
    guided_parser = subparsers.add_parser("guided", help="Interactive guided entry mode")
    guided_parser.add_argument("--date", type=str, help="Date in YYYY-MM-DD format (default: today)")
    guided_parser.add_argument("--skip-ai", action="store_true", help="Skip AI narrative/title generation")
    guided_parser.add_argument("--with-recap", action="store_true", help="Prepend a 'Previously on' recap to the narrative")
    guided_parser.add_argument("--recap-days", type=int, default=7, help="Number of days to include in recap (default: 7)")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List recent entries")
    list_parser.add_argument("--limit", "-n", type=int, default=10, help="Number of entries to show (default: 10)")
    
    # View command
    view_parser = subparsers.add_parser("view", help="View a single entry by ID")
    view_parser.add_argument("id", type=int, help="Entry ID to view")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export entries to Markdown")
    export_group = export_parser.add_mutually_exclusive_group()
    export_group.add_argument("--weekly", "-w", action="store_true", help="Export weekly summary")
    export_group.add_argument("--date", "-d", type=str, help="Export specific date (YYYY-MM-DD)")
    export_group.add_argument("--id", type=int, help="Export specific entry by ID")
    
    recap_parser = subparsers.add_parser("recap", help="Generate a 'Previously on Chronicle...' summary")
    recap_parser.add_argument("--days", type=int, default=7, help="Number of days to analyze (default: 7)")
    
    # Retitle command
    retitle_parser = subparsers.add_parser("retitle", help="Explore and pick new episode titles")
    retitle_parser.add_argument("--episode", type=int, required=True, help="Episode ID to retitle")
    retitle_parser.add_argument("--pick", action="store_true", help="Interactively pick from options")
    
    # Batch synopsis command
    batch_parser = subparsers.add_parser("batch-synopsis", help="Generate missing synopsis for all existing episodes")
    
    # Process command
    process_parser = subparsers.add_parser("process", help="Batch process episodes in a date range")
    process_parser.add_argument("--from", dest="from_date", type=str, required=True, help="Start date (YYYY-MM-DD)")
    process_parser.add_argument("--to", dest="to_date", type=str, required=True, help="End date (YYYY-MM-DD)")
    process_parser.add_argument("--force", action="store_true", help="Reprocess already processed episodes")
    
    # Seasons command
    seasons_parser = subparsers.add_parser("seasons", help="Manage life seasons")
    seasons_parser.add_argument("--list", action="store_true", help="List all seasons")
    seasons_parser.add_argument("--create", action="store_true", help="Organize all episodes into seasons")
    seasons_parser.add_argument("--mode", type=str, choices=["default", "smart", "manual"], default="default", 
                               help="Season organization mode (default: monthly, smart: chapter detection, manual: set boundaries)")
    seasons_parser.add_argument("--start", type=str, help="Start date for manual season (YYYY-MM-DD)")
    seasons_parser.add_argument("--end", type=str, help="End date for manual season (YYYY-MM-DD)")
    seasons_parser.add_argument("--title", type=str, help="Title for manual season")
    seasons_parser.add_argument("--analyze", type=int, help="Perform narrative arc analysis on a season by ID")
    
    # Visual prompt command
    visual_parser = subparsers.add_parser("visual-prompt", help="Generate Stable Diffusion prompts for an episode's cover art")
    visual_parser.add_argument("id", type=int, help="Entry ID to analyze")
    
    # Config command
    config_parser = subparsers.add_parser("config", help="Manage system configuration and preferences")
    config_parser.add_argument("--style", type=str, choices=["cinematic", "anime", "noir", "watercolor", "minimalist"], 
                              help="Set the default visual style for cover art")

    # Status command
    subparsers.add_parser("status", help="Show system status")
    
    # Benchmark command
    subparsers.add_parser("benchmark", help="Run full pipeline benchmark and report stats")
    
    # Generate cover command (leaving for backward compatibility)
    cover_parser = subparsers.add_parser("generate-cover", help="Generate cinematic cover art for an episode")
    cover_parser.add_argument("--episode", type=int, required=True, help="Episode ID to generate art for")
    cover_parser.add_argument("--regenerate", action="store_true", help="Force regeneration if cover already exists")
    cover_parser.add_argument("--style", type=str, help="Style preset to use")
    cover_parser.add_argument("--variations", type=int, default=1, help="Number of variations to generate")
    cover_parser.add_argument("--prompt", type=str, help="Custom prompt override")
    cover_parser.add_argument("--season", type=int, help="Regenerate all covers for a season")

    # Regen-cover command
    regen_cover_parser = subparsers.add_parser("regen-cover", help="Regenerate cover art with variations and style")
    regen_cover_parser.add_argument("--episode", type=int, help="Episode ID to regenerate")
    regen_cover_parser.add_argument("--style", type=str, help="Style preset to use")
    regen_cover_parser.add_argument("--variations", type=int, default=1, help="Number of variations")
    regen_cover_parser.add_argument("--prompt", type=str, help="Custom prompt override")
    regen_cover_parser.add_argument("--season", type=int, help="Regenerate all covers for a season")

    # Covers command
    covers_parser = subparsers.add_parser("covers", help="View cover history and select variants")
    covers_parser.add_argument("--episode", type=int, required=True, help="Episode ID")
    covers_parser.add_argument("--history", action="store_true", help="Show cover history")
    covers_parser.add_argument("--select", type=int, help="Select a cover from history by index")
    
    # Generate poster command
    poster_parser = subparsers.add_parser("generate-poster", help="Generate 2:3 movie posters for a season")
    poster_parser.add_argument("--season", type=int, help="Season ID to generate posters for (default: all seasons)")
    poster_parser.add_argument("--regenerate", action="store_true", help="Force regeneration of existing posters")
    
    # Storage command
    storage_parser = subparsers.add_parser("storage", help="Manage image storage and usage")
    storage_parser.add_argument("--images", action="store_true", help="Show image storage usage")
    storage_parser.add_argument("--cleanup", action="store_true", help="Remove orphaned images")
    storage_parser.add_argument("--backup", action="store_true", help="Backup all images and metadata")
    storage_parser.add_argument("--export-path", type=str, help="Path for backup export")
    
    # Gallery command
    gallery_parser = subparsers.add_parser("gallery", help="View image gallery")
    gallery_parser.add_argument("--season", type=int, help="Filter by season ID")
    gallery_parser.add_argument("--mood", help="Filter by mood")
    gallery_parser.add_argument("--style", help="Filter by style")
    gallery_parser.add_argument("--start", help="Start date (YYYY-MM-DD)")
    gallery_parser.add_argument("--end", help="End date (YYYY-MM-DD)")
    gallery_parser.add_argument("--sort", choices=["date", "mood", "generation_date"], default="date", help="Sort order")
    gallery_parser.add_argument("--limit", type=int, default=50, help="Max items to show")
    gallery_parser.add_argument("--export", help="Export to HTML file (e.g., gallery.html)")
    
    # Retry images command
    subparsers.add_parser("retry-images", help="Regenerate all placeholder images when Stable Diffusion is available")
    
    return parser


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return
    
    # Route to appropriate handler
    commands = {
        "add": cmd_add,
        "guided": cmd_guided,
        "list": cmd_list,
        "view": cmd_view,
        "export": cmd_export,
        "regenerate": cmd_regenerate,
        "status": cmd_status,
        "recap": cmd_recap,
        "retitle": cmd_retitle,
        "batch-synopsis": cmd_batch_synopsis,
        "process": cmd_process,
        "seasons": cmd_seasons,
        "benchmark": cmd_benchmark,
        "visual-prompt": cmd_visual_prompt,
        "generate-cover": cmd_generate_cover,
        "regen-cover": cmd_regen_cover,
        "covers": cmd_covers,
        "generate-poster": cmd_generate_poster,
        "config": cmd_config,
        "storage": cmd_storage,
        "gallery": cmd_gallery,
        "retry-images": cmd_retry_images,
    }
    
    handler = commands.get(args.command)
    if handler:
        try:
            handler(args)
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            sys.exit(0)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
