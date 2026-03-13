import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont
import os
from typing import Optional
import re

try:
    import webview
except ImportError:
    webview = None

from ..core.parser import PreviewRenderer


class PreviewPane:
    def __init__(self, parent: tk.Widget):
        self.parent = parent
        self.renderer = PreviewRenderer()
        self._current_html = ""
        self._scroll_position = 0.0
        
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        self._create_webview()
    
    def _create_webview(self):
        self.html_label = tk.Text(
            self.frame,
            wrap=tk.WORD,
            font=('Segoe UI', 11),
            state=tk.DISABLED,
            background='#ffffff'
        )
        self.html_label.pack(fill=tk.BOTH, expand=True)
        
        self.scrollbar = ttk.Scrollbar(self.frame, command=self.html_label.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.html_label.config(yscrollcommand=self._on_scroll)
        
        self.default_html = """
        <html>
        <body style="padding:20px; font-family:Segoe UI,sans-serif;">
        <h3>Markdown 预览区</h3>
        <p>在左侧编辑区输入 Markdown 内容，预览将实时显示在这里。</p>
        </body>
        </html>
        """
        self._render_simple_html(self.default_html)
    
    def _on_scroll(self, *args):
        self.scrollbar.set(*args)
        self._scroll_position = float(args[0])
    
    def _render_simple_html(self, html: str):
        self.html_label.config(state=tk.NORMAL)
        self.html_label.delete('1.0', tk.END)
        
        text = self._strip_html(html)
        self.html_label.insert('1.0', text)
        
        self._apply_simple_formatting()
        self.html_label.config(state=tk.DISABLED)
    
    def _strip_html(self, html: str) -> str:
        text = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', '', text)
        import html
        text = html.unescape(text)
        return text
    
    def _apply_simple_formatting(self):
        text = self.html_label.get('1.0', tk.END)
        
        self.html_label.tag_configure('h1', font=('Segoe UI', 16, 'bold'), spacing3=10)
        self.html_label.tag_configure('h2', font=('Segoe UI', 14, 'bold'), spacing3=8)
        self.html_label.tag_configure('h3', font=('Segoe UI', 12, 'bold'), spacing3=6)
        self.html_label.tag_configure('bold', font=('Segoe UI', 11, 'bold'))
        self.html_label.tag_configure('italic', font=('Segoe UI', 11, 'italic'))
        self.html_label.tag_configure('code', font=('Consolas', 10), background='#f0f0f0')
        self.html_label.tag_configure('link', foreground='#0366d6', underline=True)
        
        lines = text.split('\n')
        for i, line in enumerate(lines, 1):
            if line.startswith('# '):
                self.html_label.tag_add('h1', f'{i}.0', f'{i}.end')
            elif line.startswith('## '):
                self.html_label.tag_add('h2', f'{i}.0', f'{i}.end')
            elif line.startswith('### '):
                self.html_label.tag_add('h3', f'{i}.0', f'{i}.end')
    
    def render(self, markdown_text: str):
        if not markdown_text.strip():
            self._render_simple_html(self.default_html)
            return
        
        html = self.renderer.render(markdown_text)
        self._current_html = html
        self._render_simple_html(html)
    
    def scroll_to_anchor(self, heading_id: str):
        pass
    
    def get_scroll_position(self) -> float:
        return self._scroll_position
    
    def set_scroll_position(self, pos: float):
        self.html_label.yview_moveto(pos)
    
    def apply_theme(self, css_path: str):
        self.renderer.apply_theme(css_path)
