"""
Tests for the TemplateEngine class.
"""

import pytest
from pathlib import Path
from datetime import datetime

from markdown_note_assistant.utils.template_engine import (
    TemplateEngine,
    NoteTemplate,
    TemplateVariable,
)


class TestTemplateEngine:
    """Tests for the TemplateEngine class."""
    
    @pytest.fixture
    def engine(self):
        """Create a template engine instance."""
        return TemplateEngine()
    
    def test_engine_creation(self, engine):
        """Test creating a template engine."""
        assert engine is not None
    
    def test_builtin_templates_loaded(self, engine):
        """Test that built-in templates are loaded."""
        templates = engine.get_all_templates()
        
        assert len(templates) > 0
        
        names = [t.name for t in templates]
        assert "default" in names
        assert "diary" in names
        assert "meeting" in names
        assert "project" in names
    
    def test_get_template(self, engine):
        """Test getting a template by name."""
        template = engine.get_template("default")
        
        assert template is not None
        assert template.name == "default"
    
    def test_get_nonexistent_template(self, engine):
        """Test getting a non-existent template."""
        template = engine.get_template("nonexistent")
        
        assert template is None
    
    def test_render_template(self, engine):
        """Test rendering a template."""
        content = engine.render("default", {"title": "Test Note"})
        
        assert "Test Note" in content
        assert "title: Test Note" in content
    
    def test_render_with_date(self, engine):
        """Test rendering with date variable."""
        content = engine.render("default", {"title": "Test"})
        
        today = datetime.now().strftime("%Y-%m-%d")
        assert today in content
    
    def test_render_diary_template(self, engine):
        """Test rendering the diary template."""
        content = engine.render("diary", {"title": "Today's Diary"})
        
        assert "Today's Diary" in content
        assert "今日计划" in content
        assert "今日记录" in content
    
    def test_render_meeting_template(self, engine):
        """Test rendering the meeting template."""
        content = engine.render("meeting", {
            "title": "Team Meeting",
            "time": "10:00",
        })
        
        assert "Team Meeting" in content
        assert "会议议程" in content
        assert "决议事项" in content
    
    def test_render_project_template(self, engine):
        """Test rendering the project template."""
        content = engine.render("project", {"title": "New Project"})
        
        assert "New Project" in content
        assert "项目概述" in content
        assert "里程碑" in content
    
    def test_get_templates_by_category(self, engine):
        """Test getting templates by category."""
        work_templates = engine.get_templates_by_category("work")
        
        for t in work_templates:
            assert t.category == "work"
    
    def test_get_all_categories(self, engine):
        """Test getting all categories."""
        categories = engine.get_all_categories()
        
        assert "general" in categories
        assert "personal" in categories
        assert "work" in categories
    
    def test_add_template(self, engine):
        """Test adding a custom template."""
        template = NoteTemplate(
            name="custom",
            content="# ${title}\n\nCustom content.",
            description="Custom template",
            category="custom",
        )
        
        engine.add_template(template)
        
        assert engine.get_template("custom") is not None
    
    def test_remove_template(self, engine):
        """Test removing a template."""
        template = NoteTemplate(
            name="to_remove",
            content="# ${title}",
            category="test",
        )
        engine.add_template(template)
        
        result = engine.remove_template("to_remove")
        
        assert result is True
        assert engine.get_template("to_remove") is None
    
    def test_save_template(self, engine, temp_dir):
        """Test saving a template to a file."""
        template = NoteTemplate(
            name="saved_template",
            content="# ${title}\n\nContent.",
            description="Saved template",
            category="test",
        )
        
        path = engine.save_template(template, temp_dir)
        
        assert path.exists()
        assert path.name == "saved_template.md"
    
    def test_load_custom_templates(self, temp_dir):
        """Test loading custom templates from a directory."""
        template_content = """---
name: custom_loaded
description: Custom loaded template
category: custom
---

# ${title}

Custom content.
"""
        template_path = temp_dir / "custom_loaded.md"
        template_path.write_text(template_content, encoding="utf-8")
        
        engine = TemplateEngine(custom_template_dir=temp_dir)
        
        template = engine.get_template("custom_loaded")
        assert template is not None
        assert template.name == "custom_loaded"
    
    def test_get_default_template_for_type(self, engine):
        """Test getting default template for a note type."""
        template = engine.get_default_template_for("diary")
        assert template.name == "diary"
        
        template = engine.get_default_template_for("meeting")
        assert template.name == "meeting"
        
        template = engine.get_default_template_for("unknown")
        assert template.name == "default"
    
    def test_create_from_template(self, engine):
        """Test creating note content from a template."""
        content = engine.create_from_template(
            "default",
            title="New Note",
            extra_variables={"custom": "value"},
        )
        
        assert "New Note" in content
    
    def test_template_variables(self, engine):
        """Test template variable handling."""
        template = engine.get_template("default")
        
        assert len(template.variables) > 0
        
        title_var = next((v for v in template.variables if v.name == "title"), None)
        assert title_var is not None
        assert title_var.required is True


class TestNoteTemplate:
    """Tests for the NoteTemplate class."""
    
    def test_template_creation(self):
        """Test creating a template."""
        template = NoteTemplate(
            name="test",
            content="# ${title}",
            description="Test template",
            category="test",
        )
        
        assert template.name == "test"
        assert template.content == "# ${title}"
        assert template.description == "Test template"
        assert template.category == "test"
    
    def test_template_to_dict(self):
        """Test converting template to dictionary."""
        template = NoteTemplate(
            name="test",
            content="# ${title}",
            variables=[
                TemplateVariable("title", "Note title", required=True)
            ],
        )
        
        data = template.to_dict()
        
        assert data["name"] == "test"
        assert data["content"] == "# ${title}"
        assert len(data["variables"]) == 1


class TestTemplateVariable:
    """Tests for the TemplateVariable class."""
    
    def test_variable_creation(self):
        """Test creating a template variable."""
        var = TemplateVariable(
            name="title",
            description="Note title",
            default_value="Untitled",
            required=True,
        )
        
        assert var.name == "title"
        assert var.description == "Note title"
        assert var.default_value == "Untitled"
        assert var.required is True
    
    def test_variable_to_dict(self):
        """Test converting variable to dictionary."""
        var = TemplateVariable("title", "Note title")
        
        data = var.to_dict()
        
        assert data["name"] == "title"
        assert data["description"] == "Note title"
        assert data["default_value"] is None
        assert data["required"] is False
