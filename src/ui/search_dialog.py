#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SearchDialog 类 - 搜索对话框
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Callable, Optional, List
import re

from ..core.note_repository import NoteRepository
from ..core.note import Note


class SearchDialog:
    """搜索对话框"""
    
    def __init__(self, parent, repository: NoteRepository, 
                 on_result_select: Optional[Callable] = None):
        self.parent = parent
        self.repository = repository
        self.on_result_select = on_result_select
        self.search_history: List[str] = []
        
        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("搜索")
        self.dialog.geometry("700x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 创建界面
        self._create_ui()
        
        # 聚焦到搜索框
        self.search_entry.focus_set()
    
    def _create_ui(self):
        """创建界面"""
        # 搜索框区域
        search_frame = ttk.Frame(self.dialog)
        search_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(search_frame, text="搜索:").pack(side=tk.LEFT)
        
        self.search_entry = ttk.Entry(search_frame)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.search_entry.bind('<Return>', lambda e: self._do_search())
        
        ttk.Button(search_frame, text="搜索", command=self._do_search).pack(side=tk.LEFT)
        
        # 选项区域
        options_frame = ttk.Frame(self.dialog)
        options_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.case_sensitive = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="区分大小写", variable=self.case_sensitive).pack(side=tk.LEFT, padx=5)
        
        self.use_regex = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="正则表达式", variable=self.use_regex).pack(side=tk.LEFT, padx=5)
        
        self.search_titles = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="搜索标题", variable=self.search_titles).pack(side=tk.LEFT, padx=5)
        
        self.search_content = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="搜索内容", variable=self.search_content).pack(side=tk.LEFT, padx=5)
        
        # 结果列表
        result_frame = ttk.LabelFrame(self.dialog, text="搜索结果")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建树形视图
        columns = ('title', 'summary', 'path')
        self.result_tree = ttk.Treeview(result_frame, columns=columns, show='headings', selectmode='browse')
        
        self.result_tree.heading('title', text='标题')
        self.result_tree.heading('summary', text='摘要')
        self.result_tree.heading('path', text='路径')
        
        self.result_tree.column('title', width=150, minwidth=100)
        self.result_tree.column('summary', width=400, minwidth=200)
        self.result_tree.column('path', width=150, minwidth=100)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_tree.yview)
        self.result_tree.configure(yscrollcommand=scrollbar.set)
        
        self.result_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定双击事件
        self.result_tree.bind('<Double-1>', self._on_result_double_click)
        
        # 状态栏
        self.status_label = ttk.Label(self.dialog, text="输入关键词开始搜索")
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        
        # 历史记录下拉框
        if self.search_history:
            history_frame = ttk.Frame(self.dialog)
            history_frame.pack(fill=tk.X, padx=10, pady=5)
            ttk.Label(history_frame, text="历史:").pack(side=tk.LEFT)
            self.history_combo = ttk.Combobox(history_frame, values=self.search_history, width=50)
            self.history_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            self.history_combo.bind('<<ComboboxSelected>>', self._on_history_select)
    
    def _do_search(self):
        """执行搜索"""
        query = self.search_entry.get().strip()
        if not query:
            return
        
        # 添加到历史
        if query not in self.search_history:
            self.search_history.insert(0, query)
            if len(self.search_history) > 20:
                self.search_history.pop()
        
        # 清空结果
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        
        # 执行搜索
        results = self._search_notes(query)
        
        # 显示结果
        for note, highlights in results:
            summary = highlights[0] if highlights else note.get_summary(100)
            self.result_tree.insert('', tk.END, values=(note.title, summary, note.file_path))
        
        # 更新状态
        self.status_label.config(text=f"找到 {len(results)} 个结果")
    
    def _search_notes(self, query: str) -> List[tuple]:
        """搜索笔记"""
        results = []
        
        # 获取所有笔记
        all_notes = self.repository.get_all_notes()
        
        # 构建搜索正则
        flags = 0 if self.case_sensitive.get() else re.IGNORECASE
        
        if self.use_regex.get():
            try:
                pattern = re.compile(query, flags)
            except re.error:
                # 正则表达式错误，使用普通搜索
                pattern = re.compile(re.escape(query), flags)
        else:
            pattern = re.compile(re.escape(query), flags)
        
        for note in all_notes:
            matches = []
            
            # 搜索标题
            if self.search_titles.get():
                if pattern.search(note.title):
                    matches.append(f"标题匹配: {note.title}")
            
            # 搜索内容
            if self.search_content.get() and not matches:
                content = note.content
                for match in pattern.finditer(content):
                    # 获取上下文
                    start = max(0, match.start() - 50)
                    end = min(len(content), match.end() + 50)
                    context = content[start:end]
                    
                    # 高亮匹配
                    highlighted = self._highlight_match(context, match.group(), query)
                    matches.append(highlighted)
                    
                    if len(matches) >= 3:  # 最多显示3个匹配
                        break
            
            if matches:
                results.append((note, matches))
        
        return results
    
    def _highlight_match(self, text: str, match: str, query: str) -> str:
        """高亮匹配文本"""
        # 简化处理，实际应用中可以使用更复杂的高亮逻辑
        return text.replace(match, f"**{match}**")
    
    def _on_result_double_click(self, event):
        """处理结果双击"""
        selection = self.result_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = self.result_tree.item(item, 'values')
        
        if len(values) >= 3:
            file_path = values[2]
            if self.on_result_select:
                self.on_result_select(file_path)
            self.dialog.destroy()
    
    def _on_history_select(self, event):
        """处理历史记录选择"""
        query = self.history_combo.get()
        self.search_entry.delete(0, tk.END)
        self.search_entry.insert(0, query)
        self._do_search()


class QuickOpenDialog:
    """快速打开对话框 (Ctrl+P)"""
    
    def __init__(self, parent, repository: NoteRepository,
                 on_file_select: Optional[Callable] = None):
        self.parent = parent
        self.repository = repository
        self.on_file_select = on_file_select
        
        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("快速打开")
        self.dialog.geometry("600x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 创建界面
        self._create_ui()
        
        # 加载所有笔记
        self.all_notes = repository.get_all_notes()
        self._populate_list()
        
        # 聚焦到搜索框
        self.search_entry.focus_set()
    
    def _create_ui(self):
        """创建界面"""
        # 搜索框
        search_frame = ttk.Frame(self.dialog)
        search_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(search_frame, text=">").pack(side=tk.LEFT)
        
        self.search_entry = ttk.Entry(search_frame, font=('Segoe UI', 14))
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.search_entry.bind('<KeyRelease>', self._on_search)
        self.search_entry.bind('<Return>', self._on_enter)
        self.search_entry.bind('<Down>', self._on_down)
        self.search_entry.bind('<Up>', self._on_up)
        self.search_entry.bind('<Escape>', lambda e: self.dialog.destroy())
        
        # 结果列表
        list_frame = ttk.Frame(self.dialog)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.listbox = tk.Listbox(
            list_frame,
            font=('Segoe UI', 12),
            selectmode=tk.SINGLE,
            activestyle='none'
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        self.listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定事件
        self.listbox.bind('<Double-1>', self._on_select)
        self.listbox.bind('<Return>', self._on_select)
    
    def _populate_list(self, notes=None):
        """填充列表"""
        self.listbox.delete(0, tk.END)
        
        notes_to_show = notes if notes is not None else self.all_notes
        
        for note in notes_to_show:
            display_text = f"{note.title}  ({note.filename})"
            self.listbox.insert(tk.END, display_text)
            # 存储笔记路径
            self.listbox.itemconfig(tk.END, {'bg': '#f0f0f0' if len(self.listbox.get(0, tk.END)) % 2 == 0 else '#ffffff'})
    
    def _on_search(self, event):
        """处理搜索输入"""
        query = self.search_entry.get().lower()
        
        if not query:
            self._populate_list()
            return
        
        # 模糊匹配
        filtered = []
        for note in self.all_notes:
            if (query in note.title.lower() or 
                query in note.filename.lower() or
                any(query in tag.lower() for tag in note.tags)):
                filtered.append(note)
        
        self._populate_list(filtered)
        
        # 自动选中第一项
        if self.listbox.size() > 0:
            self.listbox.selection_set(0)
    
    def _on_enter(self, event):
        """处理回车键"""
        self._on_select(event)
    
    def _on_down(self, event):
        """处理向下键"""
        current = self.listbox.curselection()
        if current:
            next_idx = current[0] + 1
            if next_idx < self.listbox.size():
                self.listbox.selection_clear(0, tk.END)
                self.listbox.selection_set(next_idx)
                self.listbox.see(next_idx)
        else:
            if self.listbox.size() > 0:
                self.listbox.selection_set(0)
        return 'break'
    
    def _on_up(self, event):
        """处理向上键"""
        current = self.listbox.curselection()
        if current:
            prev_idx = max(0, current[0] - 1)
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(prev_idx)
            self.listbox.see(prev_idx)
        return 'break'
    
    def _on_select(self, event):
        """处理选择"""
        selection = self.listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        
        # 获取对应的笔记
        query = self.search_entry.get().lower()
        if query:
            filtered = [n for n in self.all_notes 
                       if query in n.title.lower() or query in n.filename.lower()]
            note = filtered[idx] if idx < len(filtered) else None
        else:
            note = self.all_notes[idx] if idx < len(self.all_notes) else None
        
        if note and self.on_file_select:
            self.on_file_select(note.file_path)
        
        self.dialog.destroy()
