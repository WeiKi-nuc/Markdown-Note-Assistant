"""
Test configuration and fixtures.
"""

import pytest
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    dir_path = Path(tempfile.mkdtemp())
    yield dir_path
    shutil.rmtree(dir_path)


@pytest.fixture
def sample_note_content():
    """Sample markdown note content."""
    return """---
title: Test Note
date: 2024-01-15
tags: [test, example]
---

# Test Note

This is a test note with some content.

## Section 1

- Item 1
- Item 2
- Item 3

## Section 2

Some **bold** and *italic* text.

```python
def hello():
    print("Hello, World!")
```

## Links

- [[Another Note]]
- [[Third Note#section]]

## Tasks

- [x] Completed task
- [ ] Pending task
"""


@pytest.fixture
def sample_note_file(temp_dir, sample_note_content):
    """Create a sample note file."""
    note_path = temp_dir / "test_note.md"
    note_path.write_text(sample_note_content, encoding="utf-8")
    return note_path


@pytest.fixture
def sample_notebook_dir(temp_dir):
    """Create a sample notebook directory with notes."""
    notebook_dir = temp_dir / "notebook"
    notebook_dir.mkdir()
    
    notes = {
        "note1.md": """---
title: Note 1
date: 2024-01-01
tags: [tag1, tag2]
---

# Note 1

Content of note 1.

[[Note 2]]
""",
        "note2.md": """---
title: Note 2
date: 2024-01-02
tags: [tag2, tag3]
---

# Note 2

Content of note 2.

[[Note 1]]
[[Note 3]]
""",
        "note3.md": """---
title: Note 3
date: 2024-01-03
tags: [tag1, tag3]
---

# Note 3

Content of note 3.
""",
    }
    
    for filename, content in notes.items():
        (notebook_dir / filename).write_text(content, encoding="utf-8")
    
    return notebook_dir
