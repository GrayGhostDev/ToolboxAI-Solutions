#!/usr/bin/env bash
# TODO Scanner - Comprehensive codebase TODO/FIXME/XXX discovery
# Usage: ./scripts/tools/todo-scan.sh [output_file]
#
# Scans the codebase for TODO, FIXME, XXX, and HACK comments
# Outputs a JSON catalog with proper escaping for automation consumption

set -euo pipefail

OUTPUT_FILE="${1:-docs/todos/todo-catalog.json}"
TEMP_FILE="${OUTPUT_FILE}.tmp"

echo "🔍 Scanning for TODO items across codebase..."

# Initialize Python script for JSON generation (handles escaping properly)
python3 << 'PYTHON_EOF' > "$TEMP_FILE"
import json
import os
import re
from pathlib import Path

def scan_for_todos(root_dir="."):
    """Scan codebase for TODO/FIXME/XXX/HACK comments"""
    
    todos = []
    id_counter = 1
    
    # Patterns to search for
    todo_patterns = re.compile(r'\b(TODO|FIXME|XXX|HACK)[:\s]+(.*?)$', re.IGNORECASE)
    
    # File extensions to scan
    code_extensions = {'.py', '.ts', '.tsx', '.js', '.jsx', '.lua', '.sh', '.bash', '.zsh'}
    doc_extensions = {'.md', '.rst', '.txt'}
    
    # Directories to exclude
    exclude_dirs = {
        'node_modules', 'venv', '.venv', 'dist', 'build', '.git',
        '__pycache__', '.pytest_cache', 'coverage', '.next',
        'Archive', 'worktree-tasks'
    }
    
    # Scan code files
    for ext in code_extensions:
        for file_path in Path(root_dir).rglob(f'*{ext}'):
            # Skip excluded directories
            if any(excluded in file_path.parts for excluded in exclude_dirs):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        match = todo_patterns.search(line)
                        if match:
                            tag, text = match.groups()
                            todos.append({
                                "id": f"todo-{id_counter:06d}",
                                "source": "code",
                                "file": str(file_path),
                                "line": line_num,
                                "tag": tag.upper(),
                                "text": line.strip()
                            })
                            id_counter += 1
            except Exception as e:
                print(f"Warning: Could not read {file_path}: {e}", file=sys.stderr)
    
    # Scan markdown documentation
    for file_path in Path(root_dir).rglob('*.md'):
        # Skip excluded directories
        if any(excluded in file_path.parts for excluded in exclude_dirs):
            continue
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    # Look for unchecked tasks or explicit TODO markers
                    if '- [ ]' in line or todo_patterns.search(line):
                        todos.append({
                            "id": f"md-{id_counter:06d}",
                            "source": "markdown-docs",
                            "file": str(file_path),
                            "line": line_num,
                            "tag": "TODO",
                            "text": line.strip()
                        })
                        id_counter += 1
        except Exception as e:
            print(f"Warning: Could not read {file_path}: {e}", file=sys.stderr)
    
    return todos

# Run scan
todos = scan_for_todos()

# Output as JSON
print(json.dumps(todos, indent=0))

PYTHON_EOF

# Check if generation succeeded
if [ $? -eq 0 ] && [ -f "$TEMP_FILE" ]; then
    # Validate JSON
    if python3 -c "import json; json.load(open('$TEMP_FILE'))" 2>/dev/null; then
        mv "$TEMP_FILE" "$OUTPUT_FILE"
        
        TOTAL=$(python3 -c "import json; print(len(json.load(open('$OUTPUT_FILE'))))")
        echo "✅ Scan complete! Found $TOTAL TODO items"
        echo "📄 Catalog saved to: $OUTPUT_FILE"
    else
        echo "❌ Generated JSON is invalid!"
        echo "Temporary file saved to: $TEMP_FILE"
        exit 1
    fi
else
    echo "❌ Scan failed!"
    exit 1
fi
