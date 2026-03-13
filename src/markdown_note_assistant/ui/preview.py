"""
Preview module - renders markdown to HTML for display.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import tkinter as tk
from tkinter import ttk

from markdown_note_assistant.core.parser import MarkdownParser

if TYPE_CHECKING:
    from markdown_note_assistant.ui.main_window import MainWindow


class PreviewRenderer:
    """
    Preview Renderer - renders markdown to HTML.
    
    Features:
    - GitHub Flavored Markdown
    - Code highlighting
    - Math rendering (MathJax)
    - Mermaid diagrams
    - Theme support
    """
    
    def __init__(
        self,
        math_enabled: bool = True,
        mermaid_enabled: bool = True,
        theme: str = "light",
    ):
        self.math_enabled = math_enabled
        self.mermaid_enabled = mermaid_enabled
        self.theme = theme
        
        self._parser = MarkdownParser()
    
    def render(self, markdown_text: str) -> str:
        """Render markdown to HTML."""
        html_body = self._parser.render_to_html(markdown_text)
        
        html_body = self._process_wiki_links(html_body)
        
        return self._wrap_html(html_body)
    
    def _process_wiki_links(self, html: str) -> str:
        """Process wiki links in HTML."""
        import re
        
        pattern = re.compile(r'\[\[([^\]]+)\]\]')
        
        def replace_link(match):
            link_text = match.group(1)
            parts = link_text.split("|")
            target = parts[0].strip()
            display = parts[1].strip() if len(parts) > 1 else target
            
            return f'<a href="note://{target}" class="wiki-link">{display}</a>'
        
        return pattern.sub(replace_link, html)
    
    def _wrap_html(self, body: str) -> str:
        """Wrap HTML body with full document structure."""
        mathjax_script = ""
        if self.math_enabled:
            mathjax_script = """
<script>
MathJax = {
  tex: {
    inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
    displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']]
  }
};
</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
"""
        
        mermaid_script = ""
        if self.mermaid_enabled:
            mermaid_script = """
<script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
<script>mermaid.initialize({startOnLoad:true});</script>
"""
        
        return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
{self._get_css()}
</style>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/highlight.js@11/styles/github.min.css">
<script src="https://cdn.jsdelivr.net/npm/highlight.js@11"></script>
<script>hljs.highlightAll();</script>
{mathjax_script}
{mermaid_script}
</head>
<body>
{body}
</body>
</html>"""
    
    def _get_css(self) -> str:
        """Get the CSS styles for the preview."""
        if self.theme == "dark":
            return self._get_dark_css()
        else:
            return self._get_light_css()
    
    def _get_light_css(self) -> str:
        """Get light theme CSS."""
        return """
:root {
    --bg-color: #ffffff;
    --text-color: #24292f;
    --heading-color: #24292f;
    --link-color: #0969da;
    --code-bg: #f6f8fa;
    --blockquote-border: #d0d7de;
    --table-border: #d0d7de;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    font-size: 15px;
    line-height: 1.8;
    color: var(--text-color);
    background-color: var(--bg-color);
    padding: 20px;
    max-width: 900px;
    margin: 0 auto;
}

h1, h2, h3, h4, h5, h6 {
    color: var(--heading-color);
    margin-top: 24px;
    margin-bottom: 16px;
    font-weight: 600;
    line-height: 1.25;
}

h1 { font-size: 2em; border-bottom: 1px solid var(--table-border); padding-bottom: .3em; }
h2 { font-size: 1.5em; border-bottom: 1px solid var(--table-border); padding-bottom: .3em; }
h3 { font-size: 1.25em; }
h4 { font-size: 1em; }
h5 { font-size: .875em; }
h6 { font-size: .85em; color: #57606a; }

p { margin: 0 0 16px; }

a {
    color: var(--link-color);
    text-decoration: none;
}

a:hover { text-decoration: underline; }

.wiki-link {
    color: #705DF2;
    background-color: rgba(112, 93, 242, 0.1);
    padding: 0 4px;
    border-radius: 4px;
}

.wiki-link:hover {
    background-color: rgba(112, 93, 242, 0.2);
}

code {
    padding: .2em .4em;
    margin: 0;
    font-size: 85%;
    background-color: var(--code-bg);
    border-radius: 6px;
    font-family: ui-monospace, SFMono-Regular, SF Mono, Menlo, Consolas, monospace;
}

pre {
    padding: 16px;
    overflow: auto;
    font-size: 85%;
    line-height: 1.45;
    background-color: var(--code-bg);
    border-radius: 6px;
}

pre code {
    padding: 0;
    background-color: transparent;
}

blockquote {
    padding: 0 1em;
    color: #57606a;
    border-left: .25em solid var(--blockquote-border);
    margin: 0 0 16px;
}

ul, ol {
    padding-left: 2em;
    margin: 0 0 16px;
}

li { margin: 4px 0; }

li.task-list-item {
    list-style: none;
    margin-left: -1.5em;
}

table {
    border-spacing: 0;
    border-collapse: collapse;
    margin: 0 0 16px;
    width: 100%;
}

table th, table td {
    padding: 6px 13px;
    border: 1px solid var(--table-border);
}

table th {
    font-weight: 600;
    background-color: var(--code-bg);
}

table tr:nth-child(2n) {
    background-color: var(--code-bg);
}

hr {
    height: .25em;
    padding: 0;
    margin: 24px 0;
    background-color: var(--table-border);
    border: 0;
}

img {
    max-width: 100%;
    height: auto;
    border-radius: 6px;
}

.highlight {
    background-color: #fff8c5;
    padding: 0 4px;
    border-radius: 4px;
}
"""
    
    def _get_dark_css(self) -> str:
        """Get dark theme CSS."""
        return """
:root {
    --bg-color: #0d1117;
    --text-color: #c9d1d9;
    --heading-color: #c9d1d9;
    --link-color: #58a6ff;
    --code-bg: #161b22;
    --blockquote-border: #30363d;
    --table-border: #30363d;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    font-size: 15px;
    line-height: 1.8;
    color: var(--text-color);
    background-color: var(--bg-color);
    padding: 20px;
    max-width: 900px;
    margin: 0 auto;
}

h1, h2, h3, h4, h5, h6 {
    color: var(--heading-color);
    margin-top: 24px;
    margin-bottom: 16px;
    font-weight: 600;
    line-height: 1.25;
}

h1 { font-size: 2em; border-bottom: 1px solid var(--table-border); padding-bottom: .3em; }
h2 { font-size: 1.5em; border-bottom: 1px solid var(--table-border); padding-bottom: .3em; }
h3 { font-size: 1.25em; }
h4 { font-size: 1em; }
h5 { font-size: .875em; }
h6 { font-size: .85em; color: #8b949e; }

p { margin: 0 0 16px; }

a {
    color: var(--link-color);
    text-decoration: none;
}

a:hover { text-decoration: underline; }

.wiki-link {
    color: #a5d6ff;
    background-color: rgba(165, 214, 255, 0.1);
    padding: 0 4px;
    border-radius: 4px;
}

code {
    padding: .2em .4em;
    margin: 0;
    font-size: 85%;
    background-color: var(--code-bg);
    border-radius: 6px;
    font-family: ui-monospace, SFMono-Regular, SF Mono, Menlo, Consolas, monospace;
}

pre {
    padding: 16px;
    overflow: auto;
    font-size: 85%;
    line-height: 1.45;
    background-color: var(--code-bg);
    border-radius: 6px;
}

pre code {
    padding: 0;
    background-color: transparent;
}

blockquote {
    padding: 0 1em;
    color: #8b949e;
    border-left: .25em solid var(--blockquote-border);
    margin: 0 0 16px;
}

ul, ol {
    padding-left: 2em;
    margin: 0 0 16px;
}

li { margin: 4px 0; }

table {
    border-spacing: 0;
    border-collapse: collapse;
    margin: 0 0 16px;
    width: 100%;
}

table th, table td {
    padding: 6px 13px;
    border: 1px solid var(--table-border);
}

table th {
    font-weight: 600;
    background-color: var(--code-bg);
}

table tr:nth-child(2n) {
    background-color: var(--code-bg);
}

hr {
    height: .25em;
    padding: 0;
    margin: 24px 0;
    background-color: var(--table-border);
    border: 0;
}

img {
    max-width: 100%;
    height: auto;
    border-radius: 6px;
}
"""
    
    def set_theme(self, theme: str) -> None:
        """Set the preview theme."""
        self.theme = theme
    
    def apply_custom_css(self, css_path: Path) -> None:
        """Apply custom CSS from a file."""
        try:
            with open(css_path, "r", encoding="utf-8") as f:
                self._custom_css = f.read()
        except Exception as e:
            print(f"Error loading custom CSS: {e}")


class PreviewPane:
    """
    Preview Pane - displays rendered markdown in a web view.
    
    Features:
    - HTML rendering
    - Sync scrolling
    - Click navigation
    - Theme switching
    """
    
    def __init__(self, parent: tk.Widget, main_window: "MainWindow"):
        self.parent = parent
        self.main_window = main_window
        
        self.frame = ttk.Frame(parent)
        
        self._renderer = PreviewRenderer()
        self._current_html = ""
        self._scroll_position = 0.0
        
        self._create_widgets()
        self._bind_events()
    
    def _create_widgets(self) -> None:
        toolbar = ttk.Frame(self.frame)
        toolbar.pack(side="top", fill="x")
        
        ttk.Label(toolbar, text="预览").pack(side="left", padx=5)
        
        self.theme_var = tk.StringVar(value="light")
        ttk.Radiobutton(
            toolbar, text="浅色", variable=self.theme_var,
            value="light", command=self._on_theme_change
        ).pack(side="right", padx=2)
        ttk.Radiobutton(
            toolbar, text="深色", variable=self.theme_var,
            value="dark", command=self._on_theme_change
        ).pack(side="right", padx=2)
        
        self.webview = tk.Text(
            self.frame,
            wrap="word",
            state="disabled",
            font=("Segoe UI", 11),
            padx=10,
            pady=10,
        )
        self.webview.pack(fill="both", expand=True)
        
        self._configure_tags()
        
        try:
            import tkinterweb
            
            self._use_htmlview = True
            self._setup_htmlview()
        except ImportError:
            self._use_htmlview = False
    
    def _setup_htmlview(self) -> None:
        """Setup HTML viewer if available."""
        self.webview.pack_forget()
        
        try:
            import tkinterweb
            
            self.htmlview = tkinterweb.HtmlFrame(self.frame)
            self.htmlview.pack(fill="both", expand=True)
        except ImportError:
            self.webview = tk.Text(
                self.frame,
                wrap="word",
                state="disabled",
                font=("Segoe UI", 11),
                padx=10,
                pady=10,
            )
            self.webview.pack(fill="both", expand=True)
            self._configure_tags()
    
    def _configure_tags(self) -> None:
        """Configure text tags for basic rendering."""
        self.webview.tag_configure("h1", font=("Segoe UI", 24, "bold"), spacing3=10)
        self.webview.tag_configure("h2", font=("Segoe UI", 20, "bold"), spacing3=8)
        self.webview.tag_configure("h3", font=("Segoe UI", 16, "bold"), spacing3=6)
        self.webview.tag_configure("h4", font=("Segoe UI", 14, "bold"), spacing3=4)
        self.webview.tag_configure("h5", font=("Segoe UI", 12, "bold"), spacing3=4)
        self.webview.tag_configure("h6", font=("Segoe UI", 11, "bold"), spacing3=4)
        self.webview.tag_configure("bold", font=("Segoe UI", 11, "bold"))
        self.webview.tag_configure("italic", font=("Segoe UI", 11, "italic"))
        self.webview.tag_configure("code", font=("Consolas", 10), background="#f5f5f5")
        self.webview.tag_configure("link", foreground="#0969da", underline=True)
        self.webview.tag_configure("blockquote", foreground="#666666", lmargin1=20, lmargin2=20)
    
    def _bind_events(self) -> None:
        self.webview.bind("<Button-1>", self._on_click)
        self.webview.bind("<MouseWheel>", self._on_scroll)
        self.webview.bind("<Button-4>", self._on_scroll)
        self.webview.bind("<Button-5>", self._on_scroll)
    
    def render(self, markdown_text: str) -> None:
        """Render markdown content."""
        self._current_html = self._renderer.render(markdown_text)
        
        if self._use_htmlview and hasattr(self, "htmlview"):
            self.htmlview.load_html(self._current_html)
        else:
            self._render_as_text(markdown_text)
    
    def _render_as_text(self, markdown_text: str) -> None:
        """Render markdown as formatted text (fallback)."""
        self.webview.config(state="normal")
        self.webview.delete("1.0", "end")
        
        import re
        
        lines = markdown_text.split("\n")
        for line in lines:
            if line.startswith("# "):
                self.webview.insert("end", line[2:] + "\n", "h1")
            elif line.startswith("## "):
                self.webview.insert("end", line[3:] + "\n", "h2")
            elif line.startswith("### "):
                self.webview.insert("end", line[4:] + "\n", "h3")
            elif line.startswith("#### "):
                self.webview.insert("end", line[5:] + "\n", "h4")
            elif line.startswith("##### "):
                self.webview.insert("end", line[6:] + "\n", "h5")
            elif line.startswith("###### "):
                self.webview.insert("end", line[7:] + "\n", "h6")
            elif line.startswith("> "):
                self.webview.insert("end", line[2:] + "\n", "blockquote")
            elif line.startswith("```"):
                pass
            else:
                self.webview.insert("end", line + "\n")
        
        self.webview.config(state="disabled")
    
    def _on_click(self, event) -> None:
        """Handle click events."""
        index = self.webview.index(f"@{event.x},{event.y}")
        tags = self.webview.tag_names(index)
        
        if "link" in tags:
            pass
    
    def _on_scroll(self, event) -> None:
        """Handle scroll events."""
        pass
    
    def _on_theme_change(self) -> None:
        """Handle theme change."""
        theme = self.theme_var.get()
        self._renderer.set_theme(theme)
        
        if self._current_html:
            self.render(self._current_html)
    
    def sync_scroll(self, position: float) -> None:
        """Sync scroll position with editor."""
        self._scroll_position = position
        
        if hasattr(self, "htmlview"):
            try:
                self.htmlview.yview_moveto(position)
            except Exception:
                pass
    
    def scroll_to_anchor(self, anchor: str) -> None:
        """Scroll to a heading anchor."""
        pass
    
    def get_html(self) -> str:
        """Get the current HTML content."""
        return self._current_html
    
    def set_math_enabled(self, enabled: bool) -> None:
        """Enable or disable math rendering."""
        self._renderer.math_enabled = enabled
    
    def set_mermaid_enabled(self, enabled: bool) -> None:
        """Enable or disable mermaid rendering."""
        self._renderer.mermaid_enabled = enabled
    
    def print_preview(self) -> None:
        """Print the preview content."""
        pass
    
    def export_html(self, path: Path) -> None:
        """Export the HTML to a file."""
        with open(path, "w", encoding="utf-8") as f:
            f.write(self._current_html)
