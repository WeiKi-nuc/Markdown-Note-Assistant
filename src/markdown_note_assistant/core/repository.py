"""
Note Repository module - global note management and search indexing.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional, Set, Tuple

from markdown_note_assistant.core.note import Note
from markdown_note_assistant.core.notebook import Notebook
from markdown_note_assistant.core.parser import MarkdownParser


@dataclass
class SearchResult:
    """Represents a search result."""
    note: Note
    score: float
    matches: List[Dict[str, Any]]
    snippet: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "note_path": str(self.note.file_path),
            "note_title": self.note.title,
            "score": self.score,
            "matches": self.matches,
            "snippet": self.snippet,
        }


@dataclass
class Backlink:
    """Represents a backlink to a note."""
    source_note: Note
    link_text: str
    line_number: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_path": str(self.source_note.file_path),
            "source_title": self.source_note.title,
            "link_text": self.link_text,
            "line_number": self.line_number,
        }


class SearchIndex:
    """
    Full-text search index using SQLite FTS5.
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize the search index.
        
        Args:
            db_path: Path to the SQLite database file
        """
        if db_path is None:
            config_dir = Path(__file__).parent.parent.parent.parent / ".md_note_assistant"
            db_path = config_dir / "search.db"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._lock = threading.Lock()
        self._conn: Optional[sqlite3.Connection] = None
        self._init_database()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get or create a database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn
    
    def _init_database(self) -> None:
        """Initialize the database schema."""
        conn = self._get_connection()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS notes (
                path TEXT PRIMARY KEY,
                title TEXT,
                content TEXT,
                tags TEXT,
                modified_at TEXT
            );
            
            CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(
                path,
                title,
                content,
                tags,
                content='notes',
                content_rowid='rowid'
            );
            
            CREATE TRIGGER IF NOT EXISTS notes_ai AFTER INSERT ON notes BEGIN
                INSERT INTO notes_fts(rowid, path, title, content, tags)
                VALUES (new.rowid, new.path, new.title, new.content, new.tags);
            END;
            
            CREATE TRIGGER IF NOT EXISTS notes_ad AFTER DELETE ON notes BEGIN
                INSERT INTO notes_fts(notes_fts, rowid, path, title, content, tags)
                VALUES('delete', old.rowid, old.path, old.title, old.content, old.tags);
            END;
            
            CREATE TRIGGER IF NOT EXISTS notes_au AFTER UPDATE ON notes BEGIN
                INSERT INTO notes_fts(notes_fts, rowid, path, title, content, tags)
                VALUES('delete', old.rowid, old.path, old.title, old.content, old.tags);
                INSERT INTO notes_fts(rowid, path, title, content, tags)
                VALUES (new.rowid, new.path, new.title, new.content, new.tags);
            END;
        """)
        conn.commit()
    
    def index_note(self, note: Note) -> None:
        """Add or update a note in the index."""
        with self._lock:
            conn = self._get_connection()
            conn.execute("""
                INSERT OR REPLACE INTO notes (path, title, content, tags, modified_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                str(note.file_path),
                note.title,
                note.content,
                json.dumps(note.tags),
                note.modified_at.isoformat() if note.modified_at else None,
            ))
            conn.commit()
    
    def remove_note(self, path: Path) -> None:
        """Remove a note from the index."""
        with self._lock:
            conn = self._get_connection()
            conn.execute("DELETE FROM notes WHERE path = ?", (str(path),))
            conn.commit()
    
    def search(
        self,
        query: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Search the index for matching notes.
        
        Args:
            query: Search query
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of search results
        """
        conn = self._get_connection()
        
        fts_query = self._build_fts_query(query)
        
        cursor = conn.execute("""
            SELECT path, title, snippet(notes_fts, 2, '<<', '>>', '...', 20) as snippet,
                   bm25(notes_fts) as score
            FROM notes_fts
            WHERE notes_fts MATCH ?
            ORDER BY score
            LIMIT ? OFFSET ?
        """, (fts_query, limit, offset))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "path": row["path"],
                "title": row["title"],
                "snippet": row["snippet"],
                "score": -row["score"],
            })
        
        return results
    
    def _build_fts_query(self, query: str) -> str:
        """Build an FTS5 query string."""
        query = query.strip()
        
        if not query:
            return "*"
        
        if re.match(r'^[a-zA-Z0-9_\-\u4e00-\u9fff]+$', query):
            return f'"{query}"*'
        
        return query
    
    def search_by_tag(self, tag: str) -> List[str]:
        """Search for notes by tag."""
        conn = self._get_connection()
        
        cursor = conn.execute("""
            SELECT path FROM notes
            WHERE tags LIKE ?
        """, (f'%"{tag}"%',))
        
        return [row["path"] for row in cursor.fetchall()]
    
    def clear(self) -> None:
        """Clear the entire index."""
        with self._lock:
            conn = self._get_connection()
            conn.execute("DELETE FROM notes")
            conn.commit()
    
    def close(self) -> None:
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None


class NoteRepository:
    """
    Note Repository - global note management and coordination.
    
    This class manages multiple notebooks and provides:
    - Cross-notebook search
    - Backlink tracking
    - Global tag management
    - Recent files tracking
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize the repository.
        
        Args:
            config_dir: Directory for storing configuration and cache
        """
        self.config_dir = config_dir or Path.home() / ".md_note_assistant"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.notebooks: Dict[str, Notebook] = {}
        self._note_cache: Dict[Path, Note] = {}
        self._link_graph: Dict[str, Set[str]] = defaultdict(set)
        self._backlinks: Dict[str, List[Backlink]] = defaultdict(list)
        
        self._search_index = SearchIndex(self.config_dir / "search.db")
        self._parser = MarkdownParser()
        
        self._recent_files: List[Path] = []
        self._pinned_files: Set[Path] = set()
        self._favorites: Dict[str, List[Path]] = defaultdict(list)
        
        self._load_state()
    
    def add_notebook(self, path: Path | str, name: str = "") -> Notebook:
        """
        Add a notebook to the repository.
        
        Args:
            path: Path to the notebook directory
            name: Optional display name
            
        Returns:
            The added Notebook instance
        """
        path = Path(path)
        key = str(path.resolve())
        
        if key in self.notebooks:
            return self.notebooks[key]
        
        notebook = Notebook.from_path(path, name)
        self.notebooks[key] = notebook
        
        for note in notebook.get_all_notes():
            self._note_cache[note.file_path] = note
            self._search_index.index_note(note)
            self._update_link_graph(note)
        
        self._save_state()
        
        return notebook
    
    def remove_notebook(self, path: Path | str) -> bool:
        """Remove a notebook from the repository."""
        path = Path(path)
        key = str(path.resolve())
        
        if key not in self.notebooks:
            return False
        
        notebook = self.notebooks.pop(key)
        
        for note in notebook.get_all_notes():
            if note.file_path in self._note_cache:
                del self._note_cache[note.file_path]
            self._search_index.remove_note(note.file_path)
        
        self._save_state()
        return True
    
    def get_note_by_path(self, path: Path | str) -> Optional[Note]:
        """Get a note by its file path."""
        path = Path(path).resolve()
        
        if path in self._note_cache:
            return self._note_cache[path]
        
        for notebook in self.notebooks.values():
            note = notebook.get_note_by_path(path)
            if note:
                self._note_cache[path] = note
                return note
        
        if path.exists():
            try:
                note = Note.from_file(path)
                self._note_cache[path] = note
                return note
            except Exception:
                pass
        
        return None
    
    def get_note_by_title(self, title: str) -> Optional[Note]:
        """Find a note by its title across all notebooks."""
        title_lower = title.lower()
        
        for note in self._note_cache.values():
            if note.title.lower() == title_lower:
                return note
        
        for notebook in self.notebooks.values():
            note = notebook.get_note_by_title(title)
            if note:
                return note
        
        return None
    
    def global_search(
        self,
        query: str,
        search_content: bool = True,
        search_title: bool = True,
        search_tags: bool = True,
        case_sensitive: bool = False,
        use_regex: bool = False,
        limit: int = 50,
    ) -> List[SearchResult]:
        """
        Search across all notebooks.
        
        Args:
            query: Search query
            search_content: Search in note content
            search_title: Search in note titles
            search_tags: Search in tags
            case_sensitive: Case sensitive search
            use_regex: Use regular expression
            limit: Maximum results
            
        Returns:
            List of SearchResult objects
        """
        results = []
        
        index_results = self._search_index.search(query, limit=limit * 2)
        
        for result in index_results:
            path = Path(result["path"])
            note = self.get_note_by_path(path)
            
            if note:
                matches = self._find_matches(note, query, search_content, search_title, search_tags)
                
                if matches:
                    results.append(SearchResult(
                        note=note,
                        score=result["score"],
                        matches=matches,
                        snippet=result["snippet"],
                    ))
        
        return results[:limit]
    
    def _find_matches(
        self,
        note: Note,
        query: str,
        search_content: bool,
        search_title: bool,
        search_tags: bool,
    ) -> List[Dict[str, Any]]:
        """Find all matches in a note."""
        matches = []
        
        if search_title:
            if query.lower() in note.title.lower():
                matches.append({
                    "type": "title",
                    "text": note.title,
                })
        
        if search_tags:
            for tag in note.tags:
                if query.lower() in tag.lower():
                    matches.append({
                        "type": "tag",
                        "text": tag,
                    })
        
        if search_content:
            for i, line in enumerate(note.content.split("\n"), 1):
                if query.lower() in line.lower():
                    matches.append({
                        "type": "content",
                        "line_number": i,
                        "text": line[:100],
                    })
        
        return matches
    
    def find_backlinks(self, target_note: Note) -> List[Backlink]:
        """
        Find all notes that link to the target note.
        
        Args:
            target_note: The note to find backlinks for
            
        Returns:
            List of Backlink objects
        """
        backlinks = []
        target_title = target_note.title.lower()
        target_name = target_note.file_path.stem.lower()
        
        for note in self._note_cache.values():
            if note.file_path == target_note.file_path:
                continue
            
            for link in note.linked_notes:
                link_target = link.target.lower()
                
                if link_target == target_title or link_target == target_name:
                    backlinks.append(Backlink(
                        source_note=note,
                        link_text=link.target,
                        line_number=link.line_number,
                    ))
        
        return backlinks
    
    def find_unlinked_mentions(self, note: Note) -> List[Dict[str, Any]]:
        """
        Find text that mentions the note title but isn't linked.
        
        Args:
            note: The note to check for mentions
            
        Returns:
            List of mention info dicts
        """
        mentions = []
        title = note.title
        
        for other_note in self._note_cache.values():
            if other_note.file_path == note.file_path:
                continue
            
            for i, line in enumerate(other_note.content.split("\n"), 1):
                if title in line:
                    is_linked = any(
                        link.target.lower() == title.lower()
                        for link in other_note.linked_notes
                        if link.line_number == i
                    )
                    
                    if not is_linked:
                        mentions.append({
                            "note": other_note,
                            "line_number": i,
                            "text": line[:100],
                        })
        
        return mentions
    
    def _update_link_graph(self, note: Note) -> None:
        """Update the link graph with a note's links."""
        source = str(note.file_path)
        
        if source in self._link_graph:
            old_targets = self._link_graph[source].copy()
            for target in old_targets:
                if target in self._backlinks:
                    self._backlinks[target] = [
                        bl for bl in self._backlinks[target]
                        if bl.source_note.file_path != note.file_path
                    ]
        
        self._link_graph[source] = set()
        
        for link in note.linked_notes:
            target_note = self.get_note_by_title(link.target)
            if target_note:
                target_path = str(target_note.file_path)
                self._link_graph[source].add(target_path)
                self._backlinks[target_path].append(Backlink(
                    source_note=note,
                    link_text=link.target,
                    line_number=link.line_number,
                ))
    
    def get_related_notes(self, note: Note, depth: int = 1) -> List[Note]:
        """
        Get notes related to the given note through links.
        
        Args:
            note: The source note
            depth: How many degrees of separation (1 or 2)
            
        Returns:
            List of related notes
        """
        related: Set[Note] = set()
        source_path = str(note.file_path)
        
        direct_links = self._link_graph.get(source_path, set())
        
        for target_path in direct_links:
            target_note = self.get_note_by_path(target_path)
            if target_note:
                related.add(target_note)
        
        if depth >= 2:
            for target_path in direct_links.copy():
                second_degree = self._link_graph.get(target_path, set())
                for second_path in second_degree:
                    if second_path != source_path:
                        second_note = self.get_note_by_path(second_path)
                        if second_note:
                            related.add(second_note)
        
        backlinks = self._backlinks.get(source_path, [])
        for bl in backlinks:
            related.add(bl.source_note)
        
        related.discard(note)
        return list(related)
    
    def check_broken_links(self) -> List[Dict[str, Any]]:
        """
        Check for broken wiki links.
        
        Returns:
            List of broken link info dicts
        """
        broken = []
        
        for note in self._note_cache.values():
            for link in note.linked_notes:
                target = self.get_note_by_title(link.target)
                
                if not target:
                    broken.append({
                        "source_note": note,
                        "target": link.target,
                        "line_number": link.line_number,
                    })
        
        return broken
    
    def get_all_tags(self) -> Dict[str, int]:
        """Get all tags with their frequency across all notebooks."""
        tag_counts: Dict[str, int] = defaultdict(int)
        
        for note in self._note_cache.values():
            for tag in note.tags:
                tag_counts[tag] += 1
        
        return dict(sorted(tag_counts.items(), key=lambda x: -x[1]))
    
    def get_notes_by_tag(self, tag: str) -> List[Note]:
        """Get all notes with a specific tag."""
        notes = []
        
        for note in self._note_cache.values():
            if tag in note.tags:
                notes.append(note)
        
        return sorted(notes, key=lambda n: n.modified_at or datetime.min, reverse=True)
    
    def add_recent_file(self, path: Path) -> None:
        """Add a file to recent files list."""
        path = Path(path).resolve()
        
        if path in self._recent_files:
            self._recent_files.remove(path)
        
        self._recent_files.insert(0, path)
        self._recent_files = self._recent_files[:20]
        
        self._save_state()
    
    def get_recent_files(self, limit: int = 20) -> List[Path]:
        """Get recent files list."""
        return self._recent_files[:limit]
    
    def pin_file(self, path: Path) -> None:
        """Pin a file to the pinned list."""
        self._pinned_files.add(Path(path).resolve())
        self._save_state()
    
    def unpin_file(self, path: Path) -> None:
        """Unpin a file."""
        self._pinned_files.discard(Path(path).resolve())
        self._save_state()
    
    def is_pinned(self, path: Path) -> bool:
        """Check if a file is pinned."""
        return Path(path).resolve() in self._pinned_files
    
    def add_to_favorites(self, group: str, path: Path) -> None:
        """Add a file to a favorites group."""
        path = Path(path).resolve()
        if path not in self._favorites[group]:
            self._favorites[group].append(path)
        self._save_state()
    
    def remove_from_favorites(self, group: str, path: Path) -> None:
        """Remove a file from a favorites group."""
        path = Path(path).resolve()
        if path in self._favorites[group]:
            self._favorites[group].remove(path)
        self._save_state()
    
    def get_favorites(self, group: str) -> List[Path]:
        """Get files in a favorites group."""
        return self._favorites.get(group, [])
    
    def rebuild_search_index(self) -> int:
        """
        Rebuild the search index from scratch.
        
        Returns:
            Number of notes indexed
        """
        self._search_index.clear()
        count = 0
        
        for note in self._note_cache.values():
            self._search_index.index_note(note)
            count += 1
        
        return count
    
    def refresh_note(self, path: Path) -> Optional[Note]:
        """Refresh a note from disk."""
        path = Path(path).resolve()
        
        if path in self._note_cache:
            try:
                self._note_cache[path].reload()
                self._search_index.index_note(self._note_cache[path])
                self._update_link_graph(self._note_cache[path])
                return self._note_cache[path]
            except Exception:
                del self._note_cache[path]
        
        return None
    
    def _load_state(self) -> None:
        """Load saved state from disk."""
        state_file = self.config_dir / "repository_state.json"
        
        if state_file.exists():
            try:
                with open(state_file, "r", encoding="utf-8") as f:
                    state = json.load(f)
                
                self._recent_files = [Path(p) for p in state.get("recent_files", [])]
                self._pinned_files = {Path(p) for p in state.get("pinned_files", [])}
                self._favorites = defaultdict(list)
                for group, paths in state.get("favorites", {}).items():
                    self._favorites[group] = [Path(p) for p in paths]
            except Exception:
                pass
    
    def _save_state(self) -> None:
        """Save state to disk."""
        state_file = self.config_dir / "repository_state.json"
        
        state = {
            "recent_files": [str(p) for p in self._recent_files],
            "pinned_files": [str(p) for p in self._pinned_files],
            "favorites": {
                group: [str(p) for p in paths]
                for group, paths in self._favorites.items()
            },
        }
        
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    
    def get_all_notes(self) -> Generator[Note, None, None]:
        """Iterate over all notes in all notebooks."""
        yield from self._note_cache.values()
    
    def get_note_count(self) -> int:
        """Get total number of notes."""
        return len(self._note_cache)
    
    def close(self) -> None:
        """Close the repository and save state."""
        self._save_state()
        self._search_index.close()
