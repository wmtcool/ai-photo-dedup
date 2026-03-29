"""
Deduplicator Module

Finds and groups duplicate photos based on perceptual hash similarity.
"""

from typing import List, Dict, Set, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from collections import defaultdict
from scipy.spatial.distance import hamming
import numpy as np
from rich.console import Console
from rich.table import Table

from photo_dedup.scanner import PhotoInfo

console = Console()


@dataclass
class DuplicateGroup:
    """A group of similar photos."""
    photos: List[PhotoInfo] = field(default_factory=list)
    similarity: float = 0.0
    space_wasted: int = 0  # bytes

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "photos": [p.to_dict() for p in self.photos],
            "similarity": self.similarity,
            "space_wasted": self.space_wasted,
            "photo_count": len(self.photos),
        }


class Deduplicator:
    """Finds duplicate photos using hash similarity."""

    def __init__(self, similarity_threshold: float = 0.85):
        """
        Initialize deduplicator.

        Args:
            similarity_threshold: Minimum similarity (0-1) to consider as duplicate
        """
        self.similarity_threshold = similarity_threshold
        self.groups: List[DuplicateGroup] = []

    def find_duplicates(self, photos: List[PhotoInfo]) -> List[DuplicateGroup]:
        """
        Find duplicate groups among photos.

        Args:
            photos: List of PhotoInfo objects from scanner

        Returns:
            List of DuplicateGroup objects
        """
        console.print(f"[bold blue]🔍 Finding duplicates[/] (threshold: {self.similarity_threshold})")

        # Group photos by hash similarity
        visited: Set[int] = set()
        self.groups = []

        for i, photo in enumerate(photos):
            if i in visited:
                continue

            # Find all similar photos
            similar: List[Tuple[int, PhotoInfo, float]] = [(i, photo, 1.0)]

            for j, other in enumerate(photos[i + 1:], start=i + 1):
                if j in visited:
                    continue

                similarity = self._compute_similarity(photo, other)
                if similarity >= self.similarity_threshold:
                    similar.append((j, other, similarity))
                    visited.add(j)

            # If we found duplicates, create a group
            if len(similar) > 1:
                visited.add(i)
                group_photos = [s[1] for s in similar]
                avg_similarity = sum(s[2] for s in similar) / len(similar)

                # Calculate wasted space (all except the largest file)
                sorted_by_size = sorted(group_photos, key=lambda p: p.size, reverse=True)
                wasted = sum(p.size for p in sorted_by_size[1:])

                group = DuplicateGroup(
                    photos=sorted_by_size,
                    similarity=avg_similarity,
                    space_wasted=wasted,
                )
                self.groups.append(group)

        console.print(f"[green]✅ Found {len(self.groups)} duplicate groups[/]")
        return self.groups

    def _compute_similarity(self, p1: PhotoInfo, p2: PhotoInfo) -> float:
        """Compute similarity between two photos using multiple hashes."""
        similarities = []

        # Compare each hash type
        for hash_attr in ['hash_phash', 'hash_dhash', 'hash_ahash']:
            h1 = getattr(p1, hash_attr)
            h2 = getattr(p2, hash_attr)

            # Convert hex hash to binary array
            try:
                h1_bits = np.array([int(c, 16) for c in h1])
                h2_bits = np.array([int(c, 16) for c in h2])

                # Compute similarity (1 - hamming distance normalized)
                dist = hamming(h1_bits, h2_bits)
                similarities.append(1 - dist)
            except (ValueError, TypeError):
                continue

        # Return average similarity
        return sum(similarities) / len(similarities) if similarities else 0.0

    def get_stats(self) -> Dict:
        """Get deduplication statistics."""
        if not self.groups:
            return {
                "total_groups": 0,
                "total_duplicates": 0,
                "total_space_wasted": 0,
            }

        total_duplicates = sum(len(g.photos) - 1 for g in self.groups)
        total_wasted = sum(g.space_wasted for g in self.groups)

        return {
            "total_groups": len(self.groups),
            "total_duplicates": total_duplicates,
            "total_space_wasted": total_wasted,
            "total_space_wasted_human": self._human_size(total_wasted),
            "potential_savings_human": self._human_size(total_wasted),
        }

    def print_summary(self):
        """Print a summary table of duplicates."""
        table = Table(title="📊 Duplicate Photo Summary")

        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        stats = self.get_stats()
        table.add_row("Duplicate Groups", str(stats["total_groups"]))
        table.add_row("Total Duplicates", str(stats["total_duplicates"]))
        table.add_row("Space Wasted", stats.get("total_space_wasted_human", "0 B"))
        table.add_row("Potential Savings", stats.get("potential_savings_human", "0 B"))

        console.print(table)

    @staticmethod
    def _human_size(size: int) -> str:
        """Convert bytes to human-readable size."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size //= 1024
        return f"{size} PB"

    def recommend_which_to_keep(self, group: DuplicateGroup) -> PhotoInfo:
        """
        Recommend which photo to keep based on quality heuristics.

        Prioritizes:
        1. Largest file size (usually higher quality)
        2. Highest resolution
        3. Most recent modification time
        """
        return max(
            group.photos,
            key=lambda p: (p.size, p.width * p.height, p.modified_time)
        )
