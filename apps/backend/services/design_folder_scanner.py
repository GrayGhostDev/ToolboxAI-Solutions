"""
Design Folder Scanner

Scans and processes all files in the design folder, organizing them by type
and providing a comprehensive overview for chat processing.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import defaultdict
import json

from .design_file_converter import design_file_converter

logger = logging.getLogger(__name__)

class DesignFolderScanner:
    """Scans and organizes design folder contents for chat processing"""
    
    def __init__(self, design_root: str = "/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/design"):
        self.design_root = Path(design_root)
        self.file_categories = {
            'design_files': ['.fig', '.sketch', '.xd'],
            '3d_files': ['.blend', '.obj'],
            'images': ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'],
            'videos': ['.mp4', '.mov', '.avi'],
            'text_files': ['.txt', '.md'],
            'other': []
        }
    
    async def scan_design_folder(self, include_content: bool = True) -> Dict[str, Any]:
        """Scan the entire design folder and organize files by category"""
        if not self.design_root.exists():
            return {
                'success': False,
                'error': f'Design folder not found: {self.design_root}',
                'summary': {}
            }
        
        logger.info(f"Scanning design folder: {self.design_root}")
        
        # Initialize results
        results = {
            'success': True,
            'design_root': str(self.design_root),
            'summary': {
                'total_files': 0,
                'by_category': defaultdict(int),
                'by_folder': defaultdict(int),
                'processed_files': 0,
                'errors': 0
            },
            'categories': {
                'design_files': [],
                '3d_files': [],
                'images': [],
                'videos': [],
                'text_files': [],
                'other': []
            },
            'folder_structure': {},
            'file_contents': [] if include_content else None
        }
        
        # Scan all files
        for file_path in self.design_root.rglob('*'):
            if file_path.is_file():
                await self._process_file(file_path, results, include_content)
        
        # Convert defaultdict to regular dict for JSON serialization
        results['summary']['by_category'] = dict(results['summary']['by_category'])
        results['summary']['by_folder'] = dict(results['summary']['by_folder'])
        
        # Build folder structure
        results['folder_structure'] = self._build_folder_structure(self.design_root)
        
        logger.info(f"Scan complete: {results['summary']['total_files']} files processed")
        return results
    
    async def _process_file(self, file_path: Path, results: Dict[str, Any], include_content: bool):
        """Process a single file and add to results"""
        results['summary']['total_files'] += 1
        
        # Get relative path for organization
        try:
            relative_path = file_path.relative_to(self.design_root)
            folder_path = str(relative_path.parent) if relative_path.parent != Path('.') else 'root'
        except ValueError:
            folder_path = 'external'
            relative_path = file_path.name
        
        # Categorize file
        extension = file_path.suffix.lower()
        category = self._categorize_file(extension)
        
        # Add to category
        file_info = {
            'name': file_path.name,
            'path': str(relative_path),
            'full_path': str(file_path),
            'size': file_path.stat().st_size,
            'extension': extension,
            'folder': folder_path
        }
        
        results['categories'][category].append(file_info)
        results['summary']['by_category'][category] += 1
        results['summary']['by_folder'][folder_path] += 1
        
        # Process content if requested
        if include_content:
            try:
                content_result = await design_file_converter.process_design_file(file_path)
                if content_result['success']:
                    file_info['content'] = content_result['content']
                    file_info['processed'] = True
                    results['summary']['processed_files'] += 1
                    
                    # Add to file_contents for easy access
                    if results['file_contents'] is not None:
                        results['file_contents'].append({
                            'file': str(relative_path),
                            'category': category,
                            'content': content_result['content']
                        })
                else:
                    file_info['error'] = content_result['error']
                    file_info['processed'] = False
                    results['summary']['errors'] += 1
            except Exception as e:
                file_info['error'] = str(e)
                file_info['processed'] = False
                results['summary']['errors'] += 1
                logger.error(f"Error processing {file_path}: {e}")
    
    def _categorize_file(self, extension: str) -> str:
        """Categorize file based on extension"""
        for category, extensions in self.file_categories.items():
            if extension in extensions:
                return category
        return 'other'
    
    def _build_folder_structure(self, root_path: Path) -> Dict[str, Any]:
        """Build a tree structure of the folder"""
        structure = {}
        
        for item in root_path.iterdir():
            if item.is_dir():
                structure[item.name] = {
                    'type': 'folder',
                    'path': str(item.relative_to(self.design_root)),
                    'contents': self._build_folder_structure(item)
                }
            else:
                structure[item.name] = {
                    'type': 'file',
                    'path': str(item.relative_to(self.design_root)),
                    'size': item.stat().st_size,
                    'extension': item.suffix.lower()
                }
        
        return structure
    
    async def get_design_summary(self) -> str:
        """Get a human-readable summary of the design folder"""
        scan_result = await self.scan_design_folder(include_content=False)
        
        if not scan_result['success']:
            return f"Error scanning design folder: {scan_result['error']}"
        
        summary = scan_result['summary']
        categories = scan_result['categories']
        
        content = f"# Design Folder Summary\n\n"
        content += f"**Location:** {scan_result['design_root']}\n"
        content += f"**Total Files:** {summary['total_files']}\n\n"
        
        # Files by category
        content += "## Files by Category\n\n"
        for category, count in summary['by_category'].items():
            if count > 0:
                content += f"- **{category.replace('_', ' ').title()}:** {count} files\n"
        
        # Detailed breakdown
        content += "\n## Detailed Breakdown\n\n"
        
        for category, files in categories.items():
            if files:
                content += f"### {category.replace('_', ' ').title()}\n\n"
                
                # Group by folder
                by_folder = defaultdict(list)
                for file_info in files:
                    by_folder[file_info['folder']].append(file_info)
                
                for folder, folder_files in by_folder.items():
                    content += f"**{folder}:**\n"
                    for file_info in folder_files[:10]:  # Limit to first 10 files
                        size_mb = file_info['size'] / (1024 * 1024)
                        content += f"- {file_info['name']} ({size_mb:.2f} MB)\n"
                    
                    if len(folder_files) > 10:
                        content += f"- ... and {len(folder_files) - 10} more files\n"
                    content += "\n"
        
        return content
    
    async def search_design_files(self, query: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for files in the design folder"""
        scan_result = await self.scan_design_folder(include_content=False)
        
        if not scan_result['success']:
            return []
        
        results = []
        query_lower = query.lower()
        
        for cat, files in scan_result['categories'].items():
            if category and cat != category:
                continue
                
            for file_info in files:
                if (query_lower in file_info['name'].lower() or 
                    query_lower in file_info['path'].lower()):
                    results.append({
                        'file_info': file_info,
                        'category': cat,
                        'match_type': 'filename' if query_lower in file_info['name'].lower() else 'path'
                    })
        
        return results
    
    async def get_folder_contents(self, folder_path: str) -> Dict[str, Any]:
        """Get contents of a specific folder"""
        target_path = self.design_root / folder_path
        
        if not target_path.exists() or not target_path.is_dir():
            return {
                'success': False,
                'error': f'Folder not found: {folder_path}'
            }
        
        files = []
        folders = []
        
        for item in target_path.iterdir():
            if item.is_file():
                file_info = {
                    'name': item.name,
                    'path': str(item.relative_to(self.design_root)),
                    'size': item.stat().st_size,
                    'extension': item.suffix.lower(),
                    'category': self._categorize_file(item.suffix.lower())
                }
                files.append(file_info)
            elif item.is_dir():
                folders.append({
                    'name': item.name,
                    'path': str(item.relative_to(self.design_root))
                })
        
        return {
            'success': True,
            'folder_path': folder_path,
            'files': files,
            'folders': folders,
            'file_count': len(files),
            'folder_count': len(folders)
        }

# Global instance
design_folder_scanner = DesignFolderScanner()
