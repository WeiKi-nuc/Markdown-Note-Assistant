import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml


class Note:
    def __init__(self, file_path: str):
        self.file_path = os.path.abspath(file_path)
        self.title = ""
        self.content = ""
        self.metadata: Dict[str, Any] = {}
        self.tags: List[str] = []
        self.created_at: Optional[datetime] = None
        self.modified_at: Optional[datetime] = None
        self.linked_notes: List[str] = []
        self.headings: List[Dict] = []
        
        if os.path.exists(self.file_path):
            self.reload()
        else:
            self._init_from_filename()
    
    def _init_from_filename(self):
        name = os.path.splitext(os.path.basename(self.file_path))[0]
        self.title = name
        self.created_at = datetime.now()
        self.modified_at = datetime.now()
    
    def parse_frontmatter(self, text: str) -> tuple[str, Dict[str, Any]]:
        pattern = r'^---\s*\n(.*?)\n---\s*\n'
        match = re.match(pattern, text, re.DOTALL)
        if match:
            try:
                frontmatter_text = match.group(1)
                metadata = yaml.safe_load(frontmatter_text) or {}
                content = text[match.end():]
                return content, metadata
            except:
                pass
        return text, {}
    
    def extract_wiki_links(self, text: str) -> List[str]:
        pattern = r'\[\[([^\]]+)\]\]'
        matches = re.findall(pattern, text)
        links = []
        for m in matches:
            note_name = m.split('#')[0] if '#' in m else m
            links.append(note_name.strip())
        return list(set(links))
    
    def extract_headings(self, text: str) -> List[Dict]:
        headings = []
        lines = text.split('\n')
        for i, line in enumerate(lines):
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if heading_match:
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()
                anchor = re.sub(r'[^\w\s-]', '', title.lower())
                anchor = re.sub(r'[\s-]+', '-', anchor)
                headings.append({
                    'level': level,
                    'title': title,
                    'anchor': anchor,
                    'line': i
                })
        return headings
    
    def reload(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r', encoding='utf-8') as f:
                raw_content = f.read()
            
            self.content, self.metadata = self.parse_frontmatter(raw_content)
            
            stat = os.stat(self.file_path)
            self.created_at = datetime.fromtimestamp(stat.st_ctime)
            self.modified_at = datetime.fromtimestamp(stat.st_mtime)
            
            if 'title' in self.metadata:
                self.title = str(self.metadata['title'])
            else:
                name = os.path.splitext(os.path.basename(self.file_path))[0]
                self.title = name
            
            self.tags = self.metadata.get('tags', [])
            if isinstance(self.tags, str):
                self.tags = [t.strip() for t in self.tags.split(',')]
            
            if 'date' in self.metadata:
                try:
                    self.created_at = datetime.fromisoformat(str(self.metadata['date']))
                except:
                    pass
            
            self.linked_notes = self.extract_wiki_links(self.content)
            self.headings = self.extract_headings(self.content)
    
    def save(self):
        frontmatter = {
            'title': self.title,
            'date': self.created_at.isoformat() if self.created_at else datetime.now().isoformat(),
            'tags': self.tags
        }
        frontmatter.update(self.metadata)
        
        for k, v in list(frontmatter.items()):
            if v is None or (isinstance(v, list) and len(v) == 0):
                del frontmatter[k]
        
        yaml_content = yaml.safe_dump(frontmatter, allow_unicode=True, default_flow_style=False)
        full_content = f"---\n{yaml_content}---\n{self.content}"
        
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        with open(self.file_path, 'w', encoding='utf-8') as f:
            f.write(full_content)
        
        self.modified_at = datetime.now()
        self.linked_notes = self.extract_wiki_links(self.content)
        self.headings = self.extract_headings(self.content)
    
    def update_metadata(self, key: str, value: Any):
        self.metadata[key] = value
        if key == 'tags':
            self.tags = value if isinstance(value, list) else [value]
        elif key == 'title':
            self.title = str(value)


class Notebook:
    def __init__(self, root_path: str):
        self.root_path = os.path.abspath(root_path)
        self.name = os.path.basename(self.root_path)
        self.sub_notebooks: List['Notebook'] = []
        self.notes: Dict[str, Note] = {}
        self._is_scanned = False
    
    def scan(self, recursive: bool = True):
        self.notes.clear()
        self.sub_notebooks.clear()
        
        if not os.path.isdir(self.root_path):
            return
        
        try:
            entries = os.listdir(self.root_path)
        except:
            return
        
        for entry in entries:
            if entry.startswith('.'):
                continue
            
            full_path = os.path.join(self.root_path, entry)
            
            if os.path.isdir(full_path) and recursive:
                sub_nb = Notebook(full_path)
                sub_nb.scan(True)
                self.sub_notebooks.append(sub_nb)
            elif entry.lower().endswith('.md'):
                note = Note(full_path)
                self.notes[full_path] = note
        
        self._is_scanned = True
    
    def create_note(self, title: str, template: str = "") -> Note:
        filename = f"{title}.md"
        file_path = os.path.join(self.root_path, filename)
        counter = 1
        while os.path.exists(file_path):
            file_path = os.path.join(self.root_path, f"{title}_{counter}.md")
            counter += 1
        
        note = Note(file_path)
        note.title = title
        note.content = template
        note.save()
        self.notes[file_path] = note
        return note
    
    def search(self, keyword: str) -> List[Note]:
        if not self._is_scanned:
            self.scan()
        
        results = []
        keyword_lower = keyword.lower()
        
        for note in self.notes.values():
            if keyword_lower in note.title.lower() or keyword_lower in note.content.lower():
                results.append(note)
        
        for sub_nb in self.sub_notebooks:
            results.extend(sub_nb.search(keyword))
        
        return results
    
    def get_tag_statistics(self) -> Dict[str, int]:
        if not self._is_scanned:
            self.scan()
        
        stats: Dict[str, int] = {}
        for note in self.notes.values():
            for tag in note.tags:
                stats[tag] = stats.get(tag, 0) + 1
        
        for sub_nb in self.sub_notebooks:
            sub_stats = sub_nb.get_tag_statistics()
            for tag, count in sub_stats.items():
                stats[tag] = stats.get(tag, 0) + count
        
        return stats


class NoteRepository:
    def __init__(self):
        self.notebooks: Dict[str, Notebook] = {}
        self._note_cache: Dict[str, Note] = {}
    
    def add_notebook(self, path: str) -> Notebook:
        abs_path = os.path.abspath(path)
        nb = Notebook(abs_path)
        nb.scan()
        self.notebooks[abs_path] = nb
        self._refresh_cache()
        return nb
    
    def _refresh_cache(self):
        self._note_cache.clear()
        for nb in self.notebooks.values():
            for path, note in nb.notes.items():
                self._note_cache[path] = note
    
    def get_note_by_path(self, path: str) -> Optional[Note]:
        abs_path = os.path.abspath(path)
        if abs_path in self._note_cache:
            return self._note_cache[abs_path]
        
        for nb in self.notebooks.values():
            if abs_path in nb.notes:
                return nb.notes[abs_path]
        
        if os.path.exists(abs_path):
            return Note(abs_path)
        return None
    
    def global_search(self, query: str) -> List[Note]:
        results = []
        for nb in self.notebooks.values():
            results.extend(nb.search(query))
        return list({n.file_path: n for n in results}.values())
    
    def find_backlinks(self, target_note: Note) -> List[Note]:
        target_title = os.path.splitext(os.path.basename(target_note.file_path))[0]
        backlinks = []
        
        for note in self._note_cache.values():
            if target_title in note.linked_notes:
                backlinks.append(note)
        
        return backlinks
    
    def get_all_notes(self) -> List[Note]:
        return list(self._note_cache.values())
    
    def rescan_all(self):
        for nb in self.notebooks.values():
            nb.scan()
        self._refresh_cache()
