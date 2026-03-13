import tkinter as tk
from tkinter import ttk, scrolledtext
import re
from typing import Optional, Callable, Any
from ..core.models import Note


class Editor:
    def __init__(self, parent: tk.Widget):
        self.parent = parent
        self.current_note: Optional[Note] = None
        self._change_callback: Optional[Callable] = None
        self._debounce_id = None
        self._debounce_delay = 300
        
        self._create_widgets()
        self._setup_tags()
    
    def _create_widgets(self):
        self.frame = ttk.Frame(self.parent)
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        self.text_widget = scrolledtext.ScrolledText(
            self.frame,
            wrap=tk.WORD,
            font=('Consolas', 11),
            undo=True,
            autoseparators=True
        )
        self.text_widget.pack(fill=tk.BOTH, expand=True)
        self.text_widget.bind('<<Modified>>', self._on_modified)
        self.text_widget.bind('<KeyRelease>', self._on_key_release)
    
    def _setup_tags(self):
        self.text_widget.tag_configure('h1', font=('Consolas', 16, 'bold'))
        self.text_widget.tag_configure('h2', font=('Consolas', 14, 'bold'))
        self.text_widget.tag_configure('h3', font=('Consolas', 12, 'bold'))
        self.text_widget.tag_configure('code', font=('Consolas', 11), background='#f0f0f0')
        self.text_widget.tag_configure('frontmatter', foreground='#666666')
        self.text_widget.tag_configure('link', foreground='#0366d6', underline=True)
    
    def _on_modified(self, event):
        if self.text_widget.edit_modified():
            self._schedule_change()
            self.text_widget.edit_modified(False)
    
    def _on_key_release(self, event):
        self._update_syntax_highlight()
    
    def _schedule_change(self):
        if self._debounce_id:
            self.text_widget.after_cancel(self._debounce_id)
        self._debounce_id = self.text_widget.after(self._debounce_delay, self._trigger_change)
    
    def _trigger_change(self):
        if self._change_callback:
            self._change_callback(self.get_content())
        self._debounce_id = None
    
    def on_change(self, callback: Callable[[str], Any]):
        self._change_callback = callback
    
    def load_note(self, note: Note):
        self.current_note = note
        full_content = ""
        if note.metadata:
            import yaml
            yaml_content = yaml.safe_dump(note.metadata, allow_unicode=True, default_flow_style=False)
            full_content = f"---\n{yaml_content}---\n"
        full_content += note.content
        
        self.text_widget.delete('1.0', tk.END)
        self.text_widget.insert('1.0', full_content)
        self._update_syntax_highlight()
    
    def get_content(self) -> str:
        full_text = self.text_widget.get('1.0', tk.END + '-1c')
        import re
        pattern = r'^---\s*\n(.*?)\n---\s*\n'
        match = re.match(pattern, full_text, re.DOTALL)
        if match:
            return full_text[match.end():]
        return full_text
    
    def get_full_content(self) -> str:
        return self.text_widget.get('1.0', tk.END + '-1c')
    
    def insert_template(self, template_name: str):
        from ..core.template_engine import TemplateEngine
        engine = TemplateEngine()
        content = engine.render(template_name, {})
        self.text_widget.insert(tk.INSERT, content)
    
    def toggle_format(self, style: str):
        try:
            sel = self.text_widget.tag_ranges(tk.SEL)
            if sel:
                start, end = sel
                selected_text = self.text_widget.get(start, end)
            else:
                selected_text = ""
            
            wrap_map = {
                'bold': ('**', '**'),
                'italic': ('*', '*'),
                'code': ('`', '`'),
                'strikethrough': ('~~', '~~'),
                'link': ('[', '](url)'),
                'inline_math': ('$', '$')
            }
            
            if style in wrap_map:
                prefix, suffix = wrap_map[style]
                if sel:
                    self.text_widget.delete(start, end)
                    self.text_widget.insert(start, f"{prefix}{selected_text}{suffix}")
                else:
                    self.text_widget.insert(tk.INSERT, f"{prefix}{suffix}")
                    if len(suffix) > 0:
                        self.text_widget.mark_set(tk.INSERT, f"{tk.INSERT}-{len(suffix)}c")
            elif style == 'h1':
                self._toggle_heading(1)
            elif style == 'h2':
                self._toggle_heading(2)
            elif style == 'h3':
                self._toggle_heading(3)
            elif style == 'ul':
                self._toggle_list('- ')
            elif style == 'ol':
                self._toggle_list('1. ')
            elif style == 'blockquote':
                self._toggle_blockquote()
            elif style == 'codeblock':
                self._insert_code_block()
        except:
            pass
    
    def _toggle_heading(self, level: int):
        line_start = self.text_widget.index(f"{tk.INSERT} linestart")
        line_end = self.text_widget.index(f"{tk.INSERT} lineend")
        line_text = self.text_widget.get(line_start, line_end)
        
        match = re.match(r'^(#{1,6})\s+', line_text)
        if match:
            current_level = len(match.group(1))
            if current_level == level:
                new_text = line_text[match.end():]
            else:
                new_text = '#' * level + ' ' + line_text[match.end():]
        else:
            new_text = '#' * level + ' ' + line_text
        
        self.text_widget.delete(line_start, line_end)
        self.text_widget.insert(line_start, new_text)
    
    def _toggle_list(self, prefix: str):
        line_start = self.text_widget.index(f"{tk.INSERT} linestart")
        line_end = self.text_widget.index(f"{tk.INSERT} lineend")
        line_text = self.text_widget.get(line_start, line_end)
        
        if line_text.startswith(prefix) or re.match(r'^(\d+)\.\s', line_text):
            new_text = re.sub(r'^(-|\*|\+|\d+\.)\s+', '', line_text)
        else:
            new_text = prefix + line_text
        
        self.text_widget.delete(line_start, line_end)
        self.text_widget.insert(line_start, new_text)
    
    def _toggle_blockquote(self):
        line_start = self.text_widget.index(f"{tk.INSERT} linestart")
        line_end = self.text_widget.index(f"{tk.INSERT} lineend")
        line_text = self.text_widget.get(line_start, line_end)
        
        if line_text.startswith('> '):
            new_text = line_text[2:]
        else:
            new_text = '> ' + line_text
        
        self.text_widget.delete(line_start, line_end)
        self.text_widget.insert(line_start, new_text)
    
    def _insert_code_block(self):
        sel = self.text_widget.tag_ranges(tk.SEL)
        if sel:
            start, end = sel
            selected_text = self.text_widget.get(start, end)
            self.text_widget.delete(start, end)
            self.text_widget.insert(start, f"```\n{selected_text}\n```")
        else:
            self.text_widget.insert(tk.INSERT, "\n```\n\n```\n")
            self.text_widget.mark_set(tk.INSERT, f"{tk.INSERT}-5c")
    
    def _update_syntax_highlight(self):
        try:
            self._clear_tags()
            text = self.text_widget.get('1.0', tk.END + '-1c')
            lines = text.split('\n')
            
            in_frontmatter = False
            frontmatter_start = 0
            frontmatter_count = 0
            
            for i, line in enumerate(lines, 1):
                if line.strip() == '---':
                    frontmatter_count += 1
                    if frontmatter_count == 1:
                        in_frontmatter = True
                        frontmatter_start = i
                    elif frontmatter_count == 2:
                        in_frontmatter = False
                        self.text_widget.tag_add('frontmatter', f"{frontmatter_start}.0", f"{i}.end")
                    continue
                
                if in_frontmatter:
                    self.text_widget.tag_add('frontmatter', f"{i}.0", f"{i}.end")
                    continue
                
                if re.match(r'^# .+', line):
                    self.text_widget.tag_add('h1', f"{i}.0", f"{i}.end")
                elif re.match(r'^## .+', line):
                    self.text_widget.tag_add('h2', f"{i}.0", f"{i}.end")
                elif re.match(r'^### .+', line):
                    self.text_widget.tag_add('h3', f"{i}.0", f"{i}.end")
                
                for match in re.finditer(r'`[^`]+`', line):
                    self.text_widget.tag_add('code', f"{i}.{match.start()}", f"{i}.{match.end()}")
                
                for match in re.finditer(r'\[\[[^\]]+\]\]', line):
                    self.text_widget.tag_add('link', f"{i}.{match.start()}", f"{i}.{match.end()}")
        except:
            pass
    
    def _clear_tags(self):
        for tag in ['h1', 'h2', 'h3', 'code', 'frontmatter', 'link']:
            self.text_widget.tag_remove(tag, '1.0', tk.END)
    
    def get_current_line(self) -> int:
        return int(self.text_widget.index(tk.INSERT).split('.')[0])
    
    def set_debounce_delay(self, ms: int):
        self._debounce_delay = ms
