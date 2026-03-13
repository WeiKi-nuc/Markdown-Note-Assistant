"""
Markdown Note Assistant - A powerful Markdown note-taking application.

This package provides a full-featured Markdown editor with real-time preview,
notebook management, tag system, and bidirectional linking capabilities.
"""

__version__ = "1.0.0"
__author__ = "Markdown Note Assistant Team"
__all__ = [
    "Note",
    "Notebook",
    "NoteRepository",
    "MarkdownParser",
    "PreviewRenderer",
    "Editor",
    "UIManager",
    "ConfigManager",
    "LinkManager",
    "TemplateEngine",
    "AssetManager",
]

from markdown_note_assistant.core.note import Note
from markdown_note_assistant.core.notebook import Notebook
from markdown_note_assistant.core.repository import NoteRepository
from markdown_note_assistant.core.parser import MarkdownParser
from markdown_note_assistant.ui.editor import Editor
from markdown_note_assistant.ui.preview import PreviewRenderer
from markdown_note_assistant.ui.main_window import UIManager
from markdown_note_assistant.utils.config import ConfigManager
from markdown_note_assistant.utils.link_manager import LinkManager
from markdown_note_assistant.utils.template_engine import TemplateEngine
from markdown_note_assistant.utils.asset_manager import AssetManager
