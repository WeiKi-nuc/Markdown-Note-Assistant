"""
Notebook module - manages a collection of notes in a directory.
"""

from __future__ import annotations

import os
import threading
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional, Set, Tuple

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from markdown_note_assistant.core.note import Note


@dataclass
class NotebookConfig:
    """Configuration for a notebook."""
    name: str
    icon: str = "📁"
    color: str = "#4A90D9"
    excluded_patterns: List[str] = field(default_factory=lambda: [".git", ".obsidian", "__pycache__"])
    auto_save: bool = True
    auto_save_interval: int = 30


@dataclass
class Notebook:
    """
    Notebook - represents a folder containing markdown notes.
    
    Attributes:
        root_path: Root directory path of the notebook
        name: Display name of the notebook
        config: Notebook configuration
        sub_notebooks: List of sub-notebooks
        notes: Dictionary of notes indexed by path
    """
    
    root_path: Path
    name: str = ""
    config: NotebookConfig = field(default_factory=NotebookConfig)
    sub_notebooks: List["Notebook"] = field(default_factory=list)
    notes: Dict[Path, Note] = field(default_factory=dict)
    _observer: Optional[Observer] = field(default=None, repr=False)
    _change_callbacks: List[Callable[[str, Path], None]] = field(default_factory=list, repr=False)
    
    def __post_init__(self) -> None:
        if isinstance(self.root_path, str):
            self.root_path = Path(self.root_path)
        
        if not self.name:
            self.name = self.root_path.name
    
    @classmethod
    def from_path(cls, path: Path | str, name: str = "") -> "Notebook":
        """
        Create a Notebook from a directory path.
        
        Args:
            path: Path to the notebook directory
            name: Optional display name
            
        Returns:
            Notebook instance
        """
        path = Path(path)
        
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
        
        notebook = cls(root_path=path, name=name or path.name)
        notebook.scan()
        
        return notebook
    
    def scan(self, recursive: bool = True) -> int:
        """
        Scan the directory and index all markdown files.
        
        Args:
            recursive: Whether to scan subdirectories
            
        Returns:
            Number of notes found
        """
        self.notes.clear()
        self.sub_notebooks.clear()
        
        count = self._scan_directory(self.root_path, recursive)
        
        return count
    
    def _scan_directory(self, directory: Path, recursive: bool, depth: int = 0) -> int:
        """Recursively scan a directory for markdown files."""
        count = 0
        
        try:
            items = sorted(directory.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        except PermissionError:
            return 0
        
        for item in items:
            if item.name.startswith("."):
                continue
            
            if item.name in self.config.excluded_patterns:
                continue
            
            if item.is_dir():
                if recursive:
                    sub_notebook = Notebook(
                        root_path=item,
                        config=self.config,
                    )
                    sub_count = sub_notebook._scan_directory(item, recursive, depth + 1)
                    if sub_count > 0:
                        self.sub_notebooks.append(sub_notebook)
                        count += sub_count
            elif item.suffix.lower() in (".md", ".markdown"):
                try:
                    note = Note.from_file(item)
                    self.notes[item] = note
                    count += 1
                except Exception as e:
                    print(f"Error loading note {item}: {e}")
        
        return count
    
    def create_note(
        self,
        title: str,
        template: str = "",
        folder: Optional[Path] = None,
        tags: Optional[List[str]] = None,
    ) -> Note:
        """
        Create a new note in the notebook.
        
        Args:
            title: Note title
            template: Template content to use
            folder: Subfolder to create the note in
            tags: List of tags for the note
            
        Returns:
            The created Note instance
        """
        filename = self._generate_filename(title)
        
        if folder:
            folder_path = self.root_path / folder
            folder_path.mkdir(parents=True, exist_ok=True)
        else:
            folder_path = self.root_path
        
        file_path = folder_path / filename
        
        if file_path.exists():
            base = file_path.stem
            counter = 1
            while file_path.exists():
                file_path = folder_path / f"{base}-{counter}.md"
                counter += 1
        
        now = datetime.now()
        content = self._build_initial_content(title, template, tags, now)
        
        file_path.write_text(content, encoding="utf-8")
        
        note = Note.from_file(file_path)
        self.notes[file_path] = note
        
        return note
    
    def _generate_filename(self, title: str) -> str:
        """Generate a valid filename from a title."""
        filename = title.strip()
        filename = "".join(c for c in filename if c.isalnum() or c in " -_")
        filename = filename.replace(" ", "-")
        filename = filename.strip("-_")
        
        if not filename:
            filename = f"untitled-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        return f"{filename}.md"
    
    def _build_initial_content(
        self,
        title: str,
        template: str,
        tags: Optional[List[str]],
        created: datetime,
    ) -> str:
        """Build the initial content for a new note."""
        frontmatter_lines = ["---"]
        frontmatter_lines.append(f"title: {title}")
        frontmatter_lines.append(f"date: {created.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if tags:
            frontmatter_lines.append("tags:")
            for tag in tags:
                frontmatter_lines.append(f"  - {tag}")
        
        frontmatter_lines.append("---")
        frontmatter_lines.append("")
        
        content = "\n".join(frontmatter_lines)
        
        if template:
            content += f"\n{template}"
        else:
            content += f"# {title}\n\n"
        
        return content
    
    def delete_note(self, note: Note | Path) -> bool:
        """
        Delete a note from the notebook.
        
        Args:
            note: Note instance or path to delete
            
        Returns:
            True if deleted successfully
        """
        if isinstance(note, Note):
            file_path = note.file_path
        else:
            file_path = Path(note)
        
        if file_path not in self.notes:
            return False
        
        try:
            file_path.unlink()
            del self.notes[file_path]
            return True
        except Exception as e:
            print(f"Error deleting note {file_path}: {e}")
            return False
    
    def move_note(self, note: Note | Path, new_path: Path) -> bool:
        """
        Move a note to a new location.
        
        Args:
            note: Note instance or path to move
            new_path: New path for the note
            
        Returns:
            True if moved successfully
        """
        if isinstance(note, Note):
            old_path = note.file_path
            note_obj = note
        else:
            old_path = Path(note)
            note_obj = self.notes.get(old_path)
        
        if old_path not in self.notes:
            return False
        
        try:
            new_path.parent.mkdir(parents=True, exist_ok=True)
            old_path.rename(new_path)
            
            if note_obj:
                note_obj.file_path = new_path
                del self.notes[old_path]
                self.notes[new_path] = note_obj
            
            return True
        except Exception as e:
            print(f"Error moving note {old_path}: {e}")
            return False
    
    def search(self, query: str, case_sensitive: bool = False) -> List[Tuple[Note, List[int]]]:
        """
        Search for notes containing the query.
        
        Args:
            query: Search query string
            case_sensitive: Whether search is case sensitive
            
        Returns:
            List of tuples (note, list of matching line numbers)
        """
        results = []
        
        if not case_sensitive:
            query_lower = query.lower()
        
        for note in self.notes.values():
            content = note.content
            if not case_sensitive:
                search_content = content.lower()
                search_query = query_lower
            else:
                search_content = content
                search_query = query
            
            if search_query in search_content:
                lines = []
                for i, line in enumerate(content.split("\n"), 1):
                    check_line = line if case_sensitive else line.lower()
                    if search_query in check_line:
                        lines.append(i)
                
                if lines:
                    results.append((note, lines))
        
        return results
    
    def search_by_tag(self, tag: str) -> List[Note]:
        """Find all notes with a specific tag."""
        return [note for note in self.notes.values() if tag in note.tags]
    
    def get_tag_statistics(self) -> Counter:
        """
        Get statistics about tag usage.
        
        Returns:
            Counter with tag frequencies
        """
        counter: Counter = Counter()
        for note in self.notes.values():
            for tag in note.tags:
                counter[tag] += 1
        return counter
    
    def get_all_tags(self) -> Set[str]:
        """Get all unique tags used in this notebook."""
        tags: Set[str] = set()
        for note in self.notes.values():
            tags.update(note.tags)
        return tags
    
    def get_recent_notes(self, limit: int = 20) -> List[Note]:
        """Get recently modified notes."""
        sorted_notes = sorted(
            self.notes.values(),
            key=lambda n: n.modified_at or datetime.min,
            reverse=True,
        )
        return sorted_notes[:limit]
    
    def get_notes_by_date_range(self, start: datetime, end: datetime) -> List[Note]:
        """Get notes modified within a date range."""
        return [
            note for note in self.notes.values()
            if note.modified_at and start <= note.modified_at <= end
        ]
    
    def watch_changes(self, callback: Optional[Callable[[str, Path], None]] = None) -> None:
        """
        Start watching for file system changes.
        
        Args:
            callback: Function to call on changes (event_type, path)
        """
        if callback:
            self._change_callbacks.append(callback)
        
        if self._observer is None:
            self._observer = Observer()
            handler = self._create_event_handler()
            self._observer.schedule(handler, str(self.root_path), recursive=True)
            self._observer.start()
    
    def _create_event_handler(self) -> FileSystemEventHandler:
        """Create a file system event handler."""
        notebook = self
        
        class Handler(FileSystemEventHandler):
            def on_created(self, event: FileSystemEvent) -> None:
                if not event.is_directory and event.src_path.endswith((".md", ".markdown")):
                    path = Path(event.src_path)
                    notebook._handle_file_created(path)
            
            def on_deleted(self, event: FileSystemEvent) -> None:
                if not event.is_directory and event.src_path.endswith((".md", ".markdown")):
                    path = Path(event.src_path)
                    notebook._handle_file_deleted(path)
            
            def on_modified(self, event: FileSystemEvent) -> None:
                if not event.is_directory and event.src_path.endswith((".md", ".markdown")):
                    path = Path(event.src_path)
                    notebook._handle_file_modified(path)
            
            def on_moved(self, event: FileSystemEvent) -> None:
                if not event.is_directory:
                    src_path = Path(event.src_path)
                    dest_path = Path(event.dest_path)
                    if src_path.suffix.lower() in (".md", ".markdown"):
                        notebook._handle_file_moved(src_path, dest_path)
        
        return Handler()
    
    def _handle_file_created(self, path: Path) -> None:
        """Handle file creation event."""
        try:
            note = Note.from_file(path)
            self.notes[path] = note
            self._notify_callbacks("created", path)
        except Exception as e:
            print(f"Error handling created file {path}: {e}")
    
    def _handle_file_deleted(self, path: Path) -> None:
        """Handle file deletion event."""
        if path in self.notes:
            del self.notes[path]
            self._notify_callbacks("deleted", path)
    
    def _handle_file_modified(self, path: Path) -> None:
        """Handle file modification event."""
        if path in self.notes:
            try:
                self.notes[path].reload()
                self._notify_callbacks("modified", path)
            except Exception as e:
                print(f"Error handling modified file {path}: {e}")
    
    def _handle_file_moved(self, src_path: Path, dest_path: Path) -> None:
        """Handle file move event."""
        if src_path in self.notes:
            note = self.notes.pop(src_path)
            note.file_path = dest_path
            self.notes[dest_path] = note
            self._notify_callbacks("moved", dest_path)
    
    def _notify_callbacks(self, event_type: str, path: Path) -> None:
        """Notify all registered callbacks of a change."""
        for callback in self._change_callbacks:
            try:
                callback(event_type, path)
            except Exception as e:
                print(f"Error in change callback: {e}")
    
    def stop_watching(self) -> None:
        """Stop watching for file system changes."""
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None
    
    def get_note_by_path(self, path: Path | str) -> Optional[Note]:
        """Get a note by its file path."""
        path = Path(path)
        return self.notes.get(path)
    
    def get_note_by_title(self, title: str) -> Optional[Note]:
        """Get a note by its title."""
        for note in self.notes.values():
            if note.title.lower() == title.lower():
                return note
        return None
    
    def get_all_notes(self) -> Generator[Note, None, None]:
        """Iterate over all notes including sub-notebooks."""
        yield from self.notes.values()
        for sub in self.sub_notebooks:
            yield from sub.get_all_notes()
    
    def get_note_count(self, include_sub: bool = True) -> int:
        """Get the total number of notes."""
        count = len(self.notes)
        if include_sub:
            for sub in self.sub_notebooks:
                count += sub.get_note_count(include_sub=True)
        return count
    
    def __str__(self) -> str:
        return f"Notebook(name='{self.name}', notes={len(self.notes)})"
    
    def __repr__(self) -> str:
        return f"Notebook(root_path={self.root_path!r}, name={self.name!r})"
    
    def __len__(self) -> int:
        return len(self.notes)
    
    def __iter__(self):
        return iter(self.notes.values())
    
    def __contains__(self, note: Note | Path) -> bool:
        if isinstance(note, Note):
            return note.file_path in self.notes
        return Path(note) in self.notes
