#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown Note Assistant - 主入口文件
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ui.ui_manager import UIManager
from src.core.config_manager import ConfigManager


def main():
    """应用程序主入口"""
    # 加载配置
    config = ConfigManager()
    
    # 启动主界面
    app = UIManager(config)
    app.run()


if __name__ == "__main__":
    main()
