"""
CLI Module

Command-line interface for AI Photo Dedup.
"""

import click
from pathlib import Path
from rich.console import Console
import yaml

from photo_dedup.scanner import PhotoScanner
from photo_dedup.deduplicator import Deduplicator
from photo_dedup.reporter import Reporter
from photo_dedup import __version__

console = Console()


@click.group()
@click.version_option(version=__version__)
def cli():
    """🤖 AI Photo Dedup - Smart Duplicate Photo Cleaner"""
    pass


@cli.command()
@click.argument('directory', type=click.Path(exists=True))
@click.option('--similarity', '-s', default=0.85, 
              help='Similarity threshold (0-1), default: 0.85')
@click.option('--report', '-r', type=click.Path(), 
              help='Output JSON report path')
@click.option('--format', '-f', type=click.Choice(['json', 'csv', 'html']), 
              default='json', help='Report format')
@click.option('--config', '-c', type=click.Path(exists=True),
              help='Configuration file (YAML)')
@click.option('--recursive/--no-recursive', default=True,
              help='Scan subdirectories')
@click.option('--min-size', default=1024, 
              help='Minimum file size in bytes')
def scan(directory, similarity, report, format, config, recursive, min_size):
    """Scan a directory for duplicate photos."""
    
    # Load config if provided
    cfg = {}
    if config:
        with open(config) as f:
            cfg = yaml.safe_load(f) or {}
    
    similarity = cfg.get('similarity_threshold', similarity)
    min_size = cfg.get('min_file_size', min_size)
    
    # Step 1: Scan photos
    scanner = PhotoScanner(min_file_size=min_size)
    photos = scanner.scan_directory(Path(directory), recursive=recursive)
    
    if not photos:
        console.print("[yellow]No photos found![/yellow]")
        return
    
    stats = scanner.get_stats()
    console.print(f"\n📊 Scan complete: {stats['total_photos']} photos, {stats['total_size_human']}")
    
    # Step 2: Find duplicates
    deduplicator = Deduplicator(similarity_threshold=similarity)
    groups = deduplicator.find_duplicates(photos)
    
    # Step 3: Generate report
    reporter = Reporter(groups)
    reporter.print_summary()
    
    # Export if requested
    if report:
        if format == 'json':
            reporter.export_json(Path(report))
        elif format == 'csv':
            reporter.export_csv(Path(report))
        elif format == 'html':
            reporter.generate_html_report(Path(report))


@cli.command()
@click.argument('report_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), 
              help='Output HTML report path')
def report(report_file, output):
    """Generate a report from a previous scan."""
    
    import json
    
    with open(report_file) as f:
        data = json.load(f)
    
    # Reconstruct groups (simplified - in production would use proper classes)
    # For now just display the stats
    console.print("[bold]📊 Report Summary[/bold]\n")
    console.print(f"Total Groups: {data['stats']['total_groups']}")
    console.print(f"Total Duplicates: {data['stats']['total_duplicates']}")
    console.print(f"Space Wasted: {data['stats']['potential_savings']}")
    
    if output:
        reporter = Reporter([])
        reporter.generate_html_report(Path(output))


@cli.command()
@click.argument('report_file', type=click.Path(exists=True))
@click.option('--keep', type=click.Choice(['newest', 'oldest', 'largest', 'smallest']),
              default='largest', help='Which to keep')
@click.option('--dry-run/--execute', default=True, help='Preview or execute')
def clean(report_file, keep, dry_run):
    """Clean duplicates based on a report."""
    
    import json
    
    with open(report_file) as f:
        data = json.load(f)
    
    mode = "Preview" if dry_run else "Deleting"
    console.print(f"[yellow]🔍 {mode} mode[/yellow]")
    
    deleted_count = 0
    space_freed = 0
    
    for group in data['groups']:
        # Keep first (recommended), delete rest
        to_delete = group['photos'][1:]
        
        for photo in to_delete:
            path = Path(photo['path'])
            if path.exists():
                if not dry_run:
                    path.unlink()
                deleted_count += 1
                space_freed += photo['size']
                console.print(f"{'Would delete' if dry_run else 'Deleted'}: {path.name}")
    
    console.print(f"\n[green]✅ Total: {deleted_count} files, {space_freed // (1024*1024)} MB freed[/green]")


@cli.command()
def version():
    """Show version information."""
    console.print(f"[bold]AI Photo Dedup[/bold] v{__version__}")
    console.print("🤖 Smart Duplicate Photo Cleaner")


def main():
    """Main entry point."""
    cli()


if __name__ == '__main__':
    main()
