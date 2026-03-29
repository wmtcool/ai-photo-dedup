"""
Photo Scanner Module

Scans directories for photos and generates perceptual hashes.
"""

import os
from pathlib import Path
from typing import List, Dict, Optional, Iterator, Tuple
from dataclasses import dataclass
import imagehash
from PIL import Image
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.console import Console

console = Console()

# Supported image formats
SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.heic', '.webp', '.bmp', '.tiff', '.tif'}


@dataclass
class PhotoInfo:
    """Information about a scanned photo."""
    path: Path
    size: int
    hash_phash: str
    hash_dhash: str
    hash_ahash: str
    width: int
    height: int
    created_time: float
    modified_time: float

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "path": str(self.path),
            "size": self.size,
            "hash_phash": self.hash_phash,
            "hash_dhash": self.hash_dhash,
            "hash_ahash": self.hash_ahash,
            "width": self.width,
            "height": self.height,
            "created_time": self.created_time,
            "modified_time": self.modified_time,
        }


class PhotoScanner:
    """Scans directories and collects photo information."""

    def __init__(
        self,
        min_file_size: int = 1024,
        hash_size: int = 16,
        parallel: bool = True
    ):
        self.min_file_size = min_file_size
        self.hash_size = hash_size
        self.parallel = parallel
        self.photos: List[PhotoInfo] = []

    def scan_directory(
        self,
        directory: Path,
        recursive: bool = True
    ) -> List[PhotoInfo]:
        """
        Scan a directory for photos.

        Args:
            directory: Path to directory to scan
            recursive: Whether to scan subdirectories

        Returns:
            List of PhotoInfo objects
        """
        directory = Path(directory).expanduser().resolve()

        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        console.print(f"[bold blue]🔍 Scanning[/] {directory}...")

        # Find all image files
        image_files = list(self._find_images(directory, recursive))
        console.print(f"[green]Found {len(image_files)} images[/]")

        # Process each image
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Processing images...", total=len(image_files))

            for img_path in image_files:
                try:
                    photo = self._process_image(img_path)
                    if photo:
                        self.photos.append(photo)
                except Exception as e:
                    console.print(f"[yellow]⚠️  Skipped {img_path}: {e}[/]")
                finally:
                    progress.advance(task)

        console.print(f"[green]✅ Successfully processed {len(self.photos)} photos[/]")
        return self.photos

    def _find_images(
        self,
        directory: Path,
        recursive: bool
    ) -> Iterator[Path]:
        """Find all image files in directory."""
        if recursive:
            pattern = "**/*"
        else:
            pattern = "*"

        for path in directory.glob(pattern):
            if path.is_file() and path.suffix.lower() in SUPPORTED_FORMATS:
                if path.stat().st_size >= self.min_file_size:
                    yield path

    def _process_image(self, path: Path) -> Optional[PhotoInfo]:
        """Process a single image and generate hashes."""
        try:
            stat = path.stat()
            img = Image.open(path)

            # Convert to RGB if necessary (handles RGBA, grayscale, etc.)
            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')

            # Generate perceptual hashes
            phash = str(imagehash.phash(img, hash_size=self.hash_size))
            dhash = str(imagehash.dhash(img, hash_size=self.hash_size))
            ahash = str(imagehash.average_hash(img, hash_size=self.hash_size))

            return PhotoInfo(
                path=path,
                size=stat.st_size,
                hash_phash=phash,
                hash_dhash=dhash,
                hash_ahash=ahash,
                width=img.width,
                height=img.height,
                created_time=stat.st_ctime,
                modified_time=stat.st_mtime,
            )
        except Exception as e:
            raise RuntimeError(f"Failed to process image: {e}")

    def get_stats(self) -> Dict:
        """Get scanning statistics."""
        if not self.photos:
            return {}

        total_size = sum(p.size for p in self.photos)
        return {
            "total_photos": len(self.photos),
            "total_size_bytes": total_size,
            "total_size_human": self._human_size(total_size),
            "avg_size_human": self._human_size(total_size // len(self.photos)),
        }

    @staticmethod
    def _human_size(size: int) -> str:
        """Convert bytes to human-readable size."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size //= 1024
        return f"{size} PB"
