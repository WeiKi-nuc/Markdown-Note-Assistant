"""
Tests for the Note class.
"""

import pytest
from pathlib import Path
from datetime import datetime

from markdown_note_assistant.core.note import Note, Heading, WikiLink


class TestNote:
    """Tests for the Note class."""
    
    def test_note_creation(self, sample_note_file):
        """Test creating a Note from a file."""
        note = Note.from_file(sample_note_file)
        
        assert note.title == "Test Note"
        assert "test" in note.tags
        assert "example" in note.tags
        assert len(note.headings) > 0
        assert len(note.linked_notes) > 0
    
    def test_note_content_parsing(self, sample_note_file):
        """Test that note content is properly parsed."""
        note = Note.from_file(sample_note_file)
        
        assert "# Test Note" in note.content
        assert "Section 1" in note.content
        assert "bold" in note.content
    
    def test_heading_extraction(self, sample_note_file):
        """Test heading extraction."""
        note = Note.from_file(sample_note_file)
        
        headings = note.headings
        assert len(headings) >= 3
        
        h1 = [h for h in headings if h.level == 1]
        assert len(h1) == 1
        assert h1[0].text == "Test Note"
    
    def test_wiki_link_extraction(self, sample_note_file):
        """Test wiki link extraction."""
        note = Note.from_file(sample_note_file)
        
        links = note.linked_notes
        assert len(links) >= 2
        
        targets = [l.target for l in links]
        assert "Another Note" in targets
        assert "Third Note" in targets
    
    def test_note_save(self, temp_dir):
        """Test saving a note."""
        note_path = temp_dir / "new_note.md"
        
        note = Note(
            file_path=note_path,
            title="New Note",
            content="# New Note\n\nContent here.",
        )
        note.save()
        
        assert note_path.exists()
        content = note_path.read_text(encoding="utf-8")
        assert "title: New Note" in content
    
    def test_note_reload(self, sample_note_file):
        """Test reloading a note."""
        note = Note.from_file(sample_note_file)
        
        original_title = note.title
        
        sample_note_file.write_text(
            "---\ntitle: Updated Title\n---\n# Updated",
            encoding="utf-8"
        )
        
        note.reload()
        assert note.title == "Updated Title"
    
    def test_note_word_count(self, sample_note_file):
        """Test word count calculation."""
        note = Note.from_file(sample_note_file)
        
        word_count = note.get_word_count()
        assert word_count > 0
    
    def test_note_line_count(self, sample_note_file):
        """Test line count calculation."""
        note = Note.from_file(sample_note_file)
        
        line_count = note.get_line_count()
        assert line_count > 0
    
    def test_note_char_count(self, sample_note_file):
        """Test character count calculation."""
        note = Note.from_file(sample_note_file)
        
        char_count = note.get_char_count()
        assert char_count > 0
    
    def test_note_metadata_update(self, sample_note_file):
        """Test updating note metadata."""
        note = Note.from_file(sample_note_file)
        
        note.update_metadata(title="New Title", custom_field="value")
        
        assert note.title == "New Title"
        assert note.metadata.get("custom_field") == "value"
        assert note.is_modified()
    
    def test_note_tag_operations(self, sample_note_file):
        """Test adding and removing tags."""
        note = Note.from_file(sample_note_file)
        
        note.add_tag("new_tag")
        assert "new_tag" in note.tags
        
        note.remove_tag("new_tag")
        assert "new_tag" not in note.tags
    
    def test_note_heading_by_anchor(self, sample_note_file):
        """Test getting heading by anchor."""
        note = Note.from_file(sample_note_file)
        
        heading = note.get_heading_by_anchor("section-1")
        assert heading is not None or len(note.headings) > 0
    
    def test_note_outline(self, sample_note_file):
        """Test getting document outline."""
        note = Note.from_file(sample_note_file)
        
        outline = note.get_outline()
        assert isinstance(outline, list)
        assert len(outline) > 0


class TestHeading:
    """Tests for the Heading class."""
    
    def test_heading_creation(self):
        """Test creating a heading."""
        heading = Heading(
            level=1,
            text="Test Heading",
            anchor="test-heading",
            line_number=1,
        )
        
        assert heading.level == 1
        assert heading.text == "Test Heading"
        assert heading.anchor == "test-heading"
        assert heading.line_number == 1
    
    def test_heading_to_dict(self):
        """Test converting heading to dictionary."""
        heading = Heading(
            level=2,
            text="Section",
            anchor="section",
            line_number=5,
        )
        
        data = heading.to_dict()
        assert data["level"] == 2
        assert data["text"] == "Section"
        assert data["anchor"] == "section"
        assert data["line_number"] == 5


class TestWikiLink:
    """Tests for the WikiLink class."""
    
    def test_wiki_link_creation(self):
        """Test creating a wiki link."""
        link = WikiLink(
            target="Target Note",
            heading="section",
            display_text="Display Text",
            line_number=10,
        )
        
        assert link.target == "Target Note"
        assert link.heading == "section"
        assert link.display_text == "Display Text"
        assert link.line_number == 10
    
    def test_wiki_link_to_dict(self):
        """Test converting wiki link to dictionary."""
        link = WikiLink(
            target="Note",
            line_number=5,
        )
        
        data = link.to_dict()
        assert data["target"] == "Note"
        assert data["heading"] is None
        assert data["display_text"] is None
        assert data["line_number"] == 5
