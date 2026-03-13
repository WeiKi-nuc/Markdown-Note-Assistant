"""
Editor module - the markdown editing component.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

import tkinter as tk
from tkinter import ttk, messagebox

from markdown_note_assistant.core.note import Note
from markdown_note_assistant.utils.highlighter import MarkdownHighlighter

if TYPE_CHECKING:
    from markdown_note_assistant.ui.main_window import MainWindow


class Editor:
    """
    Editor - the markdown editing component.
    
    Features:
    - Syntax highlighting
    - Line numbers
    - Auto-indent
    - Format insertion
    - Template insertion
    - Undo/redo
    """
    
    def __init__(self, parent: tk.Widget, main_window: "MainWindow"):
        self.parent = parent
        self.main_window = main_window
        
        self.frame = ttk.Frame(parent)
        
        self._current_note: Optional[Note] = None
        self._font_family = "Consolas"
        self._font_size = 14
        self._original_font_size = 14
        
        self._create_widgets()
        self._bind_events()
        self._setup_highlighter()
    
    def _create_widgets(self) -> None:
        line_frame = ttk.Frame(self.frame)
        line_frame.pack(side="left", fill="y")
        
        self.line_numbers = tk.Text(
            line_frame,
            width=4,
            font=(self._font_family, self._font_size),
            state="disabled",
            background="#f0f0f0",
            foreground="#888888",
            takefocus=0,
        )
        self.line_numbers.pack(fill="y")
        
        text_frame = ttk.Frame(self.frame)
        text_frame.pack(side="left", fill="both", expand=True)
        
        self.text = tk.Text(
            text_frame,
            font=(self._font_family, self._font_size),
            wrap="word",
            undo=True,
            maxundo=-1,
            autoseparators=True,
            padx=10,
            pady=10,
        )
        self.text.pack(side="left", fill="both", expand=True)
        
        v_scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.text.yview)
        v_scrollbar.pack(side="right", fill="y")
        self.text.configure(yscrollcommand=self._on_scroll)
        
        h_scrollbar = ttk.Scrollbar(self.frame, orient="horizontal", command=self.text.xview)
        h_scrollbar.pack(side="bottom", fill="x")
        self.text.configure(xscrollcommand=h_scrollbar.set)
    
    def _bind_events(self) -> None:
        self.text.bind("<KeyRelease>", self._on_key_release)
        self.text.bind("<KeyPress>", self._on_key_press)
        self.text.bind("<Tab>", self._on_tab)
        self.text.bind("<Return>", self._on_return)
        self.text.bind("<BackSpace>", self._on_backspace)
        self.text.bind("<Control-b>", lambda e: self.insert_format("bold"))
        self.text.bind("<Control-B>", lambda e: self.insert_format("bold"))
        self.text.bind("<Control-i>", lambda e: self.insert_format("italic"))
        self.text.bind("<Control-I>", lambda e: self.insert_format("italic"))
        self.text.bind("<Control-`>", lambda e: self.insert_format("code"))
        self.text.bind("<Control-k>", lambda e: self.insert_format("link"))
        self.text.bind("<Control-K>", lambda e: self.insert_format("link"))
        self.text.bind("<Control-1>", lambda e: self.insert_heading(1))
        self.text.bind("<Control-2>", lambda e: self.insert_heading(2))
        self.text.bind("<Control-3>", lambda e: self.insert_heading(3))
        self.text.bind("<Control-4>", lambda e: self.insert_heading(4))
        self.text.bind("<Control-5>", lambda e: self.insert_heading(5))
        self.text.bind("<Control-6>", lambda e: self.insert_heading(6))
        self.text.bind("<Control-l>", lambda e: self.insert_format("list"))
        self.text.bind("<Control-L>", lambda e: self.insert_format("list"))
        self.text.bind("<Control-q>", lambda e: self.insert_format("quote"))
        self.text.bind("<Control-Q>", lambda e: self.insert_format("quote"))
        self.text.bind("<Button-3>", self._on_right_click)
        self.text.bind("<<Modified>>", self._on_modified)
        self.text.bind("<Configure>", self._on_configure)
    
    def _setup_highlighter(self) -> None:
        self.highlighter = MarkdownHighlighter(self.text, theme="light")
    
    def _on_scroll(self, *args) -> None:
        self.line_numbers.yview_moveto(args[0])
        self.main_window.preview.sync_scroll(self._get_scroll_position())
    
    def _get_scroll_position(self) -> float:
        return self.text.yview()[0]
    
    def _on_key_release(self, event) -> None:
        self._update_line_numbers()
        self._update_cursor_position()
        
        if event.keysym not in ("Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R"):
            self.highlighter.highlight()
            
            content = self.get_content()
            self.main_window.on_editor_change(content)
    
    def _on_key_press(self, event) -> None:
        pass
    
    def _on_tab(self, event) -> str:
        self.text.insert("insert", "    ")
        return "break"
    
    def _on_return(self, event) -> str:
        line = self.text.get("insert linestart", "insert lineend")
        
        indent = ""
        for char in line:
            if char in (" ", "\t"):
                indent += char
            else:
                break
        
        list_match = None
        import re
        list_match = re.match(r"^(\s*)([-*+]|\d+\.)\s", line)
        
        if list_match:
            prefix = list_match.group(2)
            if re.match(r"^\d+\.$", prefix):
                try:
                    num = int(prefix[:-1]) + 1
                    prefix = f"{num}."
                except ValueError:
                    pass
            
            if line.strip() == list_match.group(0).strip():
                self.text.delete("insert linestart", "insert lineend")
                return "break"
            
            self.text.insert("insert", f"\n{indent}{prefix} ")
            return "break"
        
        self.text.insert("insert", f"\n{indent}")
        return "break"
    
    def _on_backspace(self, event) -> str:
        if self.text.get("insert -1c", "insert") == " ":
            line_start = self.text.get("insert linestart", "insert")
            if line_start.strip() == "":
                self.text.delete("insert linestart", "insert")
                return "break"
        return ""
    
    def _on_right_click(self, event) -> None:
        menu = tk.Menu(self.text, tearoff=0)
        menu.add_command(label="撤销", command=self.undo, accelerator="Ctrl+Z")
        menu.add_command(label="重做", command=self.redo, accelerator="Ctrl+Y")
        menu.add_separator()
        menu.add_command(label="剪切", command=self.cut, accelerator="Ctrl+X")
        menu.add_command(label="复制", command=self.copy, accelerator="Ctrl+C")
        menu.add_command(label="粘贴", command=self.paste, accelerator="Ctrl+V")
        menu.add_separator()
        menu.add_command(label="加粗", command=lambda: self.insert_format("bold"), accelerator="Ctrl+B")
        menu.add_command(label="斜体", command=lambda: self.insert_format("italic"), accelerator="Ctrl+I")
        menu.add_command(label="代码", command=lambda: self.insert_format("code"), accelerator="Ctrl+`")
        menu.add_command(label="链接", command=lambda: self.insert_format("link"), accelerator="Ctrl+K")
        
        menu.post(event.x_root, event.y_root)
    
    def _on_modified(self, event) -> None:
        pass
    
    def _on_configure(self, event) -> None:
        self._update_line_numbers()
    
    def _update_line_numbers(self) -> None:
        self.line_numbers.config(state="normal")
        self.line_numbers.delete("1.0", "end")
        
        line_count = int(self.text.index("end-1c").split(".")[0])
        
        line_numbers_text = "\n".join(str(i) for i in range(1, line_count + 1))
        self.line_numbers.insert("1.0", line_numbers_text)
        
        self.line_numbers.config(state="disabled")
    
    def _update_cursor_position(self) -> None:
        cursor_pos = self.text.index("insert")
        line, column = cursor_pos.split(".")
        self.main_window.on_cursor_change(int(line), int(column) + 1)
    
    def load_note(self, note: Note) -> None:
        """Load a note into the editor."""
        self._current_note = note
        
        self.text.delete("1.0", "end")
        self.text.insert("1.0", note.content)
        
        self.text.edit_reset()
        
        self.highlighter.highlight()
        self._update_line_numbers()
    
    def get_content(self) -> str:
        """Get the current editor content."""
        return self.text.get("1.0", "end-1c")
    
    def insert_format(self, format_type: str) -> None:
        """Insert formatting around selection or at cursor."""
        formats = {
            "bold": ("**", "**"),
            "italic": ("*", "*"),
            "strike": ("~~", "~~"),
            "code": ("`", "`"),
            "code_block": ("```\n", "\n```"),
            "link": ("[", "](url)"),
            "image": ("![alt](", ")"),
            "quote": ("> ", ""),
            "hr": ("\n---\n", ""),
            "table": ("\n| 列1 | 列2 | 列3 |\n|------|------|------|\n| 内容 | 内容 | 内容 |\n", ""),
        }
        
        if format_type == "heading":
            self.insert_heading(1)
            return
        
        if format_type == "list":
            self._insert_list()
            return
        
        if format_type not in formats:
            return
        
        prefix, suffix = formats[format_type]
        
        if self.text.tag_ranges("sel"):
            start = self.text.index("sel.first")
            end = self.text.index("sel.last")
            selected = self.text.get(start, end)
            
            self.text.delete(start, end)
            self.text.insert(start, f"{prefix}{selected}{suffix}")
        else:
            self.text.insert("insert", f"{prefix}{suffix}")
            if format_type == "link":
                self.text.mark_set("insert", f"insert - {len(suffix)}c")
            elif format_type == "image":
                self.text.mark_set("insert", f"insert - {len(suffix)}c")
            else:
                cursor_pos = len(prefix)
                self.text.mark_set("insert", f"insert - {len(suffix)}c")
        
        self.highlighter.highlight()
    
    def _insert_list(self) -> None:
        """Insert a list item."""
        line = self.text.get("insert linestart", "insert lineend")
        
        import re
        list_match = re.match(r"^(\s*)([-*+]|\d+\.)\s", line)
        
        if list_match:
            indent = list_match.group(1)
            prefix = list_match.group(2)
            
            if re.match(r"^\d+\.$", prefix):
                try:
                    num = int(prefix[:-1]) + 1
                    prefix = f"{num}."
                except ValueError:
                    prefix = "-"
            else:
                prefix = "-"
            
            self.text.insert("insert", f"\n{indent}{prefix} ")
        else:
            self.text.insert("insert", "\n- ")
    
    def insert_heading(self, level: int) -> None:
        """Insert a heading at the current line."""
        line_start = self.text.index("insert linestart")
        line = self.text.get(line_start, "insert lineend")
        
        import re
        heading_match = re.match(r"^(#{1,6})\s*", line)
        
        if heading_match:
            old_level = len(heading_match.group(1))
            new_prefix = "#" * level + " "
            self.text.delete(line_start, f"{line_start} + {len(heading_match.group(0))}c")
            self.text.insert(line_start, new_prefix)
        else:
            self.text.insert(line_start, "#" * level + " ")
        
        self.highlighter.highlight()
    
    def insert_template(self, template_name: str) -> None:
        """Insert a template at the current cursor position."""
        from markdown_note_assistant.utils.template_engine import TemplateEngine
        
        engine = TemplateEngine()
        
        try:
            content = engine.render(template_name, {"title": "新笔记"})
            self.text.insert("insert", content)
            self.highlighter.highlight()
        except Exception as e:
            messagebox.showerror("错误", f"无法插入模板: {e}")
    
    def undo(self) -> None:
        """Undo the last action."""
        try:
            self.text.edit_undo()
            self.highlighter.highlight()
        except tk.TclError:
            pass
    
    def redo(self) -> None:
        """Redo the last undone action."""
        try:
            self.text.edit_redo()
            self.highlighter.highlight()
        except tk.TclError:
            pass
    
    def cut(self) -> None:
        """Cut selected text."""
        self.text.event_generate("<<Cut>>")
    
    def copy(self) -> None:
        """Copy selected text."""
        self.text.event_generate("<<Copy>>")
    
    def paste(self) -> None:
        """Paste from clipboard."""
        try:
            from PIL import ImageGrab
            
            image = ImageGrab.grabclipboard()
            if image:
                self._paste_image(image)
                return
        except Exception:
            pass
        
        self.text.event_generate("<<Paste>>")
        self.highlighter.highlight()
    
    def _paste_image(self, image) -> None:
        """Paste an image from clipboard."""
        if not self._current_note:
            messagebox.showwarning("警告", "请先打开一个笔记")
            return
        
        from io import BytesIO
        from markdown_note_assistant.utils.asset_manager import AssetManager
        
        asset_manager = AssetManager()
        
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        image_data = buffer.getvalue()
        
        file_path, relative_path = asset_manager.save_pasted_image(
            image_data,
            self._current_note.file_path,
        )
        
        self.text.insert("insert", f"![image]({relative_path})")
        self.highlighter.highlight()
    
    def change_font_size(self, delta: int) -> None:
        """Change the font size."""
        self._font_size = max(8, min(72, self._font_size + delta))
        self._apply_font()
    
    def reset_font_size(self) -> None:
        """Reset font size to original."""
        self._font_size = self._original_font_size
        self._apply_font()
    
    def _apply_font(self) -> None:
        """Apply the current font settings."""
        font = (self._font_family, self._font_size)
        self.text.configure(font=font)
        self.line_numbers.configure(font=font)
    
    def set_font(self, family: str, size: int) -> None:
        """Set the font family and size."""
        self._font_family = family
        self._font_size = size
        self._apply_font()
    
    def toggle_format(self, style: str) -> None:
        """Toggle a format style."""
        self.insert_format(style)
    
    def on_change(self, callback: Callable) -> None:
        """Register a callback for content changes."""
        self._change_callback = callback
    
    def get_current_line(self) -> int:
        """Get the current line number."""
        return int(self.text.index("insert").split(".")[0])
    
    def go_to_line(self, line_number: int) -> None:
        """Go to a specific line."""
        self.text.mark_set("insert", f"{line_number}.0")
        self.text.see("insert")
    
    def get_selection(self) -> Optional[tuple]:
        """Get the current selection range."""
        if self.text.tag_ranges("sel"):
            return (self.text.index("sel.first"), self.text.index("sel.last"))
        return None
    
    def set_selection(self, start: str, end: str) -> None:
        """Set the selection range."""
        self.text.tag_add("sel", start, end)
    
    def find_text(self, text: str, case_sensitive: bool = False) -> List[str]:
        """Find all occurrences of text."""
        start = "1.0"
        occurrences = []
        
        while True:
            if case_sensitive:
                pos = self.text.search(text, start, stopindex="end")
            else:
                pos = self.text.search(text, start, stopindex="end", nocase=True)
            
            if not pos:
                break
            
            end_pos = f"{pos} + {len(text)}c"
            occurrences.append((pos, end_pos))
            start = end_pos
        
        return occurrences
    
    def replace_text(self, old_text: str, new_text: str, start: str, end: str) -> None:
        """Replace text in a range."""
        self.text.delete(start, end)
        self.text.insert(start, new_text)
        self.highlighter.highlight()
    
    def replace_all(self, old_text: str, new_text: str, case_sensitive: bool = False) -> int:
        """Replace all occurrences of text."""
        count = 0
        start = "1.0"
        
        while True:
            if case_sensitive:
                pos = self.text.search(old_text, start, stopindex="end")
            else:
                pos = self.text.search(old_text, start, stopindex="end", nocase=True)
            
            if not pos:
                break
            
            end_pos = f"{pos} + {len(old_text)}c"
            self.text.delete(pos, end_pos)
            self.text.insert(pos, new_text)
            count += 1
            start = f"{pos} + {len(new_text)}c"
        
        if count > 0:
            self.highlighter.highlight()
        
        return count
