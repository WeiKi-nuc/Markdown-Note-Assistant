"""
Link Manager module - handles wiki links and backlinks.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Set, Tuple

from markdown_note_assistant.core.note import Note
from markdown_note_assistant.core.parser import MarkdownParser, WikiLink


@dataclass
class LinkNode:
    """Represents a node in the link graph."""
    note_path: Path
    note_title: str
    outgoing_links: List[str] = field(default_factory=list)
    incoming_links: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": str(self.note_path),
            "title": self.note_title,
            "outgoing": self.outgoing_links,
            "incoming": self.incoming_links,
        }


@dataclass
class BrokenLink:
    """Represents a broken/invalid link."""
    source_path: Path
    source_title: str
    target: str
    line_number: int
    heading: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_path": str(self.source_path),
            "source_title": self.source_title,
            "target": self.target,
            "line_number": self.line_number,
            "heading": self.heading,
        }


@dataclass
class UnlinkedMention:
    """Represents an unlinked mention of a note."""
    source_path: Path
    source_title: str
    target_title: str
    line_number: int
    context: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_path": str(self.source_path),
            "source_title": self.source_title,
            "target_title": self.target_title,
            "line_number": self.line_number,
            "context": self.context,
        }


class LinkManager:
    """
    Link Manager - manages wiki links and relationships between notes.
    
    Features:
    - Parse and track wiki links
    - Build link graph
    - Find backlinks
    - Detect broken links
    - Find unlinked mentions
    - Generate relationship graph data
    """
    
    def __init__(self):
        """Initialize the link manager."""
        self._parser = MarkdownParser()
        self._link_graph: Dict[str, LinkNode] = {}
        self._title_to_path: Dict[str, Path] = {}
        self._path_to_title: Dict[str, str] = {}
        self._notes: Dict[Path, Note] = {}
    
    def register_note(self, note: Note) -> None:
        """
        Register a note with the link manager.
        
        Args:
            note: Note to register
        """
        path = note.file_path
        path_str = str(path)
        title_lower = note.title.lower()
        
        self._notes[path] = note
        self._title_to_path[title_lower] = path
        self._path_to_title[path_str] = note.title
        
        if path_str not in self._link_graph:
            self._link_graph[path_str] = LinkNode(
                note_path=path,
                note_title=note.title,
            )
        else:
            self._link_graph[path_str].note_title = note.title
    
    def unregister_note(self, note: Note | Path) -> None:
        """
        Unregister a note from the link manager.
        
        Args:
            note: Note or path to unregister
        """
        if isinstance(note, Note):
            path = note.file_path
        else:
            path = note
        
        path_str = str(path)
        title = self._path_to_title.get(path_str, "")
        
        if path in self._notes:
            del self._notes[path]
        
        if title.lower() in self._title_to_path:
            del self._title_to_path[title.lower()]
        
        if path_str in self._path_to_title:
            del self._path_to_title[path_str]
        
        if path_str in self._link_graph:
            node = self._link_graph.pop(path_str)
            for target in node.outgoing_links:
                if target in self._link_graph:
                    self._link_graph[target].incoming_links.remove(path_str)
        
        for node in self._link_graph.values():
            if path_str in node.outgoing_links:
                node.outgoing_links.remove(path_str)
    
    def update_note(self, note: Note) -> None:
        """
        Update a note's links in the graph.
        
        Args:
            note: Note to update
        """
        self.unregister_note(note)
        self.register_note(note)
        self._update_links(note)
    
    def _update_links(self, note: Note) -> None:
        """Update the link graph with a note's wiki links."""
        path_str = str(note.file_path)
        
        if path_str not in self._link_graph:
            return
        
        node = self._link_graph[path_str]
        old_outgoing = set(node.outgoing_links)
        
        node.outgoing_links.clear()
        
        for link in note.linked_notes:
            target_path = self.resolve_link(link.target)
            if target_path:
                target_str = str(target_path)
                if target_str not in node.outgoing_links:
                    node.outgoing_links.append(target_str)
                
                if target_str in self._link_graph:
                    target_node = self._link_graph[target_str]
                    if path_str not in target_node.incoming_links:
                        target_node.incoming_links.append(path_str)
        
        new_outgoing = set(node.outgoing_links)
        removed = old_outgoing - new_outgoing
        
        for target_str in removed:
            if target_str in self._link_graph:
                target_node = self._link_graph[target_str]
                if path_str in target_node.incoming_links:
                    target_node.incoming_links.remove(path_str)
    
    def resolve_link(self, target: str) -> Optional[Path]:
        """
        Resolve a wiki link target to a file path.
        
        Args:
            target: Link target (title or filename)
            
        Returns:
            Path to the target note, or None if not found
        """
        target_lower = target.lower()
        
        if target_lower in self._title_to_path:
            return self._title_to_path[target_lower]
        
        for path, note in self._notes.items():
            stem = path.stem.lower()
            if stem == target_lower:
                return path
        
        for path in self._notes:
            if target_lower in str(path).lower():
                return path
        
        return None
    
    def parse_links(self, note: Note) -> List[WikiLink]:
        """
        Parse all wiki links from a note.
        
        Args:
            note: Note to parse
            
        Returns:
            List of WikiLink objects
        """
        return note.linked_notes
    
    def get_backlinks(self, note: Note) -> List[Note]:
        """
        Get all notes that link to the given note.
        
        Args:
            note: Target note
            
        Returns:
            List of notes that link to the target
        """
        path_str = str(note.file_path)
        
        if path_str not in self._link_graph:
            return []
        
        node = self._link_graph[path_str]
        backlinks = []
        
        for source_str in node.incoming_links:
            source_path = Path(source_str)
            if source_path in self._notes:
                backlinks.append(self._notes[source_path])
        
        return backlinks
    
    def get_outgoing_links(self, note: Note) -> List[Note]:
        """
        Get all notes that the given note links to.
        
        Args:
            note: Source note
            
        Returns:
            List of notes linked from the source
        """
        path_str = str(note.file_path)
        
        if path_str not in self._link_graph:
            return []
        
        node = self._link_graph[path_str]
        outgoing = []
        
        for target_str in node.outgoing_links:
            target_path = Path(target_str)
            if target_path in self._notes:
                outgoing.append(self._notes[target_path])
        
        return outgoing
    
    def get_related_notes(self, note: Note, depth: int = 1) -> List[Tuple[Note, int]]:
        """
        Get notes related to the given note through links.
        
        Args:
            note: Source note
            depth: Maximum degrees of separation (1 or 2)
            
        Returns:
            List of tuples (note, distance)
        """
        path_str = str(note.file_path)
        visited: Set[str] = {path_str}
        related: List[Tuple[Note, int]] = []
        
        current_level = [path_str]
        
        for distance in range(1, depth + 1):
            next_level: List[str] = []
            
            for current in current_level:
                if current not in self._link_graph:
                    continue
                
                node = self._link_graph[current]
                
                for neighbor in node.outgoing_links + node.incoming_links:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        next_level.append(neighbor)
                        
                        neighbor_path = Path(neighbor)
                        if neighbor_path in self._notes:
                            related.append((self._notes[neighbor_path], distance))
            
            current_level = next_level
        
        return related
    
    def check_broken_links(self) -> List[BrokenLink]:
        """
        Check for broken wiki links.
        
        Returns:
            List of BrokenLink objects
        """
        broken = []
        
        for note in self._notes.values():
            for link in note.linked_links:
                target_path = self.resolve_link(link.target)
                
                if target_path is None:
                    broken.append(BrokenLink(
                        source_path=note.file_path,
                        source_title=note.title,
                        target=link.target,
                        line_number=link.line_number,
                        heading=link.heading,
                    ))
        
        return broken
    
    def get_unlinked_mentions(self, note: Note) -> List[UnlinkedMention]:
        """
        Find text that mentions the note title but isn't linked.
        
        Args:
            note: Note to check for mentions
            
        Returns:
            List of UnlinkedMention objects
        """
        mentions = []
        title = note.title.lower()
        
        for other_note in self._notes.values():
            if other_note.file_path == note.file_path:
                continue
            
            linked_titles = {
                link.target.lower()
                for link in other_note.linked_notes
            }
            
            if title in linked_titles:
                continue
            
            for i, line in enumerate(other_note.content.split("\n"), 1):
                if title in line.lower():
                    start = line.lower().find(title)
                    context_start = max(0, start - 20)
                    context_end = min(len(line), start + len(title) + 20)
                    context = line[context_start:context_end]
                    
                    mentions.append(UnlinkedMention(
                        source_path=other_note.file_path,
                        source_title=other_note.title,
                        target_title=note.title,
                        line_number=i,
                        context=context,
                    ))
        
        return mentions
    
    def get_graph_data(self) -> Dict[str, Any]:
        """
        Generate data for visualizing the link graph.
        
        Returns:
            Dict with 'nodes' and 'edges' for graph visualization
        """
        nodes = []
        edges = []
        
        for path_str, node in self._link_graph.items():
            nodes.append({
                "id": path_str,
                "title": node.note_title,
                "path": path_str,
                "link_count": len(node.outgoing_links) + len(node.incoming_links),
            })
            
            for target in node.outgoing_links:
                edges.append({
                    "source": path_str,
                    "target": target,
                })
        
        return {
            "nodes": nodes,
            "edges": edges,
        }
    
    def get_orphans(self) -> List[Note]:
        """
        Get notes that have no incoming or outgoing links.
        
        Returns:
            List of orphan notes
        """
        orphans = []
        
        for path_str, node in self._link_graph.items():
            if not node.incoming_links and not node.outgoing_links:
                path = Path(path_str)
                if path in self._notes:
                    orphans.append(self._notes[path])
        
        return orphans
    
    def get_hubs(self, min_links: int = 5) -> List[Tuple[Note, int]]:
        """
        Get notes with many connections (hubs).
        
        Args:
            min_links: Minimum number of links to be considered a hub
            
        Returns:
            List of tuples (note, link_count)
        """
        hubs = []
        
        for path_str, node in self._link_graph.items():
            link_count = len(node.incoming_links) + len(node.outgoing_links)
            if link_count >= min_links:
                path = Path(path_str)
                if path in self._notes:
                    hubs.append((self._notes[path], link_count))
        
        return sorted(hubs, key=lambda x: -x[1])
    
    def suggest_links(self, note: Note, limit: int = 5) -> List[Tuple[Note, float]]:
        """
        Suggest notes that might be relevant to link.
        
        Args:
            note: Source note
            limit: Maximum number of suggestions
            
        Returns:
            List of tuples (suggested_note, relevance_score)
        """
        suggestions: Dict[Path, float] = defaultdict(float)
        
        for tag in note.tags:
            for other_note in self._notes.values():
                if other_note.file_path == note.file_path:
                    continue
                if tag in other_note.tags:
                    suggestions[other_note.file_path] += 1.0
        
        for link in note.linked_notes:
            target_path = self.resolve_link(link.target)
            if target_path and target_path in self._notes:
                target_note = self._notes[target_path]
                for related, distance in self.get_related_notes(target_note, depth=1):
                    if related.file_path != note.file_path:
                        weight = 0.5 / distance
                        suggestions[related.file_path] += weight
        
        existing_targets = {self.resolve_link(l.target) for l in note.linked_notes}
        existing_targets.add(note.file_path)
        
        for path in list(suggestions.keys()):
            if path in existing_targets:
                del suggestions[path]
        
        sorted_suggestions = sorted(
            suggestions.items(),
            key=lambda x: -x[1]
        )[:limit]
        
        result = []
        for path, score in sorted_suggestions:
            if path in self._notes:
                result.append((self._notes[path], score))
        
        return result
    
    def clear(self) -> None:
        """Clear all registered notes and links."""
        self._link_graph.clear()
        self._title_to_path.clear()
        self._path_to_title.clear()
        self._notes.clear()
    
    def get_stats(self) -> Dict[str, int]:
        """Get statistics about the link graph."""
        total_links = sum(
            len(node.outgoing_links)
            for node in self._link_graph.values()
        )
        
        return {
            "notes": len(self._notes),
            "total_links": total_links,
            "orphans": len(self.get_orphans()),
            "hubs": len(self.get_hubs()),
        }
