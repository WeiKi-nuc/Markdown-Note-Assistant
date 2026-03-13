import os
from datetime import datetime
from typing import Dict, Any, Optional


class TemplateEngine:
    def __init__(self):
        self.templates: Dict[str, Dict[str, str]] = {
            'builtin': {},
            'custom': {}
        }
        self.load_builtin_templates()
    
    def load_builtin_templates(self):
        today = datetime.now()
        
        daily_template = """---
title: 日记 {{date}}
date: {{date}}
tags: [日记]
---

# 日记 {{date}}

## 今日计划
- [ ] 

## 今日完成


## 感悟与思考

"""
        self.templates['builtin']['daily'] = daily_template
        
        project_template = """---
title: {{title}}
date: {{date}}
tags: [项目]
status: 进行中
---

# {{title}}

## 项目概述


## 目标与里程碑
- [ ] 

## 相关文档
- 

## 更新日志
- {{date}}: 项目创建

"""
        self.templates['builtin']['project'] = project_template
        
        meeting_template = """---
title: {{title}}
date: {{date}}
tags: [会议纪要]
attendees: []
---

# {{title}}

**时间:** {{datetime}}  
**地点:**  
**参会人员:** 

## 会议议程
1. 

## 讨论要点


## 决议与行动项
- [ ] 

## 后续安排

"""
        self.templates['builtin']['meeting'] = meeting_template
    
    def load_custom_templates(self, folder: str):
        if not os.path.isdir(folder):
            return
        
        for filename in os.listdir(folder):
            if filename.endswith('.md') or filename.endswith('.template'):
                try:
                    filepath = os.path.join(folder, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    name = os.path.splitext(filename)[0]
                    self.templates['custom'][name] = content
                except:
                    pass
    
    def render(self, template_name: str, variables: Optional[Dict[str, Any]] = None) -> str:
        variables = variables or {}
        
        now = datetime.now()
        default_vars = {
            'date': now.strftime('%Y-%m-%d'),
            'datetime': now.strftime('%Y-%m-%d %H:%M:%S'),
            'year': now.strftime('%Y'),
            'month': now.strftime('%m'),
            'day': now.strftime('%d'),
            'time': now.strftime('%H:%M'),
            'title': '未命名'
        }
        default_vars.update(variables)
        
        template = self.get_template(template_name)
        if not template:
            return ""
        
        result = template
        for key, value in default_vars.items():
            result = result.replace('{{' + key + '}}', str(value))
        
        return result
    
    def get_template(self, template_name: str) -> Optional[str]:
        if template_name in self.templates['builtin']:
            return self.templates['builtin'][template_name]
        if template_name in self.templates['custom']:
            return self.templates['custom'][template_name]
        return None
    
    def get_default_template_for(self, note_type: str) -> str:
        type_map = {
            'daily': 'daily',
            '日记': 'daily',
            'project': 'project',
            '项目': 'project',
            'meeting': 'meeting',
            '会议': 'meeting',
            '会议纪要': 'meeting'
        }
        return type_map.get(note_type.lower(), '')
    
    def list_templates(self) -> Dict[str, list]:
        return {
            'builtin': list(self.templates['builtin'].keys()),
            'custom': list(self.templates['custom'].keys())
        }
