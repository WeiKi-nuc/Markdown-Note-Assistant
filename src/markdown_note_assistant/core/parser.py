"""
Markdown Parser module - parses markdown content and extracts metadata.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import markdown
from bs4 import BeautifulSoup


@dataclass
class ASTNode:
    """Represents a node in the Abstract Syntax Tree."""
    type: str
    content: str = ""
    children: List["ASTNode"] = field(default_factory=list)
    attrs: Dict[str, Any] = field(default_factory=dict)
    line_start: int = 0
    line_end: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "content": self.content,
            "children": [c.to_dict() for c in self.children],
            "attrs": self.attrs,
            "line_start": self.line_start,
            "line_end": self.line_end,
        }


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
    """Represents a wiki-style link."""
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
class TaskItem:
    """Represents a task list item."""
    text: str
    completed: bool
    line_number: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "completed": self.completed,
            "line_number": self.line_number,
        }


class MarkdownParser:
    """
    Markdown Parser - parses markdown content and extracts structured data.
    
    This parser handles:
    - YAML frontmatter extraction
    - Heading structure extraction
    - Wiki-link parsing
    - Task list detection
    - Code block detection
    - Table of contents generation
    """
    
    WIKI_LINK_PATTERN = re.compile(r"\[\[([^\]]+)\]\]")
    HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)(?:\s+\{#([^}]+)\})?$", re.MULTILINE)
    TASK_PATTERN = re.compile(r"^(\s*)[-*+]\s+\[([ xX])\]\s+(.+)$", re.MULTILINE)
    CODE_BLOCK_PATTERN = re.compile(r"^```(\w*)\n(.*?)^```", re.MULTILINE | re.DOTALL)
    YAML_FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
    
    def __init__(
        self,
        extensions: Optional[List[str]] = None,
        extension_configs: Optional[Dict[str, Dict[str, Any]]] = None,
    ):
        """
        Initialize the parser.
        
        Args:
            extensions: List of markdown extensions to use
            extension_configs: Configuration for extensions
        """
        self.extensions = extensions or [
            "fenced_code",
            "codehilite",
            "tables",
            "toc",
            "nl2br",
            "sane_lists",
            "smarty",
        ]
        self.extension_configs = extension_configs or {}
        self._md = None
    
    @property
    def md(self) -> markdown.Markdown:
        """Lazy initialization of markdown processor."""
        if self._md is None:
            self._md = markdown.Markdown(
                extensions=self.extensions,
                extension_configs=self.extension_configs,
            )
        return self._md
    
    def parse(self, content: str) -> List[ASTNode]:
        """
        Parse markdown content into an AST.
        
        Args:
            content: Raw markdown content
            
        Returns:
            List of AST nodes
        """
        nodes = []
        lines = content.split("\n")
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            if line.startswith("#"):
                node = self._parse_heading(line, i + 1)
                nodes.append(node)
                i += 1
            elif line.startswith("```"):
                node, consumed = self._parse_code_block(lines, i)
                nodes.append(node)
                i += consumed
            elif line.startswith("|") and i + 1 < len(lines) and "---" in lines[i + 1]:
                node, consumed = self._parse_table(lines, i)
                nodes.append(node)
                i += consumed
            elif re.match(r"^[-*+]\s", line):
                node, consumed = self._parse_list(lines, i)
                nodes.append(node)
                i += consumed
            elif line.strip():
                node, consumed = self._parse_paragraph(lines, i)
                nodes.append(node)
                i += consumed
            else:
                i += 1
        
        return nodes
    
    def _parse_heading(self, line: str, line_num: int) -> ASTNode:
        """Parse a heading line."""
        match = self.HEADING_PATTERN.match(line)
        if match:
            level = len(match.group(1))
            text = match.group(2).strip()
            anchor = match.group(3) or self._generate_anchor(text)
            return ASTNode(
                type="heading",
                content=text,
                attrs={"level": level, "anchor": anchor},
                line_start=line_num,
                line_end=line_num,
            )
        return ASTNode(type="text", content=line, line_start=line_num, line_end=line_num)
    
    def _parse_code_block(self, lines: List[str], start: int) -> Tuple[ASTNode, int]:
        """Parse a code block."""
        lang = lines[start][3:].strip()
        content_lines = []
        i = start + 1
        
        while i < len(lines) and not lines[i].startswith("```"):
            content_lines.append(lines[i])
            i += 1
        
        return ASTNode(
            type="code_block",
            content="\n".join(content_lines),
            attrs={"language": lang or "text"},
            line_start=start + 1,
            line_end=i + 1,
        ), i - start + 1
    
    def _parse_table(self, lines: List[str], start: int) -> Tuple[ASTNode, int]:
        """Parse a markdown table."""
        rows = []
        i = start
        
        while i < len(lines) and (lines[i].startswith("|") or lines[i].strip() == ""):
            if lines[i].strip() and not re.match(r"^\|[-:\s|]+\|$", lines[i]):
                cells = [c.strip() for c in lines[i].split("|")[1:-1]]
                rows.append(cells)
            i += 1
        
        return ASTNode(
            type="table",
            attrs={"rows": rows},
            line_start=start + 1,
            line_end=i,
        ), i - start
    
    def _parse_list(self, lines: List[str], start: int) -> Tuple[ASTNode, int]:
        """Parse a list (ordered or unordered)."""
        items = []
        i = start
        is_ordered = bool(re.match(r"^\d+\.", lines[start]))
        
        while i < len(lines):
            line = lines[i]
            if is_ordered:
                match = re.match(r"^(\d+)\.\s+(.+)$", line)
                if match:
                    items.append(match.group(2))
                    i += 1
                else:
                    break
            else:
                match = re.match(r"^[-*+]\s+(.+)$", line)
                if match:
                    items.append(match.group(1))
                    i += 1
                else:
                    break
        
        return ASTNode(
            type="ordered_list" if is_ordered else "unordered_list",
            children=[ASTNode(type="list_item", content=item) for item in items],
            line_start=start + 1,
            line_end=i,
        ), i - start
    
    def _parse_paragraph(self, lines: List[str], start: int) -> Tuple[ASTNode, int]:
        """Parse a paragraph."""
        content_lines = []
        i = start
        
        while i < len(lines) and lines[i].strip():
            if lines[i].startswith("#") or lines[i].startswith("```"):
                break
            content_lines.append(lines[i])
            i += 1
        
        return ASTNode(
            type="paragraph",
            content="\n".join(content_lines),
            line_start=start + 1,
            line_end=i,
        ), i - start
    
    def _generate_anchor(self, text: str) -> str:
        """Generate an anchor ID from text."""
        anchor = text.lower()
        anchor = re.sub(r"[^\w\u4e00-\u9fff\s-]", "", anchor)
        anchor = re.sub(r"[\s]+", "-", anchor)
        return anchor.strip("-")
    
    def extract_yaml_frontmatter(self, content: str) -> Tuple[Dict[str, Any], str]:
        """
        Extract YAML frontmatter from content.
        
        Args:
            content: Raw markdown content
            
        Returns:
            Tuple of (metadata dict, remaining content)
        """
        import yaml
        
        match = self.YAML_FRONTMATTER_PATTERN.match(content)
        
        if match:
            try:
                metadata = yaml.safe_load(match.group(1))
                if not isinstance(metadata, dict):
                    metadata = {}
                remaining = content[match.end():]
                return metadata, remaining
            except yaml.YAMLError:
                pass
        
        return {}, content
    
    def extract_headings(self, content: str) -> List[Heading]:
        """
        Extract all headings from content.
        
        Args:
            content: Markdown content
            
        Returns:
            List of Heading objects
        """
        headings = []
        
        for i, line in enumerate(content.split("\n"), 1):
            match = self.HEADING_PATTERN.match(line)
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
    
    def extract_wiki_links(self, content: str) -> List[WikiLink]:
        """
        Extract all wiki-style links from content.
        
        Args:
            content: Markdown content
            
        Returns:
            List of WikiLink objects
        """
        links = []
        
        for i, line in enumerate(content.split("\n"), 1):
            for match in self.WIKI_LINK_PATTERN.finditer(line):
                link_text = match.group(1)
                
                parts = link_text.split("|")
                target = parts[0].strip()
                display_text = parts[1].strip() if len(parts) > 1 else None
                
                heading = None
                if "#" in target:
                    target, heading = target.split("#", 1)
                    heading = heading.strip()
                
                links.append(WikiLink(
                    target=target,
                    heading=heading,
                    display_text=display_text,
                    line_number=i,
                ))
        
        return links
    
    def extract_tasks(self, content: str) -> List[TaskItem]:
        """
        Extract all task list items from content.
        
        Args:
            content: Markdown content
            
        Returns:
            List of TaskItem objects
        """
        tasks = []
        
        for i, line in enumerate(content.split("\n"), 1):
            match = self.TASK_PATTERN.match(line)
            if match:
                completed = match.group(2).lower() == "x"
                text = match.group(3)
                tasks.append(TaskItem(
                    text=text,
                    completed=completed,
                    line_number=i,
                ))
        
        return tasks
    
    def extract_code_blocks(self, content: str) -> List[Dict[str, Any]]:
        """
        Extract all code blocks from content.
        
        Args:
            content: Markdown content
            
        Returns:
            List of code block info dicts
        """
        blocks = []
        
        for match in self.CODE_BLOCK_PATTERN.finditer(content):
            lang = match.group(1) or "text"
            code = match.group(2)
            blocks.append({
                "language": lang,
                "code": code,
                "start": match.start(),
                "end": match.end(),
            })
        
        return blocks
    
    def render_to_html(
        self,
        content: str,
        strip_frontmatter: bool = True,
    ) -> str:
        """
        Render markdown content to HTML.
        
        Args:
            content: Markdown content
            strip_frontmatter: Whether to strip YAML frontmatter
            
        Returns:
            HTML string
        """
        if strip_frontmatter:
            _, content = self.extract_yaml_frontmatter(content)
        
        self.md.reset()
        return self.md.convert(content)
    
    def render_to_plaintext(self, content: str) -> str:
        """
        Extract plain text from markdown content.
        
        Args:
            content: Markdown content
            
        Returns:
            Plain text string
        """
        html = self.render_to_html(content)
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text(separator="\n")
    
    def get_toc(self, content: str, max_level: int = 3) -> List[Dict[str, Any]]:
        """
        Generate a table of contents.
        
        Args:
            content: Markdown content
            max_level: Maximum heading level to include
            
        Returns:
            List of TOC entries
        """
        headings = self.extract_headings(content)
        toc = []
        
        for h in headings:
            if h.level <= max_level:
                toc.append({
                    "level": h.level,
                    "text": h.text,
                    "anchor": h.anchor,
                    "line_number": h.line_number,
                })
        
        return toc
    
    def get_outline_tree(self, content: str) -> List[Dict[str, Any]]:
        """
        Generate a nested outline tree structure.
        
        Args:
            content: Markdown content
            
        Returns:
            Nested list structure of headings
        """
        headings = self.extract_headings(content)
        
        if not headings:
            return []
        
        root: List[Dict[str, Any]] = []
        stack: List[Tuple[int, List[Dict[str, Any]]]] = [(0, root)]
        
        for h in headings:
            node = {
                "level": h.level,
                "text": h.text,
                "anchor": h.anchor,
                "line_number": h.line_number,
                "children": [],
            }
            
            while stack and stack[-1][0] >= h.level:
                stack.pop()
            
            if stack:
                stack[-1][1].append(node)
            else:
                root.append(node)
            
            stack.append((h.level, node["children"]))
        
        return root
    
    def count_words(self, content: str) -> int:
        """
        Count words in markdown content.
        
        Args:
            content: Markdown content
            
        Returns:
            Word count
        """
        text = self.render_to_plaintext(content)
        text = re.sub(r"\s+", " ", text)
        
        if re.search(r"[\u4e00-\u9fff]", text):
            chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
            other_words = len(re.findall(r"[a-zA-Z]+", text))
            return chinese_chars + other_words
        else:
            return len(text.split())
    
    def count_chars(self, content: str) -> int:
        """Count characters in content."""
        return len(content)
    
    def count_lines(self, content: str) -> int:
        """Count lines in content."""
        return len(content.split("\n"))
    
    def extract_images(self, content: str) -> List[Dict[str, str]]:
        """
        Extract all images from content.
        
        Args:
            content: Markdown content
            
        Returns:
            List of image info dicts with 'alt' and 'src' keys
        """
        pattern = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
        images = []
        
        for match in pattern.finditer(content):
            images.append({
                "alt": match.group(1),
                "src": match.group(2),
            })
        
        return images
    
    def extract_links(self, content: str) -> List[Dict[str, str]]:
        """
        Extract all regular links from content.
        
        Args:
            content: Markdown content
            
        Returns:
            List of link info dicts with 'text' and 'url' keys
        """
        pattern = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)")
        links = []
        
        for match in pattern.finditer(content):
            links.append({
                "text": match.group(1),
                "url": match.group(2),
            })
        
        return links
