import re
from typing import Dict, List, Any, Optional
import markdown
from markdown.extensions import codehilite, fenced_code, tables, toc
from pygments import highlight
from pygments.lexers import get_lexer_by_name, TextLexer
from pygments.formatters import HtmlFormatter


class MarkdownParser:
    def __init__(self):
        self._md = markdown.Markdown(extensions=[
            'extra',
            'codehilite',
            'fenced_code',
            'tables',
            'toc',
            'nl2br',
            'sane_lists'
        ])
    
    def parse(self, content: str) -> Dict[str, Any]:
        self._md.reset()
        html = self._md.convert(content)
        return {
            'html': html,
            'toc': getattr(self._md, 'toc', ''),
            'meta': getattr(self._md, 'Meta', {})
        }
    
    def extract_yaml_frontmatter(self, text: str) -> Dict[str, Any]:
        pattern = r'^---\s*\n(.*?)\n---\s*\n'
        match = re.match(pattern, text, re.DOTALL)
        if match:
            try:
                import yaml
                frontmatter_text = match.group(1)
                return yaml.safe_load(frontmatter_text) or {}
            except:
                pass
        return {}
    
    def extract_headings(self, content: str) -> List[Dict]:
        headings = []
        lines = content.split('\n')
        for i, line in enumerate(lines):
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if heading_match:
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()
                anchor = self._generate_anchor(title)
                headings.append({
                    'level': level,
                    'title': title,
                    'anchor': anchor,
                    'line': i
                })
        return headings
    
    def _generate_anchor(self, title: str) -> str:
        anchor = re.sub(r'[^\w\s-]', '', title.lower())
        anchor = re.sub(r'[\s-]+', '-', anchor)
        return anchor
    
    def extract_wiki_links(self, text: str) -> List[str]:
        pattern = r'\[\[([^\]]+)\]\]'
        matches = re.findall(pattern, text)
        links = []
        for m in matches:
            parts = m.split('#')
            note_name = parts[0].strip()
            anchor = parts[1].strip() if len(parts) > 1 else None
            links.append({
                'full': m,
                'note': note_name,
                'anchor': anchor
            })
        return links
    
    def render_to_html(self, content: str, options: Optional[Dict] = None) -> str:
        options = options or {}
        self._md.reset()
        
        processed = self._process_wiki_links(content)
        html = self._md.convert(processed)
        return self._wrap_html(html, options)
    
    def _process_wiki_links(self, text: str) -> str:
        def replace_link(match):
            full_link = match.group(1)
            parts = full_link.split('#')
            note_name = parts[0].strip()
            anchor = parts[1].strip() if len(parts) > 1 else None
            display = note_name
            if anchor:
                display = f"{note_name} &gt; {anchor}"
            return f'<a href="#" class="wiki-link" data-note="{note_name}" data-anchor="{anchor or ""}">[[{display}]]</a>'
        
        return re.sub(r'\[\[([^\]]+)\]\]', replace_link, text)
    
    def _wrap_html(self, html: str, options: Dict) -> str:
        css = self._get_default_css()
        pygments_css = HtmlFormatter().get_style_defs('.codehilite')
        return f"""
        <html>
        <head>
            <meta charset="utf-8">
            <style>{css}\n{pygments_css}</style>
        </head>
        <body>
            <div class="markdown-body">{html}</div>
        </body>
        </html>
        """
    
    def _get_default_css(self) -> str:
        return """
        .markdown-body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .markdown-body h1, .markdown-body h2, .markdown-body h3, 
        .markdown-body h4, .markdown-body h5, .markdown-body h6 {
            margin-top: 24px;
            margin-bottom: 16px;
            font-weight: 600;
            line-height: 1.25;
        }
        .markdown-body h1 { font-size: 2em; border-bottom: 1px solid #eee; padding-bottom: 0.3em; }
        .markdown-body h2 { font-size: 1.5em; border-bottom: 1px solid #eee; padding-bottom: 0.3em; }
        .markdown-body h3 { font-size: 1.25em; }
        .markdown-body h4 { font-size: 1em; }
        .markdown-body code {
            padding: 0.2em 0.4em;
            margin: 0;
            background-color: rgba(27,31,35,0.05);
            border-radius: 3px;
            font-family: SFMono-Regular, Consolas, Liberation Mono, Menlo, monospace;
        }
        .markdown-body pre {
            padding: 16px;
            overflow: auto;
            line-height: 1.45;
            background-color: #f6f8fa;
            border-radius: 3px;
        }
        .markdown-body pre code {
            padding: 0;
            background: transparent;
        }
        .markdown-body blockquote {
            padding: 0 1em;
            color: #6a737d;
            border-left: 0.25em solid #dfe2e5;
            margin: 0;
        }
        .markdown-body table {
            border-collapse: collapse;
            width: 100%;
        }
        .markdown-body table th, .markdown-body table td {
            border: 1px solid #dfe2e5;
            padding: 6px 13px;
        }
        .markdown-body table tr:nth-child(2n) {
            background-color: #f6f8fa;
        }
        .markdown-body ul, .markdown-body ol {
            padding-left: 2em;
        }
        .markdown-body .task-list-item {
            list-style-type: none;
        }
        .markdown-body .task-list-item input {
            margin: 0 0.2em 0.25em -1.6em;
            vertical-align: middle;
        }
        .wiki-link {
            color: #0366d6;
            text-decoration: none;
        }
        .wiki-link:hover {
            text-decoration: underline;
        }
        .highlight-line {
            background-color: rgba(255, 255, 0, 0.1);
        }
        """
    
    def render_to_plaintext(self, content: str) -> str:
        html = self._md.convert(content)
        import html
        text = re.sub(r'<[^>]+>', ' ', html)
        text = html.unescape(text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()


class PreviewRenderer:
    def __init__(self):
        self.current_theme = "light"
        self.math_enabled = True
        self.mermaid_enabled = True
        self.parser = MarkdownParser()
        self._custom_css = ""
    
    def render(self, markdown_text: str, options: Optional[Dict] = None) -> str:
        options = options or {}
        base_html = self.parser.render_to_html(markdown_text, options)
        
        if self.math_enabled:
            base_html = self._add_mathjax(base_html)
        if self.mermaid_enabled:
            base_html = self._add_mermaid(base_html)
        
        return base_html
    
    def _add_mathjax(self, html: str) -> str:
        mathjax_script = """
        <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
        <script>
        MathJax = {
            tex: {
                inlineMath: [['$', '$'], ['\\(', '\\)']],
                displayMath: [['$$', '$$'], ['\\[', '\\]']]
            }
        };
        </script>
        """
        return html.replace('</head>', mathjax_script + '</head>')
    
    def _add_mermaid(self, html: str) -> str:
        mermaid_script = """
        <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
        <script>
        mermaid.initialize({ startOnLoad: true });
        </script>
        """
        return html.replace('</head>', mermaid_script + '</head>')
    
    def apply_theme(self, css_path: str):
        try:
            with open(css_path, 'r', encoding='utf-8') as f:
                self._custom_css = f.read()
        except:
            pass
    
    def set_theme(self, theme_name: str):
        self.current_theme = theme_name
    
    def highlight_line(self, html: str, line_id: str) -> str:
        marker = f'<span id="line-{line_id}"></span>'
        return html.replace(marker, f'<span id="line-{line_id}" class="highlight-line"></span>')
