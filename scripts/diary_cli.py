#!/usr/bin/env python
"""
Chronicle AI - CLI Entry Point

Run this script directly or via `python -m scripts.diary_cli` to access
the Chronicle AI command-line interface.

Usage:
    python scripts/diary_cli.py add "Today was amazing!"
    python scripts/diary_cli.py guided
    python scripts/diary_cli.py list --limit 5
    python scripts/diary_cli.py view 1
    python scripts/diary_cli.py export --weekly
    python scripts/diary_cli.py status
"""

import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from chronicle_ai.cli import main

if __name__ == "__main__":
    main()
