"""
Main entry point for Markdown Note Assistant.
"""

import sys
from pathlib import Path


def main() -> None:
    """Main entry point for the application."""
    import tkinter as tk
    from tkinter import messagebox
    
    try:
        from markdown_note_assistant.ui.main_window import UIManager
        
        root = tk.Tk()
        
        ui_manager = UIManager(root)
        ui_manager.run()
        
    except ImportError as e:
        print(f"Error importing modules: {e}")
        print("Please make sure all dependencies are installed:")
        print("  pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
