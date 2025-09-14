"""Core functionality for parsing Reaper projects and finding media files."""

import logging
import os
import re
from pathlib import Path
from typing import Set, List

from .config import MediaParsingConfig

logger = logging.getLogger(__name__)


class ReaperProject:
    """Represents a Reaper project and its media references."""
    
    def __init__(self, project_path: Path, parsing_config: MediaParsingConfig = None):
        self.project_path = project_path
        self.media_files: Set[str] = set()
        self.parsing_config = parsing_config or MediaParsingConfig()
    def parse_media_references(self) -> Set[str]:
        """Parse the .rpp file and extract media file references."""
        try:
            with open(
                self.project_path, 
                'r', 
                encoding=self.parsing_config.file_encoding,
                errors=self.parsing_config.encoding_errors
            ) as f:
                content = f.read()
                
            found_files = set()
            
            # Use configured media patterns
            for pattern in self.parsing_config.media_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    file_path = match.group(1)
                    # Convert to relative path and normalize
                    file_path = os.path.normpath(file_path)
                    
                    # Extract just the filename if it's a full path
                    if os.path.sep in file_path or '/' in file_path:
                        file_path = os.path.basename(file_path)
                    
                    found_files.add(file_path)
            
            # Also look for any file references that might be relative paths
            # Use configured media reference pattern
            matches = re.finditer(self.parsing_config.media_ref_pattern, content, re.IGNORECASE)
            for match in matches:
                filename = match.group(1)
                found_files.add(filename)
            
            self.media_files = found_files
            return found_files
            
        except Exception as e:
            logger.warning(f"Could not parse {self.project_path}: {e}")
            return set()


class MediaCleaner:
    """Handles cleanup of unused media files."""
    
    def __init__(self, project_dir: Path, parsing_config: MediaParsingConfig = None):
        self.project_dir = project_dir
        self.parsing_config = parsing_config or MediaParsingConfig()
        self.media_dir = self.parsing_config.get_media_dir(project_dir)
        
    def find_reaper_projects(self) -> List[ReaperProject]:
        """Find all .rpp files in the project directory."""
        rpp_files = list(self.project_dir.glob("*.rpp"))
        return [ReaperProject(rpp_file, self.parsing_config) for rpp_file in rpp_files]
    
    def get_referenced_media_files(self) -> Set[str]:
        """Get all media files referenced across all Reaper projects."""
        projects = self.find_reaper_projects()
        all_referenced = set()
        
        logger.info(f"Found {len(projects)} Reaper project(s):")
        for project in projects:
            logger.info(f"  - {project.project_path.name}")
            referenced = project.parse_media_references()
            all_referenced.update(referenced)
            logger.info(f"    References {len(referenced)} media file(s)")
            
        return all_referenced
    
    def get_media_files_on_disk(self) -> Set[str]:
        """Get all media files present in the Media directory."""
        if not self.media_dir.exists():
            logger.error(f"Media directory not found: {self.media_dir}")
            return set()
            
        media_files = set()
        
        for file_path in self.media_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in self.parsing_config.media_extensions:
                media_files.add(file_path.name)
                
        return media_files
    
    def find_unused_media_files(self) -> List[Path]:
        """Find media files that are not referenced in any project."""
        referenced_files = self.get_referenced_media_files()
        disk_files = self.get_media_files_on_disk()
        
        logger.info(f"\nMedia files analysis:")
        logger.info(f"  - Files on disk: {len(disk_files)}")
        logger.info(f"  - Files referenced in projects: {len(referenced_files)}")
        
        # Find files that exist on disk but are not referenced
        unused_filenames = disk_files - referenced_files
        
        # Get full paths for unused files
        unused_files = []
        for filename in unused_filenames:
            # Find the actual file path (could be in subdirectories)
            for file_path in self.media_dir.rglob(filename):
                if file_path.is_file():
                    unused_files.append(file_path)
                    break
                    
        return unused_files
    
    def delete_unused_files(self, files_to_delete: List[Path]) -> bool:
        """Delete the specified files."""
        deleted_count = 0
        failed_count = 0
        
        for file_path in files_to_delete:
            try:
                file_path.unlink()
                logger.info(f"✓ Deleted: {file_path.relative_to(self.project_dir)}")
                deleted_count += 1
            except Exception as e:
                logger.error(f"✗ Failed to delete {file_path.relative_to(self.project_dir)}: {e}")
                failed_count += 1
                
        logger.info(f"\nDeletion summary:")
        logger.info(f"  - Successfully deleted: {deleted_count} files")
        if failed_count > 0:
            logger.warning(f"  - Failed to delete: {failed_count} files")
            
        return failed_count == 0
