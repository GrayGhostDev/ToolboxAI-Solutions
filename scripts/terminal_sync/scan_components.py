#!/usr/bin/env python3
"""
Scan and document React components from the dashboard
Extracts component information, props, and generates documentation
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

class ComponentDocScanner:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.components_path = self.project_root / "src" / "dashboard" / "src" / "components"
        self.docs_path = self.project_root / "Documentation" / "05-features" / "dashboard" / "components"
        self.components_data = []
        
    def scan_components(self):
        """Scan all React components in the dashboard"""
        print("🔍 Scanning React components...")
        
        # Ensure documentation directory exists
        self.docs_path.mkdir(parents=True, exist_ok=True)
        
        # Scan all component directories
        component_dirs = [
            "layout",
            "pages",
            "widgets",
            "admin",
            "analytics",
            "debug",
            "mcp",
            "progress",
            "reports"
        ]
        
        for dir_name in component_dirs:
            dir_path = self.components_path / dir_name
            if dir_path.exists():
                self.scan_directory(dir_path, dir_name)
        
        # Generate summary documentation
        self.generate_summary()
        
        return self.components_data
    
    def scan_directory(self, directory: Path, category: str):
        """Scan a directory for React components"""
        for file_path in directory.glob("*.tsx"):
            if file_path.name.endswith(".test.tsx") or file_path.name.endswith(".spec.tsx"):
                continue
                
            component_data = self.extract_component_info(file_path, category)
            if component_data:
                self.components_data.append(component_data)
                self.generate_component_doc(component_data)
    
    def extract_component_info(self, file_path: Path, category: str) -> Optional[Dict[str, Any]]:
        """Extract component information from a TypeScript file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            component_name = file_path.stem
            
            # Extract component type (functional/class)
            is_functional = "const " in content or "function " in content
            
            # Extract props interface
            props = self.extract_props(content, component_name)
            
            # Extract imports
            imports = self.extract_imports(content)
            
            # Extract hooks used
            hooks = self.extract_hooks(content)
            
            # Extract state management
            state_management = self.extract_state_management(content)
            
            # Extract description from comments
            description = self.extract_description(content)
            
            return {
                "name": component_name,
                "category": category,
                "file_path": str(file_path.relative_to(self.project_root)),
                "type": "functional" if is_functional else "class",
                "description": description,
                "props": props,
                "imports": imports,
                "hooks": hooks,
                "state_management": state_management,
                "examples": self.find_usage_examples(component_name)
            }
            
        except Exception as e:
            print(f"⚠️  Error processing {file_path}: {e}")
            return None
    
    def extract_props(self, content: str, component_name: str) -> List[Dict[str, str]]:
        """Extract props interface from TypeScript content"""
        props = []
        
        # Look for interface definition
        interface_pattern = rf'interface\s+{component_name}Props\s*\{{([^}}]+)\}}'
        match = re.search(interface_pattern, content, re.DOTALL)
        
        if not match:
            # Try type alias pattern
            type_pattern = rf'type\s+{component_name}Props\s*=\s*\{{([^}}]+)\}}'
            match = re.search(type_pattern, content, re.DOTALL)
        
        if match:
            props_content = match.group(1)
            # Parse individual props
            prop_lines = props_content.strip().split('\n')
            for line in prop_lines:
                line = line.strip()
                if line and not line.startswith('//'):
                    # Extract prop name and type
                    prop_match = re.match(r'(\w+)(\?)?:\s*(.+?)(?:;|$)', line)
                    if prop_match:
                        props.append({
                            "name": prop_match.group(1),
                            "type": prop_match.group(3).strip(),
                            "required": prop_match.group(2) != '?',
                            "description": ""  # Could extract from JSDoc comments
                        })
        
        return props
    
    def extract_imports(self, content: str) -> List[str]:
        """Extract import statements"""
        imports = []
        import_pattern = r'import\s+.*?\s+from\s+[\'"](.+?)[\'"]'
        matches = re.findall(import_pattern, content)
        for match in matches:
            if not match.startswith('.'):
                imports.append(match)
        return list(set(imports))
    
    def extract_hooks(self, content: str) -> List[str]:
        """Extract React hooks used in the component"""
        hooks = []
        hook_pattern = r'use[A-Z]\w+(?:\s*\(|\s*<)'
        matches = re.findall(hook_pattern, content)
        for match in matches:
            hook_name = match.split('(')[0].split('<')[0].strip()
            if hook_name not in hooks:
                hooks.append(hook_name)
        return hooks
    
    def extract_state_management(self, content: str) -> Dict[str, Any]:
        """Extract state management approach"""
        state_info = {
            "redux": False,
            "context": False,
            "local_state": False,
            "websocket": False
        }
        
        if "useSelector" in content or "useDispatch" in content:
            state_info["redux"] = True
        if "useContext" in content or "createContext" in content:
            state_info["context"] = True
        if "useState" in content:
            state_info["local_state"] = True
        if "WebSocket" in content or "socket" in content.lower():
            state_info["websocket"] = True
            
        return state_info
    
    def extract_description(self, content: str) -> str:
        """Extract component description from JSDoc comments"""
        # Look for JSDoc comment before component declaration
        jsdoc_pattern = r'/\*\*\s*\n\s*\*\s*(.+?)(?:\n|\*)'
        match = re.search(jsdoc_pattern, content)
        if match:
            return match.group(1).strip()
        return ""
    
    def find_usage_examples(self, component_name: str) -> List[str]:
        """Find usage examples of the component"""
        examples = []
        # This would search for component usage in other files
        # For now, return empty list
        return examples
    
    def generate_component_doc(self, component_data: Dict[str, Any]):
        """Generate markdown documentation for a component"""
        doc = [f"# {component_data['name']}\n"]
        
        if component_data['description']:
            doc.append(f"\n{component_data['description']}\n")
        
        doc.append(f"\n## Component Information\n")
        doc.append(f"- **Category**: {component_data['category']}\n")
        doc.append(f"- **Type**: {component_data['type']}\n")
        doc.append(f"- **File**: `{component_data['file_path']}`\n")
        
        if component_data['props']:
            doc.append(f"\n## Props\n\n")
            doc.append("| Prop | Type | Required | Description |\n")
            doc.append("|------|------|----------|-------------|\n")
            for prop in component_data['props']:
                required = "✅" if prop['required'] else "❌"
                doc.append(f"| {prop['name']} | `{prop['type']}` | {required} | {prop['description']} |\n")
        
        if component_data['hooks']:
            doc.append(f"\n## Hooks Used\n")
            for hook in component_data['hooks']:
                doc.append(f"- `{hook}`\n")
        
        if component_data['state_management']:
            doc.append(f"\n## State Management\n")
            state_info = component_data['state_management']
            if state_info['redux']:
                doc.append("- Redux state management\n")
            if state_info['context']:
                doc.append("- React Context API\n")
            if state_info['local_state']:
                doc.append("- Local component state\n")
            if state_info['websocket']:
                doc.append("- WebSocket connections\n")
        
        if component_data['imports']:
            doc.append(f"\n## Key Dependencies\n")
            for imp in sorted(component_data['imports'])[:10]:  # Top 10 imports
                doc.append(f"- `{imp}`\n")
        
        # Write documentation file
        doc_file = self.docs_path / f"{component_data['name']}.md"
        with open(doc_file, 'w') as f:
            f.write(''.join(doc))
        
        print(f"✅ Generated documentation for {component_data['name']}")
    
    def generate_summary(self):
        """Generate summary documentation for all components"""
        summary = ["# React Components Documentation\n"]
        summary.append(f"\nGenerated: {datetime.now().isoformat()}\n")
        summary.append(f"Total Components: {len(self.components_data)}\n\n")
        
        # Group by category
        by_category = {}
        for comp in self.components_data:
            category = comp['category']
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(comp)
        
        # Generate table of contents
        summary.append("## Table of Contents\n\n")
        for category in sorted(by_category.keys()):
            summary.append(f"- [{category.title()}](#{category})\n")
        
        # Generate category sections
        for category in sorted(by_category.keys()):
            summary.append(f"\n## {category.title()}\n\n")
            summary.append("| Component | Type | Props | Hooks | State Management |\n")
            summary.append("|-----------|------|-------|-------|------------------|\n")
            
            for comp in sorted(by_category[category], key=lambda x: x['name']):
                props_count = len(comp['props'])
                hooks_count = len(comp['hooks'])
                state_types = [k for k, v in comp['state_management'].items() if v]
                state_str = ', '.join(state_types) if state_types else 'None'
                
                summary.append(f"| [{comp['name']}](./{comp['name']}.md) | {comp['type']} | {props_count} | {hooks_count} | {state_str} |\n")
        
        # Statistics
        summary.append("\n## Statistics\n\n")
        total_functional = sum(1 for c in self.components_data if c['type'] == 'functional')
        total_class = len(self.components_data) - total_functional
        
        summary.append(f"- **Total Components**: {len(self.components_data)}\n")
        summary.append(f"- **Functional Components**: {total_functional}\n")
        summary.append(f"- **Class Components**: {total_class}\n")
        summary.append(f"- **Categories**: {len(by_category)}\n")
        
        # Save summary
        summary_file = self.docs_path / "README.md"
        with open(summary_file, 'w') as f:
            f.write(''.join(summary))
        
        print(f"✅ Generated components summary at {summary_file}")
        
        # Save JSON data for other tools
        json_file = self.docs_path / "components.json"
        with open(json_file, 'w') as f:
            json.dump(self.components_data, f, indent=2)
        
        print(f"✅ Saved component data to {json_file}")


def main():
    """Main execution"""
    scanner = ComponentDocScanner()
    components = scanner.scan_components()
    
    print(f"\n✨ Successfully documented {len(components)} React components!")
    
    # Print statistics
    categories = {}
    for comp in components:
        cat = comp['category']
        categories[cat] = categories.get(cat, 0) + 1
    
    print("\n📊 Components by category:")
    for cat, count in sorted(categories.items()):
        print(f"  - {cat}: {count}")


if __name__ == "__main__":
    main()