#!/usr/bin/env python
"""
Run script for Markdown Note Assistant.
"""

import sys
from pathlib import Path

src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

if __name__ == "__main__":
    from markdown_note_assistant.main import main
    main()
