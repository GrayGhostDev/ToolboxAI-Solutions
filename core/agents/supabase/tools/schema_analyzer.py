"""Schema analyzer tool for PostgreSQL to Supabase migration."""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import asyncpg
from sqlalchemy import create_engine, MetaData, inspect
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


@dataclass
class TableInfo:
    """Information about a database table."""
    name: str
    columns: List[Dict[str, Any]]
    constraints: List[Dict[str, Any]]
    indexes: List[Dict[str, Any]]
    row_count: int
    size_bytes: int


class SchemaAnalyzerTool:
    """
    Tool for analyzing PostgreSQL database schemas.

    Extracts comprehensive schema information including:
    - Tables and columns
    - Relationships and foreign keys
    - Indexes and constraints
    - Data types and defaults
    - Row counts and sizes
    """

    def __init__(self):
        """Initialize the schema analyzer tool."""
        self.metadata = MetaData()
        self.engine: Optional[Engine] = None

    async def analyze(
        self,
        connection_string: str,
        database_name: str
    ) -> Dict[str, Any]:
        """
        Analyze database schema comprehensively.

        Args:
            connection_string: PostgreSQL connection string
            database_name: Name of the database to analyze

        Returns:
            Complete schema analysis
        """
        logger.info(f"Analyzing schema for database: {database_name}")

        try:
            # Create SQLAlchemy engine
            self.engine = create_engine(connection_string)

            # Get inspector
            inspector = inspect(self.engine)

            # Analyze schema
            schema = {
                'database': database_name,
                'tables': [],
                'views': [],
                'sequences': [],
                'functions': [],
                'triggers': [],
                'enums': []
            }

            # Get all tables
            for table_name in inspector.get_table_names():
                table_info = await self._analyze_table(inspector, table_name)
                schema['tables'].append(table_info)

            # Get views
            for view_name in inspector.get_view_names():
                view_info = await self._analyze_view(inspector, view_name)
                schema['views'].append(view_info)

            # Get sequences
            schema['sequences'] = await self._get_sequences()

            # Get custom types/enums
            schema['enums'] = await self._get_enums()

            # Get functions and triggers
            schema['functions'] = await self._get_functions()
            schema['triggers'] = await self._get_triggers()

            return schema

        except Exception as e:
            logger.error(f"Schema analysis failed: {str(e)}")
            raise

        finally:
            if self.engine:
                self.engine.dispose()

    async def extract_relationships(
        self,
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract relationships and dependencies from schema.

        Args:
            schema: Schema analysis results

        Returns:
            Relationship information
        """
        relationships = {
            'foreign_keys': [],
            'primary_keys': [],
            'unique_constraints': [],
            'check_constraints': [],
            'dependencies': {}
        }

        for table in schema.get('tables', []):
            table_name = table['name']

            # Extract foreign keys
            for fk in table.get('foreign_keys', []):
                relationships['foreign_keys'].append({
                    'source_table': table_name,
                    'source_column': fk['constrained_columns'],
                    'target_table': fk['referred_table'],
                    'target_column': fk['referred_columns'],
                    'name': fk['name']
                })

            # Extract primary keys
            if table.get('primary_key'):
                relationships['primary_keys'].append({
                    'table': table_name,
                    'columns': table['primary_key']['constrained_columns']
                })

            # Extract unique constraints
            for constraint in table.get('unique_constraints', []):
                relationships['unique_constraints'].append({
                    'table': table_name,
                    'columns': constraint['column_names'],
                    'name': constraint['name']
                })

            # Build dependency graph
            relationships['dependencies'][table_name] = [
                fk['referred_table']
                for fk in table.get('foreign_keys', [])
            ]

        return relationships

    async def _analyze_table(
        self,
        inspector,
        table_name: str
    ) -> Dict[str, Any]:
        """Analyze a single table."""
        table_info = {
            'name': table_name,
            'columns': [],
            'primary_key': None,
            'foreign_keys': [],
            'indexes': [],
            'unique_constraints': [],
            'check_constraints': [],
            'row_count': 0,
            'size_bytes': 0
        }

        # Get columns
        for column in inspector.get_columns(table_name):
            table_info['columns'].append({
                'name': column['name'],
                'type': str(column['type']),
                'nullable': column['nullable'],
                'default': column.get('default'),
                'autoincrement': column.get('autoincrement', False)
            })

        # Get primary key
        pk = inspector.get_pk_constraint(table_name)
        if pk:
            table_info['primary_key'] = pk

        # Get foreign keys
        table_info['foreign_keys'] = inspector.get_foreign_keys(table_name)

        # Get indexes
        table_info['indexes'] = inspector.get_indexes(table_name)

        # Get unique constraints
        table_info['unique_constraints'] = inspector.get_unique_constraints(table_name)

        # Get check constraints
        table_info['check_constraints'] = inspector.get_check_constraints(table_name)

        # Get row count and size (requires direct query)
        table_info['row_count'] = await self._get_row_count(table_name)
        table_info['size_bytes'] = await self._get_table_size(table_name)

        return table_info

    async def _analyze_view(
        self,
        inspector,
        view_name: str
    ) -> Dict[str, Any]:
        """Analyze a database view."""
        view_info = {
            'name': view_name,
            'columns': [],
            'definition': None
        }

        # Get columns
        for column in inspector.get_columns(view_name):
            view_info['columns'].append({
                'name': column['name'],
                'type': str(column['type'])
            })

        # Get view definition
        view_info['definition'] = await self._get_view_definition(view_name)

        return view_info

    async def _get_sequences(self) -> List[Dict[str, Any]]:
        """Get all sequences in the database."""
        sequences = []

        query = """
        SELECT sequence_name, data_type, start_value,
               minimum_value, maximum_value, increment
        FROM information_schema.sequences
        WHERE sequence_schema = 'public'
        """

        with self.engine.connect() as conn:
            result = conn.execute(query)
            for row in result:
                sequences.append({
                    'name': row[0],
                    'data_type': row[1],
                    'start_value': row[2],
                    'min_value': row[3],
                    'max_value': row[4],
                    'increment': row[5]
                })

        return sequences

    async def _get_enums(self) -> List[Dict[str, Any]]:
        """Get all enum types in the database."""
        enums = []

        query = """
        SELECT t.typname, array_agg(e.enumlabel ORDER BY e.enumsortorder)
        FROM pg_type t
        JOIN pg_enum e ON t.oid = e.enumtypid
        WHERE t.typtype = 'e'
        GROUP BY t.typname
        """

        with self.engine.connect() as conn:
            result = conn.execute(query)
            for row in result:
                enums.append({
                    'name': row[0],
                    'values': row[1]
                })

        return enums

    async def _get_functions(self) -> List[Dict[str, Any]]:
        """Get all functions in the database."""
        functions = []

        query = """
        SELECT routine_name, routine_type, data_type
        FROM information_schema.routines
        WHERE routine_schema = 'public'
        """

        with self.engine.connect() as conn:
            result = conn.execute(query)
            for row in result:
                functions.append({
                    'name': row[0],
                    'type': row[1],
                    'return_type': row[2]
                })

        return functions

    async def _get_triggers(self) -> List[Dict[str, Any]]:
        """Get all triggers in the database."""
        triggers = []

        query = """
        SELECT trigger_name, event_object_table,
               event_manipulation, action_timing
        FROM information_schema.triggers
        WHERE trigger_schema = 'public'
        """

        with self.engine.connect() as conn:
            result = conn.execute(query)
            for row in result:
                triggers.append({
                    'name': row[0],
                    'table': row[1],
                    'event': row[2],
                    'timing': row[3]
                })

        return triggers

    async def _get_row_count(self, table_name: str) -> int:
        """Get row count for a table."""
        query = f"SELECT COUNT(*) FROM {table_name}"

        with self.engine.connect() as conn:
            result = conn.execute(query)
            return result.scalar()

    async def _get_table_size(self, table_name: str) -> int:
        """Get table size in bytes."""
        query = f"""
        SELECT pg_total_relation_size('{table_name}')
        """

        with self.engine.connect() as conn:
            result = conn.execute(query)
            return result.scalar()

    async def _get_view_definition(self, view_name: str) -> str:
        """Get view definition SQL."""
        query = f"""
        SELECT definition
        FROM pg_views
        WHERE viewname = '{view_name}'
        """

        with self.engine.connect() as conn:
            result = conn.execute(query)
            row = result.fetchone()
            return row[0] if row else None

    def generate_migration_report(
        self,
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a migration complexity report.

        Args:
            schema: Schema analysis results

        Returns:
            Migration complexity report
        """
        report = {
            'summary': {
                'total_tables': len(schema.get('tables', [])),
                'total_views': len(schema.get('views', [])),
                'total_functions': len(schema.get('functions', [])),
                'total_triggers': len(schema.get('triggers', [])),
                'total_enums': len(schema.get('enums', []))
            },
            'complexity_factors': [],
            'recommendations': [],
            'estimated_effort': 0
        }

        # Analyze complexity factors
        if report['summary']['total_tables'] > 50:
            report['complexity_factors'].append({
                'factor': 'high_table_count',
                'impact': 'high',
                'description': f"{report['summary']['total_tables']} tables to migrate"
            })

        if report['summary']['total_triggers'] > 0:
            report['complexity_factors'].append({
                'factor': 'triggers_present',
                'impact': 'medium',
                'description': f"{report['summary']['total_triggers']} triggers need conversion"
            })

        if report['summary']['total_functions'] > 10:
            report['complexity_factors'].append({
                'factor': 'many_functions',
                'impact': 'high',
                'description': f"{report['summary']['total_functions']} functions to convert to Edge Functions"
            })

        # Generate recommendations
        if any(f['factor'] == 'high_table_count' for f in report['complexity_factors']):
            report['recommendations'].append(
                "Consider phased migration approach for large number of tables"
            )

        if any(f['factor'] == 'triggers_present' for f in report['complexity_factors']):
            report['recommendations'].append(
                "Plan trigger conversion to Supabase Realtime or Edge Functions"
            )

        # Estimate effort (in hours)
        report['estimated_effort'] = (
            report['summary']['total_tables'] * 0.5 +
            report['summary']['total_views'] * 0.3 +
            report['summary']['total_functions'] * 2 +
            report['summary']['total_triggers'] * 1
        )

        return report