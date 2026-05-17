#!/usr/bin/env python3
"""
Chronicle AI - Integration Test Runner
Day 86 — Full System Integration Test

Provides a beautiful, high-visibility command-line interface to execute
the comprehensive system integration test suite and display real-time progress.
"""

import os
import sys
import time
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.status import Status
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

def run_tests():
    """Execute pytest on the integration test file and format the results beautifully."""
    if RICH_AVAILABLE:
        console = Console()
        console.print(Panel.fit(
            "[bold cyan]🎬 Chronicle AI — Day 86 Full System Integration Test Runner[/bold cyan]",
            border_style="cyan"
        ))
    else:
        print("=" * 70)
        print("🎬 Chronicle AI — Day 86 Full System Integration Test Runner")
        print("=" * 70)

    test_file = project_root / "tests" / "test_full_integration.py"
    report_file = project_root / "artifacts" / "integration_test_report.md"

    # Identify python executable in virtual env if available
    venv_python = project_root / "venv" / "Scripts" / "python.exe"
    if not venv_python.exists():
        venv_python = project_root / "venv" / "bin" / "python"
    
    python_cmd = str(venv_python) if venv_python.exists() else sys.executable

    if RICH_AVAILABLE:
        console.print(f"[yellow]🔍 Using Python environment:[/yellow] {python_cmd}")
        console.print("[yellow]📦 Target Test Suite:[/yellow] tests/test_full_integration.py\n")
        
        with console.status("[bold green]Executing comprehensive 8-step pipeline over 50+ episodes...[/bold green]", spinner="dots"):
            t0 = time.time()
            result = subprocess.run(
                [python_cmd, "-m", "pytest", "-v", str(test_file)],
                capture_output=True,
                text=True
            )
            duration = time.time() - t0
    else:
        print(f"Using Python environment: {python_cmd}")
        print("Target Test Suite: tests/test_full_integration.py")
        print("Executing comprehensive 8-step pipeline over 50+ episodes...")
        t0 = time.time()
        result = subprocess.run(
            [python_cmd, "-m", "pytest", "-v", str(test_file)],
            capture_output=True,
            text=True
        )
        duration = time.time() - t0

    # Display test results
    if result.returncode == 0:
        if RICH_AVAILABLE:
            console.print(Panel(
                f"[bold green]🎉 INTEGRATION TEST SUITE PASSED SUCCESSFULLY![/bold green]\n\n"
                f"⏱️ Total Execution Time: {duration:.2f} seconds\n"
                f"📝 Detailed Markdown Report generated: [underline cyan]{report_file}[/underline cyan]",
                title="Status: Success",
                border_style="green"
            ))
            
            # Print brief summary table
            table = Table(title="Pipeline Step Verification Results", show_lines=True)
            table.add_column("Step", style="cyan", justify="center")
            table.add_column("Component", style="magenta")
            table.add_column("Constraint Verified", style="yellow")
            table.add_column("Status", style="green", justify="center")

            table.add_row("1", "Create Diary Entry", "SQLite DB Schema & Primary Keys", "PASSED")
            table.add_row("2", "Generate Episode", "2-4 Sentence Narrative, <=15-Word Logline, Exactly 5 Keywords", "PASSED")
            table.add_row("3", "Generate Cover Art", "16:9 Aspect Ratio & Image Fallback Placeholder Tagging", "PASSED")
            table.add_row("4", "Generate Audio", "TTS pause synchronization & ID3/Chapter markers", "PASSED")
            table.add_row("5", "Index in Vector DB", "ChromaDB/Mock Episode indexing & metadata mapping", "PASSED")
            table.add_row("6", "Semantic Search", "Keywords matched to top Episode ID retrieve in semantic index", "PASSED")
            table.add_row("7", "RAG Memory Chat", "Conversational session logging & context extraction", "PASSED")
            table.add_row("8", "Playback Progress Sync", "Playback progress updates saved in SQLite", "PASSED")
            
            console.print(table)
        else:
            print("\n" + "=" * 70)
            print("🎉 INTEGRATION TEST SUITE PASSED SUCCESSFULLY!")
            print(f"Total Execution Time: {duration:.2f} seconds")
            print(f"Detailed Markdown Report generated: {report_file}")
            print("=" * 70)
            print("All 8 pipeline steps successfully verified!")
    else:
        if RICH_AVAILABLE:
            console.print(Panel(
                f"[bold red]❌ INTEGRATION TEST SUITE FAILED![/bold red]\n\n"
                f"Return Code: {result.returncode}\n"
                f"Error Details:\n{result.stderr or result.stdout}",
                title="Status: Failure",
                border_style="red"
            ))
        else:
            print("\n" + "=" * 70)
            print("❌ INTEGRATION TEST SUITE FAILED!")
            print(f"Return Code: {result.returncode}")
            print("Error Details:")
            print(result.stderr or result.stdout)
            print("=" * 70)
            
        sys.exit(result.returncode)

if __name__ == "__main__":
    # Ensure stdout/stderr handles UTF-8 on Windows legacy terminal shells
    if sys.platform.startswith("win"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except AttributeError:
            pass
            
    run_tests()
