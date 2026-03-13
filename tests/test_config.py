"""
Tests for the ConfigManager class.
"""

import pytest
from pathlib import Path

from markdown_note_assistant.utils.config import (
    ConfigManager,
    AppConfig,
    EditorConfig,
    PreviewConfig,
    ShortcutsConfig,
    AdvancedConfig,
    UIConfig,
)


class TestConfigManager:
    """Tests for the ConfigManager class."""
    
    @pytest.fixture
    def config_manager(self, temp_dir):
        """Create a config manager with a temp directory."""
        return ConfigManager(config_dir=temp_dir)
    
    def test_config_manager_creation(self, config_manager):
        """Test creating a config manager."""
        assert config_manager is not None
        assert config_manager.config is not None
    
    def test_default_config(self, config_manager):
        """Test default configuration values."""
        config = config_manager.config
        
        assert isinstance(config.editor, EditorConfig)
        assert isinstance(config.preview, PreviewConfig)
        assert isinstance(config.shortcuts, ShortcutsConfig)
        assert isinstance(config.advanced, AdvancedConfig)
        assert isinstance(config.ui, UIConfig)
    
    def test_editor_config_defaults(self, config_manager):
        """Test default editor configuration."""
        editor = config_manager.get_editor_config()
        
        assert editor.font_family == "Consolas"
        assert editor.font_size == 14
        assert editor.auto_save is True
        assert editor.word_wrap is True
    
    def test_preview_config_defaults(self, config_manager):
        """Test default preview configuration."""
        preview = config_manager.get_preview_config()
        
        assert preview.theme == "light"
        assert preview.math_enabled is True
        assert preview.mermaid_enabled is True
        assert preview.sync_scroll is True
    
    def test_shortcuts_config_defaults(self, config_manager):
        """Test default shortcuts configuration."""
        shortcuts = config_manager.get_shortcuts_config()
        
        assert shortcuts.save == "Ctrl+S"
        assert shortcuts.new_note == "Ctrl+N"
        assert shortcuts.bold == "Ctrl+B"
    
    def test_save_and_load_config(self, config_manager, temp_dir):
        """Test saving and loading configuration."""
        config_manager.config.editor.font_size = 18
        config_manager.config.preview.theme = "dark"
        config_manager.save()
        
        new_manager = ConfigManager(config_dir=temp_dir)
        
        assert new_manager.config.editor.font_size == 18
        assert new_manager.config.preview.theme == "dark"
    
    def test_get_set_value(self, config_manager):
        """Test getting and setting configuration values."""
        config_manager.set("editor", "font_size", 20)
        
        value = config_manager.get("editor", "font_size")
        assert value == 20
    
    def test_add_notebook(self, config_manager):
        """Test adding a notebook path."""
        path = "/path/to/notebook"
        
        config_manager.add_notebook(path)
        
        assert path in config_manager.config.notebooks
    
    def test_remove_notebook(self, config_manager):
        """Test removing a notebook path."""
        path = "/path/to/notebook"
        
        config_manager.add_notebook(path)
        config_manager.remove_notebook(path)
        
        assert path not in config_manager.config.notebooks
    
    def test_add_recent_file(self, config_manager):
        """Test adding a recent file."""
        path = "/path/to/file.md"
        
        config_manager.add_recent_file(path)
        
        assert path in config_manager.config.last_opened_files
        assert config_manager.config.last_opened_files[0] == path
    
    def test_add_recent_search(self, config_manager):
        """Test adding a recent search."""
        query = "test search"
        
        config_manager.add_recent_search(query)
        
        assert query in config_manager.config.recent_searches
    
    def test_reset_config(self, config_manager):
        """Test resetting configuration."""
        config_manager.config.editor.font_size = 24
        config_manager.reset()
        
        assert config_manager.config.editor.font_size == 14
    
    def test_validate_config(self, config_manager):
        """Test configuration validation."""
        errors = config_manager.validate()
        assert len(errors) == 0
        
        config_manager.config.editor.font_size = 100
        errors = config_manager.validate()
        assert len(errors) > 0
    
    def test_export_import_config(self, config_manager, temp_dir):
        """Test exporting and importing configuration."""
        export_path = temp_dir / "exported_config.json"
        
        config_manager.config.editor.font_size = 16
        config_manager.export_config(export_path)
        
        assert export_path.exists()
        
        config_manager.reset()
        assert config_manager.config.editor.font_size == 14
        
        config_manager.import_config(export_path)
        assert config_manager.config.editor.font_size == 16
    
    def test_get_shortcut(self, config_manager):
        """Test getting a shortcut."""
        shortcut = config_manager.get_shortcut("save")
        assert shortcut == "Ctrl+S"
    
    def test_set_shortcut(self, config_manager):
        """Test setting a shortcut."""
        config_manager.set_shortcut("save", "Ctrl+Shift+S")
        
        assert config_manager.get_shortcut("save") == "Ctrl+Shift+S"
    
    def test_custom_shortcut(self, config_manager):
        """Test custom shortcuts."""
        config_manager.set_custom_shortcut("custom_action", "Ctrl+Alt+X")
        
        shortcut = config_manager.get_custom_shortcut("custom_action")
        assert shortcut == "Ctrl+Alt+X"


class TestEditorConfig:
    """Tests for the EditorConfig class."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = EditorConfig()
        
        assert config.font_family == "Consolas"
        assert config.font_size == 14
        assert config.line_height == 1.6
        assert config.tab_width == 4
        assert config.auto_save is True


class TestPreviewConfig:
    """Tests for the PreviewConfig class."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = PreviewConfig()
        
        assert config.font_family == "Segoe UI"
        assert config.font_size == 15
        assert config.theme == "light"
        assert config.math_enabled is True


class TestUIConfig:
    """Tests for the UIConfig class."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = UIConfig()
        
        assert config.window_width == 1400
        assert config.window_height == 900
        assert config.sidebar_width == 250
        assert config.sidebar_visible is True
