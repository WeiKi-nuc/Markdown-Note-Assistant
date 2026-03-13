#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Note 类 - 单篇笔记的完整抽象
"""

import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
import yaml


class Note:
    """笔记实体类，封装单篇笔记的所有属性和操作"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.title = ""
        self.content = ""
        self.metadata: Dict[str, Any] = {}
        self.tags: List[str] = []
        self.created_at: Optional[datetime] = None
        self.modified_at: Optional[datetime] = None
        self.linked_notes: List[str] = []
        self.headings: List[Dict[str, Any]] = []
        
        # 如果文件存在，立即加载
        if os.path.exists(file_path):
            self.reload()
    
    @property
    def filename(self) -> str:
        """获取文件名（不含路径）"""
        return os.path.basename(self.file_path)
    
    @property
    def dirname(self) -> str:
        """获取所在目录"""
        return os.path.dirname(self.file_path)
    
    def reload(self) -> None:
        """从文件重新加载内容"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.content = f.read()
            
            # 更新修改时间
            stat = os.stat(self.file_path)
            self.modified_at = datetime.fromtimestamp(stat.st_mtime)
            
            # 解析 Frontmatter
            self.parse_frontmatter()
            
            # 提取标题
            self._extract_title()
            
            # 提取标题结构
            self._extract_headings()
            
            # 提取双向链接
            self._extract_wiki_links()
            
        except Exception as e:
            print(f"加载笔记失败 {self.file_path}: {e}")
    
    def save(self) -> bool:
        """保存笔记到文件"""
        try:
            # 确保目录存在
            os.makedirs(self.dirname, exist_ok=True)
            
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(self.content)
            
            # 更新修改时间
            stat = os.stat(self.file_path)
            self.modified_at = datetime.fromtimestamp(stat.st_mtime)
            
            return True
        except Exception as e:
            print(f"保存笔记失败 {self.file_path}: {e}")
            return False
    
    def parse_frontmatter(self) -> None:
        """解析 YAML Frontmatter"""
        pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
        match = re.match(pattern, self.content, re.DOTALL)
        
        if match:
            try:
                self.metadata = yaml.safe_load(match.group(1)) or {}
                # 从 metadata 中提取标签
                self.tags = self.metadata.get('tags', [])
                if isinstance(self.tags, str):
                    self.tags = [tag.strip() for tag in self.tags.split(',')]
                
                # 提取创建时间
                created = self.metadata.get('created_at') or self.metadata.get('date')
                if created:
                    if isinstance(created, datetime):
                        self.created_at = created
                    else:
                        try:
                            self.created_at = datetime.fromisoformat(str(created).replace('Z', '+00:00'))
                        except:
                            pass
                            
            except yaml.YAMLError as e:
                print(f"解析 Frontmatter 失败: {e}")
                self.metadata = {}
    
    def update_metadata(self, key: str, value: Any) -> None:
        """更新元数据"""
        self.metadata[key] = value
        
        # 同步更新标签
        if key == 'tags':
            self.tags = value if isinstance(value, list) else [value]
        
        # 重建 Frontmatter
        self._rebuild_frontmatter()
    
    def _rebuild_frontmatter(self) -> None:
        """重建 YAML Frontmatter"""
        pattern = r'^---\s*\n(.*?)\n---\s*\n'
        
        # 构建新的 Frontmatter
        yaml_content = yaml.dump(self.metadata, allow_unicode=True, sort_keys=False)
        new_frontmatter = f"---\n{yaml_content}---\n\n"
        
        if re.match(pattern, self.content, re.DOTALL):
            # 替换现有 Frontmatter
            self.content = re.sub(pattern, new_frontmatter, self.content, flags=re.DOTALL)
        else:
            # 添加新的 Frontmatter
            self.content = new_frontmatter + self.content
    
    def _extract_title(self) -> None:
        """从内容或文件名提取标题"""
        # 优先从 Frontmatter 获取
        if 'title' in self.metadata:
            self.title = self.metadata['title']
            return
        
        # 从第一个一级标题获取
        match = re.search(r'^#\s+(.+)$', self.content, re.MULTILINE)
        if match:
            self.title = match.group(1).strip()
            return
        
        # 使用文件名（不含扩展名）
        self.title = os.path.splitext(self.filename)[0]
    
    def _extract_headings(self) -> None:
        """提取标题结构树"""
        self.headings = []
        pattern = r'^(#{1,6})\s+(.+)$'
        
        for match in re.finditer(pattern, self.content, re.MULTILINE):
            level = len(match.group(1))
            title = match.group(2).strip()
            # 生成锚点 ID
            heading_id = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '-').lower()
            
            self.headings.append({
                'level': level,
                'title': title,
                'id': heading_id
            })
    
    def _extract_wiki_links(self) -> None:
        """提取 [[...]] 格式的双向链接"""
        pattern = r'\[\[([^\]]+)\]\]'
        self.linked_notes = re.findall(pattern, self.content)
    
    def get_plain_text(self) -> str:
        """获取纯文本内容（用于搜索摘要）"""
        # 移除 Frontmatter
        content = re.sub(r'^---\s*\n.*?\n---\s*\n', '', self.content, flags=re.DOTALL)
        # 移除 Markdown 标记
        content = re.sub(r'[#*`\[\]()]', '', content)
        return content.strip()
    
    def get_summary(self, max_length: int = 200) -> str:
        """获取内容摘要"""
        plain_text = self.get_plain_text()
        if len(plain_text) <= max_length:
            return plain_text
        return plain_text[:max_length] + "..."
    
    def add_tag(self, tag: str) -> None:
        """添加标签"""
        if tag not in self.tags:
            self.tags.append(tag)
            self.update_metadata('tags', self.tags)
    
    def remove_tag(self, tag: str) -> None:
        """移除标签"""
        if tag in self.tags:
            self.tags.remove(tag)
            self.update_metadata('tags', self.tags)
    
    def __repr__(self) -> str:
        return f"Note({self.title!r}, {self.file_path!r})"
