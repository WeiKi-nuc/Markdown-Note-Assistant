"""
Configuration Manager module - handles application settings and preferences.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class EditorConfig:
    """Editor-related configuration."""
    font_family: str = "Consolas"
    font_size: int = 14
    line_height: float = 1.6
    tab_width: int = 4
    auto_save: bool = True
    auto_save_interval: int = 30
    word_wrap: bool = True
    show_line_numbers: bool = True
    highlight_current_line: bool = True
    show_invisibles: bool = False
    indent_with_tabs: bool = False
    auto_indent: bool = True
    auto_close_brackets: bool = True
    auto_close_quotes: bool = True
    spell_check: bool = False


@dataclass
class PreviewConfig:
    """Preview-related configuration."""
    font_family: str = "Segoe UI"
    font_size: int = 15
    line_height: float = 1.8
    code_font_family: str = "Consolas"
    code_font_size: int = 13
    theme: str = "light"
    custom_css_path: Optional[str] = None
    code_highlight_theme: str = "github"
    math_enabled: bool = True
    mermaid_enabled: bool = True
    sync_scroll: bool = True
    scroll_offset: int = 50


@dataclass
class ShortcutsConfig:
    """Keyboard shortcuts configuration."""
    save: str = "Ctrl+S"
    new_note: str = "Ctrl+N"
    open_note: str = "Ctrl+O"
    search: str = "Ctrl+F"
    global_search: str = "Ctrl+Shift+F"
    command_palette: str = "Ctrl+P"
    toggle_preview: str = "Ctrl+E"
    toggle_sidebar: str = "Ctrl+B"
    focus_mode: str = "F11"
    bold: str = "Ctrl+B"
    italic: str = "Ctrl+I"
    underline: str = "Ctrl+U"
    strike: str = "Ctrl+Shift+S"
    code: str = "Ctrl+`"
    code_block: str = "Ctrl+Shift+`"
    link: str = "Ctrl+K"
    image: str = "Ctrl+Shift+I"
    heading_1: str = "Ctrl+1"
    heading_2: str = "Ctrl+2"
    heading_3: str = "Ctrl+3"
    heading_4: str = "Ctrl+4"
    heading_5: str = "Ctrl+5"
    heading_6: str = "Ctrl+6"
    list_bullet: str = "Ctrl+L"
    list_number: str = "Ctrl+Shift+L"
    quote: str = "Ctrl+Q"
    table: str = "Ctrl+T"
    custom: Dict[str, str] = field(default_factory=dict)


@dataclass
class AdvancedConfig:
    """Advanced configuration options."""
    image_compress_quality: int = 85
    image_max_width: int = 1200
    auto_backup: bool = True
    backup_interval: int = 300
    max_backup_count: int = 10
    backup_path: Optional[str] = None
    cache_size_limit: int = 100
    log_level: str = "INFO"
    check_updates: bool = True
    default_notebook_path: Optional[str] = None
    default_template: str = "default"


@dataclass
class UIConfig:
    """User interface configuration."""
    window_width: int = 1400
    window_height: int = 900
    sidebar_width: int = 250
    sidebar_visible: bool = True
    preview_visible: bool = True
    split_orientation: str = "horizontal"
    split_ratio: float = 0.5
    status_bar_visible: bool = True
    toolbar_visible: bool = True
    toolbar_buttons: List[str] = field(default_factory=lambda: [
        "new", "open", "save", "separator",
        "bold", "italic", "strike", "separator",
        "heading", "list", "quote", "code", "separator",
        "link", "image", "table", "separator",
        "preview", "focus",
    ])
    theme: str = "system"
    accent_color: str = "#4A90D9"


@dataclass
class AppConfig:
    """Complete application configuration."""
    editor: EditorConfig = field(default_factory=EditorConfig)
    preview: PreviewConfig = field(default_factory=PreviewConfig)
    shortcuts: ShortcutsConfig = field(default_factory=ShortcutsConfig)
    advanced: AdvancedConfig = field(default_factory=AdvancedConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    notebooks: List[str] = field(default_factory=list)
    last_opened_files: List[str] = field(default_factory=list)
    recent_searches: List[str] = field(default_factory=list)
    version: str = "1.0.0"


class ConfigManager:
    """
    Configuration Manager - handles all application settings.
    
    This class provides:
    - Loading and saving configuration
    - Default values management
    - Configuration validation
    - Change notification
    """
    
    DEFAULT_CONFIG_FILENAME = "config.json"
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_dir: Directory for configuration files
        """
        if config_dir is None:
            config_dir = Path(__file__).parent.parent.parent.parent / ".md_note_assistant"
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_file = self.config_dir / self.DEFAULT_CONFIG_FILENAME
        self._config: Optional[AppConfig] = None
        self._callbacks: List[callable] = []
    
    @property
    def config(self) -> AppConfig:
        """Get the current configuration, loading if necessary."""
        if self._config is None:
            self._config = self.load()
        return self._config
    
    def load(self) -> AppConfig:
        """
        Load configuration from file.
        
        Returns:
            AppConfig instance
        """
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return self._dict_to_config(data)
            except Exception as e:
                print(f"Error loading config: {e}")
        
        return AppConfig()
    
    def _dict_to_config(self, data: Dict[str, Any]) -> AppConfig:
        """Convert a dictionary to AppConfig."""
        config = AppConfig()
        
        if "editor" in data:
            config.editor = EditorConfig(**{
                k: v for k, v in data["editor"].items()
                if k in EditorConfig.__dataclass_fields__
            })
        
        if "preview" in data:
            config.preview = PreviewConfig(**{
                k: v for k, v in data["preview"].items()
                if k in PreviewConfig.__dataclass_fields__
            })
        
        if "shortcuts" in data:
            shortcuts_data = {
                k: v for k, v in data["shortcuts"].items()
                if k in ShortcutsConfig.__dataclass_fields__
            }
            if "custom" in data["shortcuts"]:
                shortcuts_data["custom"] = data["shortcuts"]["custom"]
            config.shortcuts = ShortcutsConfig(**shortcuts_data)
        
        if "advanced" in data:
            config.advanced = AdvancedConfig(**{
                k: v for k, v in data["advanced"].items()
                if k in AdvancedConfig.__dataclass_fields__
            })
        
        if "ui" in data:
            config.ui = UIConfig(**{
                k: v for k, v in data["ui"].items()
                if k in UIConfig.__dataclass_fields__
            })
        
        for field_name in ["notebooks", "last_opened_files", "recent_searches", "version"]:
            if field_name in data:
                setattr(config, field_name, data[field_name])
        
        return config
    
    def save(self) -> None:
        """Save configuration to file."""
        data = asdict(self.config)
        
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self._notify_callbacks()
    
    def reset(self) -> None:
        """Reset configuration to defaults."""
        self._config = AppConfig()
        self.save()
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            section: Configuration section (editor, preview, etc.)
            key: Configuration key
            default: Default value if not found
            
        Returns:
            Configuration value
        """
        section_obj = getattr(self.config, section, None)
        if section_obj:
            return getattr(section_obj, key, default)
        return default
    
    def set(self, section: str, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            section: Configuration section
            key: Configuration key
            value: New value
        """
        section_obj = getattr(self.config, section, None)
        if section_obj:
            setattr(section_obj, key, value)
    
    def get_editor_config(self) -> EditorConfig:
        """Get editor configuration."""
        return self.config.editor
    
    def get_preview_config(self) -> PreviewConfig:
        """Get preview configuration."""
        return self.config.preview
    
    def get_shortcuts_config(self) -> ShortcutsConfig:
        """Get shortcuts configuration."""
        return self.config.shortcuts
    
    def get_advanced_config(self) -> AdvancedConfig:
        """Get advanced configuration."""
        return self.config.advanced
    
    def get_ui_config(self) -> UIConfig:
        """Get UI configuration."""
        return self.config.ui
    
    def add_notebook(self, path: str) -> None:
        """Add a notebook path to the list."""
        if path not in self.config.notebooks:
            self.config.notebooks.append(path)
            self.save()
    
    def remove_notebook(self, path: str) -> None:
        """Remove a notebook path from the list."""
        if path in self.config.notebooks:
            self.config.notebooks.remove(path)
            self.save()
    
    def add_recent_file(self, path: str, max_count: int = 20) -> None:
        """Add a file to recent files list."""
        files = self.config.last_opened_files
        if path in files:
            files.remove(path)
        files.insert(0, path)
        self.config.last_opened_files = files[:max_count]
        self.save()
    
    def add_recent_search(self, query: str, max_count: int = 20) -> None:
        """Add a search query to recent searches."""
        searches = self.config.recent_searches
        if query in searches:
            searches.remove(query)
        searches.insert(0, query)
        self.config.recent_searches = searches[:max_count]
        self.save()
    
    def on_change(self, callback: callable) -> None:
        """Register a callback for configuration changes."""
        self._callbacks.append(callback)
    
    def _notify_callbacks(self) -> None:
        """Notify all registered callbacks."""
        for callback in self._callbacks:
            try:
                callback(self.config)
            except Exception as e:
                print(f"Error in config callback: {e}")
    
    def export_config(self, path: Path) -> None:
        """Export configuration to a file."""
        data = asdict(self.config)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def import_config(self, path: Path) -> bool:
        """
        Import configuration from a file.
        
        Returns:
            True if import was successful
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._config = self._dict_to_config(data)
            self.save()
            return True
        except Exception as e:
            print(f"Error importing config: {e}")
            return False
    
    def get_shortcut(self, action: str) -> str:
        """Get the keyboard shortcut for an action."""
        return getattr(self.config.shortcuts, action, "")
    
    def set_shortcut(self, action: str, shortcut: str) -> None:
        """Set a keyboard shortcut for an action."""
        if hasattr(self.config.shortcuts, action):
            setattr(self.config.shortcuts, action, shortcut)
            self.save()
    
    def get_custom_shortcut(self, action_id: str) -> Optional[str]:
        """Get a custom shortcut."""
        return self.config.shortcuts.custom.get(action_id)
    
    def set_custom_shortcut(self, action_id: str, shortcut: str) -> None:
        """Set a custom shortcut."""
        self.config.shortcuts.custom[action_id] = shortcut
        self.save()
    
    def validate(self) -> List[str]:
        """
        Validate the current configuration.
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        if self.config.editor.font_size < 8 or self.config.editor.font_size > 72:
            errors.append("Editor font size must be between 8 and 72")
        
        if self.config.preview.font_size < 8 or self.config.preview.font_size > 72:
            errors.append("Preview font size must be between 8 and 72")
        
        if self.config.editor.tab_width < 1 or self.config.editor.tab_width > 8:
            errors.append("Tab width must be between 1 and 8")
        
        if self.config.advanced.image_compress_quality < 1 or self.config.advanced.image_compress_quality > 100:
            errors.append("Image quality must be between 1 and 100")
        
        if self.config.ui.split_ratio < 0.1 or self.config.ui.split_ratio > 0.9:
            errors.append("Split ratio must be between 0.1 and 0.9")
        
        return errors
