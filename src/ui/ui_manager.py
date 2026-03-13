import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
from typing import Optional

from ..core.models import Note, NoteRepository
from .editor import Editor
from .preview import PreviewPane
from .sidebar import Sidebar


class UIManager:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.note_repo = NoteRepository()
        self.current_note: Optional[Note] = None
        
        self._setup_window()
        self._create_menu()
        self._create_layout()
        self._create_status_bar()
        self._setup_bindings()
    
    def _setup_window(self):
        self.root.title("Markdown 笔记助手")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        style = ttk.Style()
        style.theme_use('clam')
    
    def _create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="新建笔记", command=self._new_note, accelerator="Ctrl+N")
        file_menu.add_command(label="打开文件", command=self._open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="保存", command=self._save_note, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="添加笔记本", command=self._add_notebook)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="编辑", menu=edit_menu)
        edit_menu.add_command(label="撤销", command=self._undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="重做", command=self._redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="查找", command=self._find, accelerator="Ctrl+F")
        
        format_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="格式", menu=format_menu)
        format_menu.add_command(label="加粗", command=lambda: self.editor.toggle_format('bold'), accelerator="Ctrl+B")
        format_menu.add_command(label="斜体", command=lambda: self.editor.toggle_format('italic'), accelerator="Ctrl+I")
        format_menu.add_separator()
        format_menu.add_command(label="标题1", command=lambda: self.editor.toggle_format('h1'), accelerator="Ctrl+1")
        format_menu.add_command(label="标题2", command=lambda: self.editor.toggle_format('h2'), accelerator="Ctrl+2")
        format_menu.add_command(label="标题3", command=lambda: self.editor.toggle_format('h3'), accelerator="Ctrl+3")
        format_menu.add_separator()
        format_menu.add_command(label="无序列表", command=lambda: self.editor.toggle_format('ul'))
        format_menu.add_command(label="有序列表", command=lambda: self.editor.toggle_format('ol'))
        format_menu.add_command(label="引用块", command=lambda: self.editor.toggle_format('blockquote'))
        format_menu.add_command(label="代码块", command=lambda: self.editor.toggle_format('codeblock'))
        
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="视图", menu=view_menu)
        self.layout_var = tk.StringVar(value="双栏")
        view_menu.add_radiobutton(label="双栏模式", variable=self.layout_var, value="双栏", command=lambda: self.set_layout("both"))
        view_menu.add_radiobutton(label="仅编辑", variable=self.layout_var, value="仅编辑", command=lambda: self.set_layout("editor"))
        view_menu.add_radiobutton(label="仅预览", variable=self.layout_var, value="仅预览", command=lambda: self.set_layout("preview"))
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self._show_about)
    
    def _create_layout(self):
        self.paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True)
        
        self.sidebar = Sidebar(self.paned, self.note_repo)
        self.sidebar.on_note_selected = self._on_note_selected
        self.paned.add(self.sidebar.frame, weight=1)
        
        self.main_paned = ttk.PanedWindow(self.paned, orient=tk.HORIZONTAL)
        self.paned.add(self.main_paned, weight=4)
        
        self.editor_frame = ttk.Frame(self.main_paned)
        self.editor = Editor(self.editor_frame)
        self.editor.on_change(self._on_content_change)
        self.main_paned.add(self.editor_frame, weight=1)
        
        self.preview_frame = ttk.Frame(self.main_paned)
        self.preview = PreviewPane(self.preview_frame)
        self.main_paned.add(self.preview_frame, weight=1)
        
        self._create_toolbar()
    
    def _create_toolbar(self):
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, side=tk.TOP, before=self.paned)
        
        tools = [
            ('B', 'bold'),
            ('I', 'italic'),
            ('H1', 'h1'),
            ('H2', 'h2'),
            ('H3', 'h3'),
            ('•', 'ul'),
            ('1.', 'ol'),
            ('"', 'blockquote'),
            ('</>', 'codeblock'),
            ('$', 'inline_math'),
            ('[]', 'link'),
        ]
        
        for text, cmd in tools:
            btn = ttk.Button(toolbar, text=text, width=3, 
                           command=lambda c=cmd: self.editor.toggle_format(c))
            btn.pack(side=tk.LEFT, padx=1, pady=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=2)
        
        self.save_btn = ttk.Button(toolbar, text="💾", width=3, command=self._save_note)
        self.save_btn.pack(side=tk.LEFT, padx=1, pady=2)
    
    def _create_status_bar(self):
        self.status_bar = ttk.Label(self.root, text="就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def _setup_bindings(self):
        self.root.bind('<Control-n>', lambda e: self._new_note())
        self.root.bind('<Control-o>', lambda e: self._open_file())
        self.root.bind('<Control-s>', lambda e: self._save_note())
        self.root.bind('<Control-f>', lambda e: self._find())
        self.root.bind('<Control-b>', lambda e: self.editor.toggle_format('bold'))
        self.root.bind('<Control-i>', lambda e: self.editor.toggle_format('italic'))
        self.root.bind('<Control-1>', lambda e: self.editor.toggle_format('h1'))
        self.root.bind('<Control-2>', lambda e: self.editor.toggle_format('h2'))
        self.root.bind('<Control-3>', lambda e: self.editor.toggle_format('h3'))
    
    def set_layout(self, mode: str):
        for pane in self.main_paned.panes():
            self.main_paned.forget(pane)
        
        if mode == "both":
            self.main_paned.add(self.editor_frame, weight=1)
            self.main_paned.add(self.preview_frame, weight=1)
        elif mode == "editor":
            self.main_paned.add(self.editor_frame, weight=1)
        elif mode == "preview":
            self.main_paned.add(self.preview_frame, weight=1)
    
    def _on_note_selected(self, file_path: str):
        note = self.note_repo.get_note_by_path(file_path)
        if note:
            self.load_note(note)
    
    def load_note(self, note: Note):
        self.current_note = note
        self.editor.load_note(note)
        self.preview.render(note.content)
        self.update_title()
        self._update_status(f"已打开: {note.title}")
    
    def _on_content_change(self, content: str):
        if self.current_note:
            self.current_note.content = content
        self.preview.render(content)
        self._update_status("已修改")
    
    def _new_note(self):
        title = simpledialog.askstring("新建笔记", "输入笔记标题:")
        if title:
            if not self.note_repo.notebooks:
                messagebox.showinfo("提示", "请先添加一个笔记本")
                self._add_notebook()
                if not self.note_repo.notebooks:
                    return
            
            notebook = list(self.note_repo.notebooks.values())[0]
            note = notebook.create_note(title)
            self.load_note(note)
            self.sidebar.update_tree()
    
    def _open_file(self):
        file_path = filedialog.askopenfilename(
            title="打开Markdown文件",
            filetypes=[("Markdown文件", "*.md"), ("所有文件", "*.*")]
        )
        if file_path:
            note = Note(file_path)
            self.load_note(note)
    
    def _save_note(self):
        if self.current_note:
            full_content = self.editor.get_full_content()
            from ..core.models import Note
            content, meta = self.current_note.parse_frontmatter(full_content)
            self.current_note.content = content
            self.current_note.metadata = meta
            self.current_note.save()
            self._update_status("已保存")
            messagebox.showinfo("保存", "笔记已保存")
    
    def _add_notebook(self):
        self.sidebar._add_notebook()
        self.sidebar.update_tree()
    
    def _undo(self):
        try:
            self.editor.text_widget.edit_undo()
        except:
            pass
    
    def _redo(self):
        try:
            self.editor.text_widget.edit_redo()
        except:
            pass
    
    def _find(self):
        find_str = simpledialog.askstring("查找", "输入查找内容:")
        if find_str:
            self._find_text(find_str)
    
    def _find_text(self, text):
        self.editor.text_widget.tag_remove('search', '1.0', tk.END)
        idx = '1.0'
        while True:
            idx = self.editor.text_widget.search(text, idx, nocase=True, stopindex=tk.END)
            if not idx:
                break
            end = f"{idx}+{len(text)}c"
            self.editor.text_widget.tag_add('search', idx, end)
            idx = end
        self.editor.text_widget.tag_config('search', background='yellow')
    
    def update_title(self):
        if self.current_note:
            self.root.title(f"{self.current_note.title} - Markdown 笔记助手")
        else:
            self.root.title("Markdown 笔记助手")
    
    def _update_status(self, text: str):
        self.status_bar.config(text=text)
    
    def _show_about(self):
        messagebox.showinfo("关于", "Markdown 笔记助手\n\n一个功能强大的Markdown笔记管理工具")
