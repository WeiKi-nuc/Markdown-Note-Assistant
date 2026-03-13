#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PreviewRenderer 类 - 右侧预览区的HTML生成与交互
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable
import re

from ..parser.markdown_parser import MarkdownParser, get_parser


class PreviewRenderer:
    """预览渲染器，负责将 Markdown 渲染为 HTML 并显示"""
    
    # 浅色主题 CSS
    LIGHT_THEME = """
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            font-size: 16px;
            line-height: 1.8;
            color: #333;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px 40px;
            background: #fff;
        }
        h1, h2, h3, h4, h5, h6 {
            margin-top: 24px;
            margin-bottom: 16px;
            font-weight: 600;
            line-height: 1.25;
            color: #2c3e50;
        }
        h1 { font-size: 2em; border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; }
        h2 { font-size: 1.5em; border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; }
        h3 { font-size: 1.25em; }
        h4 { font-size: 1em; }
        p { margin-bottom: 16px; }
        a { color: #0366d6; text-decoration: none; }
        a:hover { text-decoration: underline; }
        code {
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
            background-color: rgba(27, 31, 35, 0.05);
            padding: 0.2em 0.4em;
            border-radius: 3px;
            font-size: 85%;
        }
        pre {
            background-color: #f6f8fa;
            border-radius: 6px;
            padding: 16px;
            overflow: auto;
            line-height: 1.45;
        }
        pre code {
            background-color: transparent;
            padding: 0;
            border-radius: 0;
        }
        blockquote {
            margin: 0;
            padding: 0 1em;
            color: #6a737d;
            border-left: 0.25em solid #dfe2e5;
        }
        ul, ol {
            padding-left: 2em;
            margin-bottom: 16px;
        }
        li { margin-bottom: 0.25em; }
        table {
            border-collapse: collapse;
            width: 100%;
            margin-bottom: 16px;
        }
        th, td {
            padding: 6px 13px;
            border: 1px solid #dfe2e5;
        }
        th { background-color: #f6f8fa; font-weight: 600; }
        tr:nth-child(2n) { background-color: #f6f8fa; }
        img { max-width: 100%; height: auto; }
        hr { height: 0.25em; padding: 0; margin: 24px 0; background-color: #e1e4e8; border: 0; }
        .task-list-item { list-style-type: none; }
        .task-list-item input { margin-right: 8px; }
        .wiki-link { 
            color: #9b59b6; 
            background: #f0e6f5; 
            padding: 2px 6px; 
            border-radius: 3px;
            text-decoration: none;
        }
        .wiki-link:hover { background: #e6d5ed; }
        .highlight { background-color: #fff3cd; padding: 2px; }
    </style>
    """
    
    # 深色主题 CSS
    DARK_THEME = """
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            font-size: 16px;
            line-height: 1.8;
            color: #c9d1d9;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px 40px;
            background: #0d1117;
        }
        h1, h2, h3, h4, h5, h6 {
            margin-top: 24px;
            margin-bottom: 16px;
            font-weight: 600;
            line-height: 1.25;
            color: #e6edf3;
        }
        h1 { font-size: 2em; border-bottom: 1px solid #30363d; padding-bottom: 0.3em; }
        h2 { font-size: 1.5em; border-bottom: 1px solid #30363d; padding-bottom: 0.3em; }
        h3 { font-size: 1.25em; }
        h4 { font-size: 1em; }
        p { margin-bottom: 16px; }
        a { color: #58a6ff; text-decoration: none; }
        a:hover { text-decoration: underline; }
        code {
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
            background-color: rgba(110, 118, 129, 0.4);
            padding: 0.2em 0.4em;
            border-radius: 3px;
            font-size: 85%;
            color: #e6edf3;
        }
        pre {
            background-color: #161b22;
            border-radius: 6px;
            padding: 16px;
            overflow: auto;
            line-height: 1.45;
        }
        pre code {
            background-color: transparent;
            padding: 0;
            border-radius: 0;
            color: #e6edf3;
        }
        blockquote {
            margin: 0;
            padding: 0 1em;
            color: #8b949e;
            border-left: 0.25em solid #30363d;
        }
        ul, ol {
            padding-left: 2em;
            margin-bottom: 16px;
        }
        li { margin-bottom: 0.25em; }
        table {
            border-collapse: collapse;
            width: 100%;
            margin-bottom: 16px;
        }
        th, td {
            padding: 6px 13px;
            border: 1px solid #30363d;
        }
        th { background-color: #161b22; font-weight: 600; }
        tr:nth-child(2n) { background-color: #161b22; }
        img { max-width: 100%; height: auto; }
        hr { height: 0.25em; padding: 0; margin: 24px 0; background-color: #30363d; border: 0; }
        .task-list-item { list-style-type: none; }
        .task-list-item input { margin-right: 8px; }
        .wiki-link { 
            color: #d2a8ff; 
            background: #2d1b3d; 
            padding: 2px 6px; 
            border-radius: 3px;
            text-decoration: none;
        }
        .wiki-link:hover { background: #3d2b4d; }
        .highlight { background-color: #3d2b00; padding: 2px; }
    </style>
    """
    
    def __init__(self, parent, on_link_click: Optional[Callable] = None):
        self.parent = parent
        self.on_link_click = on_link_click
        self.current_theme = 'light'
        self.math_enabled = False
        self.mermaid_enabled = False
        
        # 创建 HTML 查看器（使用 Text 控件模拟）
        self.html_widget = tk.Text(
            parent,
            wrap=tk.WORD,
            padx=20,
            pady=20,
            font=('Segoe UI', 11),
            bg='#ffffff',
            fg='#333333',
            borderwidth=0,
            highlightthickness=0,
            cursor='arrow'
        )
        
        # 配置标签样式
        self._configure_tags()
        
        # 绑定事件
        self._bind_events()
        
        # 初始化解析器
        self.parser = get_parser()
    
    def _configure_tags(self):
        """配置文本标签样式"""
        # 标题样式
        self.html_widget.tag_configure('h1', font=('Segoe UI', 24, 'bold'), foreground='#2c3e50', spacing1=20, spacing3=10)
        self.html_widget.tag_configure('h2', font=('Segoe UI', 20, 'bold'), foreground='#34495e', spacing1=18, spacing3=8)
        self.html_widget.tag_configure('h3', font=('Segoe UI', 16, 'bold'), foreground='#7f8c8d', spacing1=16, spacing3=6)
        
        # 代码样式
        self.html_widget.tag_configure('code', font=('Consolas', 10), background='#f5f5f5', foreground='#e74c3c')
        self.html_widget.tag_configure('code_block', font=('Consolas', 10), background='#f8f8f8', foreground='#2c3e50', spacing1=10, spacing3=10)
        
        # 链接样式
        self.html_widget.tag_configure('link', foreground='#3498db', underline=True)
        
        # 强调样式
        self.html_widget.tag_configure('bold', font=('Segoe UI', 11, 'bold'))
        self.html_widget.tag_configure('italic', font=('Segoe UI', 11, 'italic'))
        
        # 引用样式
        self.html_widget.tag_configure('quote', foreground='#7f8c8d', font=('Segoe UI', 11, 'italic'), lmargin1=20, lmargin2=20)
        
        # 列表样式
        self.html_widget.tag_configure('list', foreground='#27ae60', lmargin1=20, lmargin2=40)
        
        # Wiki 链接样式
        self.html_widget.tag_configure('wiki_link', foreground='#9b59b6', background='#f0e6f5')
        
        # 任务列表
        self.html_widget.tag_configure('task', foreground='#333333')
        self.html_widget.tag_configure('task_done', foreground='#95a5a6', overstrike=True)
    
    def _bind_events(self):
        """绑定事件处理"""
        # 链接点击
        self.html_widget.tag_bind('link', '<Button-1>', self._on_link_click)
        self.html_widget.tag_bind('wiki_link', '<Button-1>', self._on_wiki_link_click)
        
        # 鼠标悬停效果
        self.html_widget.tag_bind('link', '<Enter>', lambda e: self.html_widget.config(cursor='hand2'))
        self.html_widget.tag_bind('link', '<Leave>', lambda e: self.html_widget.config(cursor='arrow'))
        self.html_widget.tag_bind('wiki_link', '<Enter>', lambda e: self.html_widget.config(cursor='hand2'))
        self.html_widget.tag_bind('wiki_link', '<Leave>', lambda e: self.html_widget.config(cursor='arrow'))
    
    def _on_link_click(self, event):
        """处理链接点击"""
        # 获取点击位置的标签
        index = self.html_widget.index(f"@{event.x},{event.y}")
        
        # 获取链接文本
        for tag in ['link', 'wiki_link']:
            ranges = self.html_widget.tag_ranges(tag)
            for i in range(0, len(ranges), 2):
                start, end = ranges[i], ranges[i+1]
                if self.html_widget.compare(start, '<=', index) and self.html_widget.compare(index, '<', end):
                    link_text = self.html_widget.get(start, end)
                    if self.on_link_click:
                        self.on_link_click(link_text, tag)
                    break
    
    def _on_wiki_link_click(self, event):
        """处理 Wiki 链接点击"""
        self._on_link_click(event)
    
    def render(self, markdown_text: str) -> str:
        """
        渲染 Markdown 为 HTML 字符串
        这里返回 HTML 字符串供外部使用
        """
        # 解析 Markdown
        result = self.parser.parse(markdown_text)
        html_content = result['html']
        
        # 选择主题
        theme_css = self.LIGHT_THEME if self.current_theme == 'light' else self.DARK_THEME
        
        # 构建完整 HTML
        full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    {theme_css}
</head>
<body>
{html_content}
</body>
</html>"""
        
        return full_html
    
    def render_to_widget(self, markdown_text: str):
        """渲染 Markdown 到控件"""
        # 清空控件
        self.html_widget.delete('1.0', tk.END)
        
        # 解析内容
        lines = markdown_text.split('\n')
        
        for line in lines:
            self._render_line(line)
            self.html_widget.insert(tk.END, '\n')
    
    def _render_line(self, line: str):
        """渲染单行"""
        # 标题
        if line.startswith('# '):
            self.html_widget.insert(tk.END, line[2:], 'h1')
        elif line.startswith('## '):
            self.html_widget.insert(tk.END, line[3:], 'h2')
        elif line.startswith('### '):
            self.html_widget.insert(tk.END, line[4:], 'h3')
        # 引用
        elif line.startswith('>'):
            self.html_widget.insert(tk.END, line[1:].strip(), 'quote')
        # 代码块
        elif line.startswith('```'):
            self.html_widget.insert(tk.END, line, 'code_block')
        # 行内代码
        elif '`' in line:
            self._render_inline_code(line)
        # 任务列表
        elif re.match(r'\s*[-*]\s+\[[ x]\]', line):
            self._render_task(line)
        # 普通列表
        elif re.match(r'\s*[-*+]\s+', line):
            self._render_list(line)
        # 普通文本
        else:
            self._render_inline_formatting(line)
    
    def _render_inline_code(self, line: str):
        """渲染行内代码"""
        parts = re.split(r'(`[^`]+`)', line)
        for part in parts:
            if part.startswith('`') and part.endswith('`'):
                self.html_widget.insert(tk.END, part[1:-1], 'code')
            else:
                self._render_inline_formatting(part)
    
    def _render_inline_formatting(self, text: str):
        """渲染行内格式（粗体、斜体、链接等）"""
        # 处理 Wiki 链接 [[...]]
        wiki_pattern = r'(\[\[[^\]]+\]\])'
        parts = re.split(wiki_pattern, text)
        
        for part in parts:
            if part.startswith('[[') and part.endswith(']]'):
                # Wiki 链接
                self.html_widget.insert(tk.END, part[2:-2], 'wiki_link')
            else:
                # 处理普通链接 [...](...)
                self._render_markdown_links(part)
    
    def _render_markdown_links(self, text: str):
        """渲染 Markdown 链接"""
        link_pattern = r'(\[([^\]]+)\]\(([^)]+)\))'
        parts = re.split(link_pattern, text)
        
        i = 0
        while i < len(parts):
            if i + 2 < len(parts) and parts[i].endswith(']') is False:
                # 这是链接的完整匹配
                link_text = parts[i+1]
                self.html_widget.insert(tk.END, link_text, 'link')
                i += 3
            else:
                # 处理粗体和斜体
                self._render_emphasis(parts[i])
                i += 1
    
    def _render_emphasis(self, text: str):
        """渲染强调（粗体、斜体）"""
        # 粗体 **text**
        bold_pattern = r'(\*\*[^*]+\*\*)'
        parts = re.split(bold_pattern, text)
        
        for part in parts:
            if part.startswith('**') and part.endswith('**'):
                self.html_widget.insert(tk.END, part[2:-2], 'bold')
            else:
                # 斜体 *text*
                italic_pattern = r'(\*[^*]+\*)'
                italic_parts = re.split(italic_pattern, part)
                for italic_part in italic_parts:
                    if italic_part.startswith('*') and italic_part.endswith('*'):
                        self.html_widget.insert(tk.END, italic_part[1:-1], 'italic')
                    else:
                        self.html_widget.insert(tk.END, italic_part)
    
    def _render_task(self, line: str):
        """渲染任务列表"""
        match = re.match(r'(\s*)([-*])\s+\[([ x])\]\s+(.*)', line)
        if match:
            indent = match.group(1)
            checked = match.group(3) == 'x'
            text = match.group(4)
            
            self.html_widget.insert(tk.END, indent + ('[x] ' if checked else '[ ] ') + text, 
                                   'task_done' if checked else 'task')
    
    def _render_list(self, line: str):
        """渲染列表"""
        match = re.match(r'(\s*)([-*+])\s+(.*)', line)
        if match:
            indent = match.group(1)
            marker = match.group(2)
            text = match.group(3)
            
            self.html_widget.insert(tk.END, indent + marker + ' ', 'list')
            self._render_inline_formatting(text)
    
    def scroll_to_anchor(self, heading_id: str):
        """滚动到指定标题"""
        # 在控件中查找对应的标题
        # TODO: 实现锚点滚动
        pass
    
    def get_scroll_position(self) -> float:
        """获取当前滚动位置"""
        return self.html_widget.yview()[0]
    
    def set_scroll_position(self, position: float):
        """设置滚动位置"""
        self.html_widget.yview_moveto(position)
    
    def apply_theme(self, theme: str):
        """切换主题（light/dark）"""
        self.current_theme = theme
        
        if theme == 'dark':
            self.html_widget.config(bg='#0d1117', fg='#c9d1d9')
            # 更新标签颜色
            self.html_widget.tag_configure('h1', foreground='#e6edf3')
            self.html_widget.tag_configure('h2', foreground='#e6edf3')
            self.html_widget.tag_configure('h3', foreground='#e6edf3')
            self.html_widget.tag_configure('code', background='rgba(110, 118, 129, 0.4)', foreground='#e6edf3')
            self.html_widget.tag_configure('code_block', background='#161b22', foreground='#e6edf3')
            self.html_widget.tag_configure('quote', foreground='#8b949e')
            self.html_widget.tag_configure('link', foreground='#58a6ff')
            self.html_widget.tag_configure('wiki_link', foreground='#d2a8ff', background='#2d1b3d')
        else:
            self.html_widget.config(bg='#ffffff', fg='#333333')
            # 恢复浅色主题标签
            self._configure_tags()
    
    def get_widget(self):
        """获取控件"""
        return self.html_widget
    
    def highlight_text(self, text: str, keyword: str):
        """高亮搜索关键词"""
        # 移除之前的高亮
        self.html_widget.tag_remove('highlight', '1.0', tk.END)
        
        # 查找并高亮
        start = '1.0'
        while True:
            pos = self.html_widget.search(keyword, start, stopindex=tk.END, nocase=True)
            if not pos:
                break
            end = f"{pos}+{len(keyword)}c"
            self.html_widget.tag_add('highlight', pos, end)
            start = end
        
        # 配置高亮样式
        self.html_widget.tag_configure('highlight', background='#fff3cd')
