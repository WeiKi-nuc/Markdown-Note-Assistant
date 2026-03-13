#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TemplateEngine 类 - 笔记模板管理与渲染
"""

import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Any


class TemplateEngine:
    """模板引擎，管理笔记模板"""
    
    # 内置模板
    BUILTIN_TEMPLATES = {
        'diary': {
            'name': '日记',
            'description': '每日记录模板',
            'category': 'daily',
            'content': '''---
title: {{title}}
date: {{date}}
tags: [日记]
category: 日记
---

# {{title}}

## 今日回顾


## 重要事项

- [ ] 

## 明日计划

- 

## 心情与感悟


'''
        },
        'weekly': {
            'name': '周报',
            'description': '工作周报模板',
            'category': 'work',
            'content': '''---
title: {{title}}
date: {{date}}
tags: [周报, 工作]
category: 工作
---

# {{title}}

## 本周完成

- 

## 进行中

- [ ] 

## 下周计划

- 

## 问题与风险


## 其他事项


'''
        },
        'meeting': {
            'name': '会议纪要',
            'description': '会议记录模板',
            'category': 'work',
            'content': '''---
title: {{title}}
date: {{date}}
tags: [会议]
category: 会议
---

# {{title}}

**时间**: {{datetime}}
**地点**: 
**参会人员**: 

## 会议议题


## 讨论内容


## 决议事项

- [ ] 

## 行动项

| 负责人 | 事项 | 截止日期 |
|--------|------|----------|
|        |      |          |

'''
        },
        'project': {
            'name': '项目文档',
            'description': '项目规划文档模板',
            'category': 'project',
            'content': '''---
title: {{title}}
date: {{date}}
tags: [项目]
category: 项目
status: 规划中
---

# {{title}}

## 项目概述


## 目标


## 任务分解

- [ ] 

## 时间线

```mermaid
gantt
    title 项目进度
    dateFormat  YYYY-MM-DD
    section 阶段1
    任务1           :a1, {{date}}, 7d
```

## 团队成员

- 

## 参考资料

- 

'''
        },
        'article': {
            'name': '文章',
            'description': '博客文章模板',
            'category': 'writing',
            'content': '''---
title: {{title}}
date: {{date}}
tags: [文章]
category: 写作
author: 
---

# {{title}}

## 引言


## 正文


## 总结


'''
        },
        'reading': {
            'name': '读书笔记',
            'description': '阅读笔记模板',
            'category': 'learning',
            'content': '''---
title: {{title}}
date: {{date}}
tags: [读书笔记]
category: 学习
book: 
author: 
---

# {{title}}

## 书籍信息

- **书名**: 
- **作者**: 
- **阅读日期**: {{date}}

## 核心观点


## 精彩摘录

> 

## 个人思考


## 行动计划

- [ ] 

'''
        }
    }
    
    def __init__(self, custom_templates_dir: Optional[str] = None):
        self.templates: Dict[str, Dict[str, Any]] = {}
        self.custom_templates_dir = custom_templates_dir
        
        # 加载内置模板
        self.load_builtin_templates()
        
        # 加载自定义模板
        if custom_templates_dir and os.path.exists(custom_templates_dir):
            self.load_custom_templates(custom_templates_dir)
    
    def load_builtin_templates(self) -> None:
        """加载内置模板"""
        self.templates.update(self.BUILTIN_TEMPLATES)
    
    def load_custom_templates(self, folder: str) -> None:
        """加载用户自定义模板"""
        if not os.path.exists(folder):
            return
        
        for filename in os.listdir(folder):
            if filename.endswith('.md'):
                template_id = os.path.splitext(filename)[0]
                file_path = os.path.join(folder, filename)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 尝试从内容中提取元数据
                    metadata = self._extract_metadata(content)
                    
                    self.templates[template_id] = {
                        'name': metadata.get('name', template_id),
                        'description': metadata.get('description', ''),
                        'category': metadata.get('category', 'custom'),
                        'content': content
                    }
                    
                except Exception as e:
                    print(f"加载模板失败 {filename}: {e}")
    
    def _extract_metadata(self, content: str) -> Dict[str, str]:
        """从模板内容中提取元数据"""
        metadata = {}
        
        # 查找 HTML 注释格式的元数据
        pattern = r'<!--\s*(\w+):\s*(.+?)\s*-->'
        matches = re.findall(pattern, content)
        
        for key, value in matches:
            metadata[key] = value.strip()
        
        return metadata
    
    def render(self, template_name: str, variables: Optional[Dict[str, str]] = None) -> str:
        """渲染模板，替换变量"""
        if template_name not in self.templates:
            raise ValueError(f"模板不存在: {template_name}")
        
        template = self.templates[template_name]['content']
        
        # 默认变量
        now = datetime.now()
        default_vars = {
            'title': '未命名',
            'date': now.strftime('%Y-%m-%d'),
            'datetime': now.strftime('%Y-%m-%d %H:%M'),
            'year': str(now.year),
            'month': str(now.month).zfill(2),
            'day': str(now.day).zfill(2),
            'time': now.strftime('%H:%M')
        }
        
        # 合并变量
        if variables:
            default_vars.update(variables)
        
        # 替换变量
        result = template
        for key, value in default_vars.items():
            result = result.replace(f'{{{{{key}}}}}', str(value))
        
        return result
    
    def get_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """获取模板信息"""
        return self.templates.get(template_name)
    
    def get_templates_by_category(self, category: str) -> List[Dict[str, Any]]:
        """按类别获取模板"""
        result = []
        for template_id, template in self.templates.items():
            if template.get('category') == category:
                template_copy = template.copy()
                template_copy['id'] = template_id
                result.append(template_copy)
        return result
    
    def get_all_templates(self) -> List[Dict[str, Any]]:
        """获取所有模板"""
        result = []
        for template_id, template in self.templates.items():
            template_copy = template.copy()
            template_copy['id'] = template_id
            result.append(template_copy)
        return result
    
    def get_categories(self) -> List[str]:
        """获取所有模板类别"""
        categories = set()
        for template in self.templates.values():
            categories.add(template.get('category', 'other'))
        return sorted(list(categories))
    
    def get_default_template_for(self, note_type: str) -> Optional[str]:
        """根据笔记类型推荐模板"""
        type_mapping = {
            'diary': 'diary',
            'journal': 'diary',
            'weekly': 'weekly',
            'meeting': 'meeting',
            'project': 'project',
            'article': 'article',
            'blog': 'article',
            'reading': 'reading',
            'book': 'reading'
        }
        
        return type_mapping.get(note_type.lower())
    
    def create_custom_template(self, template_id: str, name: str, content: str, 
                               description: str = '', category: str = 'custom') -> bool:
        """创建自定义模板"""
        try:
            # 保存到内存
            self.templates[template_id] = {
                'name': name,
                'description': description,
                'category': category,
                'content': content
            }
            
            # 保存到文件
            if self.custom_templates_dir:
                os.makedirs(self.custom_templates_dir, exist_ok=True)
                file_path = os.path.join(self.custom_templates_dir, f"{template_id}.md")
                
                # 添加元数据注释
                full_content = f"""<!-- name: {name} -->
<!-- description: {description} -->
<!-- category: {category} -->

{content}"""
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(full_content)
            
            return True
            
        except Exception as e:
            print(f"创建模板失败: {e}")
            return False
    
    def delete_template(self, template_id: str) -> bool:
        """删除自定义模板"""
        if template_id not in self.templates:
            return False
        
        # 不能删除内置模板
        if template_id in self.BUILTIN_TEMPLATES:
            return False
        
        del self.templates[template_id]
        
        # 删除文件
        if self.custom_templates_dir:
            file_path = os.path.join(self.custom_templates_dir, f"{template_id}.md")
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"删除模板文件失败: {e}")
        
        return True
