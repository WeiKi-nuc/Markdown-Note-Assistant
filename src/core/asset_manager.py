#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AssetManager 类 - 本地图片与附件管理
"""

import os
import re
import shutil
from datetime import datetime
from typing import Optional, List, Dict
from pathlib import Path


class AssetManager:
    """资源管理器，管理笔记中的图片和附件"""
    
    def __init__(self, base_path: str, assets_folder_name: str = 'assets'):
        self.base_path = base_path
        self.assets_folder_name = assets_folder_name
        self.assets_path = os.path.join(base_path, assets_folder_name)
    
    def _ensure_assets_dir(self) -> str:
        """确保资源目录存在"""
        if not os.path.exists(self.assets_path):
            os.makedirs(self.assets_path, exist_ok=True)
        return self.assets_path
    
    def save_pasted_image(self, image_data: bytes, filename: Optional[str] = None) -> Optional[str]:
        """保存剪贴板图片到 assets 目录"""
        try:
            from PIL import Image
            import io
            
            # 确保资源目录存在
            self._ensure_assets_dir()
            
            # 生成文件名
            if not filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"image_{timestamp}.png"
            
            # 确保扩展名正确
            if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')):
                filename += '.png'
            
            file_path = os.path.join(self.assets_path, filename)
            
            # 保存图片
            image = Image.open(io.BytesIO(image_data))
            image.save(file_path)
            
            # 返回相对路径
            return f"./{self.assets_folder_name}/{filename}"
            
        except Exception as e:
            print(f"保存图片失败: {e}")
            return None
    
    def save_file(self, source_path: str, filename: Optional[str] = None) -> Optional[str]:
        """保存文件到 assets 目录"""
        try:
            # 确保资源目录存在
            self._ensure_assets_dir()
            
            # 生成文件名
            if not filename:
                filename = os.path.basename(source_path)
            
            # 检查文件是否已存在
            target_path = os.path.join(self.assets_path, filename)
            counter = 1
            name, ext = os.path.splitext(filename)
            while os.path.exists(target_path):
                filename = f"{name}_{counter}{ext}"
                target_path = os.path.join(self.assets_path, filename)
                counter += 1
            
            # 复制文件
            shutil.copy2(source_path, target_path)
            
            # 返回相对路径
            return f"./{self.assets_folder_name}/{filename}"
            
        except Exception as e:
            print(f"保存文件失败: {e}")
            return None
    
    def get_asset_path(self, relative_path: str) -> Optional[str]:
        """解析相对路径为绝对路径"""
        # 处理 ./assets/image.png 或 assets/image.png 格式
        clean_path = relative_path.lstrip('./')
        
        if clean_path.startswith(self.assets_folder_name):
            full_path = os.path.join(self.base_path, clean_path)
            if os.path.exists(full_path):
                return full_path
        
        return None
    
    def get_relative_path(self, absolute_path: str) -> Optional[str]:
        """将绝对路径转换为相对路径"""
        try:
            rel_path = os.path.relpath(absolute_path, self.base_path)
            return f"./{rel_path}"
        except Exception:
            return None
    
    def cleanup_unused_assets(self, note_content: str) -> List[str]:
        """清理未被引用的图片"""
        removed = []
        
        if not os.path.exists(self.assets_path):
            return removed
        
        # 获取所有资源文件
        asset_files = []
        for filename in os.listdir(self.assets_path):
            file_path = os.path.join(self.assets_path, filename)
            if os.path.isfile(file_path):
                asset_files.append(filename)
        
        # 检查哪些文件被引用
        used_files = set()
        for filename in asset_files:
            # 检查 Markdown 图片引用 ![...](filename) 或 <img src="filename">
            patterns = [
                rf'!\[.*?\]\(.*?{re.escape(filename)}.*?\)',
                rf'<img[^>]+src=["\'].*?{re.escape(filename)}.*?["\']',
                rf'\[.*?\]\(.*?{re.escape(filename)}.*?\)'
            ]
            
            for pattern in patterns:
                if re.search(pattern, note_content):
                    used_files.add(filename)
                    break
        
        # 删除未使用的文件
        for filename in asset_files:
            if filename not in used_files:
                file_path = os.path.join(self.assets_path, filename)
                try:
                    os.remove(file_path)
                    removed.append(filename)
                except Exception as e:
                    print(f"删除未使用资源失败 {filename}: {e}")
        
        return removed
    
    def rename_asset(self, old_path: str, new_name: str, note_content: str) -> tuple:
        """重命名资源并更新所有引用"""
        try:
            # 获取旧文件名
            old_filename = os.path.basename(old_path)
            
            # 构建新路径
            new_path = os.path.join(self.assets_path, new_name)
            
            # 如果新文件名已存在，添加数字后缀
            counter = 1
            name, ext = os.path.splitext(new_name)
            while os.path.exists(new_path):
                new_name = f"{name}_{counter}{ext}"
                new_path = os.path.join(self.assets_path, new_name)
                counter += 1
            
            # 重命名文件
            os.rename(old_path, new_path)
            
            # 更新内容中的引用
            new_content = note_content
            patterns = [
                (rf'(\!\[.*?\]\(.*?){re.escape(old_filename)}(.*?\))', r'\1' + new_name + r'\2'),
                (rf'(<img[^>]+src=["\'].*?){re.escape(old_filename)}(["\'])', r'\1' + new_name + r'\2'),
                (rf'(\[.*?\]\(.*?){re.escape(old_filename)}(.*?\))', r'\1' + new_name + r'\2')
            ]
            
            for pattern, replacement in patterns:
                new_content = re.sub(pattern, replacement, new_content)
            
            # 返回新的相对路径和更新后的内容
            new_relative_path = f"./{self.assets_folder_name}/{new_name}"
            
            return new_relative_path, new_content
            
        except Exception as e:
            print(f"重命名资源失败: {e}")
            return None, note_content
    
    def list_assets(self) -> List[Dict[str, any]]:
        """列出所有资源文件"""
        assets = []
        
        if not os.path.exists(self.assets_path):
            return assets
        
        for filename in os.listdir(self.assets_path):
            file_path = os.path.join(self.assets_path, filename)
            if os.path.isfile(file_path):
                stat = os.stat(file_path)
                assets.append({
                    'name': filename,
                    'path': file_path,
                    'relative_path': f"./{self.assets_folder_name}/{filename}",
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime)
                })
        
        return assets
    
    def get_asset_info(self, filename: str) -> Optional[Dict[str, any]]:
        """获取资源文件信息"""
        file_path = os.path.join(self.assets_path, filename)
        
        if not os.path.exists(file_path):
            return None
        
        stat = os.stat(file_path)
        
        info = {
            'name': filename,
            'path': file_path,
            'relative_path': f"./{self.assets_folder_name}/{filename}",
            'size': stat.st_size,
            'modified': datetime.fromtimestamp(stat.st_mtime)
        }
        
        # 如果是图片，获取尺寸
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')):
            try:
                from PIL import Image
                with Image.open(file_path) as img:
                    info['width'] = img.width
                    info['height'] = img.height
            except Exception:
                pass
        
        return info
    
    def copy_assets_to_export(self, export_dir: str, note_content: str) -> str:
        """复制相关资源到导出目录"""
        if not os.path.exists(self.assets_path):
            return note_content
        
        # 创建导出资源目录
        export_assets_path = os.path.join(export_dir, self.assets_folder_name)
        os.makedirs(export_assets_path, exist_ok=True)
        
        # 查找所有引用的资源
        pattern = rf'!\[.*?\]\(.*?{self.assets_folder_name}/([^\)]+)\)'
        matches = re.findall(pattern, note_content)
        
        # 复制被引用的资源
        for filename in matches:
            source_path = os.path.join(self.assets_path, filename)
            if os.path.exists(source_path):
                target_path = os.path.join(export_assets_path, filename)
                try:
                    shutil.copy2(source_path, target_path)
                except Exception as e:
                    print(f"复制资源失败 {filename}: {e}")
        
        return note_content
