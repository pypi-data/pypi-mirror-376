"""Configuration dataclasses for Reaper Cleanup."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Set


@dataclass
class MediaParsingConfig:
    """Configuration for parsing media references from Reaper projects."""
    
    # File extensions to consider as media files
    media_extensions: Set[str] = field(default_factory=lambda: {
        '.wav', '.mp3', '.flac', '.aif', '.aiff', '.m4a', '.ogg', '.wma'
    })
    
    # File encoding settings
    file_encoding: str = "utf-8"
    encoding_errors: str = "ignore"
    
    # Media directory name
    media_dir_name: str = "Media"
    
    def get_media_dir(self, project_dir: Path) -> Path:
        """Get the media directory path for a given project directory."""
        return project_dir / self.media_dir_name
    
    @property
    def media_patterns(self) -> List[str]:
        """Get regex patterns for finding media file references in .rpp files."""
        # Build extension pattern from configured extensions
        ext_pattern = '|'.join(ext.lstrip('.') for ext in self.media_extensions)
        
        return [
            # SOURCE WAV pattern
            r'SOURCE WAV\s*\n\s*FILE\s+"([^"]+)"',
            # SOURCE MIDI pattern  y<x
            r'SOURCE MIDI\s+"([^"]+)"',
            # TAKE pattern
            r'<TAKE[^>]*>\s*\n[^<]*FILE\s+"([^"]+)"',
            # Direct file references with media extensions
            f'FILE\\s+"([^"]+\\.(?:{ext_pattern}))"',
            # Source file pattern
            r'<SOURCE[^>]*>\s*\n[^<]*FILE\s+"([^"]+)"',
        ]
    
    @property
    def media_ref_pattern(self) -> str:
        """Get pattern for relative media references."""
        # Build extension pattern from configured extensions
        ext_pattern = '|'.join(ext.lstrip('.') for ext in self.media_extensions)
        return f'(?:{self.media_dir_name}[/\\\\])?([^/\\\\\"\\s]+\\.(?:{ext_pattern}))'
