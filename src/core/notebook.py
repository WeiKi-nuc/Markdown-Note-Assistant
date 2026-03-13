#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notebook 类 - 文件夹级别的笔记集合管理
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Set
from collections import Counter

from .note import Note


class Notebook:
    """笔记本类，管理一个文件夹及其子文件夹中的所有笔记"""
    
    def __init__(self, root_path: str, name: Optional[str] = None):
        self.root_path = os.path.abspath(root_path)
        self.name = name or os.path.basename(self.root_path)
        self.sub_notebooks: List['Notebook'] = []
        self.notes: Dict[str, Note] = {}  # file_path -> Note
        self._file_watcher = None
        
        # 初始扫描
        self.scan()
    
    def scan(self) -> None:
        """递归扫描目录建立索引"""
        self.notes.clear()
        self.sub_notebooks.clear()
        
        if not os.path.exists(self.root_path):
            return
        
        for item in os.listdir(self.root_path):
            item_path = os.path.join(self.root_path, item)
            
            if os.path.isdir(item_path):
                # 跳过隐藏目录和特殊目录
                if item.startswith('.') or item in ['assets', 'attachments', '__pycache__']:
                    continue
                
                # 递归创建子笔记本
                sub_notebook = Notebook(item_path, item)
                self.sub_notebooks.append(sub_notebook)
                
            elif item.endswith('.md'):
                # 加载笔记
                note = Note(item_path)
                self.notes[item_path] = note
    
    def create_note(self, title: str, template: Optional[str] = None) -> Optional[Note]:
        """新建笔记文件"""
        # 生成文件名
        filename = f"{title}.md"
        file_path = os.path.join(self.root_path, filename)
        
        # 如果文件已存在，添加数字后缀
        counter = 1
        base_name = title
        while os.path.exists(file_path):
            filename = f"{base_name}_{counter}.md"
            file_path = os.path.join(self.root_path, filename)
            counter += 1
        
        # 创建笔记内容
        from datetime import datetime
        content = f"""---
title: {title}
created_at: {datetime.now().isoformat()}
tags: []
---

# {title}

"""
        
        if template:
            content = template.replace("{{title}}", title).replace("{{date}}", datetime.now().isoformat())
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 加载新创建的笔记
            note = Note(file_path)
            self.notes[file_path] = note
            return note
            
        except Exception as e:
            print(f"创建笔记失败: {e}")
            return None
    
    def delete_note(self, file_path: str) -> bool:
        """删除笔记"""
        if file_path in self.notes:
            try:
                os.remove(file_path)
                del self.notes[file_path]
                return True
            except Exception as e:
                print(f"删除笔记失败: {e}")
        return False
    
    def rename_note(self, file_path: str, new_title: str) -> Optional[Note]:
        """重命名笔记"""
        if file_path not in self.notes:
            return None
        
        note = self.notes[file_path]
        new_filename = f"{new_title}.md"
        new_path = os.path.join(self.dirname, new_filename)
        
        try:
            os.rename(file_path, new_path)
            
            # 更新索引
            del self.notes[file_path]
            note.file_path = new_path
            note.title = new_title
            note.update_metadata('title', new_title)
            self.notes[new_path] = note
            
            return note
            
        except Exception as e:
            print(f"重命名笔记失败: {e}")
            return None
    
    def search(self, keyword: str) -> List[Note]:
        """在笔记本范围内搜索"""
        results = []
        keyword_lower = keyword.lower()
        
        # 搜索当前笔记本
        for note in self.notes.values():
            if (keyword_lower in note.title.lower() or 
                keyword_lower in note.content.lower() or
                any(keyword_lower in tag.lower() for tag in note.tags)):
                results.append(note)
        
        # 递归搜索子笔记本
        for sub_nb in self.sub_notebooks:
            results.extend(sub_nb.search(keyword))
        
        return results
    
    def get_tag_statistics(self) -> Dict[str, int]:
        """获取标签使用统计"""
        all_tags = []
        
        # 收集当前笔记本的标签
        for note in self.notes.values():
            all_tags.extend(note.tags)
        
        # 递归收集子笔记本的标签
        for sub_nb in self.sub_notebooks:
            sub_stats = sub_nb.get_tag_statistics()
            for tag, count in sub_stats.items():
                all_tags.extend([tag] * count)
        
        return dict(Counter(all_tags))
    
    def get_all_notes(self) -> List[Note]:
        """获取所有笔记（包括子笔记本）"""
        all_notes = list(self.notes.values())
        
        for sub_nb in self.sub_notebooks:
            all_notes.extend(sub_nb.get_all_notes())
        
        return all_notes
    
    def get_note_by_path(self, file_path: str) -> Optional[Note]:
        """根据路径获取笔记"""
        # 在当前笔记本中查找
        if file_path in self.notes:
            return self.notes[file_path]
        
        # 在子笔记本中查找
        for sub_nb in self.sub_notebooks:
            note = sub_nb.get_note_by_path(file_path)
            if note:
                return note
        
        return None
    
    def get_note_by_title(self, title: str) -> Optional[Note]:
        """根据标题获取笔记"""
        for note in self.notes.values():
            if note.title == title:
                return note
        
        # 在子笔记本中查找
        for sub_nb in self.sub_notebooks:
            note = sub_nb.get_note_by_title(title)
            if note:
                return note
        
        return None
    
    def watch_changes(self, callback=None) -> None:
        """监听文件系统变化（简化实现）"""
        # TODO: 实现文件系统监听
        pass
    
    @property
    def dirname(self) -> str:
        """获取所在目录"""
        return self.root_path
    
    def __repr__(self) -> str:
        return f"Notebook({self.name!r}, {len(self.notes)} notes, {len(self.sub_notebooks)} sub-notebooks)"
