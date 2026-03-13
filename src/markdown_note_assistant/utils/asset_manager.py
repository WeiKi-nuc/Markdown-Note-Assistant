"""
Asset Manager module - handles images and attachments.
"""

from __future__ import annotations

import hashlib
import os
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from PIL import Image


@dataclass
class AssetInfo:
    """Information about an asset file."""
    path: Path
    relative_path: str
    size: int
    mime_type: str
    width: Optional[int] = None
    height: Optional[int] = None
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": str(self.path),
            "relative_path": self.relative_path,
            "size": self.size,
            "mime_type": self.mime_type,
            "width": self.width,
            "height": self.height,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AssetManager:
    """
    Asset Manager - manages images and attachments for notes.
    
    Features:
    - Save pasted images
    - Manage assets directory
    - Clean unused assets
    - Rename and move assets
    - Image compression
    """
    
    ASSETS_DIR_NAME = "assets"
    IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp"}
    ATTACHMENT_EXTENSIONS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip", ".tar", ".gz"}
    
    MIME_TYPES = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".svg": "image/svg+xml",
        ".bmp": "image/bmp",
        ".pdf": "application/pdf",
        ".doc": "application/msword",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".xls": "application/vnd.ms-excel",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".zip": "application/zip",
        ".tar": "application/x-tar",
        ".gz": "application/gzip",
    }
    
    def __init__(
        self,
        base_path: Optional[Path] = None,
        assets_dir_name: str = ASSETS_DIR_NAME,
        compress_images: bool = True,
        compress_quality: int = 85,
        max_image_width: int = 1200,
    ):
        """
        Initialize the asset manager.
        
        Args:
            base_path: Base directory for assets
            assets_dir_name: Name of the assets directory
            compress_images: Whether to compress images
            compress_quality: JPEG compression quality (1-100)
            max_image_width: Maximum image width (larger images will be resized)
        """
        self.base_path = base_path
        self.assets_dir_name = assets_dir_name
        self.compress_images = compress_images
        self.compress_quality = compress_quality
        self.max_image_width = max_image_width
    
    def set_base_path(self, path: Path | str) -> None:
        """Set the base path for assets."""
        self.base_path = Path(path)
    
    def get_assets_dir(self, note_path: Optional[Path] = None) -> Path:
        """
        Get the assets directory path.
        
        Args:
            note_path: Path to the note file (assets will be in same directory)
            
        Returns:
            Path to the assets directory
        """
        if note_path:
            return note_path.parent / self.assets_dir_name
        elif self.base_path:
            return self.base_path / self.assets_dir_name
        else:
            raise ValueError("No base path or note path provided")
    
    def save_pasted_image(
        self,
        image_data: bytes,
        note_path: Path,
        filename: Optional[str] = None,
    ) -> Tuple[Path, str]:
        """
        Save an image from clipboard data.
        
        Args:
            image_data: Raw image bytes
            note_path: Path to the note file
            filename: Optional custom filename
            
        Returns:
            Tuple of (absolute path, relative path for markdown)
        """
        assets_dir = self.get_assets_dir(note_path)
        assets_dir.mkdir(parents=True, exist_ok=True)
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            hash_suffix = hashlib.md5(image_data).hexdigest()[:8]
            filename = f"image_{timestamp}_{hash_suffix}.png"
        
        file_path = assets_dir / filename
        
        if self.compress_images:
            image_data = self._compress_image(image_data)
        
        with open(file_path, "wb") as f:
            f.write(image_data)
        
        relative_path = f"{self.assets_dir_name}/{filename}"
        
        return file_path, relative_path
    
    def save_image_from_file(
        self,
        source_path: Path,
        note_path: Path,
        new_filename: Optional[str] = None,
    ) -> Tuple[Path, str]:
        """
        Copy an image file to the assets directory.
        
        Args:
            source_path: Path to the source image
            note_path: Path to the note file
            new_filename: Optional new filename
            
        Returns:
            Tuple of (absolute path, relative path for markdown)
        """
        assets_dir = self.get_assets_dir(note_path)
        assets_dir.mkdir(parents=True, exist_ok=True)
        
        if not new_filename:
            new_filename = source_path.name
        
        dest_path = assets_dir / new_filename
        
        if dest_path.exists():
            stem = dest_path.stem
            suffix = dest_path.suffix
            counter = 1
            while dest_path.exists():
                dest_path = assets_dir / f"{stem}_{counter}{suffix}"
                counter += 1
            new_filename = dest_path.name
        
        if self.compress_images and source_path.suffix.lower() in {".jpg", ".jpeg", ".png"}:
            self._compress_and_save_image(source_path, dest_path)
        else:
            shutil.copy2(source_path, dest_path)
        
        relative_path = f"{self.assets_dir_name}/{new_filename}"
        
        return dest_path, relative_path
    
    def _compress_image(self, image_data: bytes) -> bytes:
        """Compress image data."""
        try:
            from io import BytesIO
            
            img = Image.open(BytesIO(image_data))
            
            if img.width > self.max_image_width:
                ratio = self.max_image_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((self.max_image_width, new_height), Image.Resampling.LANCZOS)
            
            output = BytesIO()
            
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            img.save(output, format="JPEG", quality=self.compress_quality, optimize=True)
            
            return output.getvalue()
        except Exception as e:
            print(f"Error compressing image: {e}")
            return image_data
    
    def _compress_and_save_image(self, source_path: Path, dest_path: Path) -> None:
        """Compress and save an image file."""
        try:
            img = Image.open(source_path)
            
            if img.width > self.max_image_width:
                ratio = self.max_image_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((self.max_image_width, new_height), Image.Resampling.LANCZOS)
            
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            img.save(dest_path, format="JPEG", quality=self.compress_quality, optimize=True)
        except Exception as e:
            print(f"Error compressing image: {e}")
            shutil.copy2(source_path, dest_path)
    
    def get_asset_path(self, relative_path: str, note_path: Path) -> Path:
        """
        Resolve a relative asset path to an absolute path.
        
        Args:
            relative_path: Relative path from the note
            note_path: Path to the note file
            
        Returns:
            Absolute path to the asset
        """
        if relative_path.startswith(("http://", "https://", "data:")):
            raise ValueError("Cannot resolve URL as local path")
        
        if Path(relative_path).is_absolute():
            return Path(relative_path)
        
        return note_path.parent / relative_path
    
    def get_asset_info(self, asset_path: Path) -> Optional[AssetInfo]:
        """
        Get information about an asset file.
        
        Args:
            asset_path: Path to the asset
            
        Returns:
            AssetInfo or None if file doesn't exist
        """
        if not asset_path.exists():
            return None
        
        stat = asset_path.stat()
        suffix = asset_path.suffix.lower()
        mime_type = self.MIME_TYPES.get(suffix, "application/octet-stream")
        
        width = None
        height = None
        
        if suffix in self.IMAGE_EXTENSIONS:
            try:
                with Image.open(asset_path) as img:
                    width, height = img.size
            except Exception:
                pass
        
        return AssetInfo(
            path=asset_path,
            relative_path=asset_path.name,
            size=stat.st_size,
            mime_type=mime_type,
            width=width,
            height=height,
            created_at=datetime.fromtimestamp(stat.st_ctime),
        )
    
    def list_assets(self, note_path: Path) -> List[AssetInfo]:
        """
        List all assets in the note's assets directory.
        
        Args:
            note_path: Path to the note file
            
        Returns:
            List of AssetInfo objects
        """
        assets_dir = self.get_assets_dir(note_path)
        
        if not assets_dir.exists():
            return []
        
        assets = []
        
        for file_path in assets_dir.iterdir():
            if file_path.is_file():
                info = self.get_asset_info(file_path)
                if info:
                    info.relative_path = f"{self.assets_dir_name}/{file_path.name}"
                    assets.append(info)
        
        return sorted(assets, key=lambda x: x.created_at or datetime.min, reverse=True)
    
    def find_referenced_assets(self, content: str) -> Set[str]:
        """
        Find all asset references in markdown content.
        
        Args:
            content: Markdown content
            
        Returns:
            Set of referenced asset paths
        """
        referenced = set()
        
        image_pattern = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
        for match in image_pattern.finditer(content):
            path = match.group(1)
            if not path.startswith(("http://", "https://", "data:")):
                referenced.add(path)
        
        link_pattern = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
        for match in link_pattern.finditer(content):
            path = match.group(1)
            if not path.startswith(("http://", "https://", "data:")):
                suffix = Path(path).suffix.lower()
                if suffix in self.ATTACHMENT_EXTENSIONS:
                    referenced.add(path)
        
        return referenced
    
    def find_unused_assets(self, note_path: Path, content: str) -> List[AssetInfo]:
        """
        Find assets that are not referenced in the note.
        
        Args:
            note_path: Path to the note file
            content: Note content
            
        Returns:
            List of unused AssetInfo objects
        """
        all_assets = self.list_assets(note_path)
        referenced = self.find_referenced_assets(content)
        
        unused = []
        for asset in all_assets:
            relative = f"{self.assets_dir_name}/{asset.path.name}"
            if relative not in referenced and asset.path.name not in referenced:
                unused.append(asset)
        
        return unused
    
    def cleanup_unused_assets(self, note_path: Path, content: str) -> int:
        """
        Remove assets that are not referenced in the note.
        
        Args:
            note_path: Path to the note file
            content: Note content
            
        Returns:
            Number of assets removed
        """
        unused = self.find_unused_assets(note_path, content)
        
        for asset in unused:
            try:
                asset.path.unlink()
            except Exception as e:
                print(f"Error removing asset {asset.path}: {e}")
        
        assets_dir = self.get_assets_dir(note_path)
        if assets_dir.exists() and not any(assets_dir.iterdir()):
            try:
                assets_dir.rmdir()
            except Exception:
                pass
        
        return len(unused)
    
    def rename_asset(
        self,
        old_path: Path,
        new_name: str,
        note_path: Path,
        content: str,
    ) -> Tuple[Path, str, str]:
        """
        Rename an asset and update references.
        
        Args:
            old_path: Current path to the asset
            new_name: New filename
            note_path: Path to the note file
            content: Note content
            
        Returns:
            Tuple of (new_path, old_relative, new_relative)
        """
        new_path = old_path.parent / new_name
        
        if new_path.exists():
            raise FileExistsError(f"File already exists: {new_path}")
        
        old_relative = f"{self.assets_dir_name}/{old_path.name}"
        new_relative = f"{self.assets_dir_name}/{new_name}"
        
        old_path.rename(new_path)
        
        return new_path, old_relative, new_relative
    
    def update_references(
        self,
        content: str,
        old_relative: str,
        new_relative: str,
    ) -> str:
        """
        Update asset references in content.
        
        Args:
            content: Note content
            old_relative: Old relative path
            new_relative: New relative path
            
        Returns:
            Updated content
        """
        content = content.replace(f"]({old_relative})", f"]({new_relative})")
        
        return content
    
    def move_asset_to_notebook(
        self,
        asset_path: Path,
        target_note_path: Path,
    ) -> Tuple[Path, str]:
        """
        Move an asset to another note's assets directory.
        
        Args:
            asset_path: Current asset path
            target_note_path: Path to the target note
            
        Returns:
            Tuple of (new_path, new_relative_path)
        """
        target_assets_dir = self.get_assets_dir(target_note_path)
        target_assets_dir.mkdir(parents=True, exist_ok=True)
        
        new_path = target_assets_dir / asset_path.name
        
        if new_path.exists():
            stem = new_path.stem
            suffix = new_path.suffix
            counter = 1
            while new_path.exists():
                new_path = target_assets_dir / f"{stem}_{counter}{suffix}"
                counter += 1
        
        shutil.move(str(asset_path), str(new_path))
        
        relative_path = f"{self.assets_dir_name}/{new_path.name}"
        
        return new_path, relative_path
    
    def get_total_size(self, note_path: Path) -> int:
        """
        Get total size of all assets for a note.
        
        Args:
            note_path: Path to the note file
            
        Returns:
            Total size in bytes
        """
        assets = self.list_assets(note_path)
        return sum(asset.size for asset in assets)
    
    def export_assets(
        self,
        note_path: Path,
        output_dir: Path,
        content: str,
    ) -> Dict[str, str]:
        """
        Export referenced assets to an output directory.
        
        Args:
            note_path: Path to the note file
            output_dir: Directory to export to
            content: Note content
            
        Returns:
            Dict mapping old relative paths to new paths
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        referenced = self.find_referenced_assets(content)
        path_mapping = {}
        
        for rel_path in referenced:
            abs_path = self.get_asset_path(rel_path, note_path)
            
            if abs_path.exists():
                dest_path = output_dir / abs_path.name
                
                if dest_path.exists():
                    stem = dest_path.stem
                    suffix = dest_path.suffix
                    counter = 1
                    while dest_path.exists():
                        dest_path = output_dir / f"{stem}_{counter}{suffix}"
                        counter += 1
                
                shutil.copy2(abs_path, dest_path)
                path_mapping[rel_path] = dest_path.name
        
        return path_mapping
    
    def is_image(self, path: Path | str) -> bool:
        """Check if a file is an image."""
        return Path(path).suffix.lower() in self.IMAGE_EXTENSIONS
    
    def is_attachment(self, path: Path | str) -> bool:
        """Check if a file is an attachment."""
        return Path(path).suffix.lower() in self.ATTACHMENT_EXTENSIONS
