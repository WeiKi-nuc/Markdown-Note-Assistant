"""
Markdown Syntax Highlighter module for Tkinter Text widget.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from pygments import highlight
from pygments.formatters import get_formatter_by_name
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.util import ClassNotFound


@dataclass
class HighlightRule:
    """A syntax highlighting rule."""
    pattern: re.Pattern
    tag: str
    group: int = 0


class MarkdownHighlighter:
    """
    Markdown Syntax Highlighter for Tkinter Text widget.
    
    Provides real-time syntax highlighting for:
    - Headings
    - Bold, italic, strikethrough
    - Code blocks and inline code
    - Links and images
    - Lists (ordered and unordered)
    - Blockquotes
    - Tables
    - YAML frontmatter
    - Wiki links
    """
    
    def __init__(
        self,
        text_widget,
        theme: str = "light",
        custom_colors: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize the highlighter.
        
        Args:
            text_widget: Tkinter Text widget to highlight
            theme: Color theme ('light' or 'dark')
            custom_colors: Custom color overrides
        """
        self.text_widget = text_widget
        self.theme = theme
        self.custom_colors = custom_colors or {}
        
        self._setup_colors()
        self._setup_tags()
        self._setup_rules()
        
        self._enabled = True
        self._highlight_scheduled = False
    
    def _setup_colors(self) -> None:
        """Set up color schemes."""
        light_colors = {
            "heading": "#0066CC",
            "heading_marker": "#0066CC",
            "bold": "#000000",
            "italic": "#333333",
            "strikethrough": "#666666",
            "code_block": "#F5F5F5",
            "code_inline": "#E8E8E8",
            "code_text": "#D63384",
            "link": "#0066CC",
            "link_text": "#0066CC",
            "link_url": "#666666",
            "image": "#28A745",
            "list_marker": "#0066CC",
            "blockquote": "#6A737D",
            "blockquote_marker": "#6A737D",
            "hr": "#CCCCCC",
            "table": "#0066CC",
            "frontmatter": "#6A737D",
            "frontmatter_marker": "#CC00CC",
            "wiki_link": "#705DF2",
            "wiki_link_bracket": "#705DF2",
            "task_done": "#28A745",
            "task_pending": "#6A737D",
            "escape": "#D63384",
            "comment": "#6A737D",
        }
        
        dark_colors = {
            "heading": "#79C0FF",
            "heading_marker": "#79C0FF",
            "bold": "#FFFFFF",
            "italic": "#C9D1D9",
            "strikethrough": "#8B949E",
            "code_block": "#161B22",
            "code_inline": "#21262D",
            "code_text": "#FF7B72",
            "link": "#58A6FF",
            "link_text": "#58A6FF",
            "link_url": "#8B949E",
            "image": "#7EE787",
            "list_marker": "#79C0FF",
            "blockquote": "#8B949E",
            "blockquote_marker": "#8B949E",
            "hr": "#30363D",
            "table": "#79C0FF",
            "frontmatter": "#8B949E",
            "frontmatter_marker": "#D2A8FF",
            "wiki_link": "#A5D6FF",
            "wiki_link_bracket": "#A5D6FF",
            "task_done": "#7EE787",
            "task_pending": "#8B949E",
            "escape": "#FF7B72",
            "comment": "#8B949E",
        }
        
        base_colors = light_colors if self.theme == "light" else dark_colors
        self.colors = {**base_colors, **self.custom_colors}
    
    def _setup_tags(self) -> None:
        """Set up text widget tags for highlighting."""
        tag_configs = {
            "heading": {
                "foreground": self.colors["heading"],
                "font": ("", -1, "bold"),
            },
            "heading_marker": {
                "foreground": self.colors["heading_marker"],
            },
            "bold": {
                "font": ("", -1, "bold"),
            },
            "italic": {
                "font": ("", -1, "italic"),
            },
            "strikethrough": {
                "overstrike": True,
                "foreground": self.colors["strikethrough"],
            },
            "code_block": {
                "background": self.colors["code_block"],
                "font": ("Consolas", -1),
            },
            "code_inline": {
                "background": self.colors["code_inline"],
                "font": ("Consolas", -1),
            },
            "code_text": {
                "foreground": self.colors["code_text"],
            },
            "link": {
                "foreground": self.colors["link"],
                "underline": True,
            },
            "link_text": {
                "foreground": self.colors["link_text"],
            },
            "link_url": {
                "foreground": self.colors["link_url"],
            },
            "image": {
                "foreground": self.colors["image"],
            },
            "list_marker": {
                "foreground": self.colors["list_marker"],
            },
            "blockquote": {
                "foreground": self.colors["blockquote"],
                "font": ("", -1, "italic"),
            },
            "blockquote_marker": {
                "foreground": self.colors["blockquote_marker"],
            },
            "hr": {
                "foreground": self.colors["hr"],
            },
            "table": {
                "foreground": self.colors["table"],
            },
            "frontmatter": {
                "foreground": self.colors["frontmatter"],
            },
            "frontmatter_marker": {
                "foreground": self.colors["frontmatter_marker"],
            },
            "wiki_link": {
                "foreground": self.colors["wiki_link"],
                "underline": True,
            },
            "wiki_link_bracket": {
                "foreground": self.colors["wiki_link_bracket"],
            },
            "task_done": {
                "foreground": self.colors["task_done"],
            },
            "task_pending": {
                "foreground": self.colors["task_pending"],
            },
            "escape": {
                "foreground": self.colors["escape"],
            },
            "comment": {
                "foreground": self.colors["comment"],
            },
        }
        
        for tag_name, config in tag_configs.items():
            self.text_widget.tag_configure(tag_name, **config)
    
    def _setup_rules(self) -> None:
        """Set up highlighting rules."""
        self.rules: List[HighlightRule] = [
            HighlightRule(
                pattern=re.compile(r"^(#{1,6})\s+.+$", re.MULTILINE),
                tag="heading",
            ),
            HighlightRule(
                pattern=re.compile(r"^(#{1,6})(?=\s)", re.MULTILINE),
                tag="heading_marker",
            ),
            HighlightRule(
                pattern=re.compile(r"\*\*[^*]+\*\*"),
                tag="bold",
            ),
            HighlightRule(
                pattern=re.compile(r"__[^_]+__"),
                tag="bold",
            ),
            HighlightRule(
                pattern=re.compile(r"\*[^*]+\*"),
                tag="italic",
            ),
            HighlightRule(
                pattern=re.compile(r"_[^_]+_"),
                tag="italic",
            ),
            HighlightRule(
                pattern=re.compile(r"~~[^~]+~~"),
                tag="strikethrough",
            ),
            HighlightRule(
                pattern=re.compile(r"`[^`]+`"),
                tag="code_inline",
            ),
            HighlightRule(
                pattern=re.compile(r"!\[[^\]]*\]\([^)]+\)"),
                tag="image",
            ),
            HighlightRule(
                pattern=re.compile(r"(?<!!)\[[^\]]+\]\([^)]+\)"),
                tag="link",
            ),
            HighlightRule(
                pattern=re.compile(r"\[\[[^\]]+\]\]"),
                tag="wiki_link",
            ),
            HighlightRule(
                pattern=re.compile(r"^\s*[-*+]\s+", re.MULTILINE),
                tag="list_marker",
            ),
            HighlightRule(
                pattern=re.compile(r"^\s*\d+\.\s+", re.MULTILINE),
                tag="list_marker",
            ),
            HighlightRule(
                pattern=re.compile(r"^\s*[-*+]\s+\[[xX ]\]", re.MULTILINE),
                tag="task_done",
            ),
            HighlightRule(
                pattern=re.compile(r"^>\s+", re.MULTILINE),
                tag="blockquote_marker",
            ),
            HighlightRule(
                pattern=re.compile(r"^---\s*$", re.MULTILINE),
                tag="frontmatter_marker",
            ),
            HighlightRule(
                pattern=re.compile(r"^-{3,}\s*$", re.MULTILINE),
                tag="hr",
            ),
            HighlightRule(
                pattern=re.compile(r"^\|.*\|$", re.MULTILINE),
                tag="table",
            ),
            HighlightRule(
                pattern=re.compile(r"\\[\\`*_{}\[\]()#+\-.!]"),
                tag="escape",
            ),
        ]
    
    def highlight(self, content: Optional[str] = None) -> None:
        """
        Apply syntax highlighting to the text widget.
        
        Args:
            content: Content to highlight (uses widget content if None)
        """
        if not self._enabled:
            return
        
        for tag in self.text_widget.tag_names():
            if tag != "sel":
                self.text_widget.tag_remove(tag, "1.0", "end")
        
        if content is None:
            content = self.text_widget.get("1.0", "end-1c")
        
        self._highlight_frontmatter(content)
        
        self._highlight_code_blocks(content)
        
        for rule in self.rules:
            self._apply_rule(rule, content)
    
    def _apply_rule(self, rule: HighlightRule, content: str) -> None:
        """Apply a single highlighting rule."""
        for match in rule.pattern.finditer(content):
            start = match.start()
            end = match.end()
            
            start_index = self._offset_to_index(start, content)
            end_index = self._offset_to_index(end, content)
            
            self.text_widget.tag_add(rule.tag, start_index, end_index)
    
    def _offset_to_index(self, offset: int, content: str) -> str:
        """Convert a character offset to a Tkinter text index."""
        line = 1
        col = 0
        current = 0
        
        for char in content:
            if current >= offset:
                break
            if char == "\n":
                line += 1
                col = 0
            else:
                col += 1
            current += 1
        
        return f"{line}.{col}"
    
    def _highlight_frontmatter(self, content: str) -> None:
        """Highlight YAML frontmatter."""
        if not content.startswith("---"):
            return
        
        lines = content.split("\n")
        end_line = None
        
        for i, line in enumerate(lines[1:], 2):
            if line.strip() == "---":
                end_line = i
                break
        
        if end_line:
            self.text_widget.tag_add("frontmatter", "1.0", f"{end_line}.end")
            self.text_widget.tag_add("frontmatter_marker", "1.0", "1.end")
            self.text_widget.tag_add("frontmatter_marker", f"{end_line}.0", f"{end_line}.end")
    
    def _highlight_code_blocks(self, content: str) -> None:
        """Highlight fenced code blocks."""
        pattern = re.compile(r"^```(\w*)\n(.*?)^```", re.MULTILINE | re.DOTALL)
        
        for match in pattern.finditer(content):
            start = match.start()
            end = match.end()
            lang = match.group(1)
            code = match.group(2)
            
            start_index = self._offset_to_index(start, content)
            end_index = self._offset_to_index(end, content)
            
            self.text_widget.tag_add("code_block", start_index, end_index)
            
            if lang:
                self._highlight_code_language(code, start_index, lang)
    
    def _highlight_code_language(self, code: str, start_index: str, lang: str) -> None:
        """Apply syntax highlighting for a specific language."""
        try:
            lexer = get_lexer_by_name(lang, stripall=True)
        except ClassNotFound:
            try:
                lexer = guess_lexer(code)
            except ClassNotFound:
                return
        
        formatter = TkFormatter(start_index)
        
        try:
            tokens = lexer.get_tokens(code)
            self._apply_pygments_tokens(tokens, formatter)
        except Exception:
            pass
    
    def _apply_pygments_tokens(self, tokens, formatter) -> None:
        """Apply pygments tokens to the text widget."""
        for token_type, token_value in tokens:
            if not token_value:
                continue
            
            tag_name = self._get_pygments_tag_name(token_type)
            if tag_name:
                start, end = formatter.get_position(token_value)
                self.text_widget.tag_add(tag_name, start, end)
    
    def _get_pygments_tag_name(self, token_type) -> Optional[str]:
        """Convert a pygments token type to a tag name."""
        token_str = str(token_type)
        
        if "Keyword" in token_str:
            return "code_text"
        elif "String" in token_str:
            return "link_text"
        elif "Comment" in token_str:
            return "comment"
        elif "Number" in token_str:
            return "code_text"
        elif "Name.Function" in token_str:
            return "code_text"
        elif "Name.Class" in token_str:
            return "code_text"
        
        return None
    
    def highlight_line(self, line_number: int) -> None:
        """
        Highlight a single line.
        
        Args:
            line_number: Line number to highlight (1-indexed)
        """
        line_start = f"{line_number}.0"
        line_end = f"{line_number}.end"
        content = self.text_widget.get(line_start, line_end)
        
        for tag in self.text_widget.tag_names():
            if tag != "sel":
                self.text_widget.tag_remove(tag, line_start, line_end)
        
        for rule in self.rules:
            for match in rule.pattern.finditer(content):
                start_col = match.start()
                end_col = match.end()
                self.text_widget.tag_add(
                    rule.tag,
                    f"{line_number}.{start_col}",
                    f"{line_number}.{end_col}",
                )
    
    def enable(self) -> None:
        """Enable highlighting."""
        self._enabled = True
        self.highlight()
    
    def disable(self) -> None:
        """Disable highlighting."""
        self._enabled = False
        for tag in self.text_widget.tag_names():
            if tag != "sel":
                self.text_widget.tag_remove(tag, "1.0", "end")
    
    def set_theme(self, theme: str) -> None:
        """Change the color theme."""
        self.theme = theme
        self._setup_colors()
        self._setup_tags()
        if self._enabled:
            self.highlight()
    
    def update_colors(self, colors: Dict[str, str]) -> None:
        """Update custom colors."""
        self.custom_colors.update(colors)
        self._setup_colors()
        self._setup_tags()
        if self._enabled:
            self.highlight()


class TkFormatter:
    """Helper class for pygments formatting with Tkinter indices."""
    
    def __init__(self, start_index: str):
        """Initialize with a starting index."""
        self.start_line = int(start_index.split(".")[0])
        self.start_col = int(start_index.split(".")[1])
        self.current_line = self.start_line
        self.current_col = self.start_col
    
    def get_position(self, text: str) -> Tuple[str, str]:
        """Get start and end positions for text."""
        start = f"{self.current_line}.{self.current_col}"
        
        for char in text:
            if char == "\n":
                self.current_line += 1
                self.current_col = 0
            else:
                self.current_col += 1
        
        end = f"{self.current_line}.{self.current_col}"
        return start, end
