"""
Reporter Module

Generates reports and exports deduplication results.
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from datetime import datetime

from photo_dedup.deduplicator import DuplicateGroup

console = Console()


class Reporter:
    """Generates reports from deduplication results."""

    def __init__(self, groups: List[DuplicateGroup]):
        self.groups = groups
        self.stats = self._compute_stats()

    def _compute_stats(self) -> Dict:
        """Compute overall statistics."""
        total_duplicates = sum(len(g.photos) - 1 for g in self.groups)
        total_wasted = sum(g.space_wasted for g in self.groups)

        return {
            "total_groups": len(self.groups),
            "total_duplicates": total_duplicates,
            "total_space_wasted": total_wasted,
            "potential_savings": self._human_size(total_wasted),
            "generated_at": datetime.now().isoformat(),
        }

    def export_json(self, output_path: Path) -> Path:
        """Export results to JSON."""
        data = {
            "stats": self.stats,
            "groups": [g.to_dict() for g in self.groups],
        }

        output_path = Path(output_path)
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        console.print(f"[green]✅ Exported to {output_path}[/]")
        return output_path

    def export_csv(self, output_path: Path) -> Path:
        """Export results to CSV."""
        import csv

        output_path = Path(output_path)
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'group_id',
                'similarity',
                'path',
                'size',
                'width',
                'height',
                'is_recommended',
            ])

            for gid, group in enumerate(self.groups, 1):
                for i, photo in enumerate(group.photos):
                    writer.writerow([
                        gid,
                        f"{group.similarity:.2%}",
                        str(photo.path),
                        photo.size,
                        photo.width,
                        photo.height,
                        i == 0,  # First photo is recommended to keep
                    ])

        console.print(f"[green]✅ Exported to {output_path}[/]")
        return output_path

    def generate_html_report(self, output_path: Path) -> Path:
        """Generate an HTML report."""
        html = self._build_html_report()

        output_path = Path(output_path)
        with open(output_path, 'w') as f:
            f.write(html)

        console.print(f"[green]✅ HTML report: {output_path}[/]")
        return output_path

    def _build_html_report(self) -> str:
        """Build HTML report content."""
        groups_html = ""

        for gid, group in enumerate(self.groups[:20], 1):  # Limit to 20 groups
            photos_html = ""
            for i, photo in enumerate(group.photos):
                recommended = "✅ RECOMMENDED" if i == 0 else "❌ Duplicate"
                photos_html += f"""
                <div class="photo">
                    <div class="path">{photo.path}</div>
                    <div class="meta">
                        <span>Size: {self._human_size(photo.size)}</span>
                        <span>Resolution: {photo.width}x{photo.height}</span>
                        <span>{recommended}</span>
                    </div>
                </div>
                """

            groups_html += f"""
            <div class="group">
                <h3>Group #{gid} (Similarity: {group.similarity:.1%})</h3>
                <p>Space wasted: {self._human_size(group.space_wasted)}</p>
                {photos_html}
            </div>
            """

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Photo Dedup Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
               max-width: 900px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
        h1 {{ color: #333; }}
        .stats {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 20px 0; }}
        .stat-card {{ background: white; padding: 20px; border-radius: 10px; 
                     box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }}
        .stat-value {{ font-size: 2em; font-weight: bold; color: #4CAF50; }}
        .stat-label {{ color: #666; }}
        .group {{ background: white; padding: 20px; margin: 20px 0; 
                 border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .photo {{ padding: 10px; margin: 10px 0; background: #f9f9f9; border-radius: 5px; }}
        .path {{ font-family: monospace; word-break: break-all; }}
        .meta {{ display: flex; gap: 15px; margin-top: 5px; color: #666; font-size: 0.9em; }}
    </style>
</head>
<body>
    <h1>🤖 AI Photo Dedup Report</h1>
    <p>Generated: {self.stats['generated_at']}</p>

    <div class="stats">
        <div class="stat-card">
            <div class="stat-value">{self.stats['total_groups']}</div>
            <div class="stat-label">Duplicate Groups</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{self.stats['total_duplicates']}</div>
            <div class="stat-label">Total Duplicates</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{self.stats['potential_savings']}</div>
            <div class="stat-label">Space Wasted</div>
        </div>
    </div>

    {groups_html}
</body>
</html>"""

    def print_summary(self):
        """Print a text summary to console."""
        table = Table(title="📊 AI Photo Dedup Summary")

        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Duplicate Groups", str(self.stats["total_groups"]))
        table.add_row("Total Duplicates", str(self.stats["total_duplicates"]))
        table.add_row("Space Wasted", self.stats["potential_savings"])

        console.print(table)

        # Show top groups
        if self.groups:
            console.print("\n[bold]Top 5 Duplicate Groups:[/bold]")
            top_groups = sorted(self.groups, key=lambda g: g.space_wasted, reverse=True)[:5]

            for gid, group in enumerate(top_groups, 1):
                console.print(f"\n[cyan]Group #{gid}[/cyan] (Similarity: {group.similarity:.1%})")
                for i, photo in enumerate(group.photos):
                    recommended = "✅" if i == 0 else "❌"
                    console.print(f"  {recommended} {photo.path.name} ({self._human_size(photo.size)})")

    @staticmethod
    def _human_size(size: int) -> str:
        """Convert bytes to human-readable size."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size //= 1024
        return f"{size} PB"
