#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Editor 类 - 左侧编辑区的功能封装
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import re
from typing import Callable, Optional

from ..core.note import Note


class Editor:
    """编辑器组件，封装文本编辑功能"""
    
    def __init__(self, parent, on_change_callback: Optional[Callable] = None):
        self.parent = parent
        self.current_note: Optional[Note] = None
        self.on_change_callback = on_change_callback
        self._change_after_id = None
        self._is_loading = False
        
        # 创建文本控件
        self.text_widget = scrolledtext.ScrolledText(
            parent,
            wrap=tk.WORD,
            undo=True,
            maxundo=-1,
            padx=10,
            pady=10,
            font=('Consolas', 12),
            bg='#ffffff',
            fg='#333333',
            insertbackground='#333333',
            selectbackground='#b4d7ff',
            selectforeground='#000000',
            borderwidth=0,
            highlightthickness=0
        )
        
        # 配置标签样式（语法高亮）
        self._configure_tags()
        
        # 绑定事件
        self._bind_events()
    
    def _configure_tags(self):
        """配置文本标签样式"""
        # 标题样式
        self.text_widget.tag_configure('h1', font=('Consolas', 20, 'bold'), foreground='#2c3e50')
        self.text_widget.tag_configure('h2', font=('Consolas', 16, 'bold'), foreground='#34495e')
        self.text_widget.tag_configure('h3', font=('Consolas', 14, 'bold'), foreground='#7f8c8d')
        
        # 代码样式
        self.text_widget.tag_configure('code', font=('Consolas', 11), background='#f5f5f5', foreground='#e74c3c')
        self.text_widget.tag_configure('code_block', font=('Consolas', 11), background='#f8f8f8', foreground='#2c3e50')
        
        # 链接样式
        self.text_widget.tag_configure('link', foreground='#3498db', underline=True)
        
        # 强调样式
        self.text_widget.tag_configure('bold', font=('Consolas', 12, 'bold'))
        self.text_widget.tag_configure('italic', font=('Consolas', 12, 'italic'))
        
        # 引用样式
        self.text_widget.tag_configure('quote', foreground='#7f8c8d', font=('Consolas', 12, 'italic'))
        
        # 列表样式
        self.text_widget.tag_configure('list', foreground='#27ae60')
        
        # Wiki 链接样式
        self.text_widget.tag_configure('wiki_link', foreground='#9b59b6', background='#f0e6f5')
    
    def _bind_events(self):
        """绑定事件处理"""
        # 内容变化事件（防抖）
        self.text_widget.bind('<<Modified>>', self._on_modified)
        
        # 键盘快捷键
        self.text_widget.bind('<Control-b>', lambda e: self.toggle_format('bold'))
        self.text_widget.bind('<Control-i>', lambda e: self.toggle_format('italic'))
        self.text_widget.bind('<Control-k>', lambda e: self.insert_code())
        self.text_widget.bind('<Control-l>', lambda e: self.insert_link())
        
        # Tab 键处理
        self.text_widget.bind('<Tab>', self._on_tab)
        self.text_widget.bind('<Shift-Tab>', self._on_shift_tab)
        
        # 回车键处理（自动列表）
        self.text_widget.bind('<Return>', self._on_return)
        
        # 滚动同步
        self.text_widget.bind('<KeyRelease>', self._on_scroll)
        self.text_widget.bind('<ButtonRelease>', self._on_scroll)
    
    def _on_modified(self, event=None):
        """内容变化回调（防抖处理）"""
        if self._is_loading:
            return
        
        if self.text_widget.edit_modified():
            self.text_widget.edit_modified(False)
            
            # 取消之前的定时器
            if self._change_after_id:
                self.text_widget.after_cancel(self._change_after_id)
            
            # 设置新的定时器（300ms 防抖）
            self._change_after_id = self.text_widget.after(300, self._trigger_change)
    
    def _trigger_change(self):
        """触发内容变化回调"""
        if self.on_change_callback:
            self.on_change_callback(self.get_content())
    
    def _on_scroll(self, event=None):
        """滚动事件处理"""
        # TODO: 实现滚动同步
        pass
    
    def _on_tab(self, event):
        """Tab 键处理"""
        self.text_widget.insert(tk.INSERT, '    ')
        return 'break'
    
    def _on_shift_tab(self, event):
        """Shift+Tab 键处理"""
        # 获取当前行
        line_start = self.text_widget.index('insert linestart')
        line_end = self.text_widget.index('insert lineend')
        line_text = self.text_widget.get(line_start, line_end)
        
        # 移除缩进
        if line_text.startswith('    '):
            self.text_widget.delete(line_start, f'{line_start}+4c')
        elif line_text.startswith('\t'):
            self.text_widget.delete(line_start, f'{line_start}+1c')
        
        return 'break'
    
    def _on_return(self, event):
        """回车键处理（自动列表）"""
        # 获取当前行
        line_start = self.text_widget.index('insert linestart')
        line_end = self.text_widget.index('insert lineend')
        line_text = self.text_widget.get(line_start, line_end)
        
        # 检查是否是列表项
        list_match = re.match(r'^(\s*)([-*+]\s+|\d+\.\s+)(.*)', line_text)
        if list_match:
            indent = list_match.group(1)
            marker = list_match.group(2)
            content = list_match.group(3)
            
            if content.strip():
                # 继续列表
                if re.match(r'\d+\.', marker):
                    # 有序列表，递增数字
                    num = int(re.match(r'(\d+)', marker).group(1)) + 1
                    new_marker = f'{num}. '
                else:
                    new_marker = marker
                
                self.text_widget.insert(tk.INSERT, f'\n{indent}{new_marker}')
            else:
                # 空列表项，结束列表
                self.text_widget.delete(line_start, line_end)
                self.text_widget.insert(tk.INSERT, '\n')
            
            return 'break'
        
        return None
    
    def load_note(self, note: Note):
        """加载笔记内容"""
        self._is_loading = True
        self.current_note = note
        
        # 清空并插入内容
        self.text_widget.delete('1.0', tk.END)
        self.text_widget.insert('1.0', note.content)
        
        # 应用语法高亮
        self._apply_syntax_highlight()
        
        self._is_loading = False
        
        # 更新窗口标题
        self._update_title()
    
    def _apply_syntax_highlight(self):
        """应用语法高亮"""
        content = self.text_widget.get('1.0', tk.END)
        
        # 清除所有标签
        for tag in ['h1', 'h2', 'h3', 'code', 'code_block', 'link', 'bold', 'italic', 'quote', 'list', 'wiki_link']:
            self.text_widget.tag_remove(tag, '1.0', tk.END)
        
        # 高亮标题
        for match in re.finditer(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            level = len(match.group(1))
            tag = f'h{min(level, 3)}'
            self.text_widget.tag_add(tag, start, end)
        
        # 高亮代码块
        for match in re.finditer(r'```[\s\S]*?```', content):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.text_widget.tag_add('code_block', start, end)
        
        # 高亮行内代码
        for match in re.finditer(r'`[^`]+`', content):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.text_widget.tag_add('code', start, end)
        
        # 高亮 Wiki 链接
        for match in re.finditer(r'\[\[[^\]]+\]\]', content):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.text_widget.tag_add('wiki_link', start, end)
        
        # 高亮粗体
        for match in re.finditer(r'\*\*[^*]+\*\*|__[^_]+__', content):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.text_widget.tag_add('bold', start, end)
        
        # 高亮斜体
        for match in re.finditer(r'\*[^*]+\*|_[^_]+_', content):
            # 排除粗体
            if not re.match(r'\*\*', match.group()):
                start = f"1.0+{match.start()}c"
                end = f"1.0+{match.end()}c"
                self.text_widget.tag_add('italic', start, end)
        
        # 高亮引用
        for match in re.finditer(r'^>\s*.+$', content, re.MULTILINE):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.text_widget.tag_add('quote', start, end)
        
        # 高亮列表
        for match in re.finditer(r'^(\s*)([-*+]|\d+\.)\s+', content, re.MULTILINE):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.text_widget.tag_add('list', start, end)
    
    def get_content(self) -> str:
        """获取当前文本内容"""
        return self.text_widget.get('1.0', tk.END).rstrip()
    
    def insert_template(self, template_name: str):
        """插入模板内容"""
        from datetime import datetime
        
        templates = {
            'diary': f"""# {datetime.now().strftime('%Y年%m月%d日')} 日记

## 今日回顾


## 重要事项

- [ ] 

## 明日计划

- 

## 心情与感悟


""",
            'meeting': f"""# 会议记录

**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
**地点**: 
**参会人员**: 

## 会议议题


## 讨论内容


## 决议事项

- [ ] 

## 行动项

| 负责人 | 事项 | 截止日期 |
|--------|------|----------|
|        |      |          |

""",
            'project': f"""# 项目文档

## 项目概述


## 目标


## 任务分解

- [ ] 

## 时间线

```mermaid
gantt
    title 项目进度
    dateFormat  YYYY-MM-DD
    section 阶段1
    任务1           :a1, {datetime.now().strftime('%Y-%m-%d')}, 7d
```

## 参考资料

- 

"""
        }
        
        template = templates.get(template_name, '')
        if template:
            self.text_widget.insert(tk.INSERT, template)
    
    def toggle_format(self, style: str):
        """切换文本格式"""
        try:
            # 获取选中的文本
            sel_start = self.text_widget.index(tk.SEL_FIRST)
            sel_end = self.text_widget.index(tk.SEL_LAST)
            selected_text = self.text_widget.get(sel_start, sel_end)
            
            if not selected_text:
                return
            
            # 根据样式添加标记
            markers = {
                'bold': ('**', '**'),
                'italic': ('*', '*'),
                'code': ('`', '`'),
                'strike': ('~~', '~~')
            }
            
            prefix, suffix = markers.get(style, ('', ''))
            
            # 检查是否已有标记
            if selected_text.startswith(prefix) and selected_text.endswith(suffix):
                # 移除标记
                new_text = selected_text[len(prefix):-len(suffix)]
            else:
                # 添加标记
                new_text = f"{prefix}{selected_text}{suffix}"
            
            # 替换文本
            self.text_widget.delete(sel_start, sel_end)
            self.text_widget.insert(sel_start, new_text)
            
            # 重新选中
            new_end = f"{sel_start}+{len(new_text)}c"
            self.text_widget.tag_add(tk.SEL, sel_start, new_end)
            
        except tk.TclError:
            # 没有选中文本
            pass
    
    def insert_code(self):
        """插入代码块"""
        self.text_widget.insert(tk.INSERT, '\n```\n\n```\n')
        # 移动光标到代码块中间
        self.text_widget.mark_set(tk.INSERT, 'insert-4l')
    
    def insert_link(self):
        """插入链接"""
        try:
            sel_start = self.text_widget.index(tk.SEL_FIRST)
            sel_end = self.text_widget.index(tk.SEL_LAST)
            selected_text = self.text_widget.get(sel_start, sel_end)
            
            # 替换为链接格式
            link_text = f"[{selected_text}]()"
            self.text_widget.delete(sel_start, sel_end)
            self.text_widget.insert(sel_start, link_text)
            
            # 移动光标到括号内
            new_pos = f"{sel_start}+{len(link_text)-1}c"
            self.text_widget.mark_set(tk.INSERT, new_pos)
            
        except tk.TclError:
            # 没有选中文本
            self.text_widget.insert(tk.INSERT, '[链接文字](url)')
    
    def insert_heading(self, level: int):
        """插入标题"""
        # 获取当前行
        line_start = self.text_widget.index('insert linestart')
        line_end = self.text_widget.index('insert lineend')
        line_text = self.text_widget.get(line_start, line_end)
        
        # 移除已有的标题标记
        line_text = re.sub(r'^#{1,6}\s*', '', line_text)
        
        # 添加新的标题标记
        new_text = f"{'#' * level} {line_text}"
        
        self.text_widget.delete(line_start, line_end)
        self.text_widget.insert(line_start, new_text)
    
    def insert_list(self, ordered: bool = False):
        """插入列表"""
        if ordered:
            self.text_widget.insert(tk.INSERT, '1. ')
        else:
            self.text_widget.insert(tk.INSERT, '- ')
    
    def insert_quote(self):
        """插入引用"""
        self.text_widget.insert(tk.INSERT, '> ')
    
    def insert_task(self):
        """插入任务列表"""
        self.text_widget.insert(tk.INSERT, '- [ ] ')
    
    def insert_table(self, rows: int = 3, cols: int = 3):
        """插入表格"""
        header = '| ' + ' | '.join([f'标题{i+1}' for i in range(cols)]) + ' |\n'
        separator = '|' + '|'.join(['------' for _ in range(cols)]) + '|\n'
        
        body = ''
        for _ in range(rows - 1):
            body += '| ' + ' | '.join([' ' for _ in range(cols)]) + ' |\n'
        
        table = header + separator + body
        self.text_widget.insert(tk.INSERT, table)
    
    def insert_wiki_link(self, note_name: str):
        """插入 Wiki 链接"""
        self.text_widget.insert(tk.INSERT, f'[[{note_name}]]')
    
    def focus(self):
        """设置焦点"""
        self.text_widget.focus_set()
    
    def _update_title(self):
        """更新窗口标题"""
        # 通过父窗口更新标题
        if self.current_note:
            title = f"{self.current_note.title} - Markdown Note Assistant"
            self.parent.winfo_toplevel().title(title)
    
    def get_widget(self):
        """获取文本控件"""
        return self.text_widget
