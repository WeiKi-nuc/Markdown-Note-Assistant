"""
Tests for the MarkdownParser class.
"""

import pytest

from markdown_note_assistant.core.parser import MarkdownParser


class TestMarkdownParser:
    """Tests for the MarkdownParser class."""
    
    @pytest.fixture
    def parser(self):
        """Create a parser instance."""
        return MarkdownParser()
    
    @pytest.fixture
    def sample_content(self):
        """Sample markdown content."""
        return """---
title: Test Document
date: 2024-01-15
tags: [test, example]
---

# Main Heading

This is a paragraph with **bold** and *italic* text.

## Section 1

- Item 1
- Item 2
- Item 3

### Subsection

1. First
2. Second
3. Third

## Section 2

> This is a blockquote.

```python
def hello():
    print("Hello, World!")
```

## Links

[Regular Link](https://example.com)

[[Wiki Link]]

[[Another Link|Display Text]]

[[Note#Section]]

## Tasks

- [x] Done
- [ ] Todo

## Table

| A | B | C |
|---|---|---|
| 1 | 2 | 3 |

---

![Image](image.png)
"""
    
    def test_parser_creation(self, parser):
        """Test creating a parser."""
        assert parser is not None
    
    def test_extract_frontmatter(self, parser, sample_content):
        """Test extracting YAML frontmatter."""
        metadata, content = parser.extract_yaml_frontmatter(sample_content)
        
        assert metadata["title"] == "Test Document"
        assert metadata["date"] == "2024-01-15"
        assert "test" in metadata["tags"]
    
    def test_extract_headings(self, parser, sample_content):
        """Test extracting headings."""
        headings = parser.extract_headings(sample_content)
        
        assert len(headings) >= 3
        
        h1 = [h for h in headings if h.level == 1]
        assert len(h1) == 1
        assert h1[0].text == "Main Heading"
    
    def test_extract_wiki_links(self, parser, sample_content):
        """Test extracting wiki links."""
        links = parser.extract_wiki_links(sample_content)
        
        assert len(links) >= 3
        
        targets = [l.target for l in links]
        assert "Wiki Link" in targets
        assert "Another Link" in targets
        assert "Note" in targets
    
    def test_extract_tasks(self, parser, sample_content):
        """Test extracting task list items."""
        tasks = parser.extract_tasks(sample_content)
        
        assert len(tasks) == 2
        
        done_tasks = [t for t in tasks if t.completed]
        pending_tasks = [t for t in tasks if not t.completed]
        
        assert len(done_tasks) == 1
        assert len(pending_tasks) == 1
    
    def test_extract_code_blocks(self, parser, sample_content):
        """Test extracting code blocks."""
        blocks = parser.extract_code_blocks(sample_content)
        
        assert len(blocks) >= 1
        assert blocks[0]["language"] == "python"
    
    def test_render_to_html(self, parser, sample_content):
        """Test rendering to HTML."""
        html = parser.render_to_html(sample_content)
        
        assert "<h1>" in html or "<h2>" in html
        assert "<p>" in html
    
    def test_render_to_plaintext(self, parser, sample_content):
        """Test rendering to plain text."""
        text = parser.render_to_plaintext(sample_content)
        
        assert "Main Heading" in text
        assert "---" not in text
    
    def test_get_toc(self, parser, sample_content):
        """Test getting table of contents."""
        toc = parser.get_toc(sample_content)
        
        assert len(toc) >= 3
        assert toc[0]["level"] == 1
    
    def test_get_outline_tree(self, parser, sample_content):
        """Test getting outline tree."""
        outline = parser.get_outline_tree(sample_content)
        
        assert len(outline) >= 1
        assert "children" in outline[0]
    
    def test_count_words(self, parser, sample_content):
        """Test counting words."""
        count = parser.count_words(sample_content)
        
        assert count > 0
    
    def test_count_chars(self, parser, sample_content):
        """Test counting characters."""
        count = parser.count_chars(sample_content)
        
        assert count > 0
    
    def test_count_lines(self, parser, sample_content):
        """Test counting lines."""
        count = parser.count_lines(sample_content)
        
        assert count > 0
    
    def test_extract_images(self, parser, sample_content):
        """Test extracting images."""
        images = parser.extract_images(sample_content)
        
        assert len(images) >= 1
        assert images[0]["src"] == "image.png"
    
    def test_extract_links(self, parser, sample_content):
        """Test extracting regular links."""
        links = parser.extract_links(sample_content)
        
        assert len(links) >= 1
        
        urls = [l["url"] for l in links]
        assert "https://example.com" in urls
    
    def test_parse_empty_content(self, parser):
        """Test parsing empty content."""
        metadata, content = parser.extract_yaml_frontmatter("")
        assert metadata == {}
        assert content == ""
        
        headings = parser.extract_headings("")
        assert headings == []
        
        links = parser.extract_wiki_links("")
        assert links == []
    
    def test_parse_no_frontmatter(self, parser):
        """Test parsing content without frontmatter."""
        content = "# Heading\n\nParagraph"
        
        metadata, body = parser.extract_yaml_frontmatter(content)
        assert metadata == {}
        assert body == content
