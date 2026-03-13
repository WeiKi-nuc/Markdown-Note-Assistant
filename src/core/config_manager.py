#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ConfigManager 类 - 应用设置与用户偏好
"""

import os
import json
from typing import Dict, Any, Optional


class ConfigManager:
    """配置管理器，管理应用设置和用户偏好"""
    
    DEFAULT_CONFIG = {
        # 编辑器设置
        'editor': {
            'font_family': 'Consolas',
            'font_size': 12,
            'line_height': 1.5,
            'auto_save_interval': 30000,  # 毫秒
            'word_wrap': True,
            'show_line_numbers': True,
            'tab_size': 4,
            'use_spaces': True,
        },
        # 预览设置
        'preview': {
            'theme': 'light',  # light/dark
            'code_highlight_theme': 'default',
            'math_enabled': True,
            'mermaid_enabled': True,
            'sync_scroll': True,
        },
        # 界面设置
        'ui': {
            'layout': 'split',  # split/edit/preview
            'sidebar_width': 250,
            'window_width': 1400,
            'window_height': 900,
            'window_x': None,
            'window_y': None,
            'maximized': False,
        },
        # 快捷键设置
        'shortcuts': {
            'new_note': 'Ctrl+N',
            'open_note': 'Ctrl+O',
            'save_note': 'Ctrl+S',
            'search': 'Ctrl+F',
            'global_search': 'Ctrl+Shift+F',
            'quick_open': 'Ctrl+P',
            'toggle_preview': 'Ctrl+E',
            'toggle_sidebar': 'Ctrl+B',
            'focus_mode': 'F11',
            'insert_link': 'Ctrl+K',
            'insert_image': 'Ctrl+Shift+I',
            'bold': 'Ctrl+B',
            'italic': 'Ctrl+I',
            'code': 'Ctrl+Shift+C',
        },
        # 高级设置
        'advanced': {
            'image_compression_quality': 85,
            'auto_backup': True,
            'backup_interval': 300000,  # 5分钟
            'backup_count': 10,
            'default_notebook': None,
            'assets_folder_name': 'assets',
        }
    }
    
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.config_path = self._get_config_path()
        self.load()
    
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
        return os.path.join(config_dir, 'config.json')
    
    def load(self) -> None:
        """加载配置"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                
                # 合并配置（保留默认值）
                self.config = self._merge_config(self.DEFAULT_CONFIG, loaded_config)
            except Exception as e:
                print(f"加载配置失败: {e}")
                self.config = self.DEFAULT_CONFIG.copy()
        else:
            self.config = self.DEFAULT_CONFIG.copy()
            self.save()
    
    def save(self) -> None:
        """保存配置"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def _merge_config(self, default: Dict, loaded: Dict) -> Dict:
        """合并配置，保留默认值中未在加载配置中的项"""
        result = {}
        for key, value in default.items():
            if key in loaded:
                if isinstance(value, dict) and isinstance(loaded[key], dict):
                    result[key] = self._merge_config(value, loaded[key])
                else:
                    result[key] = loaded[key]
            else:
                result[key] = value
        return result
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项（支持点号分隔的路径）"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """设置配置项（支持点号分隔的路径）"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self.save()
    
    def get_editor_font(self) -> tuple:
        """获取编辑器字体设置"""
        family = self.get('editor.font_family', 'Consolas')
        size = self.get('editor.font_size', 12)
        return (family, size)
    
    def get_preview_theme(self) -> str:
        """获取预览主题"""
        return self.get('preview.theme', 'light')
    
    def set_preview_theme(self, theme: str) -> None:
        """设置预览主题"""
        self.set('preview.theme', theme)
    
    def get_layout(self) -> str:
        """获取布局模式"""
        return self.get('ui.layout', 'split')
    
    def set_layout(self, layout: str) -> None:
        """设置布局模式"""
        self.set('ui.layout', layout)
    
    def get_shortcut(self, action: str) -> str:
        """获取快捷键"""
        return self.get(f'shortcuts.{action}', '')
    
    def set_shortcut(self, action: str, shortcut: str) -> None:
        """设置快捷键"""
        self.set(f'shortcuts.{action}', shortcut)
    
    def get_window_geometry(self) -> tuple:
        """获取窗口几何信息"""
        width = self.get('ui.window_width', 1400)
        height = self.get('ui.window_height', 900)
        x = self.get('ui.window_x')
        y = self.get('ui.window_y')
        
        if x is not None and y is not None:
            return (width, height, x, y)
        return (width, height)
    
    def set_window_geometry(self, width: int, height: int, x: int = None, y: int = None) -> None:
        """设置窗口几何信息"""
        self.set('ui.window_width', width)
        self.set('ui.window_height', height)
        if x is not None:
            self.set('ui.window_x', x)
        if y is not None:
            self.set('ui.window_y', y)
    
    def is_maximized(self) -> bool:
        """获取窗口是否最大化"""
        return self.get('ui.maximized', False)
    
    def set_maximized(self, maximized: bool) -> None:
        """设置窗口最大化状态"""
        self.set('ui.maximized', maximized)
    
    def get_sidebar_width(self) -> int:
        """获取侧边栏宽度"""
        return self.get('ui.sidebar_width', 250)
    
    def set_sidebar_width(self, width: int) -> None:
        """设置侧边栏宽度"""
        self.set('ui.sidebar_width', width)
    
    def get_auto_save_interval(self) -> int:
        """获取自动保存间隔（毫秒）"""
        return self.get('editor.auto_save_interval', 30000)
    
    def get_assets_folder_name(self) -> str:
        """获取资源文件夹名称"""
        return self.get('advanced.assets_folder_name', 'assets')
    
    def get_default_notebook(self) -> Optional[str]:
        """获取默认笔记本路径"""
        return self.get('advanced.default_notebook')
    
    def set_default_notebook(self, path: str) -> None:
        """设置默认笔记本路径"""
        self.set('advanced.default_notebook', path)
    
    def reset_to_default(self) -> None:
        """重置为默认配置"""
        self.config = self.DEFAULT_CONFIG.copy()
        self.save()
