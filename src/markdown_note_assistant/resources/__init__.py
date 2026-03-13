"""
Resources module for Markdown Note Assistant.
"""

from pathlib import Path

RESOURCES_DIR = Path(__file__).parent

TEMPLATES_DIR = RESOURCES_DIR / "templates"
THEMES_DIR = RESOURCES_DIR / "themes"


def get_template_path(name: str) -> Path:
    """Get the path to a template file."""
    return TEMPLATES_DIR / f"{name}.md"


def get_theme_path(name: str) -> Path:
    """Get the path to a theme CSS file."""
    return THEMES_DIR / f"{name}.css"


def list_templates() -> list:
    """List all available templates."""
    if TEMPLATES_DIR.exists():
        return [f.stem for f in TEMPLATES_DIR.glob("*.md")]
    return []


def list_themes() -> list:
    """List all available themes."""
    if THEMES_DIR.exists():
        return [f.stem for f in THEMES_DIR.glob("*.css")]
    return []
