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
        print(f"   🎬 {title}")
        if entry.logline:
            print(f"   💡 {entry.logline}")
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
            
            
def cmd_batch_synopsis(args):
    """Handle 'batch-synopsis' command - generate missing synopsis for all episodes."""
    repo = get_repository()
    entries = repo.list_entries()
    
    to_process = [e for e in entries if not e.logline or not e.synopsis]
    
    if not to_process:
        print("✅ All episodes already have synopsis metadata.")
        return
        
    print(f"🤖 Found {len(to_process)} episodes missing synopsis metadata.")
    print(f"🔄 Starting batch generation (this may take a while)...")
    
    if not is_ollama_available():
        print("❌ Ollama not available.")
        return

    from .llm_client import ensure_synopsis
    
    success_count = 0
    for i, entry in enumerate(to_process, 1):
        print(f"[{i}/{len(to_process)}] Processing Episode {entry.id}: {entry.display_title()}...")
        try:
            ensure_synopsis(entry)
            repo.update_entry(entry)
            success_count += 1
        except Exception as e:
            print(f"  ❌ Failed: {e}")
            
    print(f"\n✅ Batch processing complete! {success_count}/{len(to_process)} episodes updated.")


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
    
    # Ollama status
    if is_ollama_available():
        print("✅ Ollama: Connected")
    else:
        print("⚠️  Ollama: Not available")
    
    print("=" * 40)


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
    
    # Status command
    subparsers.add_parser("status", help="Show system status")
    
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
        "seasons": cmd_seasons,
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
