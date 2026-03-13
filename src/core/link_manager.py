#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LinkManager 类 - 双向链接与关系图谱维护
"""

import re
from typing import Dict, List, Set, Optional
from collections import defaultdict

from .note import Note
from .note_repository import NoteRepository


class LinkManager:
    """链接管理器，维护笔记间的双向链接关系"""
    
    def __init__(self, repository: NoteRepository):
        self.repository = repository
        self.link_graph: Dict[str, Set[str]] = defaultdict(set)  # note_path -> {linked_note_paths}
        self.backlinks: Dict[str, Set[str]] = defaultdict(set)  # note_path -> {backlink_note_paths}
    
    def parse_links(self, note: Note) -> List[str]:
        """解析笔记内所有 Wiki 链接"""
        pattern = r'\[\[([^\]]+)\]\]'
        links = re.findall(pattern, note.content)
        
        # 处理带锚点的链接 [[笔记名#标题]]
        result = []
        for link in links:
            if '#' in link:
                note_name = link.split('#')[0]
                result.append(note_name)
            else:
                result.append(link)
        
        return result
    
    def update_graph(self, note: Note) -> None:
        """更新全局链接图"""
        note_path = note.file_path
        
        # 清除旧的链接
        if note_path in self.link_graph:
            old_links = self.link_graph[note_path].copy()
            for linked_path in old_links:
                if note_path in self.backlinks[linked_path]:
                    self.backlinks[linked_path].remove(note_path)
        
        self.link_graph[note_path].clear()
        
        # 解析新的链接
        linked_titles = self.parse_links(note)
        
        for title in linked_titles:
            # 查找目标笔记
            target_note = self.repository.get_note_by_title(title)
            if target_note:
                target_path = target_note.file_path
                self.link_graph[note_path].add(target_path)
                self.backlinks[target_path].add(note_path)
    
    def build_full_graph(self) -> None:
        """构建完整的链接图"""
        self.link_graph.clear()
        self.backlinks.clear()
        
        for note in self.repository.get_all_notes():
            self.update_graph(note)
    
    def get_backlinks(self, note: Note) -> List[Note]:
        """获取反向链接（引用此笔记的笔记）"""
        note_path = note.file_path
        backlink_paths = self.backlinks.get(note_path, set())
        
        result = []
        for path in backlink_paths:
            linked_note = self.repository.get_note_by_path(path)
            if linked_note:
                result.append(linked_note)
        
        return result
    
    def get_outgoing_links(self, note: Note) -> List[Note]:
        """获取出站链接（此笔记引用的笔记）"""
        note_path = note.file_path
        linked_paths = self.link_graph.get(note_path, set())
        
        result = []
        for path in linked_paths:
            linked_note = self.repository.get_note_by_path(path)
            if linked_note:
                result.append(linked_note)
        
        return result
    
    def get_related_notes(self, note: Note, depth: int = 1) -> Dict[int, List[Note]]:
        """获取关联笔记（一度/二度关系）"""
        related = {i: [] for i in range(1, depth + 1)}
        visited = {note.file_path}
        
        current_level = [note.file_path]
        
        for d in range(1, depth + 1):
            next_level = []
            
            for path in current_level:
                # 获取链接和反向链接
                linked_paths = self.link_graph.get(path, set())
                backlink_paths = self.backlinks.get(path, set())
                all_related = linked_paths | backlink_paths
                
                for related_path in all_related:
                    if related_path not in visited:
                        visited.add(related_path)
                        related_note = self.repository.get_note_by_path(related_path)
                        if related_note:
                            related[d].append(related_note)
                            next_level.append(related_path)
            
            current_level = next_level
            if not current_level:
                break
        
        return related
    
    def get_unlinked_mentions(self, note: Note) -> List[str]:
        """查找文本提及但未链接的笔记名"""
        mentions = []
        all_notes = self.repository.get_all_notes()
        all_titles = {n.title for n in all_notes if n.file_path != note.file_path}
        
        # 获取已链接的笔记
        linked_titles = set(self.parse_links(note))
        
        for title in all_titles:
            if title in linked_titles:
                continue
            
            # 检查文本中是否提及
            pattern = r'\b' + re.escape(title) + r'\b'
            if re.search(pattern, note.content):
                mentions.append(title)
        
        return mentions
    
    def check_broken_links(self) -> List[Dict]:
        """检测失效链接"""
        broken = []
        
        for note in self.repository.get_all_notes():
            linked_titles = self.parse_links(note)
            
            for title in linked_titles:
                # 检查目标笔记是否存在
                target_note = self.repository.get_note_by_title(title)
                if not target_note:
                    broken.append({
                        'source_note': note,
                        'broken_link': title,
                        'line_number': self._find_link_line(note.content, title)
                    })
        
        return broken
    
    def _find_link_line(self, content: str, link_text: str) -> int:
        """查找链接所在行号"""
        lines = content.split('\n')
        pattern = r'\[\[' + re.escape(link_text) + r'(\|[^\]]+)?\]\]'
        
        for i, line in enumerate(lines, 1):
            if re.search(pattern, line):
                return i
        
        return 0
    
    def get_graph_data(self) -> Dict:
        """获取图谱数据（用于可视化）"""
        nodes = []
        edges = []
        
        all_notes = self.repository.get_all_notes()
        note_paths = {note.file_path for note in all_notes}
        
        # 创建节点
        for note in all_notes:
            nodes.append({
                'id': note.file_path,
                'label': note.title,
                'tags': note.tags
            })
        
        # 创建边
        for source_path, target_paths in self.link_graph.items():
            for target_path in target_paths:
                if target_path in note_paths:
                    edges.append({
                        'source': source_path,
                        'target': target_path
                    })
        
        return {
            'nodes': nodes,
            'edges': edges
        }
    
    def suggest_links(self, note: Note) -> List[str]:
        """为笔记建议可能的链接"""
        suggestions = []
        all_notes = self.repository.get_all_notes()
        
        # 基于标签相似度
        note_tags = set(note.tags)
        for other in all_notes:
            if other.file_path == note.file_path:
                continue
            
            other_tags = set(other.tags)
            common_tags = note_tags & other_tags
            
            if len(common_tags) >= 2:  # 至少2个共同标签
                suggestions.append(other.title)
                continue
            
            # 基于标题相似度（简单实现）
            title_words = set(note.title.lower().split())
            other_words = set(other.title.lower().split())
            common_words = title_words & other_words
            
            if len(common_words) >= 1:
                suggestions.append(other.title)
        
        # 去重并返回
        return list(set(suggestions))
