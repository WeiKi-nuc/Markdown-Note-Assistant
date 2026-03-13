#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UIManager 类 - 主窗口布局与视图协调
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import os
import webbrowser

from ..core.config_manager import ConfigManager
from ..core.note_repository import NoteRepository
from ..core.note import Note
from ..core.notebook import Notebook
from ..core.link_manager import LinkManager
from ..core.template_engine import TemplateEngine
from .editor import Editor
from .preview_renderer import PreviewRenderer
from .sidebar import Sidebar
from .search_dialog import SearchDialog, QuickOpenDialog


class UIManager:
    """UI 管理器，协调主窗口布局和各组件"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.repository = NoteRepository()
        self.link_manager = LinkManager(self.repository)
        self.template_engine = TemplateEngine()
        
        self.current_note: Note = None
        self.current_layout = config.get_layout()
        
        # 创建主窗口
        self.root = tk.Tk()
        self.root.title("Markdown Note Assistant")
        
        # 设置窗口大小和位置
        self._setup_window_geometry()
        
        # 创建菜单栏
        self._create_menu()
        
        # 创建工具栏
        self._create_toolbar()
        
        # 创建状态栏（先创建，因为 set_layout 需要引用 layout_label）
        self._create_statusbar()
        
        # 创建主布局
        self._create_main_layout()
        
        # 绑定快捷键
        self._bind_shortcuts()
        
        # 加载默认笔记本
        self._load_default_notebook()
    
    def _setup_window_geometry(self):
        """设置窗口几何属性"""
        geometry = self.config.get_window_geometry()
        
        if len(geometry) == 4:
            width, height, x, y = geometry
            self.root.geometry(f"{width}x{height}+{x}+{y}")
        else:
            width, height = geometry
            self.root.geometry(f"{width}x{height}")
        
        # 设置最小窗口大小
        self.root.minsize(800, 600)
        
        # 恢复最大化状态
        if self.config.is_maximized():
            self.root.state('zoomed')
    
    def _create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="新建笔记", command=self._on_new_note, accelerator="Ctrl+N")
        file_menu.add_command(label="打开笔记本", command=self._on_open_notebook)
        file_menu.add_separator()
        file_menu.add_command(label="保存", command=self._on_save, accelerator="Ctrl+S")
        file_menu.add_command(label="另存为...", command=self._on_save_as)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self._on_exit)
        
        # 编辑菜单
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="编辑", menu=edit_menu)
        edit_menu.add_command(label="撤销", command=self._on_undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="重做", command=self._on_redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="剪切", command=self._on_cut, accelerator="Ctrl+X")
        edit_menu.add_command(label="复制", command=self._on_copy, accelerator="Ctrl+C")
        edit_menu.add_command(label="粘贴", command=self._on_paste, accelerator="Ctrl+V")
        edit_menu.add_separator()
        edit_menu.add_command(label="查找", command=self._on_find, accelerator="Ctrl+F")
        
        # 插入菜单
        insert_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="插入", menu=insert_menu)
        insert_menu.add_command(label="链接", command=self._on_insert_link, accelerator="Ctrl+K")
        insert_menu.add_command(label="图片", command=self._on_insert_image)
        insert_menu.add_command(label="表格", command=self._on_insert_table)
        insert_menu.add_separator()
        insert_menu.add_command(label="模板", command=self._on_insert_template)
        
        # 视图菜单
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="视图", menu=view_menu)
        view_menu.add_command(label="切换侧边栏", command=self._on_toggle_sidebar, accelerator="Ctrl+B")
        view_menu.add_separator()
        view_menu.add_command(label="编辑模式", command=lambda: self.set_layout('edit'))
        view_menu.add_command(label="预览模式", command=lambda: self.set_layout('preview'))
        view_menu.add_command(label="分屏模式", command=lambda: self.set_layout('split'))
        view_menu.add_separator()
        view_menu.add_command(label="浅色主题", command=lambda: self._set_theme('light'))
        view_menu.add_command(label="深色主题", command=lambda: self._set_theme('dark'))
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="快捷键", command=self._on_show_shortcuts)
        help_menu.add_command(label="关于", command=self._on_about)
    
    def _create_toolbar(self):
        """创建工具栏"""
        self.toolbar = ttk.Frame(self.root)
        self.toolbar.pack(side=tk.TOP, fill=tk.X, padx=2, pady=2)
        
        # 格式按钮（使用延迟绑定）
        self._add_toolbar_btn("B", 3, lambda: self._editor_cmd('toggle_format', 'bold'))
        self._add_toolbar_btn("I", 3, lambda: self._editor_cmd('toggle_format', 'italic'))
        self._add_toolbar_btn("`", 3, lambda: self._editor_cmd('insert_code'))
        
        ttk.Separator(self.toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=2)
        
        # 标题按钮
        self._add_toolbar_btn("H1", 4, lambda: self._editor_cmd('insert_heading', 1))
        self._add_toolbar_btn("H2", 4, lambda: self._editor_cmd('insert_heading', 2))
        self._add_toolbar_btn("H3", 4, lambda: self._editor_cmd('insert_heading', 3))
        
        ttk.Separator(self.toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=2)
        
        # 列表按钮
        self._add_toolbar_btn("•", 3, lambda: self._editor_cmd('insert_list', False))
        self._add_toolbar_btn("1.", 3, lambda: self._editor_cmd('insert_list', True))
        self._add_toolbar_btn("☐", 3, lambda: self._editor_cmd('insert_task'))
        self._add_toolbar_btn('"', 3, lambda: self._editor_cmd('insert_quote'))
        
        ttk.Separator(self.toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=2)
        
        # 布局按钮
        ttk.Button(self.toolbar, text="编辑", command=lambda: self.set_layout('edit')).pack(side=tk.LEFT, padx=1)
        ttk.Button(self.toolbar, text="预览", command=lambda: self.set_layout('preview')).pack(side=tk.LEFT, padx=1)
        ttk.Button(self.toolbar, text="分屏", command=lambda: self.set_layout('split')).pack(side=tk.LEFT, padx=1)
    
    def _add_toolbar_btn(self, text, width, command):
        """添加工具栏按钮"""
        ttk.Button(self.toolbar, text=text, width=width, command=command).pack(side=tk.LEFT, padx=1)
    
    def _editor_cmd(self, method_name, *args):
        """执行编辑器命令（延迟绑定）"""
        if hasattr(self, 'editor') and self.editor:
            method = getattr(self.editor, method_name)
            method(*args)
    
    def _create_main_layout(self):
        """创建主布局"""
        # 创建主 PanedWindow
        self.main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True)
        
        # 创建侧边栏
        self.sidebar = Sidebar(
            self.main_paned,
            on_note_select=self._on_note_selected,
            on_notebook_select=self._on_notebook_selected
        )
        self.main_paned.add(self.sidebar.get_widget())
        
        # 创建编辑/预览区域
        self.content_paned = ttk.PanedWindow(self.main_paned, orient=tk.HORIZONTAL)
        self.main_paned.add(self.content_paned, weight=1)
        
        # 创建编辑器
        self.editor = Editor(self.content_paned, on_change_callback=self._on_content_changed)
        self.content_paned.add(self.editor.get_widget(), weight=1)
        
        # 创建预览器
        self.preview = PreviewRenderer(self.content_paned)
        self.content_paned.add(self.preview.get_widget(), weight=1)
        
        # 应用初始布局
        self.set_layout(self.current_layout)
    
    def _create_statusbar(self):
        """创建状态栏"""
        self.statusbar = ttk.Frame(self.root)
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 左侧状态信息
        self.status_label = ttk.Label(self.statusbar, text="就绪")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(self.statusbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # 字数统计
        self.word_count_label = ttk.Label(self.statusbar, text="0 字")
        self.word_count_label.pack(side=tk.LEFT, padx=5)
        
        # 右侧布局指示
        self.layout_label = ttk.Label(self.statusbar, text="分屏模式")
        self.layout_label.pack(side=tk.RIGHT, padx=5)
    
    def _bind_shortcuts(self):
        """绑定快捷键"""
        self.root.bind('<Control-n>', lambda e: self._on_new_note())
        self.root.bind('<Control-s>', lambda e: self._on_save())
        self.root.bind('<Control-b>', lambda e: self._on_toggle_sidebar())
        self.root.bind('<Control-f>', lambda e: self._on_find())
        self.root.bind('<Control-p>', lambda e: self._on_quick_open())
    
    def _load_default_notebook(self):
        """加载默认笔记本"""
        default_notebook = self.config.get_default_notebook()
        
        if default_notebook and os.path.exists(default_notebook):
            notebook = self.repository.add_notebook(default_notebook)
            if notebook:
                self.sidebar.add_notebook(notebook)
        else:
            # 创建默认笔记本（使用当前工作目录）
            default_path = os.path.join(os.getcwd(), 'MarkdownNotes')
            notebook = self.repository.add_notebook(default_path)
            if notebook:
                self.sidebar.add_notebook(notebook)
                self.config.set_default_notebook(default_path)
    
    def set_layout(self, mode: str):
        """切换布局模式"""
        self.current_layout = mode
        
        # 获取当前所有 pane
        current_panes = list(self.content_paned.panes())
        editor_widget = self.editor.get_widget()
        preview_widget = self.preview.get_widget()
        
        # 将控件转换为字符串路径进行比较
        editor_str = str(editor_widget)
        preview_str = str(preview_widget)
        
        if mode == 'edit':
            # 仅编辑模式
            if preview_str in current_panes:
                self.content_paned.forget(preview_widget)
            if editor_str not in current_panes:
                self.content_paned.add(editor_widget, weight=1)
            self.layout_label.config(text="编辑模式")
            
        elif mode == 'preview':
            # 仅预览模式
            if editor_str in current_panes:
                self.content_paned.forget(editor_widget)
            if preview_str not in current_panes:
                self.content_paned.add(preview_widget, weight=1)
            self.layout_label.config(text="预览模式")
            
        elif mode == 'split':
            # 分屏模式
            if editor_str not in current_panes:
                self.content_paned.add(editor_widget, weight=1)
            if preview_str not in current_panes:
                self.content_paned.add(preview_widget, weight=1)
            self.layout_label.config(text="分屏模式")
        
        self.config.set_layout(mode)
    
    def _on_note_selected(self, file_path: str):
        """处理笔记选择"""
        note = self.repository.get_note_by_path(file_path)
        
        if note:
            # 保存当前笔记
            if self.current_note:
                self._on_save()
            
            # 加载新笔记
            self.current_note = note
            self.editor.load_note(note)
            self.preview.render_to_widget(note.content)
            
            # 添加到最近文件
            self.repository.add_to_recent(file_path)
            
            # 更新状态栏
            self._update_statusbar()
    
    def _on_notebook_selected(self, path: str):
        """处理笔记本选择"""
        pass
    
    def _on_content_changed(self, content: str):
        """处理内容变化"""
        # 更新预览
        self.preview.render_to_widget(content)
        
        # 更新当前笔记内容
        if self.current_note:
            self.current_note.content = content
        
        # 更新状态栏
        self._update_statusbar()
    
    def _update_statusbar(self):
        """更新状态栏"""
        if self.current_note:
            from ..parser.markdown_parser import get_parser
            parser = get_parser()
            word_count = parser.get_word_count(self.current_note.content)
            self.word_count_label.config(text=f"{word_count} 字")
            
            if self.current_note.file_path:
                self.status_label.config(text=f"已打开: {self.current_note.title}")
    
    def _on_new_note(self):
        """新建笔记"""
        title = simpledialog.askstring("新建笔记", "请输入笔记标题:")
        if title:
            # 使用默认笔记本
            default_path = self.config.get_default_notebook()
            if default_path:
                notebook = self.repository.add_notebook(default_path)
                note = notebook.create_note(title)
                if note:
                    self.sidebar.refresh()
                    self._on_note_selected(note.file_path)
    
    def _on_open_notebook(self):
        """打开笔记本"""
        path = filedialog.askdirectory(title="选择笔记本文件夹")
        if path:
            notebook = self.repository.add_notebook(path)
            if notebook:
                self.sidebar.add_notebook(notebook)
                self.config.set_default_notebook(path)
    
    def _on_save(self):
        """保存笔记"""
        if self.current_note:
            self.current_note.content = self.editor.get_content()
            if self.current_note.save():
                self.status_label.config(text=f"已保存: {self.current_note.title}")
                self.root.after(2000, lambda: self._update_statusbar())
    
    def _on_save_as(self):
        """另存为"""
        if self.current_note:
            path = filedialog.asksaveasfilename(
                defaultextension=".md",
                filetypes=[("Markdown files", "*.md"), ("All files", "*.*")]
            )
            if path:
                self.current_note.file_path = path
                self._on_save()
    
    def _on_exit(self):
        """退出应用"""
        self._on_save()
        self._save_window_state()
        self.root.quit()
    
    def _on_undo(self):
        """撤销"""
        try:
            self.editor.text_widget.edit_undo()
        except tk.TclError:
            pass
    
    def _on_redo(self):
        """重做"""
        try:
            self.editor.text_widget.edit_redo()
        except tk.TclError:
            pass
    
    def _on_cut(self):
        """剪切"""
        self.editor.text_widget.event_generate("<<Cut>>")
    
    def _on_copy(self):
        """复制"""
        self.editor.text_widget.event_generate("<<Copy>>")
    
    def _on_paste(self):
        """粘贴"""
        self.editor.text_widget.event_generate("<<Paste>>")
    
    def _on_find(self):
        """查找"""
        SearchDialog(self.root, self.repository, on_result_select=self._on_note_selected)
    
    def _on_quick_open(self):
        """快速打开"""
        QuickOpenDialog(self.root, self.repository, on_file_select=self._on_note_selected)
    
    def _on_insert_link(self):
        """插入链接"""
        self.editor.insert_link()
    
    def _on_insert_image(self):
        """插入图片"""
        path = filedialog.askopenfilename(
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("All files", "*.*")
            ]
        )
        if path and self.current_note:
            from ..core.asset_manager import AssetManager
            asset_manager = AssetManager(self.current_note.dirname)
            relative_path = asset_manager.save_file(path)
            if relative_path:
                filename = os.path.basename(path)
                self.editor.text_widget.insert(tk.INSERT, f"![{filename}]({relative_path})")
    
    def _on_insert_table(self):
        """插入表格"""
        self.editor.insert_table(3, 3)
    
    def _on_insert_template(self):
        """插入模板"""
        # 创建模板选择对话框
        dialog = tk.Toplevel(self.root)
        dialog.title("选择模板")
        dialog.geometry("300x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 模板列表
        listbox = tk.Listbox(dialog, font=('Segoe UI', 11))
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        templates = self.template_engine.get_all_templates()
        for template in templates:
            listbox.insert(tk.END, f"{template['name']} - {template['description']}")
        
        def on_select():
            selection = listbox.curselection()
            if selection:
                template_id = templates[selection[0]]['id']
                content = self.template_engine.render(template_id, {'title': '未命名'})
                self.editor.text_widget.insert(tk.INSERT, content)
            dialog.destroy()
        
        ttk.Button(dialog, text="插入", command=on_select).pack(pady=10)
    
    def _on_toggle_sidebar(self):
        """切换侧边栏显示"""
        # TODO: 实现侧边栏切换
        pass
    
    def _set_theme(self, theme: str):
        """设置主题"""
        self.preview.apply_theme(theme)
        self.config.set_preview_theme(theme)
    
    def _on_show_shortcuts(self):
        """显示快捷键帮助"""
        shortcuts = """快捷键列表:

文件:
  Ctrl+N - 新建笔记
  Ctrl+S - 保存
  Ctrl+O - 打开笔记本

编辑:
  Ctrl+Z - 撤销
  Ctrl+Y - 重做
  Ctrl+X - 剪切
  Ctrl+C - 复制
  Ctrl+V - 粘贴
  Ctrl+F - 查找

格式:
  Ctrl+B - 粗体
  Ctrl+I - 斜体
  Ctrl+K - 插入链接

视图:
  Ctrl+B - 切换侧边栏
  Ctrl+P - 快速打开
"""
        messagebox.showinfo("快捷键", shortcuts)
    
    def _on_about(self):
        """显示关于对话框"""
        messagebox.showinfo(
            "关于",
            "Markdown Note Assistant\n\n"
            "一个功能强大的 Markdown 笔记应用\n"
            "支持实时预览、双向链接、标签管理等功能"
        )
    
    def _save_window_state(self):
        """保存窗口状态"""
        # 保存最大化状态
        is_maximized = self.root.state() == 'zoomed'
        self.config.set_maximized(is_maximized)
        
        # 如果不是最大化，保存位置和大小
        if not is_maximized:
            geometry = self.root.geometry()
            # 解析 geometry 字符串
            parts = geometry.split('+')
            size = parts[0].split('x')
            width = int(size[0])
            height = int(size[1])
            x = int(parts[1]) if len(parts) > 1 else None
            y = int(parts[2]) if len(parts) > 2 else None
            
            self.config.set_window_geometry(width, height, x, y)
    
    def run(self):
        """运行应用"""
        self.root.protocol("WM_DELETE_WINDOW", self._on_exit)
        self.root.mainloop()
