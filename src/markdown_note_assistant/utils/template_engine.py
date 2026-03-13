"""
Template Engine module - manages note templates.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from string import Template
from typing import Any, Dict, List, Optional


@dataclass
class TemplateVariable:
    """Represents a template variable."""
    name: str
    description: str
    default_value: Optional[str] = None
    required: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "default_value": self.default_value,
            "required": self.required,
        }


@dataclass
class NoteTemplate:
    """Represents a note template."""
    name: str
    content: str
    description: str = ""
    category: str = "general"
    variables: List[TemplateVariable] = field(default_factory=list)
    file_extension: str = ".md"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "content": self.content,
            "description": self.description,
            "category": self.category,
            "variables": [v.to_dict() for v in self.variables],
            "file_extension": self.file_extension,
        }


class TemplateEngine:
    """
    Template Engine - manages and renders note templates.
    
    Features:
    - Built-in templates (diary, meeting, project, etc.)
    - Custom template loading
    - Variable substitution
    - Date/time formatting
    - Template categories
    """
    
    BUILTIN_TEMPLATES = {
        "default": NoteTemplate(
            name="default",
            content="""---
title: ${title}
date: ${date}
tags: []
---

# ${title}

""",
            description="Default empty note template",
            category="general",
            variables=[
                TemplateVariable("title", "Note title", required=True),
                TemplateVariable("date", "Creation date"),
            ],
        ),
        "diary": NoteTemplate(
            name="diary",
            content="""---
title: ${title}
date: ${date}
tags: [diary, journal]
mood: 
weather: 
---

# ${title}

## 今日计划

- [ ] 
- [ ] 
- [ ] 

## 今日记录



## 明日计划

- [ ] 
- [ ] 

## 反思与感悟


""",
            description="Daily journal template with tasks and reflection",
            category="personal",
            variables=[
                TemplateVariable("title", "Diary title", default_value="日记"),
                TemplateVariable("date", "Date"),
            ],
        ),
        "meeting": NoteTemplate(
            name="meeting",
            content="""---
title: ${title}
date: ${date}
tags: [meeting]
attendees: []
---

# ${title}

**日期**: ${date}  
**时间**: ${time}  
**地点**:  
**参会人员**:  

## 会议议程

1. 
2. 
3. 

## 会议内容

### 议题一


### 议题二


## 决议事项

| 序号 | 决议内容 | 负责人 | 截止日期 |
|------|----------|--------|----------|
| 1 |  |  |  |
| 2 |  |  |  |

## 待办事项

- [ ] 
- [ ] 

## 下次会议

**时间**:  
**议题**: 

""",
            description="Meeting notes template",
            category="work",
            variables=[
                TemplateVariable("title", "Meeting title", required=True),
                TemplateVariable("date", "Meeting date"),
                TemplateVariable("time", "Meeting time"),
            ],
        ),
        "project": NoteTemplate(
            name="project",
            content="""---
title: ${title}
date: ${date}
tags: [project]
status: planning
priority: medium
---

# ${title}

## 项目概述

**目标**: 

**时间范围**: ${date} - 

**负责人**: 

## 背景


## 目标

- [ ] 主要目标 1
- [ ] 主要目标 2

## 里程碑

| 里程碑 | 截止日期 | 状态 | 备注 |
|--------|----------|------|------|
| 需求确认 |  | 待定 |  |
| 设计完成 |  | 待定 |  |
| 开发完成 |  | 待定 |  |
| 测试完成 |  | 待定 |  |
| 上线 |  | 待定 |  |

## 任务清单

### 第一阶段

- [ ] 
- [ ] 

### 第二阶段

- [ ] 
- [ ] 

## 资源需求

- 人员: 
- 预算: 
- 工具: 

## 风险评估

| 风险 | 影响 | 概率 | 应对措施 |
|------|------|------|----------|
|  |  |  |  |

## 相关链接

- [[相关笔记]]

## 更新日志

- ${date}: 项目创建

""",
            description="Project management template",
            category="work",
            variables=[
                TemplateVariable("title", "Project name", required=True),
                TemplateVariable("date", "Start date"),
            ],
        ),
        "weekly": NoteTemplate(
            name="weekly",
            content="""---
title: ${title}
date: ${date}
tags: [weekly, review]
week: ${week_number}
---

# ${title}

## 本周目标完成情况

| 目标 | 完成度 | 备注 |
|------|--------|------|
|  |  |  |
|  |  |  |

## 本周完成事项

- [x] 
- [x] 
- [ ] 

## 本周学习

### 技术学习


### 其他学习


## 本周问题与解决

### 问题 1

**描述**: 

**解决方案**: 

## 下周计划

### 工作目标

- [ ] 
- [ ] 

### 学习目标

- [ ] 
- [ ] 

## 本周总结


""",
            description="Weekly review template",
            category="personal",
            variables=[
                TemplateVariable("title", "Week title"),
                TemplateVariable("date", "Week start date"),
                TemplateVariable("week_number", "Week number of the year"),
            ],
        ),
        "reading": NoteTemplate(
            name="reading",
            content="""---
title: ${title}
date: ${date}
tags: [reading, book]
author: 
rating: 
status: reading
---

# ${title}

## 基本信息

- **作者**: 
- **出版社**: 
- **出版日期**: 
- **阅读日期**: ${date}
- **评分**: /5

## 内容简介


## 核心观点

1. 
2. 
3. 

## 精彩摘录

> 

## 个人感悟


## 行动计划

- [ ] 
- [ ] 

## 相关资源

- 

""",
            description="Reading notes template",
            category="personal",
            variables=[
                TemplateVariable("title", "Book title", required=True),
                TemplateVariable("date", "Reading date"),
            ],
        ),
        "code": NoteTemplate(
            name="code",
            content="""---
title: ${title}
date: ${date}
tags: [code, snippet]
language: 
---

# ${title}

## 问题描述


## 解决方案

\`\`\`${language}
${code}
\`\`\`

## 使用说明


## 注意事项


## 参考资料

- 

""",
            description="Code snippet template",
            category="development",
            variables=[
                TemplateVariable("title", "Snippet title", required=True),
                TemplateVariable("date", "Creation date"),
                TemplateVariable("language", "Programming language", default_value="python"),
                TemplateVariable("code", "Code content"),
            ],
        ),
        "tutorial": NoteTemplate(
            name="tutorial",
            content="""---
title: ${title}
date: ${date}
tags: [tutorial]
difficulty: beginner
---

# ${title}

## 概述

**难度**: 初级  
**预计时间**:   
**前置知识**: 

## 目标

完成本教程后，你将能够：

- 
- 
- 

## 准备工作

### 环境要求

- 

### 所需工具

- 

## 步骤一：标题

### 操作步骤

1. 
2. 
3. 

### 代码示例

\`\`\`
\`\`\`

### 说明


## 步骤二：标题

### 操作步骤

1. 
2. 
3. 

## 常见问题

### Q1: 

**A**: 

## 总结


## 扩展阅读

- 

""",
            description="Tutorial template",
            category="development",
            variables=[
                TemplateVariable("title", "Tutorial title", required=True),
                TemplateVariable("date", "Creation date"),
            ],
        ),
    }
    
    def __init__(self, custom_template_dir: Optional[Path] = None):
        """
        Initialize the template engine.
        
        Args:
            custom_template_dir: Directory for custom templates
        """
        self.custom_template_dir = custom_template_dir
        self.templates: Dict[str, NoteTemplate] = {}
        self._categories: Dict[str, List[str]] = defaultdict(list)
        
        self._load_builtin_templates()
        
        if custom_template_dir:
            self.load_custom_templates(custom_template_dir)
    
    def _load_builtin_templates(self) -> None:
        """Load built-in templates."""
        for name, template in self.BUILTIN_TEMPLATES.items():
            self.templates[name] = template
            self._categories[template.category].append(name)
    
    def load_custom_templates(self, directory: Path | str) -> int:
        """
        Load custom templates from a directory.
        
        Args:
            directory: Directory containing template files
            
        Returns:
            Number of templates loaded
        """
        directory = Path(directory)
        
        if not directory.exists():
            return 0
        
        count = 0
        
        for template_file in directory.glob("*.md"):
            try:
                template = self._load_template_file(template_file)
                if template:
                    self.templates[template.name] = template
                    self._categories[template.category].append(template.name)
                    count += 1
            except Exception as e:
                print(f"Error loading template {template_file}: {e}")
        
        return count
    
    def _load_template_file(self, file_path: Path) -> Optional[NoteTemplate]:
        """Load a template from a file."""
        import frontmatter
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        try:
            post = frontmatter.loads(content)
            metadata = dict(post.metadata)
            template_content = post.content
        except Exception:
            metadata = {}
            template_content = content
        
        name = metadata.get("name", file_path.stem)
        description = metadata.get("description", "")
        category = metadata.get("category", "custom")
        
        variables = []
        for var_data in metadata.get("variables", []):
            if isinstance(var_data, dict):
                variables.append(TemplateVariable(
                    name=var_data.get("name", ""),
                    description=var_data.get("description", ""),
                    default_value=var_data.get("default_value"),
                    required=var_data.get("required", False),
                ))
        
        return NoteTemplate(
            name=name,
            content=template_content,
            description=description,
            category=category,
            variables=variables,
        )
    
    def get_template(self, name: str) -> Optional[NoteTemplate]:
        """
        Get a template by name.
        
        Args:
            name: Template name
            
        Returns:
            NoteTemplate or None if not found
        """
        return self.templates.get(name)
    
    def get_templates_by_category(self, category: str) -> List[NoteTemplate]:
        """
        Get all templates in a category.
        
        Args:
            category: Category name
            
        Returns:
            List of templates
        """
        template_names = self._categories.get(category, [])
        return [self.templates[name] for name in template_names if name in self.templates]
    
    def get_all_categories(self) -> List[str]:
        """Get all template categories."""
        return list(self._categories.keys())
    
    def get_all_templates(self) -> List[NoteTemplate]:
        """Get all templates."""
        return list(self.templates.values())
    
    def render(
        self,
        template_name: str,
        variables: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Render a template with variables.
        
        Args:
            template_name: Name of the template to render
            variables: Variables to substitute
            
        Returns:
            Rendered template content
        """
        template = self.get_template(template_name)
        
        if not template:
            raise ValueError(f"Template not found: {template_name}")
        
        return self.render_template(template, variables)
    
    def render_template(
        self,
        template: NoteTemplate,
        variables: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Render a template object with variables.
        
        Args:
            template: NoteTemplate object
            variables: Variables to substitute
            
        Returns:
            Rendered template content
        """
        variables = variables or {}
        
        default_vars = self._get_default_variables()
        
        for var in template.variables:
            if var.name not in variables:
                if var.default_value is not None:
                    variables[var.name] = var.default_value
                elif var.required:
                    raise ValueError(f"Required variable '{var.name}' not provided")
                else:
                    variables[var.name] = ""
        
        all_vars = {**default_vars, **variables}
        
        content = template.content
        
        for key, value in all_vars.items():
            placeholder = f"${{{key}}}"
            content = content.replace(placeholder, str(value))
        
        return content
    
    def _get_default_variables(self) -> Dict[str, str]:
        """Get default variables for template rendering."""
        now = datetime.now()
        
        week_number = now.isocalendar()[1]
        
        return {
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M"),
            "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
            "year": str(now.year),
            "month": str(now.month),
            "day": str(now.day),
            "weekday": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][now.weekday()],
            "week_number": str(week_number),
            "timestamp": str(int(now.timestamp())),
        }
    
    def add_template(self, template: NoteTemplate) -> None:
        """
        Add a new template.
        
        Args:
            template: Template to add
        """
        self.templates[template.name] = template
        if template.name not in self._categories[template.category]:
            self._categories[template.category].append(template.name)
    
    def remove_template(self, name: str) -> bool:
        """
        Remove a template.
        
        Args:
            name: Template name to remove
            
        Returns:
            True if removed, False if not found
        """
        if name not in self.templates:
            return False
        
        template = self.templates.pop(name)
        if name in self._categories[template.category]:
            self._categories[template.category].remove(name)
        
        return True
    
    def save_template(self, template: NoteTemplate, directory: Path | str) -> Path:
        """
        Save a template to a file.
        
        Args:
            template: Template to save
            directory: Directory to save to
            
        Returns:
            Path to the saved file
        """
        import frontmatter
        
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        
        file_path = directory / f"{template.name}.md"
        
        metadata = {
            "name": template.name,
            "description": template.description,
            "category": template.category,
            "variables": [v.to_dict() for v in template.variables],
        }
        
        post = frontmatter.Post(template.content, **metadata)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))
        
        return file_path
    
    def get_default_template_for(self, note_type: str) -> Optional[NoteTemplate]:
        """
        Get the default template for a note type.
        
        Args:
            note_type: Type of note (diary, meeting, project, etc.)
            
        Returns:
            Default template for the type
        """
        type_mapping = {
            "diary": "diary",
            "journal": "diary",
            "meeting": "meeting",
            "project": "project",
            "weekly": "weekly",
            "reading": "reading",
            "book": "reading",
            "code": "code",
            "snippet": "code",
            "tutorial": "tutorial",
        }
        
        template_name = type_mapping.get(note_type.lower(), "default")
        return self.get_template(template_name)
    
    def create_from_template(
        self,
        template_name: str,
        title: str,
        extra_variables: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create note content from a template.
        
        Args:
            template_name: Name of the template
            title: Note title
            extra_variables: Additional variables
            
        Returns:
            Rendered note content
        """
        variables = {"title": title}
        if extra_variables:
            variables.update(extra_variables)
        
        return self.render(template_name, variables)
