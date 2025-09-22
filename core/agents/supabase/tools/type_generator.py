"""Type generator tool for creating TypeScript types from Supabase schema."""

import json
import logging
import re
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import aiofiles
import asyncpg

logger = logging.getLogger(__name__)


class TypeStyle(Enum):
    """TypeScript type generation styles."""
    INTERFACE = "interface"
    TYPE_ALIAS = "type_alias"
    CLASS = "class"


@dataclass
class ColumnType:
    """Information about a database column type."""
    name: str
    data_type: str
    is_nullable: bool
    default_value: Optional[str]
    is_primary_key: bool
    is_foreign_key: bool
    foreign_table: Optional[str]
    foreign_column: Optional[str]
    enum_values: Optional[List[str]] = None


@dataclass
class TableType:
    """Information about a database table for type generation."""
    name: str
    columns: List[ColumnType]
    relationships: List[Dict[str, Any]]
    description: Optional[str] = None


@dataclass
class GeneratedTypes:
    """Generated TypeScript types."""
    interfaces: str
    types: str
    zod_schemas: str
    api_client: str
    database_types: str


class TypeGeneratorTool:
    """
    Tool for generating TypeScript types from Supabase schema.

    Features:
    - TypeScript interface generation
    - Zod schema generation
    - API client types
    - Database types
    - Relationship mapping
    """

    def __init__(self):
        """Initialize the type generator."""
        self.postgres_to_ts_mapping = {
            # Numeric types
            'smallint': 'number',
            'integer': 'number',
            'bigint': 'number',
            'decimal': 'number',
            'numeric': 'number',
            'real': 'number',
            'double precision': 'number',
            'smallserial': 'number',
            'serial': 'number',
            'bigserial': 'number',

            # String types
            'character varying': 'string',
            'varchar': 'string',
            'character': 'string',
            'char': 'string',
            'text': 'string',

            # Date/time types
            'timestamp': 'string',
            'timestamp with time zone': 'string',
            'timestamp without time zone': 'string',
            'date': 'string',
            'time': 'string',
            'interval': 'string',

            # Boolean
            'boolean': 'boolean',

            # JSON
            'json': 'any',
            'jsonb': 'any',

            # UUID
            'uuid': 'string',

            # Arrays
            'ARRAY': 'Array',

            # Geometric types
            'point': 'string',
            'line': 'string',
            'lseg': 'string',
            'box': 'string',
            'path': 'string',
            'polygon': 'string',
            'circle': 'string',

            # Network types
            'cidr': 'string',
            'inet': 'string',
            'macaddr': 'string',

            # Other
            'bytea': 'string',
            'bit': 'string',
            'bit varying': 'string',
            'money': 'number',
        }

        self.reserved_words = {
            'abstract', 'arguments', 'await', 'boolean', 'break', 'byte',
            'case', 'catch', 'char', 'class', 'const', 'continue',
            'debugger', 'default', 'delete', 'do', 'double', 'else',
            'enum', 'eval', 'export', 'extends', 'false', 'final',
            'finally', 'float', 'for', 'function', 'goto', 'if',
            'implements', 'import', 'in', 'instanceof', 'int', 'interface',
            'let', 'long', 'native', 'new', 'null', 'package', 'private',
            'protected', 'public', 'return', 'short', 'static', 'super',
            'switch', 'synchronized', 'this', 'throw', 'throws',
            'transient', 'true', 'try', 'typeof', 'var', 'void',
            'volatile', 'while', 'with', 'yield'
        }

    async def generate_types_from_connection(
        self,
        connection_string: str,
        output_directory: str,
        table_filter: Optional[List[str]] = None,
        exclude_tables: Optional[List[str]] = None,
        type_style: TypeStyle = TypeStyle.INTERFACE,
        include_relationships: bool = True
    ) -> GeneratedTypes:
        """
        Generate TypeScript types from database connection.

        Args:
            connection_string: Database connection string
            output_directory: Directory to write generated files
            table_filter: Only include specified tables
            exclude_tables: Exclude specified tables
            type_style: Style of TypeScript types to generate
            include_relationships: Include relationship types

        Returns:
            Generated types
        """
        logger.info("Generating TypeScript types from database")

        # Extract schema information
        tables = await self._extract_schema_info(
            connection_string,
            table_filter,
            exclude_tables
        )

        # Generate types
        generated = await self._generate_all_types(
            tables,
            type_style,
            include_relationships
        )

        # Write files
        await self._write_type_files(output_directory, generated)

        return generated

    async def generate_types_from_schema(
        self,
        schema_json: Dict[str, Any],
        output_directory: str,
        type_style: TypeStyle = TypeStyle.INTERFACE,
        include_relationships: bool = True
    ) -> GeneratedTypes:
        """
        Generate TypeScript types from schema JSON.

        Args:
            schema_json: Schema information as JSON
            output_directory: Directory to write generated files
            type_style: Style of TypeScript types to generate
            include_relationships: Include relationship types

        Returns:
            Generated types
        """
        logger.info("Generating TypeScript types from schema JSON")

        # Convert JSON to table types
        tables = self._convert_schema_json_to_tables(schema_json)

        # Generate types
        generated = await self._generate_all_types(
            tables,
            type_style,
            include_relationships
        )

        # Write files
        await self._write_type_files(output_directory, generated)

        return generated

    async def generate_api_client_types(
        self,
        tables: List[TableType],
        output_directory: str,
        base_url: str = "{{SUPABASE_URL}}",
        include_crud_operations: bool = True
    ) -> str:
        """
        Generate API client with TypeScript types.

        Args:
            tables: List of table types
            output_directory: Directory to write files
            base_url: Base URL for API calls
            include_crud_operations: Include CRUD operation methods

        Returns:
            Generated API client code
        """
        logger.info("Generating API client types")

        api_client_code = await self._generate_api_client(
            tables,
            base_url,
            include_crud_operations
        )

        # Write API client file
        output_path = Path(output_directory)
        output_path.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(output_path / "api-client.ts", 'w') as f:
            await f.write(api_client_code)

        return api_client_code

    async def _extract_schema_info(
        self,
        connection_string: str,
        table_filter: Optional[List[str]],
        exclude_tables: Optional[List[str]]
    ) -> List[TableType]:
        """Extract schema information from database."""
        conn = await asyncpg.connect(connection_string)
        tables = []

        try:
            # Get all tables
            table_query = """
            SELECT table_name, obj_description(c.oid) as description
            FROM information_schema.tables t
            LEFT JOIN pg_class c ON c.relname = t.table_name
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
            """

            table_rows = await conn.fetch(table_query)

            for table_row in table_rows:
                table_name = table_row['table_name']

                # Apply filters
                if table_filter and table_name not in table_filter:
                    continue

                if exclude_tables and table_name in exclude_tables:
                    continue

                # Get column information
                columns = await self._get_table_columns(conn, table_name)

                # Get relationships
                relationships = await self._get_table_relationships(conn, table_name)

                table_type = TableType(
                    name=table_name,
                    columns=columns,
                    relationships=relationships,
                    description=table_row['description']
                )

                tables.append(table_type)

        finally:
            await conn.close()

        return tables

    async def _get_table_columns(
        self,
        conn: asyncpg.Connection,
        table_name: str
    ) -> List[ColumnType]:
        """Get column information for a table."""
        query = """
        SELECT
            c.column_name,
            c.data_type,
            c.is_nullable,
            c.column_default,
            CASE WHEN pk.column_name IS NOT NULL THEN true ELSE false END as is_primary_key,
            CASE WHEN fk.column_name IS NOT NULL THEN true ELSE false END as is_foreign_key,
            fk.foreign_table_name,
            fk.foreign_column_name,
            c.udt_name
        FROM information_schema.columns c
        LEFT JOIN (
            SELECT ku.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage ku
                ON tc.constraint_name = ku.constraint_name
            WHERE tc.table_name = $1
                AND tc.constraint_type = 'PRIMARY KEY'
        ) pk ON c.column_name = pk.column_name
        LEFT JOIN (
            SELECT
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.table_name = $1
                AND tc.constraint_type = 'FOREIGN KEY'
        ) fk ON c.column_name = fk.column_name
        WHERE c.table_name = $1
        ORDER BY c.ordinal_position
        """

        rows = await conn.fetch(query, table_name)
        columns = []

        for row in rows:
            # Get enum values if applicable
            enum_values = None
            if row['udt_name'] and not row['udt_name'].startswith('_'):
                enum_values = await self._get_enum_values(conn, row['udt_name'])

            column = ColumnType(
                name=row['column_name'],
                data_type=row['data_type'],
                is_nullable=row['is_nullable'] == 'YES',
                default_value=row['column_default'],
                is_primary_key=row['is_primary_key'],
                is_foreign_key=row['is_foreign_key'],
                foreign_table=row['foreign_table_name'],
                foreign_column=row['foreign_column_name'],
                enum_values=enum_values
            )

            columns.append(column)

        return columns

    async def _get_enum_values(
        self,
        conn: asyncpg.Connection,
        enum_name: str
    ) -> Optional[List[str]]:
        """Get enum values for a custom type."""
        try:
            query = """
            SELECT enumlabel
            FROM pg_enum e
            JOIN pg_type t ON e.enumtypid = t.oid
            WHERE t.typname = $1
            ORDER BY e.enumsortorder
            """

            rows = await conn.fetch(query, enum_name)
            return [row['enumlabel'] for row in rows]

        except Exception:
            return None

    async def _get_table_relationships(
        self,
        conn: asyncpg.Connection,
        table_name: str
    ) -> List[Dict[str, Any]]:
        """Get relationship information for a table."""
        query = """
        SELECT
            tc.constraint_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name,
            'belongs_to' as relationship_type
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.table_name = $1
            AND tc.constraint_type = 'FOREIGN KEY'

        UNION ALL

        SELECT
            tc.constraint_name,
            ccu.column_name,
            kcu.table_name AS foreign_table_name,
            kcu.column_name AS foreign_column_name,
            'has_many' as relationship_type
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE ccu.table_name = $1
            AND tc.constraint_type = 'FOREIGN KEY'
        """

        rows = await conn.fetch(query, table_name)
        return [dict(row) for row in rows]

    def _convert_schema_json_to_tables(
        self,
        schema_json: Dict[str, Any]
    ) -> List[TableType]:
        """Convert schema JSON to table types."""
        tables = []

        for table_data in schema_json.get('tables', []):
            columns = []

            for col_data in table_data.get('columns', []):
                column = ColumnType(
                    name=col_data['name'],
                    data_type=col_data['type'],
                    is_nullable=col_data.get('nullable', True),
                    default_value=col_data.get('default'),
                    is_primary_key=col_data.get('primary_key', False),
                    is_foreign_key=col_data.get('foreign_key', False),
                    foreign_table=col_data.get('foreign_table'),
                    foreign_column=col_data.get('foreign_column'),
                    enum_values=col_data.get('enum_values')
                )
                columns.append(column)

            table = TableType(
                name=table_data['name'],
                columns=columns,
                relationships=table_data.get('relationships', []),
                description=table_data.get('description')
            )

            tables.append(table)

        return tables

    async def _generate_all_types(
        self,
        tables: List[TableType],
        type_style: TypeStyle,
        include_relationships: bool
    ) -> GeneratedTypes:
        """Generate all TypeScript types."""
        # Generate interfaces
        interfaces = await self._generate_interfaces(tables, include_relationships)

        # Generate type aliases
        types = await self._generate_type_aliases(tables)

        # Generate Zod schemas
        zod_schemas = await self._generate_zod_schemas(tables)

        # Generate API client
        api_client = await self._generate_api_client(tables)

        # Generate database types
        database_types = await self._generate_database_types(tables)

        return GeneratedTypes(
            interfaces=interfaces,
            types=types,
            zod_schemas=zod_schemas,
            api_client=api_client,
            database_types=database_types
        )

    async def _generate_interfaces(
        self,
        tables: List[TableType],
        include_relationships: bool
    ) -> str:
        """Generate TypeScript interfaces."""
        code = "// Generated TypeScript interfaces\n\n"

        # Generate enums first
        enums = self._extract_enums(tables)
        for enum_name, enum_values in enums.items():
            code += f"export enum {self._to_pascal_case(enum_name)} {{\n"
            for value in enum_values:
                enum_key = self._to_enum_key(value)
                code += f"  {enum_key} = '{value}',\n"
            code += "}\n\n"

        # Generate interfaces
        for table in tables:
            interface_name = self._to_pascal_case(table.name)
            code += f"export interface {interface_name} {{\n"

            for column in table.columns:
                prop_name = self._to_camel_case(column.name)
                prop_type = self._get_typescript_type(column)

                # Make nullable if needed
                if column.is_nullable and not column.is_primary_key:
                    prop_type += " | null"

                # Optional for nullable columns
                optional = "?" if column.is_nullable and not column.is_primary_key else ""

                code += f"  {prop_name}{optional}: {prop_type};\n"

            code += "}\n\n"

            # Generate input/update interfaces
            code += f"export interface {interface_name}Input {{\n"
            for column in table.columns:
                if column.is_primary_key:
                    continue

                prop_name = self._to_camel_case(column.name)
                prop_type = self._get_typescript_type(column)

                # Make optional for inputs
                optional = "?" if column.is_nullable or column.default_value else ""

                code += f"  {prop_name}{optional}: {prop_type};\n"

            code += "}\n\n"

            code += f"export interface {interface_name}Update {{\n"
            for column in table.columns:
                if column.is_primary_key:
                    continue

                prop_name = self._to_camel_case(column.name)
                prop_type = self._get_typescript_type(column)

                code += f"  {prop_name}?: {prop_type};\n"

            code += "}\n\n"

            # Generate relationship interfaces if requested
            if include_relationships:
                for relationship in table.relationships:
                    if relationship['relationship_type'] == 'has_many':
                        related_table = self._to_pascal_case(relationship['foreign_table_name'])
                        code += f"export interface {interface_name}With{related_table}s extends {interface_name} {{\n"
                        code += f"  {self._to_camel_case(relationship['foreign_table_name'])}s: {related_table}[];\n"
                        code += "}\n\n"

        return code

    async def _generate_type_aliases(self, tables: List[TableType]) -> str:
        """Generate TypeScript type aliases."""
        code = "// Generated TypeScript type aliases\n\n"

        for table in tables:
            table_name = self._to_pascal_case(table.name)

            # Primary key type
            pk_columns = [col for col in table.columns if col.is_primary_key]
            if pk_columns:
                pk_types = [self._get_typescript_type(col) for col in pk_columns]
                if len(pk_types) == 1:
                    code += f"export type {table_name}Id = {pk_types[0]};\n"
                else:
                    code += f"export type {table_name}Id = {{{', '.join([f'{self._to_camel_case(col.name)}: {self._get_typescript_type(col)}' for col in pk_columns])}}};\n"

            # Partial types
            code += f"export type Partial{table_name} = Partial<{table_name}>;\n"

            # Required types
            required_fields = [self._to_camel_case(col.name) for col in table.columns if not col.is_nullable and not col.default_value]
            if required_fields:
                code += f"export type Required{table_name}Fields = Pick<{table_name}, {'|'.join([f\"'{field}'\" for field in required_fields])}>;\n"

            code += "\n"

        return code

    async def _generate_zod_schemas(self, tables: List[TableType]) -> str:
        """Generate Zod validation schemas."""
        code = "// Generated Zod validation schemas\n"
        code += "import { z } from 'zod';\n\n"

        # Generate enum schemas first
        enums = self._extract_enums(tables)
        for enum_name, enum_values in enums.items():
            schema_name = f"{self._to_camel_case(enum_name)}Schema"
            values_list = ", ".join([f"'{value}'" for value in enum_values])
            code += f"export const {schema_name} = z.enum([{values_list}]);\n\n"

        # Generate table schemas
        for table in tables:
            schema_name = f"{self._to_camel_case(table.name)}Schema"
            code += f"export const {schema_name} = z.object({{\n"

            for column in table.columns:
                prop_name = self._to_camel_case(column.name)
                zod_type = self._get_zod_type(column)

                # Make optional if nullable
                if column.is_nullable and not column.is_primary_key:
                    zod_type += ".nullable().optional()"
                elif column.default_value:
                    zod_type += ".optional()"

                code += f"  {prop_name}: {zod_type},\n"

            code += "});\n\n"

            # Input schema (without primary key)
            input_schema_name = f"{self._to_camel_case(table.name)}InputSchema"
            code += f"export const {input_schema_name} = {schema_name}.omit({{\n"
            pk_fields = [f"  {self._to_camel_case(col.name)}: true" for col in table.columns if col.is_primary_key]
            code += ",\n".join(pk_fields) + "\n"
            code += "});\n\n"

            # Update schema (all fields optional)
            update_schema_name = f"{self._to_camel_case(table.name)}UpdateSchema"
            code += f"export const {update_schema_name} = {schema_name}.partial();\n\n"

        return code

    async def _generate_api_client(
        self,
        tables: List[TableType],
        base_url: str = "{{SUPABASE_URL}}",
        include_crud_operations: bool = True
    ) -> str:
        """Generate API client with TypeScript types."""
        code = "// Generated API client\n"
        code += "import { createClient, SupabaseClient } from '@supabase/supabase-js';\n\n"

        # Import generated types
        code += "// Import generated types\n"
        for table in tables:
            table_name = self._to_pascal_case(table.name)
            code += f"import {{ {table_name}, {table_name}Input, {table_name}Update }} from './interfaces';\n"

        code += "\n"

        # Database type
        code += "export interface Database {\n"
        code += "  public: {\n"
        code += "    Tables: {\n"

        for table in tables:
            table_name = table.name
            type_name = self._to_pascal_case(table.name)
            code += f"      {table_name}: {{\n"
            code += f"        Row: {type_name};\n"
            code += f"        Insert: {type_name}Input;\n"
            code += f"        Update: {type_name}Update;\n"
            code += "      };\n"

        code += "    };\n"
        code += "  };\n"
        code += "}\n\n"

        # API client class
        code += "export class ApiClient {\n"
        code += "  private supabase: SupabaseClient<Database>;\n\n"
        code += "  constructor(url: string, key: string) {\n"
        code += "    this.supabase = createClient<Database>(url, key);\n"
        code += "  }\n\n"

        if include_crud_operations:
            for table in tables:
                code += self._generate_table_methods(table)

        code += "}\n\n"

        # Export default instance
        code += f"export const apiClient = new ApiClient(\n"
        code += f"  process.env.NEXT_PUBLIC_SUPABASE_URL || '{base_url}',\n"
        code += f"  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '{{SUPABASE_ANON_KEY}}'\n"
        code += ");\n"

        return code

    async def _generate_database_types(self, tables: List[TableType]) -> str:
        """Generate database-specific types."""
        code = "// Generated database types\n\n"

        # Database response types
        code += "export interface DatabaseResponse<T> {\n"
        code += "  data: T | null;\n"
        code += "  error: Error | null;\n"
        code += "}\n\n"

        code += "export interface DatabaseListResponse<T> {\n"
        code += "  data: T[] | null;\n"
        code += "  error: Error | null;\n"
        code += "  count?: number;\n"
        code += "}\n\n"

        # Query options
        code += "export interface QueryOptions {\n"
        code += "  limit?: number;\n"
        code += "  offset?: number;\n"
        code += "  orderBy?: string;\n"
        code += "  ascending?: boolean;\n"
        code += "  filters?: Record<string, any>;\n"
        code += "}\n\n"

        # Table names enum
        code += "export enum TableNames {\n"
        for table in tables:
            enum_key = table.name.upper()
            code += f"  {enum_key} = '{table.name}',\n"
        code += "}\n\n"

        return code

    def _extract_enums(self, tables: List[TableType]) -> Dict[str, List[str]]:
        """Extract enum types from tables."""
        enums = {}

        for table in tables:
            for column in table.columns:
                if column.enum_values:
                    enum_name = f"{table.name}_{column.name}"
                    enums[enum_name] = column.enum_values

        return enums

    def _get_typescript_type(self, column: ColumnType) -> str:
        """Get TypeScript type for a column."""
        if column.enum_values:
            # Use enum type
            enum_name = self._to_pascal_case(f"{column.name}")
            return enum_name

        # Handle array types
        if column.data_type.startswith('ARRAY'):
            base_type = column.data_type.replace('ARRAY', '').strip('()')
            element_type = self.postgres_to_ts_mapping.get(base_type, 'any')
            return f"{element_type}[]"

        # Standard mapping
        return self.postgres_to_ts_mapping.get(column.data_type, 'any')

    def _get_zod_type(self, column: ColumnType) -> str:
        """Get Zod type for a column."""
        if column.enum_values:
            values = ", ".join([f"'{value}'" for value in column.enum_values])
            return f"z.enum([{values}])"

        type_mapping = {
            'string': 'z.string()',
            'number': 'z.number()',
            'boolean': 'z.boolean()',
            'any': 'z.any()',
        }

        ts_type = self._get_typescript_type(column)

        # Handle arrays
        if ts_type.endswith('[]'):
            element_type = ts_type[:-2]
            element_zod = type_mapping.get(element_type, 'z.any()')
            return f"z.array({element_zod})"

        return type_mapping.get(ts_type, 'z.any()')

    def _generate_table_methods(self, table: TableType) -> str:
        """Generate CRUD methods for a table."""
        table_name = table.name
        type_name = self._to_pascal_case(table.name)
        method_prefix = self._to_camel_case(table.name)

        pk_columns = [col for col in table.columns if col.is_primary_key]
        pk_type = pk_columns[0].name if len(pk_columns) == 1 else 'Record<string, any>'

        methods = f"""
  // {type_name} methods
  async get{type_name}(id: {self._get_typescript_type(pk_columns[0]) if len(pk_columns) == 1 else 'any'}): Promise<DatabaseResponse<{type_name}>> {{
    const {{ data, error }} = await this.supabase
      .from('{table_name}')
      .select('*')
      .eq('{pk_columns[0].name if len(pk_columns) == 1 else 'id'}', id)
      .single();

    return {{ data, error }};
  }}

  async list{type_name}s(options?: QueryOptions): Promise<DatabaseListResponse<{type_name}>> {{
    let query = this.supabase.from('{table_name}').select('*', {{ count: 'exact' }});

    if (options?.limit) query = query.limit(options.limit);
    if (options?.offset) query = query.range(options.offset, (options.offset + (options.limit || 10)) - 1);
    if (options?.orderBy) {{
      query = query.order(options.orderBy, {{ ascending: options.ascending ?? true }});
    }}
    if (options?.filters) {{
      Object.entries(options.filters).forEach(([key, value]) => {{
        query = query.eq(key, value);
      }});
    }}

    const {{ data, error, count }} = await query;
    return {{ data, error, count }};
  }}

  async create{type_name}(input: {type_name}Input): Promise<DatabaseResponse<{type_name}>> {{
    const {{ data, error }} = await this.supabase
      .from('{table_name}')
      .insert(input)
      .select()
      .single();

    return {{ data, error }};
  }}

  async update{type_name}(id: {self._get_typescript_type(pk_columns[0]) if len(pk_columns) == 1 else 'any'}, updates: {type_name}Update): Promise<DatabaseResponse<{type_name}>> {{
    const {{ data, error }} = await this.supabase
      .from('{table_name}')
      .update(updates)
      .eq('{pk_columns[0].name if len(pk_columns) == 1 else 'id'}', id)
      .select()
      .single();

    return {{ data, error }};
  }}

  async delete{type_name}(id: {self._get_typescript_type(pk_columns[0]) if len(pk_columns) == 1 else 'any'}): Promise<DatabaseResponse<null>> {{
    const {{ data, error }} = await this.supabase
      .from('{table_name}')
      .delete()
      .eq('{pk_columns[0].name if len(pk_columns) == 1 else 'id'}', id);

    return {{ data, error }};
  }}
"""

        return methods

    def _to_pascal_case(self, text: str) -> str:
        """Convert text to PascalCase."""
        # Handle snake_case and kebab-case
        words = re.split(r'[_-]', text)
        return ''.join(word.capitalize() for word in words if word)

    def _to_camel_case(self, text: str) -> str:
        """Convert text to camelCase."""
        pascal = self._to_pascal_case(text)
        if not pascal:
            return text

        # Make first letter lowercase
        result = pascal[0].lower() + pascal[1:] if len(pascal) > 1 else pascal.lower()

        # Handle reserved words
        if result in self.reserved_words:
            result = f"{result}_"

        return result

    def _to_enum_key(self, value: str) -> str:
        """Convert enum value to valid enum key."""
        # Replace special characters with underscores
        key = re.sub(r'[^a-zA-Z0-9]', '_', value)
        # Remove leading/trailing underscores
        key = key.strip('_')
        # Ensure it starts with a letter
        if key and not key[0].isalpha():
            key = f"VALUE_{key}"
        # Convert to uppercase
        return key.upper()

    async def _write_type_files(
        self,
        output_directory: str,
        generated: GeneratedTypes
    ):
        """Write generated types to files."""
        output_path = Path(output_directory)
        output_path.mkdir(parents=True, exist_ok=True)

        # Write interfaces
        async with aiofiles.open(output_path / "interfaces.ts", 'w') as f:
            await f.write(generated.interfaces)

        # Write type aliases
        async with aiofiles.open(output_path / "types.ts", 'w') as f:
            await f.write(generated.types)

        # Write Zod schemas
        async with aiofiles.open(output_path / "schemas.ts", 'w') as f:
            await f.write(generated.zod_schemas)

        # Write API client
        async with aiofiles.open(output_path / "api-client.ts", 'w') as f:
            await f.write(generated.api_client)

        # Write database types
        async with aiofiles.open(output_path / "database.ts", 'w') as f:
            await f.write(generated.database_types)

        # Write index file
        index_content = """// Generated type exports
export * from './interfaces';
export * from './types';
export * from './schemas';
export * from './api-client';
export * from './database';
"""

        async with aiofiles.open(output_path / "index.ts", 'w') as f:
            await f.write(index_content)

        logger.info(f"Generated TypeScript types in {output_directory}")

    def generate_usage_guide(self, tables: List[TableType]) -> str:
        """Generate usage guide for the generated types."""
        guide = """# Generated TypeScript Types Usage Guide

## Overview

This package contains TypeScript types, validation schemas, and API client generated from your Supabase database schema.

## Files

- `interfaces.ts` - TypeScript interfaces for all tables
- `types.ts` - Type aliases and utility types
- `schemas.ts` - Zod validation schemas
- `api-client.ts` - Supabase API client with typed methods
- `database.ts` - Database-specific types and utilities

## Usage Examples

### Basic Usage

```typescript
import { apiClient, User, UserInput } from './generated-types';

// Get a user
const { data: user, error } = await apiClient.getUser(123);

// Create a user
const newUser: UserInput = {
  name: 'John Doe',
  email: 'john@example.com'
};
const { data: createdUser } = await apiClient.createUser(newUser);

// Update a user
const updates: UserUpdate = {
  name: 'Jane Doe'
};
await apiClient.updateUser(123, updates);
```

### Validation with Zod

```typescript
import { userInputSchema } from './generated-types';

// Validate user input
const result = userInputSchema.safeParse(userInput);
if (result.success) {
  // Input is valid
  const validatedData = result.data;
} else {
  // Handle validation errors
  console.error(result.error.issues);
}
```

### Direct Supabase Usage

```typescript
import { createClient } from '@supabase/supabase-js';
import { Database } from './generated-types';

const supabase = createClient<Database>(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_ANON_KEY!
);

// Fully typed Supabase client
const { data } = await supabase
  .from('users')
  .select('*')
  .eq('email', 'john@example.com');
```

## Available Tables

"""

        for table in tables:
            table_name = self._to_pascal_case(table.name)
            guide += f"### {table_name}\n\n"
            guide += f"- Interface: `{table_name}`\n"
            guide += f"- Input type: `{table_name}Input`\n"
            guide += f"- Update type: `{table_name}Update`\n"
            guide += f"- Validation schema: `{self._to_camel_case(table.name)}Schema`\n"
            guide += f"- API methods: `get{table_name}()`, `list{table_name}s()`, `create{table_name}()`, `update{table_name}()`, `delete{table_name}()`\n\n"

        guide += """
## Environment Variables

Make sure to set these environment variables:

```env
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

## Type Safety Tips

1. Always use the generated interfaces for function parameters
2. Use Zod schemas for runtime validation
3. Leverage TypeScript's strict mode for better type checking
4. Use the generated API client for consistent error handling

## Regeneration

To regenerate types after schema changes:

1. Update your database schema
2. Run the type generator tool
3. Review and commit the generated files
"""

        return guide