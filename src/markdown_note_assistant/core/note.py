"""
Note entity module - represents a single markdown note file.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import frontmatter


@dataclass
class Heading:
    """Represents a heading in the document."""
    level: int
    text: str
    anchor: str
    line_number: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level,
            "text": self.text,
            "anchor": self.anchor,
            "line_number": self.line_number,
        }


@dataclass
class WikiLink:
    """Represents a wiki-style link [[note name]]."""
    target: str
    heading: Optional[str] = None
    display_text: Optional[str] = None
    line_number: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "target": self.target,
            "heading": self.heading,
            "display_text": self.display_text,
            "line_number": self.line_number,
        }


@dataclass
class Note:
    """
    Note entity - represents a single markdown note file.
    
    Attributes:
        file_path: Absolute path to the note file
        title: Note title (from frontmatter or filename)
        content: Raw markdown content
        metadata: YAML frontmatter metadata
        tags: List of tags
        created_at: Creation timestamp
        modified_at: Last modification timestamp
        linked_notes: List of wiki links in this note
        headings: List of headings structure
    """
    
    file_path: Path
    title: str = ""
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    linked_notes: List[WikiLink] = field(default_factory=list)
    headings: List[Heading] = field(default_factory=list)
    _is_modified: bool = field(default=False, repr=False)
    
    def __post_init__(self) -> None:
        if isinstance(self.file_path, str):
            self.file_path = Path(self.file_path)
        if not self.title:
            self.title = self._extract_title_from_filename()
    
    def _extract_title_from_filename(self) -> str:
        """Extract title from filename (without extension)."""
        stem = self.file_path.stem
        stem = re.sub(r"^\d{4}-\d{2}-\d{2}[-_]?", "", stem)
        stem = re.sub(r"[-_]+", " ", stem)
        return stem.strip().title()
    
    @classmethod
    def from_file(cls, file_path: Path | str) -> "Note":
        """
        Create a Note instance from a file.
        
        Args:
            file_path: Path to the markdown file
            
        Returns:
            Note instance with loaded content
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Note file not found: {file_path}")
        
        stat = file_path.stat()
        created_at = datetime.fromtimestamp(stat.st_ctime)
        modified_at = datetime.fromtimestamp(stat.st_mtime)
        
        with open(file_path, "r", encoding="utf-8") as f:
            raw_content = f.read()
        
        note = cls(
            file_path=file_path,
            created_at=created_at,
            modified_at=modified_at,
        )
        note._parse_content(raw_content)
        
        return note
    
    def _parse_content(self, raw_content: str) -> None:
        """Parse the raw content to extract metadata and body."""
        try:
            post = frontmatter.loads(raw_content)
            self.metadata = dict(post.metadata)
            self.content = post.content
        except Exception:
            self.metadata = {}
            self.content = raw_content
        
        self.title = self.metadata.get("title", self._extract_title_from_filename())
        self.tags = self._extract_tags()
        self.headings = self._extract_headings()
        self.linked_notes = self._extract_wiki_links()
    
    def _extract_tags(self) -> List[str]:
        """Extract tags from metadata."""
        tags = self.metadata.get("tags", [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",")]
        return list(tags) if tags else []
    
    def _extract_headings(self) -> List[Heading]:
        """Extract heading structure from content."""
        headings = []
        heading_pattern = re.compile(r"^(#{1,6})\s+(.+?)(?:\s+\{#([^}]+)\})?$", re.MULTILINE)
        
        for i, line in enumerate(self.content.split("\n"), 1):
            match = heading_pattern.match(line)
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                anchor = match.group(3) or self._generate_anchor(text)
                headings.append(Heading(
                    level=level,
                    text=text,
                    anchor=anchor,
                    line_number=i,
                ))
        
        return headings
    
    def _generate_anchor(self, text: str) -> str:
        """Generate an anchor ID from heading text."""
        anchor = text.lower()
        anchor = re.sub(r"[^\w\u4e00-\u9fff\s-]", "", anchor)
        anchor = re.sub(r"[\s]+", "-", anchor)
        return anchor.strip("-")
    
    def _extract_wiki_links(self) -> List[WikiLink]:
        """Extract wiki-style links from content."""
        links = []
        link_pattern = re.compile(r"\[\[([^\]]+)\]\]")
        
        for i, line in enumerate(self.content.split("\n"), 1):
            for match in link_pattern.finditer(line):
                link_text = match.group(1)
                
                parts = link_text.split("|")
                target = parts[0].strip()
                display_text = parts[1].strip() if len(parts) > 1 else None
                
                if "#" in target:
                    target, heading = target.split("#", 1)
                    heading = heading.strip()
                else:
                    heading = None
                
                links.append(WikiLink(
                    target=target,
                    heading=heading,
                    display_text=display_text,
                    line_number=i,
                ))
        
        return links
    
    def save(self) -> None:
        """Save the note to file."""
        self._ensure_directory_exists()
        
        raw_content = self._build_raw_content()
        
        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write(raw_content)
        
        self._is_modified = False
        self.modified_at = datetime.now()
    
    def _ensure_directory_exists(self) -> None:
        """Ensure the parent directory exists."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _build_raw_content(self) -> str:
        """Build the raw content with frontmatter."""
        metadata = self.metadata.copy()
        metadata["title"] = self.title
        if self.tags:
            metadata["tags"] = self.tags
        
        if metadata:
            post = frontmatter.Post(self.content, **metadata)
            return frontmatter.dumps(post)
        else:
            return self.content
    
    def reload(self) -> None:
        """Reload the note from file."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"Note file not found: {self.file_path}")
        
        with open(self.file_path, "r", encoding="utf-8") as f:
            raw_content = f.read()
        
        self._parse_content(raw_content)
        
        stat = self.file_path.stat()
        self.modified_at = datetime.fromtimestamp(stat.st_mtime)
        self._is_modified = False
    
    def update_metadata(self, **kwargs: Any) -> None:
        """
        Update metadata fields.
        
        Args:
            **kwargs: Key-value pairs to update in metadata
        """
        for key, value in kwargs.items():
            self.metadata[key] = value
        
        if "title" in kwargs:
            self.title = kwargs["title"]
        if "tags" in kwargs:
            self.tags = kwargs["tags"] if isinstance(kwargs["tags"], list) else [kwargs["tags"]]
        
        self._is_modified = True
    
    def set_content(self, content: str) -> None:
        """Set the note content and re-parse."""
        self._parse_content(content)
        self._is_modified = True
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to the note."""
        if tag not in self.tags:
            self.tags.append(tag)
            self.metadata["tags"] = self.tags
            self._is_modified = True
    
    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the note."""
        if tag in self.tags:
            self.tags.remove(tag)
            self.metadata["tags"] = self.tags
            self._is_modified = True
    
    def get_heading_by_anchor(self, anchor: str) -> Optional[Heading]:
        """Get a heading by its anchor."""
        for heading in self.headings:
            if heading.anchor == anchor:
                return heading
        return None
    
    def get_outline(self) -> List[Dict[str, Any]]:
        """Get the document outline as a list of dicts."""
        return [h.to_dict() for h in self.headings]
    
    def get_word_count(self) -> int:
        """Get the word count of the content."""
        text = re.sub(r"\s+", " ", self.content)
        if re.search(r"[\u4e00-\u9fff]", text):
            chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
            other_words = len(re.findall(r"[a-zA-Z]+", text))
            return chinese_chars + other_words
        else:
            return len(text.split())
    
    def get_char_count(self) -> int:
        """Get the character count of the content."""
        return len(self.content)
    
    def get_line_count(self) -> int:
        """Get the line count of the content."""
        return len(self.content.split("\n"))
    
    def is_modified(self) -> bool:
        """Check if the note has unsaved changes."""
        return self._is_modified
    
    def get_relative_path(self, base_path: Path) -> Path:
        """Get the relative path from a base directory."""
        return self.file_path.relative_to(base_path)
    
    def __str__(self) -> str:
        return f"Note(title='{self.title}', path='{self.file_path}')"
    
    def __repr__(self) -> str:
        return (
            f"Note(file_path={self.file_path!r}, title={self.title!r}, "
            f"tags={self.tags!r}, modified_at={self.modified_at!r})"
        )
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Note):
            return False
        return self.file_path == other.file_path
    
    def __hash__(self) -> int:
        return hash(self.file_path)
