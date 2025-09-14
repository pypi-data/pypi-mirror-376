"""Command-line interface for Reaper Cleanup."""

import logging
import sys
from pathlib import Path
from typing import Optional

import click

from .core import MediaCleaner
from .config import MediaParsingConfig

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(message)s',  # Simple format for CLI output
        handlers=[logging.StreamHandler()]
    )


@click.command()
@click.argument('project_dir', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--dry-run', is_flag=True, help='Show what would be deleted without actually deleting')
@click.option('--auto-confirm', is_flag=True, help='Skip confirmation prompt and delete automatically')
@click.option('--media-dir', default='Media', help='Name of the media directory (default: Media)')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def cleanup(project_dir: str, dry_run: bool, auto_confirm: bool, media_dir: str, verbose: bool):
    """Clean up unused media files from Reaper projects.
    
    PROJECT_DIR should be the directory containing your .rpp files and Media folder.
    """
    # Setup logging first
    setup_logging(verbose)
    
    project_path = Path(project_dir).resolve()
    
    click.echo(f"🎵 Reaper Cleanup Tool")
    click.echo(f"📁 Project directory: {project_path}")
    click.echo()
    
    # Create parsing configuration
    parsing_config = MediaParsingConfig(media_dir_name=media_dir)
    
    # Initialize the media cleaner
    cleaner = MediaCleaner(project_path, parsing_config)
    
    # Check if Media directory exists
    if not cleaner.media_dir.exists():
        click.echo(f"❌ Media directory not found: {cleaner.media_dir}")
        click.echo("   Make sure you're running this in a directory that contains a 'Media' folder.")
        sys.exit(1)
    
    # Find unused files
    try:
        unused_files = cleaner.find_unused_media_files()
    except Exception as e:
        click.echo(f"❌ Error analyzing media files: {e}")
        sys.exit(1)
    
    if not unused_files:
        click.echo("✅ No unused media files found!")
        return
    
    # Display unused files
    click.echo(f"\n🗑️  Found {len(unused_files)} unused media file(s):")
    total_size = 0
    
    for file_path in sorted(unused_files):
        try:
            size = file_path.stat().st_size
            size_mb = size / (1024 * 1024)
            total_size += size
            relative_path = file_path.relative_to(project_path)
            click.echo(f"   - {relative_path} ({size_mb:.1f} MB)")
        except Exception as e:
            relative_path = file_path.relative_to(project_path)
            click.echo(f"   - {relative_path} (size unknown: {e})")
    
    total_size_mb = total_size / (1024 * 1024)
    click.echo(f"\n💾 Total size: {total_size_mb:.1f} MB")
    
    if dry_run:
        click.echo("\n🔍 Dry run mode - no files will be deleted.")
        return
    
    # Ask for confirmation
    if not auto_confirm:
        click.echo()
        if not click.confirm("⚠️  Are you sure you want to delete these files? This action cannot be undone!"):
            click.echo("❌ Operation cancelled.")
            return
    
    # Delete the files
    click.echo("\n🗑️  Deleting unused files...")
    success = cleaner.delete_unused_files(unused_files)
    
    if success:
        click.echo(f"\n✅ Successfully cleaned up {len(unused_files)} unused media files!")
        click.echo(f"💾 Freed up {total_size_mb:.1f} MB of disk space.")
    else:
        click.echo("\n⚠️  Some files could not be deleted. Check the output above for details.")
        sys.exit(1)


def main():
    """Entry point for the CLI application."""
    cleanup()


if __name__ == '__main__':
    main()
