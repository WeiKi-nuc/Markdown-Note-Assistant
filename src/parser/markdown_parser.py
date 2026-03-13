#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MarkdownParser 类 - Markdown解析与元数据提取
"""

import re
import markdown
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor
from typing import Dict, List, Any, Optional


class WikiLinkExtension(Extension):
    """Wiki链接扩展 [[笔记名]]"""
    
    def extendMarkdown(self, md):
        """扩展 Markdown 解析器"""
        md.preprocessors.register(WikiLinkPreprocessor(md), 'wikilink', 200)


class WikiLinkPreprocessor(Preprocessor):
    """Wiki链接预处理器"""
    
    WIKI_LINK_RE = re.compile(r'\[\[([^\]]+)\]\]')
    
    def run(self, lines):
        """处理 Wiki 链接"""
        new_lines = []
        for line in lines:
            # 将 [[笔记名]] 转换为 [笔记名](笔记名.md)
            def replace_wikilink(match):
                link_text = match.group(1)
                # 支持 [[笔记名#标题]] 格式
                if '#' in link_text:
                    parts = link_text.split('#', 1)
                    note_name = parts[0]
                    heading = parts[1]
                    return f'[{link_text}]({note_name}.md#{heading})'
                return f'[{link_text}]({link_text}.md)'
            
            new_line = self.WIKI_LINK_RE.sub(replace_wikilink, line)
            new_lines.append(new_line)
        return new_lines


class MarkdownParser:
    """Markdown 解析引擎"""
    
    def __init__(self):
        """初始化解析器"""
        self.md = markdown.Markdown(extensions=[
            'tables',
            'fenced_code',
            'toc',
            'nl2br',
            'sane_lists',
            WikiLinkExtension()
        ])
    
    def parse(self, content: str) -> Any:
        """
        解析 Markdown 内容为 AST（简化实现）
        返回解析后的 HTML 和元数据
        """
        # 提取 Frontmatter
        metadata = self.extract_yaml_frontmatter(content)
        
        # 移除 Frontmatter 后的内容
        body_content = self._remove_frontmatter(content)
        
        # 转换为 HTML
        html = self.render_to_html(body_content)
        
        return {
            'metadata': metadata,
            'html': html,
            'headings': self.extract_headings(content)
        }
    
    def extract_yaml_frontmatter(self, text: str) -> Dict[str, Any]:
        """提取 YAML Frontmatter"""
        pattern = r'^---\s*\n(.*?)\n---\s*\n'
        match = re.match(pattern, text, re.DOTALL)
        
        if match:
            try:
                import yaml
                return yaml.safe_load(match.group(1)) or {}
            except Exception as e:
                print(f"解析 Frontmatter 失败: {e}")
        
        return {}
    
    def extract_headings(self, content: str) -> List[Dict[str, Any]]:
        """提取标题层级列表"""
        headings = []
        pattern = r'^(#{1,6})\s+(.+)$'
        
        # 移除 Frontmatter
        body_content = self._remove_frontmatter(content)
        
        for match in re.finditer(pattern, body_content, re.MULTILINE):
            level = len(match.group(1))
            title = match.group(2).strip()
            # 生成锚点 ID
            heading_id = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '-').lower()
            
            headings.append({
                'level': level,
                'title': title,
                'id': heading_id
            })
        
        return headings
    
    def extract_wiki_links(self, text: str) -> List[str]:
        """提取 [[...]] 格式的 Wiki 链接"""
        pattern = r'\[\[([^\]]+)\]\]'
        return re.findall(pattern, text)
    
    def render_to_html(self, content: str, options: Optional[Dict] = None) -> str:
        """渲染为 HTML"""
        # 移除 Frontmatter
        body_content = self._remove_frontmatter(content)
        
        # 重置解析器状态
        self.md.reset()
        
        # 转换 Markdown 到 HTML
        html = self.md.convert(body_content)
        
        return html
    
    def render_to_plaintext(self, content: str) -> str:
        """提取纯文本用于摘要"""
        # 移除 Frontmatter
        text = self._remove_frontmatter(content)
        
        # 移除代码块
        text = re.sub(r'```[\s\S]*?```', '', text)
        text = re.sub(r'`[^`]*`', '', text)
        
        # 移除 HTML 标签
        text = re.sub(r'<[^>]+>', '', text)
        
        # 移除 Markdown 标记
        text = re.sub(r'[#*\[\]()!>|]', '', text)
        
        # 移除多余空白
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _remove_frontmatter(self, content: str) -> str:
        """移除 YAML Frontmatter"""
        pattern = r'^---\s*\n.*?\n---\s*\n'
        return re.sub(pattern, '', content, flags=re.DOTALL, count=1)
    
    def extract_tasks(self, content: str) -> List[Dict[str, Any]]:
        """提取任务列表"""
        tasks = []
        pattern = r'^\s*[-*]\s+\[([ x])\]\s+(.+)$'
        
        for match in re.finditer(pattern, content, re.MULTILINE):
            is_completed = match.group(1) == 'x'
            task_text = match.group(2).strip()
            
            tasks.append({
                'completed': is_completed,
                'text': task_text
            })
        
        return tasks
    
    def extract_code_blocks(self, content: str) -> List[Dict[str, Any]]:
        """提取代码块"""
        code_blocks = []
        pattern = r'```(\w+)?\n([\s\S]*?)```'
        
        for match in re.finditer(pattern, content):
            language = match.group(1) or 'text'
            code = match.group(2)
            
            code_blocks.append({
                'language': language,
                'code': code
            })
        
        return code_blocks
    
    def extract_tables(self, content: str) -> List[List[List[str]]]:
        """提取表格数据"""
        tables = []
        lines = content.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # 检测表格开始（以 | 开头）
            if line.startswith('|') and '|' in line[1:]:
                table_lines = []
                
                # 收集表格所有行
                while i < len(lines) and lines[i].strip().startswith('|'):
                    table_lines.append(lines[i].strip())
                    i += 1
                
                # 解析表格（跳过分隔行）
                if len(table_lines) >= 2:
                    table_data = []
                    for j, table_line in enumerate(table_lines):
                        if j == 1:  # 跳过分隔行
                            continue
                        # 分割单元格
                        cells = [cell.strip() for cell in table_line.split('|')[1:-1]]
                        table_data.append(cells)
                    
                    tables.append(table_data)
            else:
                i += 1
        
        return tables
    
    def get_word_count(self, content: str) -> int:
        """获取字数统计"""
        plain_text = self.render_to_plaintext(content)
        # 中文字符 + 英文单词
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', plain_text))
        english_words = len(re.findall(r'[a-zA-Z]+', plain_text))
        return chinese_chars + english_words
    
    def get_reading_time(self, content: str, words_per_minute: int = 300) -> int:
        """估算阅读时间（分钟）"""
        word_count = self.get_word_count(content)
        return max(1, word_count // words_per_minute)


# 全局解析器实例
_parser = None


def get_parser() -> MarkdownParser:
    """获取全局解析器实例"""
    global _parser
    if _parser is None:
        _parser = MarkdownParser()
    return _parser
