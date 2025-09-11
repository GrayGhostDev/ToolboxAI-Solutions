#!/usr/bin/env python3
"""
Generate comprehensive database schema documentation
Creates ERDs and detailed schema documentation for all databases
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import subprocess

class DatabaseDocGenerator:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.schemas = {
            'educational_platform': self.project_root / 'database' / 'schemas' / '01_core_schema.sql',
            'dashboard': self.project_root / 'database' / 'schemas' / '05_dashboard_schema.sql',
        }
        self.docs_path = self.project_root / 'Documentation' / '02-architecture' / 'data-models'
        self.tables_data = {}
        
    def generate_all_docs(self):
        """Generate documentation for all database schemas"""
        print("📚 Starting database schema documentation generation...")
        
        # Ensure documentation directory exists
        self.docs_path.mkdir(parents=True, exist_ok=True)
        
        # Process each schema
        for db_name, schema_path in self.schemas.items():
            if schema_path.exists():
                print(f"\n🔍 Processing {db_name} schema...")
                self.process_schema(db_name, schema_path)
            else:
                print(f"⚠️  Schema file not found: {schema_path}")
        
        # Generate combined ERD
        self.generate_combined_erd()
        
        # Generate summary documentation
        self.generate_summary()
        
        return self.tables_data
    
    def process_schema(self, db_name: str, schema_path: Path):
        """Process a single schema file"""
        with open(schema_path, 'r') as f:
            schema_content = f.read()
        
        # Parse tables from SQL
        tables = self.parse_sql_schema(schema_content)
        self.tables_data[db_name] = tables
        
        # Generate documentation
        self.generate_schema_docs(db_name, tables)
        
        # Generate PlantUML ERD
        self.generate_plantuml_erd(db_name, tables)
        
        print(f"✅ Documented {len(tables)} tables for {db_name}")
    
    def parse_sql_schema(self, sql_content: str) -> Dict[str, Any]:
        """Parse SQL schema to extract table definitions"""
        tables = {}
        
        # Remove comments
        sql_content = re.sub(r'--.*$', '', sql_content, flags=re.MULTILINE)
        sql_content = re.sub(r'/\*.*?\*/', '', sql_content, flags=re.DOTALL)
        
        # Find CREATE TABLE statements
        table_pattern = r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(["\w\.]+)\s*\((.*?)\);'
        matches = re.findall(table_pattern, sql_content, re.IGNORECASE | re.DOTALL)
        
        for table_name, table_body in matches:
            # Clean table name
            table_name = table_name.strip('"').split('.')[-1]
            
            # Parse columns
            columns = self.parse_columns(table_body)
            
            # Parse constraints
            constraints = self.parse_constraints(table_body)
            
            tables[table_name] = {
                'columns': columns,
                'constraints': constraints,
                'indexes': self.find_indexes(sql_content, table_name),
                'foreign_keys': self.extract_foreign_keys(constraints)
            }
        
        return tables
    
    def parse_columns(self, table_body: str) -> List[Dict[str, Any]]:
        """Parse column definitions from CREATE TABLE body"""
        columns = []
        lines = table_body.split(',')
        
        for line in lines:
            line = line.strip()
            
            # Skip constraint lines
            if any(keyword in line.upper() for keyword in ['PRIMARY KEY', 'FOREIGN KEY', 'UNIQUE', 'CHECK', 'CONSTRAINT']):
                continue
            
            # Parse column
            col_match = re.match(r'(["\w]+)\s+(\w+(?:\([^)]+\))?)\s*(.*)', line)
            if col_match:
                col_name = col_match.group(1).strip('"')
                col_type = col_match.group(2)
                col_modifiers = col_match.group(3) if col_match.group(3) else ''
                
                columns.append({
                    'name': col_name,
                    'type': col_type,
                    'nullable': 'NOT NULL' not in col_modifiers.upper(),
                    'primary_key': 'PRIMARY KEY' in col_modifiers.upper(),
                    'unique': 'UNIQUE' in col_modifiers.upper(),
                    'default': self.extract_default(col_modifiers),
                    'references': self.extract_references(col_modifiers)
                })
        
        return columns
    
    def parse_constraints(self, table_body: str) -> List[Dict[str, Any]]:
        """Parse table constraints"""
        constraints = []
        
        # Find PRIMARY KEY constraints
        pk_pattern = r'(?:CONSTRAINT\s+(\w+)\s+)?PRIMARY\s+KEY\s*\(([^)]+)\)'
        for match in re.finditer(pk_pattern, table_body, re.IGNORECASE):
            constraints.append({
                'type': 'PRIMARY KEY',
                'name': match.group(1) if match.group(1) else 'PRIMARY',
                'columns': [col.strip().strip('"') for col in match.group(2).split(',')]
            })
        
        # Find FOREIGN KEY constraints
        fk_pattern = r'(?:CONSTRAINT\s+(\w+)\s+)?FOREIGN\s+KEY\s*\(([^)]+)\)\s+REFERENCES\s+(["\w\.]+)\s*\(([^)]+)\)'
        for match in re.finditer(fk_pattern, table_body, re.IGNORECASE):
            constraints.append({
                'type': 'FOREIGN KEY',
                'name': match.group(1) if match.group(1) else f'FK_{match.group(2)}',
                'columns': [col.strip().strip('"') for col in match.group(2).split(',')],
                'ref_table': match.group(3).strip('"').split('.')[-1],
                'ref_columns': [col.strip().strip('"') for col in match.group(4).split(',')]
            })
        
        # Find UNIQUE constraints
        unique_pattern = r'(?:CONSTRAINT\s+(\w+)\s+)?UNIQUE\s*\(([^)]+)\)'
        for match in re.finditer(unique_pattern, table_body, re.IGNORECASE):
            constraints.append({
                'type': 'UNIQUE',
                'name': match.group(1) if match.group(1) else f'UQ_{match.group(2)}',
                'columns': [col.strip().strip('"') for col in match.group(2).split(',')]
            })
        
        return constraints
    
    def find_indexes(self, sql_content: str, table_name: str) -> List[Dict[str, Any]]:
        """Find indexes for a specific table"""
        indexes = []
        
        # Find CREATE INDEX statements
        index_pattern = rf'CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)\s+ON\s+{table_name}\s*\(([^)]+)\)'
        for match in re.finditer(index_pattern, sql_content, re.IGNORECASE):
            indexes.append({
                'name': match.group(1),
                'columns': [col.strip().strip('"') for col in match.group(2).split(',')],
                'unique': 'UNIQUE' in match.group(0).upper()
            })
        
        return indexes
    
    def extract_foreign_keys(self, constraints: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract foreign key relationships from constraints"""
        foreign_keys = []
        for constraint in constraints:
            if constraint['type'] == 'FOREIGN KEY':
                foreign_keys.append({
                    'columns': constraint['columns'],
                    'ref_table': constraint['ref_table'],
                    'ref_columns': constraint['ref_columns']
                })
        return foreign_keys
    
    def extract_default(self, modifiers: str) -> Optional[str]:
        """Extract default value from column modifiers"""
        default_match = re.search(r'DEFAULT\s+([^\s,]+)', modifiers, re.IGNORECASE)
        if default_match:
            return default_match.group(1)
        return None
    
    def extract_references(self, modifiers: str) -> Optional[Dict[str, str]]:
        """Extract REFERENCES clause from column modifiers"""
        ref_match = re.search(r'REFERENCES\s+(["\w\.]+)\s*\(([^)]+)\)', modifiers, re.IGNORECASE)
        if ref_match:
            return {
                'table': ref_match.group(1).strip('"').split('.')[-1],
                'column': ref_match.group(2).strip('"')
            }
        return None
    
    def generate_schema_docs(self, db_name: str, tables: Dict[str, Any]):
        """Generate markdown documentation for schema"""
        doc = [f"# {db_name.replace('_', ' ').title()} Database Schema\n"]
        doc.append(f"\nGenerated: {datetime.now().isoformat()}\n")
        doc.append(f"Total Tables: {len(tables)}\n\n")
        
        # Table of contents
        doc.append("## Table of Contents\n\n")
        for table_name in sorted(tables.keys()):
            doc.append(f"- [{table_name}](#{table_name})\n")
        
        # Detailed table documentation
        for table_name in sorted(tables.keys()):
            table_data = tables[table_name]
            doc.append(f"\n## {table_name}\n\n")
            
            # Columns
            doc.append("### Columns\n\n")
            doc.append("| Column | Type | Nullable | Default | Description |\n")
            doc.append("|--------|------|----------|---------|-------------|\n")
            
            for column in table_data['columns']:
                nullable = "Yes" if column['nullable'] else "No"
                default = column['default'] if column['default'] else "-"
                
                # Add indicators for special columns
                indicators = []
                if column['primary_key']:
                    indicators.append("PK")
                if column['unique']:
                    indicators.append("UQ")
                if column['references']:
                    indicators.append(f"FK→{column['references']['table']}")
                
                indicator_str = f" ({', '.join(indicators)})" if indicators else ""
                
                doc.append(f"| {column['name']}{indicator_str} | {column['type']} | {nullable} | {default} | |\n")
            
            # Indexes
            if table_data['indexes']:
                doc.append("\n### Indexes\n\n")
                for index in table_data['indexes']:
                    unique_str = " (UNIQUE)" if index['unique'] else ""
                    columns_str = ', '.join(index['columns'])
                    doc.append(f"- **{index['name']}**{unique_str}: {columns_str}\n")
            
            # Foreign Keys
            if table_data['foreign_keys']:
                doc.append("\n### Foreign Keys\n\n")
                for fk in table_data['foreign_keys']:
                    columns_str = ', '.join(fk['columns'])
                    ref_str = f"{fk['ref_table']}.{', '.join(fk['ref_columns'])}"
                    doc.append(f"- {columns_str} → {ref_str}\n")
            
            doc.append("\n---\n")
        
        # Save documentation
        doc_file = self.docs_path / f"{db_name}_schema.md"
        with open(doc_file, 'w') as f:
            f.write(''.join(doc))
        
        print(f"✅ Generated schema documentation: {doc_file}")
    
    def generate_plantuml_erd(self, db_name: str, tables: Dict[str, Any]):
        """Generate PlantUML ERD diagram"""
        uml = ["@startuml\n"]
        uml.append(f"!define ENTITY entity\n")
        uml.append(f"!define TABLE(x) class x << (T,#FFAAAA) >>\n")
        uml.append(f"!define PRIMARY_KEY(x) <u>x</u>\n")
        uml.append(f"!define FOREIGN_KEY(x) <i>x</i>\n")
        uml.append(f"\ntitle {db_name.replace('_', ' ').title()} Database ERD\n\n")
        
        # Define entities
        for table_name, table_data in tables.items():
            uml.append(f"TABLE({table_name}) {{\n")
            
            # Add columns
            for column in table_data['columns']:
                col_str = f"  {column['name']}: {column['type']}"
                if column['primary_key']:
                    col_str = f"  PRIMARY_KEY({column['name']}): {column['type']}"
                elif column['references']:
                    col_str = f"  FOREIGN_KEY({column['name']}): {column['type']}"
                uml.append(f"{col_str}\n")
            
            uml.append("}\n\n")
        
        # Add relationships
        for table_name, table_data in tables.items():
            for fk in table_data['foreign_keys']:
                uml.append(f"{table_name} --> {fk['ref_table']}\n")
        
        uml.append("\n@enduml")
        
        # Save PlantUML file
        uml_file = self.docs_path / f"{db_name}_erd.puml"
        with open(uml_file, 'w') as f:
            f.write(''.join(uml))
        
        print(f"✅ Generated PlantUML ERD: {uml_file}")
        
        # Try to generate PNG if PlantUML is available
        self.generate_erd_image(uml_file, db_name)
    
    def generate_erd_image(self, uml_file: Path, db_name: str):
        """Generate PNG image from PlantUML file if possible"""
        try:
            # Check if plantuml is available
            result = subprocess.run(['which', 'plantuml'], capture_output=True, text=True)
            if result.returncode == 0:
                png_file = self.docs_path / f"{db_name}_erd.png"
                subprocess.run(['plantuml', '-tpng', str(uml_file)], check=True)
                print(f"✅ Generated ERD image: {png_file}")
            else:
                print(f"ℹ️  PlantUML not found. Install it to generate ERD images.")
        except Exception as e:
            print(f"ℹ️  Could not generate ERD image: {e}")
    
    def generate_combined_erd(self):
        """Generate a combined ERD for all databases"""
        if not self.tables_data:
            return
        
        uml = ["@startuml\n"]
        uml.append("!define ENTITY entity\n")
        uml.append("!define TABLE(x) class x << (T,#FFAAAA) >>\n")
        uml.append("\ntitle ToolBoxAI Complete Database ERD\n\n")
        
        # Add all tables from all databases
        for db_name, tables in self.tables_data.items():
            uml.append(f"package {db_name} {{\n")
            for table_name in tables.keys():
                uml.append(f"  TABLE({db_name}.{table_name})\n")
            uml.append("}\n\n")
        
        # Add cross-database relationships if any
        # (This would require analyzing foreign keys across databases)
        
        uml.append("@enduml")
        
        # Save combined ERD
        combined_file = self.docs_path / "combined_erd.puml"
        with open(combined_file, 'w') as f:
            f.write(''.join(uml))
        
        print(f"✅ Generated combined ERD: {combined_file}")
    
    def generate_summary(self):
        """Generate summary documentation for all schemas"""
        summary = ["# Database Schema Documentation Summary\n"]
        summary.append(f"\nGenerated: {datetime.now().isoformat()}\n\n")
        
        # Overview
        summary.append("## Overview\n\n")
        summary.append("| Database | Tables | Total Columns | Indexes | Foreign Keys |\n")
        summary.append("|----------|--------|---------------|---------|-------------|\n")
        
        for db_name, tables in self.tables_data.items():
            total_columns = sum(len(t['columns']) for t in tables.values())
            total_indexes = sum(len(t['indexes']) for t in tables.values())
            total_fks = sum(len(t['foreign_keys']) for t in tables.values())
            
            summary.append(f"| {db_name} | {len(tables)} | {total_columns} | {total_indexes} | {total_fks} |\n")
        
        # Relationships
        summary.append("\n## Key Relationships\n\n")
        for db_name, tables in self.tables_data.items():
            for table_name, table_data in tables.items():
                for fk in table_data['foreign_keys']:
                    summary.append(f"- `{db_name}.{table_name}` → `{fk['ref_table']}`\n")
        
        # Documentation files
        summary.append("\n## Generated Documentation\n\n")
        for db_name in self.tables_data.keys():
            summary.append(f"- [{db_name} Schema](./{db_name}_schema.md)\n")
            summary.append(f"- [{db_name} ERD](./{db_name}_erd.puml)\n")
        
        # Save summary
        summary_file = self.docs_path / "README.md"
        with open(summary_file, 'w') as f:
            f.write(''.join(summary))
        
        print(f"✅ Generated database documentation summary: {summary_file}")
        
        # Save JSON data
        json_file = self.docs_path / "schemas.json"
        with open(json_file, 'w') as f:
            json.dump(self.tables_data, f, indent=2)
        
        print(f"✅ Saved schema data to {json_file}")


def main():
    """Main execution"""
    print("🚀 Starting database schema documentation generation...")
    
    generator = DatabaseDocGenerator()
    schemas = generator.generate_all_docs()
    
    print(f"\n✨ Successfully documented {len(schemas)} database schemas!")
    
    # Print statistics
    for db_name, tables in schemas.items():
        print(f"\n📊 {db_name}:")
        print(f"  - Tables: {len(tables)}")
        total_columns = sum(len(t['columns']) for t in tables.values())
        print(f"  - Total columns: {total_columns}")


if __name__ == "__main__":
    main()