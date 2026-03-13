#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NoteRepository 类 - 全局笔记数据管理与持久化协调
"""

import os
import json
from typing import Dict, List, Optional, Set
from datetime import datetime

from .note import Note
from .notebook import Notebook


class NoteRepository:
    """笔记仓库类，管理所有笔记本和全局搜索索引"""
    
    _instance = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.notebooks: Dict[str, Notebook] = {}  # root_path -> Notebook
        self.index: Dict[str, str] = {}  # file_path -> content_hash (简化索引)
        self.recent_files: List[str] = []
        self.favorites: List[str] = []
        self._initialized = True
        
        # 加载配置
        self._load_config()
    
    def add_notebook(self, path: str) -> Optional[Notebook]:
        """添加笔记本到库"""
        abs_path = os.path.abspath(path)
        
        if abs_path in self.notebooks:
            return self.notebooks[abs_path]
        
        if not os.path.exists(abs_path):
            try:
                os.makedirs(abs_path, exist_ok=True)
            except Exception as e:
                print(f"创建笔记本目录失败: {e}")
                return None
        
        notebook = Notebook(abs_path)
        self.notebooks[abs_path] = notebook
        
        # 更新索引
        self._update_index_for_notebook(notebook)
        
        # 保存配置
        self._save_config()
        
        return notebook
    
    def remove_notebook(self, path: str) -> bool:
        """从库中移除笔记本"""
        abs_path = os.path.abspath(path)
        
        if abs_path in self.notebooks:
            del self.notebooks[abs_path]
            self._save_config()
            return True
        return False
    
    def get_note_by_path(self, file_path: str) -> Optional[Note]:
        """根据路径获取笔记"""
        abs_path = os.path.abspath(file_path)
        
        for notebook in self.notebooks.values():
            note = notebook.get_note_by_path(abs_path)
            if note:
                return note
        return None
    
    def get_note_by_title(self, title: str) -> Optional[Note]:
        """根据标题获取笔记"""
        for notebook in self.notebooks.values():
            note = notebook.get_note_by_title(title)
            if note:
                return note
        return None
    
    def global_search(self, query: str) -> List[Note]:
        """跨库全文搜索"""
        results = []
        query_lower = query.lower()
        
        for notebook in self.notebooks.values():
            results.extend(notebook.search(query))
        
        # 按相关性排序（标题匹配优先）
        def sort_key(note):
            title_match = query_lower in note.title.lower()
            return (not title_match, note.title)
        
        return sorted(results, key=sort_key)
    
    def find_backlinks(self, target_note: Note) -> List[Note]:
        """查找引用目标笔记的所有笔记"""
        backlinks = []
        target_title = target_note.title
        
        for notebook in self.notebooks.values():
            for note in notebook.get_all_notes():
                if note.file_path == target_note.file_path:
                    continue
                
                # 检查是否包含对目标笔记的链接
                if target_title in note.linked_notes:
                    backlinks.append(note)
                # 或者文本中提及目标笔记标题
                elif target_title in note.content:
                    backlinks.append(note)
        
        return backlinks
    
    def build_search_index(self) -> None:
        """重建搜索索引"""
        self.index.clear()
        
        for notebook in self.notebooks.values():
            self._update_index_for_notebook(notebook)
    
    def _update_index_for_notebook(self, notebook: Notebook) -> None:
        """更新笔记本的搜索索引"""
        for note in notebook.get_all_notes():
            # 使用文件内容的哈希作为简单索引
            import hashlib
            content_hash = hashlib.md5(note.content.encode()).hexdigest()
            self.index[note.file_path] = content_hash
    
    def add_to_recent(self, file_path: str) -> None:
        """添加到最近文件"""
        abs_path = os.path.abspath(file_path)
        
        # 移除已存在的相同路径
        if abs_path in self.recent_files:
            self.recent_files.remove(abs_path)
        
        # 添加到开头
        self.recent_files.insert(0, abs_path)
        
        # 只保留最近20个
        self.recent_files = self.recent_files[:20]
        
        self._save_config()
    
    def get_recent_notes(self) -> List[Note]:
        """获取最近打开的笔记"""
        notes = []
        for file_path in self.recent_files:
            note = self.get_note_by_path(file_path)
            if note and os.path.exists(file_path):
                notes.append(note)
        return notes
    
    def add_to_favorites(self, file_path: str) -> bool:
        """添加到收藏"""
        abs_path = os.path.abspath(file_path)
        
        if abs_path not in self.favorites:
            self.favorites.append(abs_path)
            self._save_config()
            return True
        return False
    
    def remove_from_favorites(self, file_path: str) -> bool:
        """从收藏中移除"""
        abs_path = os.path.abspath(file_path)
        
        if abs_path in self.favorites:
            self.favorites.remove(abs_path)
            self._save_config()
            return True
        return False
    
    def get_favorite_notes(self) -> List[Note]:
        """获取收藏的笔记"""
        notes = []
        for file_path in self.favorites:
            note = self.get_note_by_path(file_path)
            if note and os.path.exists(file_path):
                notes.append(note)
        return notes
    
    def get_all_tags(self) -> Dict[str, int]:
        """获取所有标签及其使用次数"""
        all_tags = {}
        
        for notebook in self.notebooks.values():
            tags = notebook.get_tag_statistics()
            for tag, count in tags.items():
                all_tags[tag] = all_tags.get(tag, 0) + count
        
        return all_tags
    
    def get_all_notes(self) -> List[Note]:
        """获取所有笔记"""
        all_notes = []
        for notebook in self.notebooks.values():
            all_notes.extend(notebook.get_all_notes())
        return all_notes
    
    def _get_config_path(self) -> str:
        """获取配置文件路径"""
        # 使用当前工作目录下的 .markdown_note_assistant 目录
        config_dir = os.path.join(os.getcwd(), '.markdown_note_assistant')
        try:
            os.makedirs(config_dir, exist_ok=True)
        except Exception:
            # 如果创建失败，使用临时目录
            import tempfile
            config_dir = os.path.join(tempfile.gettempdir(), '.markdown_note_assistant')
            os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, 'repository.json')
    
    def _load_config(self) -> None:
        """加载配置"""
        config_path = self._get_config_path()
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 加载笔记本路径
                for path in config.get('notebooks', []):
                    if os.path.exists(path):
                        self.add_notebook(path)
                
                # 加载最近文件
                self.recent_files = config.get('recent_files', [])
                
                # 加载收藏
                self.favorites = config.get('favorites', [])
                
            except Exception as e:
                print(f"加载配置失败: {e}")
    
    def _save_config(self) -> None:
        """保存配置"""
        config_path = self._get_config_path()
        
        config = {
            'notebooks': list(self.notebooks.keys()),
            'recent_files': self.recent_files,
            'favorites': self.favorites
        }
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def __repr__(self) -> str:
        return f"NoteRepository({len(self.notebooks)} notebooks, {len(self.get_all_notes())} notes)"
