"""
Sidebar module - notebook tree navigation.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

import tkinter as tk
from tkinter import ttk, messagebox

if TYPE_CHECKING:
    from markdown_note_assistant.ui.main_window import MainWindow
    from markdown_note_assistant.core.notebook import Notebook
    from markdown_note_assistant.core.note import Note


class Sidebar:
    """
    Sidebar - displays notebook tree and file navigation.
    
    Features:
    - Notebook tree view
    - File list
    - Context menu
    - Drag and drop
    - Quick actions
    """
    
    def __init__(self, parent: tk.Widget, main_window: "MainWindow"):
        self.parent = parent
        self.main_window = main_window
        
        self.frame = ttk.Frame(parent, style="Sidebar.TFrame", width=250)
        self.frame.pack_propagate(False)
        
        self._create_widgets()
        self._bind_events()
    
    def _create_widgets(self) -> None:
        header_frame = ttk.Frame(self.frame, style="Sidebar.TFrame")
        header_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(header_frame, text="笔记本", style="Sidebar.TLabel").pack(side="left")
        
        ttk.Button(
            header_frame,
            text="+",
            width=3,
            command=self._on_add_notebook,
        ).pack(side="right")
        
        ttk.Button(
            header_frame,
            text="⟳",
            width=3,
            command=self.refresh,
        ).pack(side="right", padx=2)
        
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(self.frame, textvariable=self.search_var)
        self.search_entry.pack(fill="x", padx=5, pady=2)
        self.search_entry.insert(0, "搜索...")
        self.search_entry.bind("<FocusIn>", self._on_search_focus_in)
        self.search_entry.bind("<FocusOut>", self._on_search_focus_out)
        self.search_entry.bind("<KeyRelease>", self._on_search)
        
        tree_frame = ttk.Frame(self.frame)
        tree_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.tree = ttk.Treeview(tree_frame, show="tree", selectmode="browse")
        self.tree.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self._create_context_menu()
    
    def _create_context_menu(self) -> None:
        self.context_menu = tk.Menu(self.tree, tearoff=0)
        self.context_menu.add_command(label="新建笔记", command=self._on_new_note)
        self.context_menu.add_command(label="新建文件夹", command=self._on_new_folder)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="重命名", command=self._on_rename)
        self.context_menu.add_command(label="删除", command=self._on_delete)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="在资源管理器中打开", command=self._on_open_in_explorer)
    
    def _bind_events(self) -> None:
        self.tree.bind("<Double-Button-1>", self._on_double_click)
        self.tree.bind("<Button-3>", self._on_right_click)
        self.tree.bind("<Return>", self._on_enter)
        self.tree.bind("<Delete>", self._on_delete_key)
        
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
    
    def refresh(self) -> None:
        """Refresh the notebook tree."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for notebook_path, notebook in self.main_window.repository.notebooks.items():
            self._add_notebook_to_tree(notebook, "")
    
    def _add_notebook_to_tree(self, notebook: "Notebook", parent: str) -> None:
        """Add a notebook and its contents to the tree."""
        notebook_id = self.tree.insert(
            parent,
            "end",
            text=f"📁 {notebook.name}",
            values=("notebook", str(notebook.root_path)),
            open=True,
        )
        
        for sub_notebook in notebook.sub_notebooks:
            self._add_notebook_to_tree(sub_notebook, notebook_id)
        
        for note_path, note in notebook.notes.items():
            self.tree.insert(
                notebook_id,
                "end",
                text=f"📝 {note.title}",
                values=("note", str(note_path)),
            )
    
    def _on_search_focus_in(self, event) -> None:
        if self.search_entry.get() == "搜索...":
            self.search_entry.delete(0, tk.END)
    
    def _on_search_focus_out(self, event) -> None:
        if not self.search_entry.get():
            self.search_entry.insert(0, "搜索...")
    
    def _on_search(self, event) -> None:
        query = self.search_var.get().lower()
        
        if query == "搜索...":
            query = ""
        
        self._filter_tree(query)
    
    def _filter_tree(self, query: str) -> None:
        """Filter tree items based on search query."""
        def hide_items(parent=""):
            for item in self.tree.get_children(parent):
                values = self.tree.item(item, "values")
                if values and values[0] == "note":
                    text = self.tree.item(item, "text").lower()
                    if query and query not in text:
                        self.tree.detach(item)
                    else:
                        self.tree.move(item, parent, "end")
                
                hide_items(item)
        
        def show_all(parent=""):
            for item in self.tree.get_children(parent):
                self.tree.move(item, parent, "end")
                show_all(item)
        
        if query:
            hide_items()
        else:
            show_all()
    
    def _on_double_click(self, event) -> None:
        item = self.tree.selection()
        if item:
            values = self.tree.item(item[0], "values")
            if values and values[0] == "note":
                path = Path(values[1])
                self.main_window.open_note(path)
    
    def _on_right_click(self, event) -> None:
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def _on_enter(self, event) -> None:
        item = self.tree.selection()
        if item:
            values = self.tree.item(item[0], "values")
            if values and values[0] == "note":
                path = Path(values[1])
                self.main_window.open_note(path)
    
    def _on_select(self, event) -> None:
        pass
    
    def _on_delete_key(self, event) -> None:
        self._on_delete()
    
    def _on_add_notebook(self) -> None:
        self.main_window.open_notebook()
    
    def _on_new_note(self) -> None:
        item = self.tree.selection()
        if not item:
            return
        
        values = self.tree.item(item[0], "values")
        if not values:
            return
        
        item_type = values[0]
        path = Path(values[1])
        
        if item_type == "notebook":
            notebook = self.main_window.repository.notebooks.get(str(path))
            if notebook:
                self.main_window.new_note()
        elif item_type == "note":
            notebook_path = path.parent
            while notebook_path:
                notebook = self.main_window.repository.notebooks.get(str(notebook_path))
                if notebook:
                    self.main_window.new_note()
                    break
                notebook_path = notebook_path.parent
    
    def _on_new_folder(self) -> None:
        item = self.tree.selection()
        if not item:
            return
        
        values = self.tree.item(item[0], "values")
        if not values or values[0] != "notebook":
            return
        
        path = Path(values[1])
        
        dialog = tk.Toplevel(self.main_window.root)
        dialog.title("新建文件夹")
        dialog.geometry("300x100")
        dialog.transient(self.main_window.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="文件夹名称:").pack(pady=5)
        
        name_var = tk.StringVar()
        entry = ttk.Entry(dialog, textvariable=name_var, width=30)
        entry.pack(pady=5)
        
        def create():
            name = name_var.get().strip()
            if name:
                new_path = path / name
                new_path.mkdir(parents=True, exist_ok=True)
                self.refresh()
                dialog.destroy()
        
        ttk.Button(dialog, text="创建", command=create).pack(pady=5)
        entry.focus_set()
    
    def _on_rename(self) -> None:
        item = self.tree.selection()
        if not item:
            return
        
        values = self.tree.item(item[0], "values")
        if not values:
            return
        
        item_type = values[0]
        old_path = Path(values[1])
        
        dialog = tk.Toplevel(self.main_window.root)
        dialog.title("重命名")
        dialog.geometry("300x100")
        dialog.transient(self.main_window.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="新名称:").pack(pady=5)
        
        name_var = tk.StringVar(value=old_path.stem)
        entry = ttk.Entry(dialog, textvariable=name_var, width=30)
        entry.pack(pady=5)
        
        def rename():
            new_name = name_var.get().strip()
            if new_name:
                new_path = old_path.parent / (new_name + old_path.suffix)
                try:
                    old_path.rename(new_path)
                    self.refresh()
                    dialog.destroy()
                except Exception as e:
                    messagebox.showerror("错误", f"重命名失败: {e}")
        
        ttk.Button(dialog, text="重命名", command=rename).pack(pady=5)
        entry.focus_set()
        entry.select_range(0, tk.END)
    
    def _on_delete(self) -> None:
        item = self.tree.selection()
        if not item:
            return
        
        values = self.tree.item(item[0], "values")
        if not values:
            return
        
        item_type = values[0]
        path = Path(values[1])
        
        if item_type == "note":
            if messagebox.askyesno("确认删除", f"确定要删除 '{path.name}' 吗？"):
                try:
                    path.unlink()
                    self.refresh()
                except Exception as e:
                    messagebox.showerror("错误", f"删除失败: {e}")
    
    def _on_open_in_explorer(self) -> None:
        item = self.tree.selection()
        if not item:
            return
        
        values = self.tree.item(item[0], "values")
        if not values:
            return
        
        path = Path(values[1])
        
        import subprocess
        import sys
        
        if sys.platform == "win32":
            subprocess.run(["explorer", "/select,", str(path)])
        elif sys.platform == "darwin":
            subprocess.run(["open", "-R", str(path)])
        else:
            subprocess.run(["xdg-open", str(path.parent)])
    
    def get_selected_notebook(self) -> Optional["Notebook"]:
        """Get the currently selected notebook."""
        item = self.tree.selection()
        if not item:
            return None
        
        values = self.tree.item(item[0], "values")
        if not values:
            return None
        
        item_type = values[0]
        path = Path(values[1])
        
        if item_type == "notebook":
            return self.main_window.repository.notebooks.get(str(path))
        elif item_type == "note":
            for notebook in self.main_window.repository.notebooks.values():
                if path in notebook.notes:
                    return notebook
        
        return None
    
    def get_selected_note(self) -> Optional["Note"]:
        """Get the currently selected note."""
        item = self.tree.selection()
        if not item:
            return None
        
        values = self.tree.item(item[0], "values")
        if not values or values[0] != "note":
            return None
        
        path = Path(values[1])
        return self.main_window.repository.get_note_by_path(path)
