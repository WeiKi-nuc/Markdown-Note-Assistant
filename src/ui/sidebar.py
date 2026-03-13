#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sidebar 类 - 左侧笔记本树形导航
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import os
from typing import Callable, Optional, List

from ..core.notebook import Notebook
from ..core.note import Note


class Sidebar:
    """侧边栏组件，显示笔记本树形导航"""
    
    def __init__(self, parent, on_note_select: Optional[Callable] = None,
                 on_notebook_select: Optional[Callable] = None):
        self.parent = parent
        self.on_note_select = on_note_select
        self.on_notebook_select = on_notebook_select
        self.notebooks: List[Notebook] = []
        
        # 创建主框架
        self.frame = ttk.Frame(parent)
        
        # 创建工具栏
        self._create_toolbar()
        
        # 创建树形视图
        self._create_treeview()
        
        # 创建右键菜单
        self._create_context_menu()
    
    def _create_toolbar(self):
        """创建工具栏"""
        toolbar = ttk.Frame(self.frame)
        toolbar.pack(fill=tk.X, padx=2, pady=2)
        
        # 新建笔记按钮
        ttk.Button(toolbar, text="+ 笔记", command=self._on_new_note).pack(side=tk.LEFT, padx=2)
        
        # 新建文件夹按钮
        ttk.Button(toolbar, text="+ 文件夹", command=self._on_new_folder).pack(side=tk.LEFT, padx=2)
        
        # 刷新按钮
        ttk.Button(toolbar, text="↻", width=3, command=self.refresh).pack(side=tk.RIGHT, padx=2)
    
    def _create_treeview(self):
        """创建树形视图"""
        # 创建滚动条
        scrollbar = ttk.Scrollbar(self.frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 创建树形视图
        self.tree = ttk.Treeview(
            self.frame,
            yscrollcommand=scrollbar.set,
            selectmode='browse',
            show='tree'
        )
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        scrollbar.config(command=self.tree.yview)
        
        # 绑定事件
        self.tree.bind('<<TreeviewSelect>>', self._on_select)
        self.tree.bind('<Double-1>', self._on_double_click)
        self.tree.bind('<Button-3>', self._on_right_click)
        
        # 配置样式
        self.tree.tag_configure('notebook', font=('Segoe UI', 10, 'bold'))
        self.tree.tag_configure('note', font=('Segoe UI', 10))
        self.tree.tag_configure('folder', font=('Segoe UI', 10))
    
    def _create_context_menu(self):
        """创建右键菜单"""
        self.context_menu = tk.Menu(self.tree, tearoff=0)
        self.context_menu.add_command(label="新建笔记", command=self._on_new_note)
        self.context_menu.add_command(label="新建文件夹", command=self._on_new_folder)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="重命名", command=self._on_rename)
        self.context_menu.add_command(label="删除", command=self._on_delete)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="刷新", command=self.refresh)
    
    def add_notebook(self, notebook: Notebook):
        """添加笔记本到侧边栏"""
        if notebook not in self.notebooks:
            self.notebooks.append(notebook)
            self._populate_tree()
    
    def remove_notebook(self, notebook: Notebook):
        """从侧边栏移除笔记本"""
        if notebook in self.notebooks:
            self.notebooks.remove(notebook)
            self._populate_tree()
    
    def _populate_tree(self):
        """填充树形视图"""
        # 清空树
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 添加笔记本
        for notebook in self.notebooks:
            self._add_notebook_to_tree(notebook, '')
    
    def _add_notebook_to_tree(self, notebook: Notebook, parent: str):
        """递归添加笔记本到树"""
        # 创建笔记本节点
        notebook_node = self.tree.insert(
            parent,
            'end',
            text=notebook.name,
            values=['notebook', notebook.root_path],
            tags=('notebook',),
            open=True
        )
        
        # 添加子笔记本
        for sub_notebook in notebook.sub_notebooks:
            self._add_notebook_to_tree(sub_notebook, notebook_node)
        
        # 添加笔记
        for note in notebook.notes.values():
            self.tree.insert(
                notebook_node,
                'end',
                text=note.title,
                values=['note', note.file_path],
                tags=('note',)
            )
    
    def refresh(self):
        """刷新侧边栏"""
        # 重新扫描所有笔记本
        for notebook in self.notebooks:
            notebook.scan()
        
        self._populate_tree()
    
    def _on_select(self, event):
        """处理选择事件"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = self.tree.item(item, 'values')
        
        if len(values) >= 2:
            item_type = values[0]
            item_path = values[1]
            
            if item_type == 'note' and self.on_note_select:
                self.on_note_select(item_path)
            elif item_type == 'notebook' and self.on_notebook_select:
                self.on_notebook_select(item_path)
    
    def _on_double_click(self, event):
        """处理双击事件"""
        # 双击展开/折叠
        item = self.tree.identify('item', event.x, event.y)
        if item:
            if self.tree.item(item, 'open'):
                self.tree.item(item, open=False)
            else:
                self.tree.item(item, open=True)
    
    def _on_right_click(self, event):
        """处理右键点击"""
        # 选择点击的项
        item = self.tree.identify('item', event.x, event.y)
        if item:
            self.tree.selection_set(item)
        
        # 显示右键菜单
        self.context_menu.post(event.x_root, event.y_root)
    
    def _on_new_note(self):
        """新建笔记"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一个笔记本或文件夹")
            return
        
        item = selection[0]
        values = self.tree.item(item, 'values')
        
        if len(values) >= 2:
            item_type = values[0]
            item_path = values[1]
            
            # 获取目标目录
            if item_type == 'note':
                # 如果是笔记，使用其所在目录
                target_dir = os.path.dirname(item_path)
            else:
                target_dir = item_path
            
            # 弹出对话框输入标题
            title = simpledialog.askstring("新建笔记", "请输入笔记标题:")
            if title:
                # 查找对应的笔记本
                for notebook in self.notebooks:
                    if target_dir.startswith(notebook.root_path):
                        note = notebook.create_note(title)
                        if note and self.on_note_select:
                            self.refresh()
                            self.on_note_select(note.file_path)
                        break
    
    def _on_new_folder(self):
        """新建文件夹"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一个笔记本或文件夹")
            return
        
        item = selection[0]
        values = self.tree.item(item, 'values')
        
        if len(values) >= 2:
            item_type = values[0]
            item_path = values[1]
            
            # 获取目标目录
            if item_type == 'note':
                target_dir = os.path.dirname(item_path)
            else:
                target_dir = item_path
            
            # 弹出对话框输入文件夹名
            folder_name = simpledialog.askstring("新建文件夹", "请输入文件夹名称:")
            if folder_name:
                new_folder_path = os.path.join(target_dir, folder_name)
                try:
                    os.makedirs(new_folder_path, exist_ok=True)
                    self.refresh()
                except Exception as e:
                    messagebox.showerror("错误", f"创建文件夹失败: {e}")
    
    def _on_rename(self):
        """重命名"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = self.tree.item(item, 'values')
        
        if len(values) >= 2:
            item_type = values[0]
            item_path = values[1]
            
            current_name = os.path.basename(item_path)
            if item_type == 'note':
                current_name = os.path.splitext(current_name)[0]
            
            new_name = simpledialog.askstring("重命名", "请输入新名称:", initialvalue=current_name)
            
            if new_name and new_name != current_name:
                try:
                    if item_type == 'note':
                        # 重命名笔记
                        new_path = os.path.join(os.path.dirname(item_path), f"{new_name}.md")
                        os.rename(item_path, new_path)
                    else:
                        # 重命名文件夹
                        new_path = os.path.join(os.path.dirname(item_path), new_name)
                        os.rename(item_path, new_path)
                    
                    self.refresh()
                except Exception as e:
                    messagebox.showerror("错误", f"重命名失败: {e}")
    
    def _on_delete(self):
        """删除"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = self.tree.item(item, 'values')
        
        if len(values) >= 2:
            item_type = values[0]
            item_path = values[1]
            
            item_name = os.path.basename(item_path)
            if item_type == 'note':
                item_name = os.path.splitext(item_name)[0]
            
            if messagebox.askyesno("确认删除", f"确定要删除 '{item_name}' 吗?"):
                try:
                    if item_type == 'note':
                        os.remove(item_path)
                    else:
                        import shutil
                        shutil.rmtree(item_path)
                    
                    self.refresh()
                except Exception as e:
                    messagebox.showerror("错误", f"删除失败: {e}")
    
    def select_note(self, file_path: str):
        """选中指定笔记"""
        for item in self.tree.get_children():
            if self._select_note_recursive(item, file_path):
                return
    
    def _select_note_recursive(self, parent: str, file_path: str) -> bool:
        """递归查找并选中笔记"""
        values = self.tree.item(parent, 'values')
        
        if len(values) >= 2 and values[1] == file_path:
            self.tree.selection_set(parent)
            self.tree.see(parent)
            return True
        
        for child in self.tree.get_children(parent):
            if self._select_note_recursive(child, file_path):
                return True
        
        return False
    
    def get_widget(self):
        """获取主框架"""
        return self.frame
