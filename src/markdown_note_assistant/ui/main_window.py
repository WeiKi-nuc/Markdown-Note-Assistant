"""
Main Window module - the primary application window.
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import Menu, messagebox, ttk
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

from markdown_note_assistant.core.note import Note
from markdown_note_assistant.core.notebook import Notebook
from markdown_note_assistant.core.repository import NoteRepository
from markdown_note_assistant.ui.editor import Editor
from markdown_note_assistant.ui.preview import PreviewPane
from markdown_note_assistant.ui.sidebar import Sidebar
from markdown_note_assistant.utils.config import ConfigManager
from markdown_note_assistant.utils.debounce import Debouncer

if TYPE_CHECKING:
    pass


class StatusBar:
    """Status bar at the bottom of the window."""
    
    def __init__(self, parent: tk.Widget):
        self.frame = ttk.Frame(parent)
        self.frame.pack(side="bottom", fill="x")
        
        self._create_widgets()
    
    def _create_widgets(self) -> None:
        self.position_label = ttk.Label(self.frame, text="行 1, 列 1", width=15)
        self.position_label.pack(side="left", padx=5)
        
        ttk.Separator(self.frame, orient="vertical").pack(side="left", fill="y", padx=2)
        
        self.word_count_label = ttk.Label(self.frame, text="字数: 0", width=12)
        self.word_count_label.pack(side="left", padx=5)
        
        ttk.Separator(self.frame, orient="vertical").pack(side="left", fill="y", padx=2)
        
        self.line_count_label = ttk.Label(self.frame, text="行数: 0", width=12)
        self.line_count_label.pack(side="left", padx=5)
        
        ttk.Separator(self.frame, orient="vertical").pack(side="left", fill="y", padx=2)
        
        self.encoding_label = ttk.Label(self.frame, text="UTF-8", width=8)
        self.encoding_label.pack(side="left", padx=5)
        
        self.message_label = ttk.Label(self.frame, text="")
        self.message_label.pack(side="right", padx=5)
    
    def update_position(self, line: int, column: int) -> None:
        self.position_label.config(text=f"行 {line}, 列 {column}")
    
    def update_word_count(self, count: int) -> None:
        self.word_count_label.config(text=f"字数: {count}")
    
    def update_line_count(self, count: int) -> None:
        self.line_count_label.config(text=f"行数: {count}")
    
    def show_message(self, message: str, duration: int = 3000) -> None:
        self.message_label.config(text=message)
        if duration > 0:
            self.message_label.after(duration, lambda: self.message_label.config(text=""))


class CommandPalette:
    """Quick command palette (Ctrl+P)."""
    
    def __init__(self, parent: tk.Widget, main_window: "MainWindow"):
        self.parent = parent
        self.main_window = main_window
        
        self.window = tk.Toplevel(parent)
        self.window.withdraw()
        self.window.overrideredirect(True)
        
        self._create_widgets()
        self._bind_events()
    
    def _create_widgets(self) -> None:
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(self.window, textvariable=self.search_var, width=60)
        self.search_entry.pack(padx=5, pady=5)
        
        self.listbox = tk.Listbox(self.window, width=60, height=15)
        self.listbox.pack(padx=5, pady=(0, 5))
        
        self._items: List[Dict[str, Any]] = []
    
    def _bind_events(self) -> None:
        self.search_entry.bind("<KeyRelease>", self._on_search)
        self.search_entry.bind("<Return>", self._on_select)
        self.search_entry.bind("<Escape>", lambda e: self.hide())
        self.search_entry.bind("<Down>", self._on_down)
        self.search_entry.bind("<Up>", self._on_up)
        
        self.listbox.bind("<Return>", self._on_select)
        self.listbox.bind("<Double-Button-1>", self._on_select)
        self.listbox.bind("<Escape>", lambda e: self.hide())
    
    def show(self, mode: str = "files") -> None:
        self._mode = mode
        self._refresh_items()
        
        self.window.update_idletasks()
        
        x = self.parent.winfo_rootx() + 100
        y = self.parent.winfo_rooty() + 100
        self.window.geometry(f"+{x}+{y}")
        
        self.window.deiconify()
        self.search_entry.focus_set()
        self.search_var.set("")
        self._filter_items("")
    
    def hide(self) -> None:
        self.window.withdraw()
    
    def _refresh_items(self) -> None:
        self._items = []
        
        if self._mode == "files":
            for note in self.main_window.repository.get_all_notes():
                self._items.append({
                    "type": "file",
                    "title": note.title,
                    "path": str(note.file_path),
                    "action": lambda n=note: self.main_window.open_note(n.file_path),
                })
        elif self._mode == "commands":
            commands = [
                ("新建笔记", self.main_window.new_note),
                ("打开笔记本", self.main_window.open_notebook),
                ("保存", self.main_window.save_current_note),
                ("搜索", self.main_window.show_search),
                ("切换预览", self.main_window.toggle_preview),
                ("切换侧边栏", self.main_window.toggle_sidebar),
                ("专注模式", self.main_window.toggle_focus_mode),
            ]
            for name, action in commands:
                self._items.append({
                    "type": "command",
                    "title": name,
                    "action": action,
                })
    
    def _filter_items(self, query: str) -> None:
        self.listbox.delete(0, tk.END)
        
        query_lower = query.lower()
        
        for item in self._items:
            if query_lower in item["title"].lower():
                self.listbox.insert(tk.END, item["title"])
    
    def _on_search(self, event) -> None:
        self._filter_items(self.search_var.get())
    
    def _on_select(self, event) -> None:
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            visible_items = [
                item for item in self._items
                if self.search_var.get().lower() in item["title"].lower()
            ]
            if index < len(visible_items):
                self.hide()
                visible_items[index]["action"]()
    
    def _on_down(self, event) -> None:
        selection = self.listbox.curselection()
        if selection:
            if selection[0] < self.listbox.size() - 1:
                self.listbox.selection_clear(selection[0])
                self.listbox.selection_set(selection[0] + 1)
        else:
            self.listbox.selection_set(0)
    
    def _on_up(self, event) -> None:
        selection = self.listbox.curselection()
        if selection:
            if selection[0] > 0:
                self.listbox.selection_clear(selection[0])
                self.listbox.selection_set(selection[0] - 1)


class SearchPanel:
    """Search panel for finding text in notes."""
    
    def __init__(self, parent: tk.Widget, main_window: "MainWindow"):
        self.parent = parent
        self.main_window = main_window
        
        self.frame = ttk.Frame(parent)
        
        self._create_widgets()
        self._bind_events()
    
    def _create_widgets(self) -> None:
        search_frame = ttk.Frame(self.frame)
        search_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(search_frame, text="搜索:").pack(side="left")
        
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=40)
        self.search_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        ttk.Button(search_frame, text="搜索", command=self._do_search).pack(side="left", padx=2)
        ttk.Button(search_frame, text="关闭", command=self.hide).pack(side="left", padx=2)
        
        options_frame = ttk.Frame(self.frame)
        options_frame.pack(fill="x", padx=5, pady=2)
        
        self.case_sensitive = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="区分大小写", variable=self.case_sensitive).pack(side="left")
        
        self.use_regex = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="正则表达式", variable=self.use_regex).pack(side="left")
        
        self.search_content = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="搜索内容", variable=self.search_content).pack(side="left")
        
        self.search_title = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="搜索标题", variable=self.search_title).pack(side="left")
        
        self.results_frame = ttk.Frame(self.frame)
        self.results_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        columns = ("title", "path", "line")
        self.results_tree = ttk.Treeview(self.results_frame, columns=columns, show="headings", height=10)
        self.results_tree.heading("title", text="标题")
        self.results_tree.heading("path", text="路径")
        self.results_tree.heading("line", text="行号")
        self.results_tree.column("title", width=200)
        self.results_tree.column("path", width=300)
        self.results_tree.column("line", width=60)
        
        scrollbar = ttk.Scrollbar(self.results_frame, orient="vertical", command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scrollbar.set)
        
        self.results_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def _bind_events(self) -> None:
        self.search_entry.bind("<Return>", lambda e: self._do_search())
        self.results_tree.bind("<Double-Button-1>", self._on_result_select)
    
    def show(self) -> None:
        self.frame.pack(side="top", fill="x")
        self.search_entry.focus_set()
    
    def hide(self) -> None:
        self.frame.pack_forget()
    
    def toggle(self) -> None:
        if self.frame.winfo_ismapped():
            self.hide()
        else:
            self.show()
    
    def _do_search(self) -> None:
        query = self.search_var.get()
        if not query:
            return
        
        results = self.main_window.repository.global_search(
            query=query,
            search_content=self.search_content.get(),
            search_title=self.search_title.get(),
            case_sensitive=self.case_sensitive.get(),
            use_regex=self.use_regex.get(),
        )
        
        self._display_results(results)
    
    def _display_results(self, results) -> None:
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        for result in results:
            for match in result.matches:
                if match.get("type") == "content":
                    line = match.get("line_number", "")
                else:
                    line = "-"
                
                self.results_tree.insert("", "end", values=(
                    result.note.title,
                    str(result.note.file_path),
                    line,
                ), tags=(str(result.note.file_path),))
    
    def _on_result_select(self, event) -> None:
        selection = self.results_tree.selection()
        if selection:
            item = selection[0]
            values = self.results_tree.item(item, "values")
            if values:
                path = Path(values[1])
                self.main_window.open_note(path)


class MainWindow:
    """
    Main application window.
    
    This is the primary window that contains:
    - Menu bar
    - Toolbar
    - Sidebar (notebook tree)
    - Editor pane
    - Preview pane
    - Status bar
    """
    
    def __init__(self, root: Optional[tk.Tk] = None):
        self.root = root or tk.Tk()
        self.root.title("Markdown 笔记助手")
        
        self.config_manager = ConfigManager()
        self.repository = NoteRepository()
        
        self._current_note: Optional[Note] = None
        self._focus_mode = False
        self._preview_visible = True
        self._sidebar_visible = True
        
        self._debouncer = Debouncer(delay_ms=300)
        
        self._setup_styles()
        self._create_widgets()
        self._create_menus()
        self._bind_events()
        self._load_config()
        
        self._auto_save_id = None
        self._start_auto_save()
    
    def _setup_styles(self) -> None:
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        self.style.configure("TFrame", background="#f5f5f5")
        self.style.configure("TLabel", background="#f5f5f5")
        self.style.configure("TButton", padding=5)
        self.style.configure("Sidebar.TFrame", background="#e8e8e8")
        self.style.configure("Sidebar.TLabel", background="#e8e8e8")
    
    def _create_widgets(self) -> None:
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True)
        
        self.toolbar = self._create_toolbar(self.main_frame)
        
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(fill="both", expand=True)
        
        self.sidebar = Sidebar(self.content_frame, self)
        self.sidebar.pack(side="left", fill="y")
        
        self.editor_frame = ttk.Frame(self.content_frame)
        self.editor_frame.pack(side="left", fill="both", expand=True)
        
        self.search_panel = SearchPanel(self.editor_frame, self)
        
        self.paned_window = ttk.PanedWindow(self.editor_frame, orient="horizontal")
        self.paned_window.pack(fill="both", expand=True)
        
        self.editor = Editor(self.paned_window, self)
        self.paned_window.add(self.editor.frame, weight=1)
        
        self.preview = PreviewPane(self.paned_window, self)
        self.paned_window.add(self.preview.frame, weight=1)
        
        self.status_bar = StatusBar(self.root)
        
        self.command_palette = CommandPalette(self.root, self)
    
    def _create_toolbar(self, parent: tk.Widget) -> ttk.Frame:
        toolbar = ttk.Frame(parent)
        toolbar.pack(side="top", fill="x")
        
        buttons = [
            ("新建", self.new_note, "Ctrl+N"),
            ("打开", self.open_notebook, "Ctrl+O"),
            ("保存", self.save_current_note, "Ctrl+S"),
            ("|", None, None),
            ("加粗", lambda: self.editor.insert_format("bold"), "Ctrl+B"),
            ("斜体", lambda: self.editor.insert_format("italic"), "Ctrl+I"),
            ("删除线", lambda: self.editor.insert_format("strike"), "Ctrl+Shift+S"),
            ("|", None, None),
            ("标题", lambda: self.editor.insert_format("heading"), "Ctrl+1"),
            ("列表", lambda: self.editor.insert_format("list"), "Ctrl+L"),
            ("引用", lambda: self.editor.insert_format("quote"), "Ctrl+Q"),
            ("代码", lambda: self.editor.insert_format("code"), "Ctrl+`"),
            ("|", None, None),
            ("链接", lambda: self.editor.insert_format("link"), "Ctrl+K"),
            ("图片", lambda: self.editor.insert_format("image"), "Ctrl+Shift+I"),
            ("表格", lambda: self.editor.insert_format("table"), "Ctrl+T"),
            ("|", None, None),
            ("预览", self.toggle_preview, "Ctrl+E"),
            ("专注", self.toggle_focus_mode, "F11"),
        ]
        
        for text, command, shortcut in buttons:
            if text == "|":
                ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=3)
            else:
                btn = ttk.Button(toolbar, text=text, command=command, width=6)
                btn.pack(side="left", padx=1)
        
        return toolbar
    
    def _create_menus(self) -> None:
        menubar = Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="新建笔记", command=self.new_note, accelerator="Ctrl+N")
        file_menu.add_command(label="新建笔记本", command=self.new_notebook)
        file_menu.add_separator()
        file_menu.add_command(label="打开笔记本", command=self.open_notebook, accelerator="Ctrl+O")
        file_menu.add_command(label="打开最近", command=self.show_recent_files)
        file_menu.add_separator()
        file_menu.add_command(label="保存", command=self.save_current_note, accelerator="Ctrl+S")
        file_menu.add_command(label="另存为", command=self.save_as)
        file_menu.add_separator()
        file_menu.add_command(label="导出 HTML", command=self.export_html)
        file_menu.add_command(label="导出 PDF", command=self.export_pdf)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.quit_app)
        
        edit_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="编辑", menu=edit_menu)
        edit_menu.add_command(label="撤销", command=lambda: self.editor.undo(), accelerator="Ctrl+Z")
        edit_menu.add_command(label="重做", command=lambda: self.editor.redo(), accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="剪切", command=lambda: self.editor.cut(), accelerator="Ctrl+X")
        edit_menu.add_command(label="复制", command=lambda: self.editor.copy(), accelerator="Ctrl+C")
        edit_menu.add_command(label="粘贴", command=lambda: self.editor.paste(), accelerator="Ctrl+V")
        edit_menu.add_separator()
        edit_menu.add_command(label="查找", command=self.show_search, accelerator="Ctrl+F")
        edit_menu.add_command(label="全局搜索", command=self.show_global_search, accelerator="Ctrl+Shift+F")
        
        view_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="视图", menu=view_menu)
        view_menu.add_command(label="切换侧边栏", command=self.toggle_sidebar, accelerator="Ctrl+B")
        view_menu.add_command(label="切换预览", command=self.toggle_preview, accelerator="Ctrl+E")
        view_menu.add_separator()
        view_menu.add_command(label="专注模式", command=self.toggle_focus_mode, accelerator="F11")
        view_menu.add_separator()
        view_menu.add_command(label="放大", command=lambda: self.editor.change_font_size(2))
        view_menu.add_command(label="缩小", command=lambda: self.editor.change_font_size(-2))
        view_menu.add_command(label="重置缩放", command=lambda: self.editor.reset_font_size())
        
        notebook_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="笔记本", menu=notebook_menu)
        notebook_menu.add_command(label="刷新索引", command=self.refresh_repository)
        notebook_menu.add_command(label="检查断链", command=self.check_broken_links)
        notebook_menu.add_separator()
        notebook_menu.add_command(label="标签统计", command=self.show_tag_statistics)
        
        help_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="快捷键", command=self.show_shortcuts)
        help_menu.add_command(label="关于", command=self.show_about)
    
    def _bind_events(self) -> None:
        self.root.bind("<Control-n>", lambda e: self.new_note())
        self.root.bind("<Control-N>", lambda e: self.new_note())
        self.root.bind("<Control-o>", lambda e: self.open_notebook())
        self.root.bind("<Control-O>", lambda e: self.open_notebook())
        self.root.bind("<Control-s>", lambda e: self.save_current_note())
        self.root.bind("<Control-S>", lambda e: self.save_current_note())
        self.root.bind("<Control-f>", lambda e: self.show_search())
        self.root.bind("<Control-F>", lambda e: self.show_search())
        self.root.bind("<Control-Shift-F>", lambda e: self.show_global_search())
        self.root.bind("<Control-p>", lambda e: self.show_command_palette())
        self.root.bind("<Control-P>", lambda e: self.show_command_palette())
        self.root.bind("<Control-e>", lambda e: self.toggle_preview())
        self.root.bind("<Control-E>", lambda e: self.toggle_preview())
        self.root.bind("<Control-b>", lambda e: self.toggle_sidebar())
        self.root.bind("<Control-B>", lambda e: self.toggle_sidebar())
        self.root.bind("<F11>", lambda e: self.toggle_focus_mode())
        
        self.root.protocol("WM_DELETE_WINDOW", self.quit_app)
        
        self.root.bind("<Configure>", self._on_window_resize)
    
    def _load_config(self) -> None:
        config = self.config_manager.get_ui_config()
        
        self.root.geometry(f"{config.window_width}x{config.window_height}")
        
        self._preview_visible = config.preview_visible
        self._sidebar_visible = config.sidebar_visible
        
        if not self._preview_visible:
            self.preview.frame.pack_forget()
        
        if not self._sidebar_visible:
            self.sidebar.pack_forget()
        
        for notebook_path in self.config_manager.config.notebooks:
            try:
                self.repository.add_notebook(notebook_path)
            except Exception as e:
                print(f"Error loading notebook {notebook_path}: {e}")
        
        self.sidebar.refresh()
    
    def _save_config(self) -> None:
        geometry = self.root.geometry()
        match = geometry.match(r"(\d+)x(\d+)")
        if match:
            self.config_manager.set("ui", "window_width", int(match.group(1)))
            self.config_manager.set("ui", "window_height", int(match.group(2)))
        
        self.config_manager.set("ui", "preview_visible", self._preview_visible)
        self.config_manager.set("ui", "sidebar_visible", self._sidebar_visible)
        
        self.config_manager.save()
    
    def _on_window_resize(self, event) -> None:
        pass
    
    def _start_auto_save(self) -> None:
        interval = self.config_manager.get("editor", "auto_save_interval", 30) * 1000
        
        if self.config_manager.get("editor", "auto_save", True):
            self._auto_save()
        
        self._auto_save_id = self.root.after(interval, self._start_auto_save)
    
    def _auto_save(self) -> None:
        if self._current_note and self._current_note.is_modified():
            self.save_current_note()
    
    def new_note(self) -> None:
        from markdown_note_assistant.utils.template_engine import TemplateEngine
        
        template_engine = TemplateEngine()
        
        dialog = tk.Toplevel(self.root)
        dialog.title("新建笔记")
        dialog.geometry("400x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="标题:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        title_var = tk.StringVar()
        title_entry = ttk.Entry(dialog, textvariable=title_var, width=40)
        title_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(dialog, text="模板:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        templates = [t.name for t in template_engine.get_all_templates()]
        template_var = tk.StringVar(value="default")
        template_combo = ttk.Combobox(dialog, textvariable=template_var, values=templates, width=37)
        template_combo.grid(row=1, column=1, padx=5, pady=5)
        
        def create():
            title = title_var.get().strip()
            if not title:
                messagebox.showwarning("警告", "请输入标题")
                return
            
            notebook = self.sidebar.get_selected_notebook()
            if not notebook:
                notebooks = list(self.repository.notebooks.values())
                if notebooks:
                    notebook = notebooks[0]
            
            if notebook:
                content = template_engine.create_from_template(
                    template_var.get(),
                    title,
                )
                note = notebook.create_note(title, template=content)
                self.open_note(note.file_path)
                dialog.destroy()
            else:
                messagebox.showwarning("警告", "请先打开一个笔记本")
        
        ttk.Button(dialog, text="创建", command=create).grid(row=2, column=0, columnspan=2, pady=10)
        
        title_entry.focus_set()
    
    def new_notebook(self) -> None:
        from tkinter import filedialog
        
        path = filedialog.askdirectory(title="选择笔记本目录")
        if path:
            self.repository.add_notebook(path)
            self.sidebar.refresh()
            self.config_manager.add_notebook(path)
    
    def open_notebook(self) -> None:
        from tkinter import filedialog
        
        path = filedialog.askdirectory(title="打开笔记本目录")
        if path:
            self.repository.add_notebook(path)
            self.sidebar.refresh()
            self.config_manager.add_notebook(path)
    
    def open_note(self, path: Path) -> None:
        note = self.repository.get_note_by_path(path)
        
        if note is None:
            messagebox.showerror("错误", f"无法打开文件: {path}")
            return
        
        if self._current_note and self._current_note.is_modified():
            if messagebox.askyesno("保存", "当前笔记已修改，是否保存？"):
                self.save_current_note()
        
        self._current_note = note
        self.editor.load_note(note)
        self.preview.render(note.content)
        
        self.root.title(f"Markdown 笔记助手 - {note.title}")
        
        self.repository.add_recent_file(path)
        self.config_manager.add_recent_file(str(path))
        
        self._update_status_bar()
    
    def save_current_note(self) -> None:
        if self._current_note is None:
            return
        
        content = self.editor.get_content()
        self._current_note.set_content(content)
        self._current_note.save()
        
        self.repository.refresh_note(self._current_note.file_path)
        
        self.status_bar.show_message("已保存")
    
    def save_as(self) -> None:
        from tkinter import filedialog
        
        if self._current_note is None:
            return
        
        path = filedialog.asksaveasfilename(
            title="另存为",
            defaultextension=".md",
            filetypes=[("Markdown", "*.md"), ("所有文件", "*.*")],
        )
        
        if path:
            self._current_note.file_path = Path(path)
            self.save_current_note()
    
    def export_html(self) -> None:
        from tkinter import filedialog
        
        if self._current_note is None:
            messagebox.showwarning("警告", "请先打开一个笔记")
            return
        
        path = filedialog.asksaveasfilename(
            title="导出 HTML",
            defaultextension=".html",
            filetypes=[("HTML", "*.html"), ("所有文件", "*.*")],
        )
        
        if path:
            html = self.preview.get_html()
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
            self.status_bar.show_message(f"已导出到 {path}")
    
    def export_pdf(self) -> None:
        messagebox.showinfo("提示", "PDF 导出功能需要安装 weasyprint 库")
    
    def show_search(self) -> None:
        self.search_panel.toggle()
    
    def show_global_search(self) -> None:
        self.search_panel.show()
        self.search_panel.search_entry.focus_set()
    
    def show_command_palette(self) -> None:
        self.command_palette.show(mode="commands")
    
    def show_recent_files(self) -> None:
        recent = self.repository.get_recent_files()
        if not recent:
            messagebox.showinfo("最近文件", "没有最近打开的文件")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("最近文件")
        dialog.geometry("500x300")
        
        listbox = tk.Listbox(dialog)
        listbox.pack(fill="both", expand=True, padx=10, pady=10)
        
        for path in recent:
            listbox.insert(tk.END, str(path))
        
        def open_selected():
            selection = listbox.curselection()
            if selection:
                path = Path(listbox.get(selection[0]))
                self.open_note(path)
                dialog.destroy()
        
        listbox.bind("<Double-Button-1>", lambda e: open_selected())
        ttk.Button(dialog, text="打开", command=open_selected).pack(pady=5)
    
    def toggle_sidebar(self) -> None:
        if self._focus_mode:
            return
        
        self._sidebar_visible = not self._sidebar_visible
        
        if self._sidebar_visible:
            self.sidebar.pack(side="left", fill="y", before=self.editor_frame)
        else:
            self.sidebar.pack_forget()
    
    def toggle_preview(self) -> None:
        if self._focus_mode:
            return
        
        self._preview_visible = not self._preview_visible
        
        if self._preview_visible:
            self.preview.frame.pack(side="left", fill="both", expand=True, in_=self.paned_window)
        else:
            self.preview.frame.pack_forget()
    
    def toggle_focus_mode(self) -> None:
        self._focus_mode = not self._focus_mode
        
        if self._focus_mode:
            self.toolbar.pack_forget()
            self.sidebar.pack_forget()
            self.preview.frame.pack_forget()
            self.status_bar.frame.pack_forget()
            
            self.root.attributes("-fullscreen", True)
        else:
            self.toolbar.pack(side="top", fill="x", in_=self.main_frame, before=self.content_frame)
            
            if self._sidebar_visible:
                self.sidebar.pack(side="left", fill="y", before=self.editor_frame)
            
            if self._preview_visible:
                self.preview.frame.pack(side="left", fill="both", expand=True)
            
            self.status_bar.frame.pack(side="bottom", fill="x")
            
            self.root.attributes("-fullscreen", False)
    
    def refresh_repository(self) -> None:
        for notebook in self.repository.notebooks.values():
            notebook.scan()
        self.sidebar.refresh()
        self.status_bar.show_message("索引已刷新")
    
    def check_broken_links(self) -> None:
        broken = self.repository.check_broken_links()
        
        if not broken:
            messagebox.showinfo("检查断链", "没有发现断开的链接")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("断开的链接")
        dialog.geometry("600x400")
        
        columns = ("source", "target", "line")
        tree = ttk.Treeview(dialog, columns=columns, show="headings")
        tree.heading("source", text="来源笔记")
        tree.heading("target", text="目标")
        tree.heading("line", text="行号")
        tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        for link in broken:
            tree.insert("", "end", values=(
                link["source_note"].title,
                link["target"],
                link["line_number"],
            ))
    
    def show_tag_statistics(self) -> None:
        tags = self.repository.get_all_tags()
        
        dialog = tk.Toplevel(self.root)
        dialog.title("标签统计")
        dialog.geometry("400x500")
        
        listbox = tk.Listbox(dialog)
        listbox.pack(fill="both", expand=True, padx=10, pady=10)
        
        for tag, count in tags.items():
            listbox.insert(tk.END, f"{tag} ({count})")
    
    def show_shortcuts(self) -> None:
        shortcuts = self.config_manager.get_shortcuts_config()
        
        dialog = tk.Toplevel(self.root)
        dialog.title("快捷键")
        dialog.geometry("400x500")
        
        text = tk.Text(dialog, wrap="word")
        text.pack(fill="both", expand=True, padx=10, pady=10)
        
        shortcut_list = [
            ("保存", shortcuts.save),
            ("新建笔记", shortcuts.new_note),
            ("打开笔记", shortcuts.open_note),
            ("搜索", shortcuts.search),
            ("全局搜索", shortcuts.global_search),
            ("命令面板", shortcuts.command_palette),
            ("切换预览", shortcuts.toggle_preview),
            ("切换侧边栏", shortcuts.toggle_sidebar),
            ("专注模式", shortcuts.focus_mode),
            ("加粗", shortcuts.bold),
            ("斜体", shortcuts.italic),
            ("删除线", shortcuts.strike),
            ("代码", shortcuts.code),
            ("链接", shortcuts.link),
            ("图片", shortcuts.image),
            ("标题 1-6", f"{shortcuts.heading_1} - {shortcuts.heading_6}"),
        ]
        
        for name, key in shortcut_list:
            text.insert(tk.END, f"{name}: {key}\n")
        
        text.config(state="disabled")
    
    def show_about(self) -> None:
        messagebox.showinfo(
            "关于",
            "Markdown 笔记助手 v1.0.0\n\n"
            "一个功能丰富的 Markdown 笔记应用\n\n"
            "功能特点:\n"
            "- 实时预览\n"
            "- 双向链接\n"
            "- 标签管理\n"
            "- 全文搜索\n"
            "- 多种模板\n",
        )
    
    def _update_status_bar(self) -> None:
        if self._current_note:
            self.status_bar.update_word_count(self._current_note.get_word_count())
            self.status_bar.update_line_count(self._current_note.get_line_count())
    
    def on_editor_change(self, content: str) -> None:
        self._debouncer.call(
            self._update_preview,
            "preview",
            content,
        )
        
        self._update_status_bar()
    
    def _update_preview(self, content: str) -> None:
        self.preview.render(content)
    
    def on_cursor_change(self, line: int, column: int) -> None:
        self.status_bar.update_position(line, column)
    
    def quit_app(self) -> None:
        if self._current_note and self._current_note.is_modified():
            if messagebox.askyesno("保存", "当前笔记已修改，是否保存？"):
                self.save_current_note()
        
        self._save_config()
        
        if self._auto_save_id:
            self.root.after_cancel(self._auto_save_id)
        
        self.repository.close()
        
        self.root.destroy()


class UIManager:
    """UI Manager - coordinates all UI components."""
    
    def __init__(self, root: Optional[tk.Tk] = None):
        self.main_window = MainWindow(root)
    
    def run(self) -> None:
        """Start the application main loop."""
        self.main_window.root.mainloop()
    
    def set_layout(self, mode: str) -> None:
        """Set the layout mode (edit, preview, split)."""
        if mode == "edit":
            self.main_window._preview_visible = False
            self.main_window.preview.frame.pack_forget()
        elif mode == "preview":
            self.main_window._sidebar_visible = False
            self.main_window.sidebar.pack_forget()
        elif mode == "split":
            self.main_window._preview_visible = True
            self.main_window._sidebar_visible = True
    
    def show_search_panel(self) -> None:
        """Show the search panel."""
        self.main_window.show_search()
    
    def update_title(self) -> None:
        """Update the window title."""
        if self.main_window._current_note:
            self.main_window.root.title(
                f"Markdown 笔记助手 - {self.main_window._current_note.title}"
            )
        else:
            self.main_window.root.title("Markdown 笔记助手")
