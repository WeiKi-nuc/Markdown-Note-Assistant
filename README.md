# Markdown Note Assistant

一个功能强大的 Markdown 笔记应用，支持实时预览、双向链接、标签管理等功能。

## 功能特性

### 核心功能
- **双栏编辑器**：左侧编辑，右侧实时预览（300ms 防抖）
- **同步滚动**：编辑区与预览区滚动位置联动
- **多种布局**：支持编辑/预览/分屏三种模式
- **笔记本管理**：本地文件夹即笔记本，支持多级目录

### Markdown 支持
- **标准 Markdown**：标题、列表、链接、图片、代码块等
- **GitHub Flavored**：表格、任务列表、删除线
- **扩展语法**：数学公式（LaTeX）、Mermaid 图表
- **Wiki 链接**：`[[笔记名]]` 双向链接语法

### 组织与导航
- **标签系统**：YAML Frontmatter 标签管理
- **双向链接**：自动识别笔记间的引用关系
- **全文搜索**：支持正则表达式搜索
- **快速打开**：Ctrl+P 模糊匹配文件名

### 编辑增强
- **语法高亮**：Markdown 语法实时高亮
- **快捷键**：丰富的键盘快捷键支持
- **模板系统**：日记、周报、会议纪要等模板
- **自动保存**：定时自动保存笔记

## 项目结构

```
Markdown-Note-Assistant/
├── main.py                      # 程序入口
├── requirements.txt             # 依赖列表
├── src/
│   ├── core/                    # 核心模块
│   │   ├── note.py             # 笔记实体类
│   │   ├── notebook.py         # 笔记本类
│   │   ├── note_repository.py  # 笔记仓库（全局管理）
│   │   ├── config_manager.py   # 配置管理
│   │   ├── link_manager.py     # 链接管理器
│   │   ├── template_engine.py  # 模板引擎
│   │   └── asset_manager.py    # 资源管理器
│   ├── parser/                  # 解析模块
│   │   └── markdown_parser.py  # Markdown 解析引擎
│   └── ui/                      # UI 模块
│       ├── ui_manager.py       # 主界面管理器
│       ├── editor.py           # 编辑器组件
│       ├── preview_renderer.py # 预览渲染器
│       ├── sidebar.py          # 侧边栏导航
│       └── search_dialog.py    # 搜索对话框
```

## 安装运行

### 安装依赖
```bash
pip install -r requirements.txt
```

### 运行程序
```bash
python main.py
```

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| Ctrl+N | 新建笔记 |
| Ctrl+S | 保存 |
| Ctrl+O | 打开笔记本 |
| Ctrl+F | 查找 |
| Ctrl+P | 快速打开 |
| Ctrl+B | 切换侧边栏 |
| Ctrl+B | 粗体 |
| Ctrl+I | 斜体 |
| Ctrl+K | 插入链接 |

## 配置

配置文件位于 `~/.markdown_note_assistant/config.json`，包含：
- 编辑器设置（字体、字号、自动保存间隔）
- 预览设置（主题、代码高亮）
- 界面设置（布局、窗口大小）
- 快捷键设置

## 技术栈

- **Python 3.8+**
- **Tkinter**：GUI 框架
- **Markdown**：Markdown 解析
- **PyYAML**：YAML Frontmatter 解析
- **Pillow**：图片处理

## 许可证

MIT License
