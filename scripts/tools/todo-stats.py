#!/usr/bin/env python3
"""
TODO Catalog Statistics and Analysis
Usage: python3 scripts/tools/todo-stats.py [catalog_file]

Analyzes the TODO catalog and generates comprehensive statistics
for tracking progress and prioritizing work.
"""

import json
import sys
from collections import defaultdict
from pathlib import Path


def analyze_catalog(catalog_path: str = "docs/todos/todo-catalog.json"):
    """Analyze TODO catalog and generate statistics"""
    
    try:
        with open(catalog_path) as f:
            todos = json.load(f)
    except FileNotFoundError:
        print(f"❌ Catalog file not found: {catalog_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in catalog: {e}")
        sys.exit(1)
    
    # Statistics
    by_source = defaultdict(int)
    by_tag = defaultdict(int)
    by_extension = defaultdict(int)
    by_directory = defaultdict(int)
    by_component = defaultdict(int)
    
    for todo in todos:
        by_source[todo['source']] += 1
        by_tag[todo['tag']] += 1
        
        file_path = Path(todo['file'])
        ext = file_path.suffix or 'no_extension'
        by_extension[ext] += 1
        
        # Get top-level directory
        parts = file_path.parts
        dir_name = parts[0] if parts else 'root'
        by_directory[dir_name] += 1
        
        # Categorize by component
        if 'apps/backend' in str(file_path):
            by_component['backend'] += 1
        elif 'apps/dashboard' in str(file_path):
            by_component['frontend'] += 1
        elif 'roblox' in str(file_path):
            by_component['roblox'] += 1
        elif 'docs' in str(file_path):
            by_component['documentation'] += 1
        elif '.github' in str(file_path):
            by_component['ci-cd'] += 1
        elif 'scripts' in str(file_path):
            by_component['scripts'] += 1
        else:
            by_component['other'] += 1
    
    # Print report
    print(f"\n{'=' * 70}")
    print(f"📊 TODO CATALOG STATISTICS")
    print(f"{'=' * 70}")
    print(f"\n📈 Total Items: {len(todos)}")
    
    print(f"\n📁 By Source:")
    for source, count in sorted(by_source.items(), key=lambda x: x[1], reverse=True):
        pct = (count / len(todos)) * 100
        print(f"  {source:20s}: {count:5d} ({pct:5.1f}%)")
    
    print(f"\n🏷️  By Tag:")
    for tag, count in sorted(by_tag.items(), key=lambda x: x[1], reverse=True):
        pct = (count / len(todos)) * 100
        print(f"  {tag:20s}: {count:5d} ({pct:5.1f}%)")
    
    print(f"\n📄 By File Type (Top 10):")
    for ext, count in sorted(by_extension.items(), key=lambda x: x[1], reverse=True)[:10]:
        pct = (count / len(todos)) * 100
        print(f"  {ext:20s}: {count:5d} ({pct:5.1f}%)")
    
    print(f"\n📂 By Directory (Top 10):")
    for dir_name, count in sorted(by_directory.items(), key=lambda x: x[1], reverse=True)[:10]:
        pct = (count / len(todos)) * 100
        print(f"  {dir_name:20s}: {count:5d} ({pct:5.1f}%)")
    
    print(f"\n🧩 By Component:")
    for component, count in sorted(by_component.items(), key=lambda x: x[1], reverse=True):
        pct = (count / len(todos)) * 100
        print(f"  {component:20s}: {count:5d} ({pct:5.1f}%)")
    
    # Agent assignment recommendations
    print(f"\n{'=' * 70}")
    print(f"🤖 RECOMMENDED AGENT ASSIGNMENTS")
    print(f"{'=' * 70}")
    
    print(f"\n@copilot (Code Implementation):")
    code_items = sum([
        by_extension.get('.py', 0),
        by_extension.get('.ts', 0),
        by_extension.get('.tsx', 0),
        by_extension.get('.js', 0),
        by_extension.get('.jsx', 0),
        by_extension.get('.lua', 0)
    ])
    print(f"  Total Code Items: {code_items}")
    print(f"    - Python (.py): {by_extension.get('.py', 0)}")
    print(f"    - TypeScript (.ts/.tsx): {by_extension.get('.ts', 0) + by_extension.get('.tsx', 0)}")
    print(f"    - Lua (.lua): {by_extension.get('.lua', 0)}")
    print(f"    - JavaScript (.js/.jsx): {by_extension.get('.js', 0) + by_extension.get('.jsx', 0)}")
    
    print(f"\n@claude (Documentation):")
    doc_items = by_extension.get('.md', 0) + by_extension.get('.rst', 0)
    print(f"  Total Documentation Items: {doc_items}")
    print(f"    - Markdown (.md): {by_extension.get('.md', 0)}")
    print(f"    - RestructuredText (.rst): {by_extension.get('.rst', 0)}")
    
    print(f"\n@coderabbit (Security/Quality):")
    quality_items = by_tag.get('FIXME', 0) + by_tag.get('HACK', 0)
    print(f"  Total Quality Items: {quality_items}")
    print(f"    - FIXME tags: {by_tag.get('FIXME', 0)}")
    print(f"    - HACK tags: {by_tag.get('HACK', 0)}")
    
    print(f"\n@sentry (Error Handling):")
    # Count items with error-related keywords
    error_keywords = ['error', 'exception', 'logging', 'monitoring', 'trace']
    error_items = sum(1 for todo in todos if any(kw in todo['text'].lower() for kw in error_keywords))
    print(f"  Error Handling Items: {error_items}")
    
    print(f"\n@openai (AI/ML Tasks):")
    # Count items in AI-related directories
    ai_items = sum(1 for todo in todos if 'agents' in todo['file'].lower() or 'langchain' in todo['file'].lower())
    print(f"  AI/ML Items: {ai_items}")
    
    print(f"\n{'=' * 70}")
    print(f"💡 PRIORITY RECOMMENDATIONS")
    print(f"{'=' * 70}")
    
    # Calculate priority scores
    high_priority = by_tag.get('FIXME', 0) + by_tag.get('HACK', 0)
    medium_priority = by_tag.get('TODO', 0)
    low_priority = by_tag.get('XXX', 0)
    
    print(f"\n🔴 High Priority (FIXME/HACK): {high_priority} items")
    print(f"  → Immediate attention required")
    print(f"\n🟡 Medium Priority (TODO): {medium_priority} items")
    print(f"  → Plan for implementation")
    print(f"\n🟢 Low Priority (XXX): {low_priority} items")
    print(f"  → Review and document")
    
    print(f"\n{'=' * 70}\n")


if __name__ == "__main__":
    catalog_file = sys.argv[1] if len(sys.argv) > 1 else "docs/todos/todo-catalog.json"
    analyze_catalog(catalog_file)
