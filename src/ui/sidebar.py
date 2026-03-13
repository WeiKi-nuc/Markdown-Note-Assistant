import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from typing import Callable, Optional, Dict, Any

from ..core.models import Notebook, NoteRepository


class Sidebar:
    def __init__(self, parent: tk.Widget, note_repo: NoteRepository):
        self.parent = parent
        self.note_repo = note_repo
        self.on_note_selected: Optional[Callable[[str], Any]] = None
        
        self.frame = ttk.Frame(parent, width=200)
        self.frame.pack_propagate(False)
        self.frame.pack(fill=tk.Y, side=tk.LEFT)
        
        self._create_widgets()
    
    def _create_widgets(self):
        top_frame = ttk.Frame(self.frame)
        top_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(top_frame, text="笔记本", font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT)
        
        add_btn = ttk.Button(top_frame, text="+", width=2, command=self._add_notebook)
        add_btn.pack(side=tk.RIGHT)
        
        refresh_btn = ttk.Button(top_frame, text="⟳", width=2, command=self._refresh_all)
        refresh_btn.pack(side=tk.RIGHT, padx=2)
        
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.files_tab = ttk.Frame(self.notebook)
        self.tags_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.files_tab, text="文件")
        self.notebook.add(self.tags_tab, text="标签")
        
        self._create_files_tree()
        self._create_tags_tree()
    
    def _create_files_tree(self):
        self.file_tree = ttk.Treeview(self.files_tab, show='tree')
        yscroll = ttk.Scrollbar(self.files_tab, orient=tk.VERTICAL, command=self.file_tree.yview)
        xscroll = ttk.Scrollbar(self.files_tab, orient=tk.HORIZONTAL, command=self.file_tree.xview)
        self.file_tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        
        self.file_tree.grid(row=0, column=0, sticky='nsew')
        yscroll.grid(row=0, column=1, sticky='ns')
        xscroll.grid(row=1, column=0, sticky='ew')
        
        self.files_tab.grid_rowconfigure(0, weight=1)
        self.files_tab.grid_columnconfigure(0, weight=1)
        
        self.file_tree.bind('<<TreeviewSelect>>', self._on_file_select)
        self.file_tree.bind('<Double-1>', self._on_file_double_click)
    
    def _create_tags_tree(self):
        self.tag_tree = ttk.Treeview(self.tags_tab, show='tree')
        yscroll = ttk.Scrollbar(self.tags_tab, orient=tk.VERTICAL, command=self.tag_tree.yview)
        self.tag_tree.configure(yscrollcommand=yscroll.set)
        
        self.tag_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _add_notebook(self):
        path = filedialog.askdirectory(title="选择笔记本目录")
        if path:
            try:
                nb = self.note_repo.add_notebook(path)
                self._add_notebook_to_tree(nb)
            except Exception as e:
                messagebox.showerror("错误", f"无法添加笔记本: {e}")
    
    def _refresh_all(self):
        self.note_repo.rescan_all()
        self.update_tree()
        self.update_tags()
    
    def _add_notebook_to_tree(self, nb: Notebook, parent: str = ''):
        display_name = nb.name
        if not parent:
            display_name = f"📁 {display_name}"
        node_id = self.file_tree.insert(parent, 'end', text=display_name, open=True, values=[nb.root_path, 'notebook'])
        
        for path, note in sorted(nb.notes.items()):
            self.file_tree.insert(node_id, 'end', text=f"📄 {note.title}", values=[path, 'note'])
        
        for sub_nb in nb.sub_notebooks:
            self._add_notebook_to_tree(sub_nb, node_id)
    
    def _on_file_select(self, event):
        selection = self.file_tree.selection()
        if selection:
            item = selection[0]
            values = self.file_tree.item(item, 'values')
            if values and len(values) >= 2 and values[1] == 'note':
                if self.on_note_selected:
                    self.on_note_selected(values[0])
    
    def _on_file_double_click(self, event):
        selection = self.file_tree.selection()
        if selection:
            item = selection[0]
            values = self.file_tree.item(item, 'values')
            if values and len(values) >= 2 and values[1] == 'notebook':
                os.startfile(values[0])
    
    def update_tree(self):
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        
        for path, nb in self.note_repo.notebooks.items():
            self._add_notebook_to_tree(nb)
    
    def update_tags(self):
        for item in self.tag_tree.get_children():
            self.tag_tree.delete(item)
        
        all_tags: Dict[str, int] = {}
        for nb in self.note_repo.notebooks.values():
            stats = nb.get_tag_statistics()
            for tag, count in stats.items():
                all_tags[tag] = all_tags.get(tag, 0) + count
        
        for tag, count in sorted(all_tags.items(), key=lambda x: -x[1]):
            self.tag_tree.insert('', 'end', text=f"#{tag} ({count})")
