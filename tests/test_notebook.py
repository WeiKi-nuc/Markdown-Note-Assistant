"""
Tests for the Notebook class.
"""

import pytest
from pathlib import Path
from datetime import datetime

from markdown_note_assistant.core.notebook import Notebook, NotebookConfig


class TestNotebook:
    """Tests for the Notebook class."""
    
    def test_notebook_creation(self, sample_notebook_dir):
        """Test creating a notebook from a directory."""
        notebook = Notebook.from_path(sample_notebook_dir)
        
        assert notebook.name == sample_notebook_dir.name
        assert len(notebook.notes) == 3
    
    def test_notebook_scan(self, sample_notebook_dir):
        """Test scanning a notebook directory."""
        notebook = Notebook(root_path=sample_notebook_dir)
        count = notebook.scan()
        
        assert count == 3
        assert len(notebook.notes) == 3
    
    def test_notebook_get_note_by_path(self, sample_notebook_dir):
        """Test getting a note by path."""
        notebook = Notebook.from_path(sample_notebook_dir)
        
        note_paths = list(notebook.notes.keys())
        assert len(note_paths) > 0
        
        note = notebook.get_note_by_path(note_paths[0])
        assert note is not None
    
    def test_notebook_get_note_by_title(self, sample_notebook_dir):
        """Test getting a note by title."""
        notebook = Notebook.from_path(sample_notebook_dir)
        
        note = notebook.get_note_by_title("Note 1")
        assert note is not None
        assert note.title == "Note 1"
    
    def test_notebook_create_note(self, sample_notebook_dir):
        """Test creating a new note."""
        notebook = Notebook.from_path(sample_notebook_dir)
        initial_count = len(notebook.notes)
        
        note = notebook.create_note(
            title="New Note",
            tags=["new", "test"],
        )
        
        assert note.title == "New Note"
        assert len(notebook.notes) == initial_count + 1
        assert note.file_path.exists()
    
    def test_notebook_delete_note(self, sample_notebook_dir):
        """Test deleting a note."""
        notebook = Notebook.from_path(sample_notebook_dir)
        
        note_paths = list(notebook.notes.keys())
        note_path = note_paths[0]
        
        result = notebook.delete_note(note_path)
        
        assert result is True
        assert note_path not in notebook.notes
        assert not note_path.exists()
    
    def test_notebook_search(self, sample_notebook_dir):
        """Test searching within a notebook."""
        notebook = Notebook.from_path(sample_notebook_dir)
        
        results = notebook.search("Content")
        
        assert len(results) > 0
        for note, lines in results:
            assert "Content" in note.content
    
    def test_notebook_search_by_tag(self, sample_notebook_dir):
        """Test searching notes by tag."""
        notebook = Notebook.from_path(sample_notebook_dir)
        
        results = notebook.search_by_tag("tag1")
        
        assert len(results) == 2
    
    def test_notebook_tag_statistics(self, sample_notebook_dir):
        """Test getting tag statistics."""
        notebook = Notebook.from_path(sample_notebook_dir)
        
        stats = notebook.get_tag_statistics()
        
        assert "tag1" in stats
        assert "tag2" in stats
        assert "tag3" in stats
        assert stats["tag1"] == 2
        assert stats["tag2"] == 2
        assert stats["tag3"] == 2
    
    def test_notebook_get_all_tags(self, sample_notebook_dir):
        """Test getting all tags."""
        notebook = Notebook.from_path(sample_notebook_dir)
        
        tags = notebook.get_all_tags()
        
        assert "tag1" in tags
        assert "tag2" in tags
        assert "tag3" in tags
    
    def test_notebook_get_recent_notes(self, sample_notebook_dir):
        """Test getting recent notes."""
        notebook = Notebook.from_path(sample_notebook_dir)
        
        recent = notebook.get_recent_notes(limit=2)
        
        assert len(recent) <= 2
    
    def test_notebook_get_all_notes(self, sample_notebook_dir):
        """Test iterating over all notes."""
        notebook = Notebook.from_path(sample_notebook_dir)
        
        notes = list(notebook.get_all_notes())
        
        assert len(notes) == 3
    
    def test_notebook_get_note_count(self, sample_notebook_dir):
        """Test getting note count."""
        notebook = Notebook.from_path(sample_notebook_dir)
        
        count = notebook.get_note_count()
        
        assert count == 3
    
    def test_notebook_contains(self, sample_notebook_dir):
        """Test checking if a note is in the notebook."""
        notebook = Notebook.from_path(sample_notebook_dir)
        
        note_paths = list(notebook.notes.keys())
        assert note_paths[0] in notebook
        
        note = notebook.notes[note_paths[0]]
        assert note in notebook
    
    def test_notebook_iteration(self, sample_notebook_dir):
        """Test iterating over notebook notes."""
        notebook = Notebook.from_path(sample_notebook_dir)
        
        count = 0
        for note in notebook:
            count += 1
            assert isinstance(note, type(list(notebook.notes.values())[0]))
        
        assert count == 3
    
    def test_notebook_len(self, sample_notebook_dir):
        """Test notebook length."""
        notebook = Notebook.from_path(sample_notebook_dir)
        
        assert len(notebook) == 3


class TestNotebookConfig:
    """Tests for the NotebookConfig class."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = NotebookConfig(name="Test")
        
        assert config.name == "Test"
        assert config.icon == "📁"
        assert config.auto_save is True
        assert ".git" in config.excluded_patterns
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = NotebookConfig(
            name="Custom",
            icon="📚",
            auto_save=False,
            auto_save_interval=60,
        )
        
        assert config.name == "Custom"
        assert config.icon == "📚"
        assert config.auto_save is False
        assert config.auto_save_interval == 60
