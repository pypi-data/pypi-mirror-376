# Reaper Cleanup

A CLI tool to clean up unused media files from Reaper projects. It covers the use case of having multiple projects in the same folder refering to the same medias (e.g., for version control). 

## Features

- Scans all Reaper project files (`.rpp`) in a given directory
- Identifies media files referenced in the projects
- Finds unused media files in the Media folder (configurable, type `reaper-cleanup --help`)
- Shows a list of files to be deleted and asks for confirmation
- Safely removes unused media files

## Installation

```bash
pip install -e .
```

## Usage

```bash
reaper-cleanup /path/to/your/reaper/project/folder
```

The tool will:

1. Scan all `.rpp` files in the specified folder
2. Check which media files are referenced
3. List all unused media files in the Media subfolder
4. Ask for confirmation before deletion
