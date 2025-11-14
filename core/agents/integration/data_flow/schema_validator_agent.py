"""
Schema Validator Agent - Ensures data consistency across platforms

This agent handles:
- Schema validation across platforms
- Data format transformation
- Type checking and coercion
- Schema evolution management
- Compatibility checking
- Validation rule enforcement
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

# Optional jsonschema for advanced validation
try:
    import jsonschema
    from jsonschema import Draft7Validator

    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    Draft7Validator = None

from core.agents.base_agent import AgentConfig

from ..base_integration_agent import (
    BaseIntegrationAgent,
    IntegrationEvent,
    IntegrationPlatform,
    TaskResult,
)

logger = logging.getLogger(__name__)


class SchemaType(Enum):
    """Schema types for different platforms"""

    JSON_SCHEMA = "json_schema"
    PYDANTIC = "pydantic"
    TYPESCRIPT = "typescript"
    GRAPHQL = "graphql"
    SQL = "sql"
    ROBLOX_DATASTORE = "roblox_datastore"


class ValidationLevel(Enum):
    """Validation strictness levels"""

    STRICT = "strict"  # All fields must match exactly
    NORMAL = "normal"  # Required fields must match, optional allowed
    LENIENT = "lenient"  # Best effort validation
    WARN_ONLY = "warn_only"  # Validate but don't fail


@dataclass
class Schema:
    """Schema definition"""

    schema_id: str
    schema_name: str
    schema_type: SchemaType
    version: str
    definition: dict[str, Any]
    platform: IntegrationPlatform
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    deprecated: bool = False
    compatible_versions: list[str] = field(default_factory=list)


@dataclass
class ValidationResult:
    """Validation result"""

    is_valid: bool
    errors: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)
    transformed_data: Optional[Any] = None
    schema_version: Optional[str] = None
    validation_time_ms: float = 0.0


@dataclass
class SchemaMapping:
    """Mapping between schemas of different platforms"""

    mapping_id: str
    source_schema_id: str
    target_schema_id: str
    field_mappings: dict[str, str]  # source_field -> target_field
    transformations: dict[str, str]  # field -> transformation function name
    bidirectional: bool = False


@dataclass
class SchemaEvolution:
    """Schema version evolution tracking"""

    schema_id: str
    from_version: str
    to_version: str
    changes: list[dict[str, Any]]
    migration_script: Optional[str] = None
    breaking_changes: bool = False
    applied_at: Optional[datetime] = None


class SchemaValidatorAgent(BaseIntegrationAgent):
    """
    Schema Validator Agent for cross-platform data consistency
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize Schema Validator Agent"""
        if config is None:
            config = AgentConfig(
                name="SchemaValidatorAgent",
                system_prompt="""You are a Schema Validator Agent responsible for:
                - Validating data against platform-specific schemas
                - Transforming data between different schema formats
                - Managing schema evolution and versioning
                - Ensuring cross-platform data consistency
                - Detecting and resolving schema conflicts
                - Enforcing validation rules and constraints
                """,
            )
        super().__init__(config)

        # Schema registry
        self.schemas: dict[str, Schema] = {}
        self.schema_mappings: dict[str, SchemaMapping] = {}
        self.schema_evolutions: dict[str, list[SchemaEvolution]] = {}

        # Validation configuration
        self.default_validation_level = ValidationLevel.NORMAL
        self.platform_validation_levels: dict[IntegrationPlatform, ValidationLevel] = {}

        # Validators
        self.json_validators: dict[str, Draft7Validator] = {}

        # Transformation functions
        self.transformations = self._init_transformations()

        # Validation metrics
        self.validation_counts: dict[str, int] = {}
        self.validation_errors: dict[str, list[str]] = {}

    def _init_transformations(self) -> dict[str, callable]:
        """Initialize data transformation functions"""
        return {
            "snake_to_camel": lambda x: self._snake_to_camel(x),
            "camel_to_snake": lambda x: self._camel_to_snake(x),
            "string_to_number": lambda x: float(x) if "." in str(x) else int(x),
            "number_to_string": lambda x: str(x),
            "iso_to_timestamp": lambda x: datetime.fromisoformat(x).timestamp(),
            "timestamp_to_iso": lambda x: datetime.fromtimestamp(x).isoformat(),
            "boolean_to_string": lambda x: "true" if x else "false",
            "string_to_boolean": lambda x: x.lower() in ["true", "1", "yes"],
        }

    def _snake_to_camel(self, snake_str: str) -> str:
        """Convert snake_case to camelCase"""
        components = snake_str.split("_")
        return components[0] + "".join(x.title() for x in components[1:])

    def _camel_to_snake(self, camel_str: str) -> str:
        """Convert camelCase to snake_case"""
        import re

        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", camel_str).lower()

    async def register_schema(
        self,
        schema_name: str,
        schema_type: SchemaType,
        definition: dict[str, Any],
        platform: IntegrationPlatform,
        version: str = "1.0.0",
    ) -> TaskResult:
        """Register a new schema"""
        try:
            schema_id = f"{platform.value}_{schema_name}_{version}"

            # Check if schema already exists
            if schema_id in self.schemas:
                return TaskResult(
                    success=False,
                    output=None,
                    error=f"Schema already exists: {schema_id}",
                )

            schema = Schema(
                schema_id=schema_id,
                schema_name=schema_name,
                schema_type=schema_type,
                version=version,
                definition=definition,
                platform=platform,
            )

            self.schemas[schema_id] = schema

            # Create JSON validator if applicable
            if schema_type == SchemaType.JSON_SCHEMA and HAS_JSONSCHEMA:
                try:
                    self.json_validators[schema_id] = Draft7Validator(definition)
                except jsonschema.SchemaError as e:
                    logger.error(f"Invalid JSON schema: {e}")
                    del self.schemas[schema_id]
                    return TaskResult(success=False, output=None, error=f"Invalid JSON schema: {e}")

            logger.info(f"Registered schema: {schema_id}")

            # Emit schema registration event
            await self.emit_event(
                IntegrationEvent(
                    event_id=f"schema_registered_{schema_id}",
                    event_type="schema_registered",
                    source_platform=platform,
                    payload={
                        "schema_id": schema_id,
                        "schema_name": schema_name,
                        "version": version,
                        "platform": platform.value,
                    },
                )
            )

            return TaskResult(success=True, output={"schema_id": schema_id, "registered": True})

        except Exception as e:
            logger.error(f"Error registering schema: {e}")
            return TaskResult(success=False, output=None, error=str(e))

    async def validate_data(
        self,
        data: Any,
        schema_id: str,
        validation_level: Optional[ValidationLevel] = None,
    ) -> ValidationResult:
        """Validate data against a schema"""
        start_time = datetime.utcnow()
        result = ValidationResult(is_valid=True)

        try:
            if schema_id not in self.schemas:
                result.is_valid = False
                result.errors.append(
                    {
                        "error": "schema_not_found",
                        "message": f"Schema not found: {schema_id}",
                    }
                )
                return result

            schema = self.schemas[schema_id]
            result.schema_version = schema.version

            # Determine validation level
            level = validation_level or self.platform_validation_levels.get(
                schema.platform, self.default_validation_level
            )

            # Perform validation based on schema type
            if schema.schema_type == SchemaType.JSON_SCHEMA:
                result = await self._validate_json_schema(data, schema, level)
            elif schema.schema_type == SchemaType.PYDANTIC:
                result = await self._validate_pydantic(data, schema, level)
            elif schema.schema_type == SchemaType.SQL:
                result = await self._validate_sql_schema(data, schema, level)
            elif schema.schema_type == SchemaType.ROBLOX_DATASTORE:
                result = await self._validate_roblox_datastore(data, schema, level)
            else:
                result.warnings.append(
                    {
                        "warning": "unsupported_schema_type",
                        "message": f"Schema type not fully supported: {schema.schema_type.value}",
                    }
                )

            # Track validation metrics
            self.validation_counts[schema_id] = self.validation_counts.get(schema_id, 0) + 1
            if not result.is_valid:
                if schema_id not in self.validation_errors:
                    self.validation_errors[schema_id] = []
                self.validation_errors[schema_id].extend([e["message"] for e in result.errors])

        except Exception as e:
            logger.error(f"Error validating data: {e}")
            result.is_valid = False
            result.errors.append({"error": "validation_error", "message": str(e)})

        finally:
            result.validation_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        return result

    async def _validate_json_schema(
        self, data: Any, schema: Schema, level: ValidationLevel
    ) -> ValidationResult:
        """Validate data against JSON schema"""
        result = ValidationResult(is_valid=True)

        if not HAS_JSONSCHEMA:
            # Fallback to basic validation if jsonschema not available
            result.warnings.append(
                {
                    "warning": "jsonschema_not_available",
                    "message": "Advanced JSON schema validation not available, using basic validation",
                }
            )
            return await self._validate_pydantic(data, schema, level)

        try:
            validator = self.json_validators.get(schema.schema_id)
            if not validator:
                validator = Draft7Validator(schema.definition)
                self.json_validators[schema.schema_id] = validator

            # Perform validation
            validation_errors = list(validator.iter_errors(data))

            if validation_errors:
                if level == ValidationLevel.WARN_ONLY:
                    # Convert errors to warnings
                    for error in validation_errors:
                        result.warnings.append({"path": list(error.path), "message": error.message})
                else:
                    result.is_valid = False
                    for error in validation_errors:
                        result.errors.append({"path": list(error.path), "message": error.message})

            result.transformed_data = data

        except Exception as e:
            result.is_valid = False
            result.errors.append({"error": "json_schema_validation_failed", "message": str(e)})

        return result

    async def _validate_pydantic(
        self, data: Any, schema: Schema, level: ValidationLevel
    ) -> ValidationResult:
        """Validate data against Pydantic model (simulated)"""
        result = ValidationResult(is_valid=True)

        # This would use actual Pydantic validation
        # For now, basic type checking
        definition = schema.definition
        required_fields = definition.get("required", [])
        properties = definition.get("properties", {})

        if isinstance(data, dict):
            # Check required fields
            for field in required_fields:
                if field not in data:
                    if level != ValidationLevel.LENIENT:
                        result.is_valid = False
                        result.errors.append({"field": field, "error": "required_field_missing"})

            # Check field types
            for field, value in data.items():
                if field in properties:
                    expected_type = properties[field].get("type")
                    if expected_type and not self._check_type(value, expected_type):
                        if level == ValidationLevel.STRICT:
                            result.is_valid = False
                            result.errors.append(
                                {
                                    "field": field,
                                    "error": "type_mismatch",
                                    "expected": expected_type,
                                    "actual": type(value).__name__,
                                }
                            )
                        else:
                            result.warnings.append({"field": field, "warning": "type_mismatch"})

        result.transformed_data = data
        return result

    async def _validate_sql_schema(
        self, data: Any, schema: Schema, level: ValidationLevel
    ) -> ValidationResult:
        """Validate data against SQL schema"""
        result = ValidationResult(is_valid=True)

        # SQL schema validation would check:
        # - Column types
        # - Constraints (NOT NULL, UNIQUE, etc.)
        # - Foreign key relationships
        # For now, basic implementation

        columns = schema.definition.get("columns", {})

        if isinstance(data, dict):
            for column, constraints in columns.items():
                if "not_null" in constraints and constraints["not_null"]:
                    if column not in data or data[column] is None:
                        result.is_valid = False
                        result.errors.append(
                            {"column": column, "error": "null_constraint_violation"}
                        )

        result.transformed_data = data
        return result

    async def _validate_roblox_datastore(
        self, data: Any, schema: Schema, level: ValidationLevel
    ) -> ValidationResult:
        """Validate data for Roblox DataStore"""
        result = ValidationResult(is_valid=True)

        # Roblox DataStore has specific limitations:
        # - Max key length: 50 characters
        # - Max value size: 4MB
        # - Specific data types supported

        if isinstance(data, dict):
            # Check size limitations
            data_str = json.dumps(data)
            if len(data_str) > 4 * 1024 * 1024:  # 4MB
                result.is_valid = False
                result.errors.append(
                    {
                        "error": "datastore_size_limit",
                        "message": "Data exceeds 4MB limit",
                        "size": len(data_str),
                    }
                )

            # Check for unsupported types
            for key, value in data.items():
                if len(str(key)) > 50:
                    result.is_valid = False
                    result.errors.append(
                        {
                            "error": "key_length_limit",
                            "key": key,
                            "length": len(str(key)),
                        }
                    )

        result.transformed_data = data
        return result

    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected type"""
        type_mapping = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict,
        }

        expected = type_mapping.get(expected_type)
        if expected:
            return isinstance(value, expected)
        return True

    async def transform_data(
        self,
        data: Any,
        source_schema_id: str,
        target_schema_id: str,
        mapping_id: Optional[str] = None,
    ) -> TaskResult:
        """Transform data from source schema to target schema"""
        try:
            # Validate against source schema first
            source_validation = await self.validate_data(data, source_schema_id)
            if not source_validation.is_valid:
                return TaskResult(
                    success=False,
                    output=None,
                    error="Source data validation failed",
                    metadata={"errors": source_validation.errors},
                )

            # Find or create mapping
            if not mapping_id:
                mapping_id = f"{source_schema_id}_to_{target_schema_id}"

            if mapping_id not in self.schema_mappings:
                # Create automatic mapping
                mapping = await self._create_automatic_mapping(source_schema_id, target_schema_id)
                if not mapping:
                    return TaskResult(
                        success=False,
                        output=None,
                        error="Could not create schema mapping",
                    )
                self.schema_mappings[mapping_id] = mapping
            else:
                mapping = self.schema_mappings[mapping_id]

            # Apply transformations
            transformed_data = await self._apply_transformations(data, mapping)

            # Validate against target schema
            target_validation = await self.validate_data(transformed_data, target_schema_id)

            if not target_validation.is_valid:
                logger.warning(f"Target validation failed: {target_validation.errors}")

            return TaskResult(
                success=True,
                output=transformed_data,
                metadata={
                    "source_schema": source_schema_id,
                    "target_schema": target_schema_id,
                    "validation_passed": target_validation.is_valid,
                },
            )

        except Exception as e:
            logger.error(f"Error transforming data: {e}")
            return TaskResult(success=False, output=None, error=str(e))

    async def _create_automatic_mapping(
        self, source_schema_id: str, target_schema_id: str
    ) -> Optional[SchemaMapping]:
        """Create automatic mapping between schemas"""
        try:
            source_schema = self.schemas.get(source_schema_id)
            target_schema = self.schemas.get(target_schema_id)

            if not source_schema or not target_schema:
                return None

            # Simple field name matching
            field_mappings = {}
            transformations = {}

            source_fields = self._extract_fields(source_schema)
            target_fields = self._extract_fields(target_schema)

            for source_field in source_fields:
                # Try exact match
                if source_field in target_fields:
                    field_mappings[source_field] = source_field
                # Try case conversion
                elif self._snake_to_camel(source_field) in target_fields:
                    field_mappings[source_field] = self._snake_to_camel(source_field)
                    transformations[source_field] = "snake_to_camel"
                elif self._camel_to_snake(source_field) in target_fields:
                    field_mappings[source_field] = self._camel_to_snake(source_field)
                    transformations[source_field] = "camel_to_snake"

            return SchemaMapping(
                mapping_id=f"{source_schema_id}_to_{target_schema_id}",
                source_schema_id=source_schema_id,
                target_schema_id=target_schema_id,
                field_mappings=field_mappings,
                transformations=transformations,
            )

        except Exception as e:
            logger.error(f"Error creating automatic mapping: {e}")
            return None

    def _extract_fields(self, schema: Schema) -> list[str]:
        """Extract field names from schema"""
        if schema.schema_type in [SchemaType.JSON_SCHEMA, SchemaType.PYDANTIC]:
            return list(schema.definition.get("properties", {}).keys())
        elif schema.schema_type == SchemaType.SQL:
            return list(schema.definition.get("columns", {}).keys())
        return []

    async def _apply_transformations(self, data: Any, mapping: SchemaMapping) -> Any:
        """Apply transformations based on mapping"""
        if not isinstance(data, dict):
            return data

        transformed = {}

        for source_field, target_field in mapping.field_mappings.items():
            if source_field in data:
                value = data[source_field]

                # Apply transformation if defined
                if source_field in mapping.transformations:
                    transform_name = mapping.transformations[source_field]
                    if transform_name in self.transformations:
                        try:
                            value = self.transformations[transform_name](value)
                        except Exception as e:
                            logger.warning(f"Transformation failed: {e}")

                transformed[target_field] = value

        return transformed

    async def check_compatibility(self, schema1_id: str, schema2_id: str) -> TaskResult:
        """Check if two schemas are compatible"""
        try:
            schema1 = self.schemas.get(schema1_id)
            schema2 = self.schemas.get(schema2_id)

            if not schema1 or not schema2:
                return TaskResult(success=False, output=None, error="One or both schemas not found")

            fields1 = set(self._extract_fields(schema1))
            fields2 = set(self._extract_fields(schema2))

            common_fields = fields1 & fields2
            only_in_1 = fields1 - fields2
            only_in_2 = fields2 - fields1

            compatibility_score = len(common_fields) / max(len(fields1), len(fields2))

            return TaskResult(
                success=True,
                output={
                    "compatible": compatibility_score > 0.7,  # 70% threshold
                    "compatibility_score": compatibility_score,
                    "common_fields": list(common_fields),
                    "only_in_first": list(only_in_1),
                    "only_in_second": list(only_in_2),
                },
            )

        except Exception as e:
            logger.error(f"Error checking compatibility: {e}")
            return TaskResult(success=False, output=None, error=str(e))

    async def _process_integration_event(self, event: IntegrationEvent):
        """Process integration events for schema validation"""
        if event.event_type == "schema_registration_request":
            # Register new schema
            await self.register_schema(
                schema_name=event.payload["name"],
                schema_type=SchemaType[event.payload["type"]],
                definition=event.payload["definition"],
                platform=IntegrationPlatform[event.payload["platform"]],
                version=event.payload.get("version", "1.0.0"),
            )

        elif event.event_type == "validation_request":
            # Validate data
            result = await self.validate_data(
                data=event.payload["data"],
                schema_id=event.payload["schema_id"],
                validation_level=ValidationLevel[event.payload.get("level", "NORMAL")],
            )

            # Emit validation result
            await self.emit_event(
                IntegrationEvent(
                    event_id=f"validation_result_{event.event_id}",
                    event_type="validation_completed",
                    source_platform=IntegrationPlatform.BACKEND,
                    payload={
                        "is_valid": result.is_valid,
                        "errors": result.errors,
                        "warnings": result.warnings,
                    },
                    correlation_id=event.correlation_id,
                )
            )

    async def execute_task(self, task: str, context: Optional[dict[str, Any]] = None) -> TaskResult:
        """Execute schema validator specific tasks"""
        if task == "register_schema":
            return await self.register_schema(**context)
        elif task == "validate":
            result = await self.validate_data(
                data=context["data"],
                schema_id=context["schema_id"],
                validation_level=ValidationLevel[context.get("level", "NORMAL")],
            )
            return TaskResult(success=result.is_valid, output=result.__dict__)
        elif task == "transform":
            return await self.transform_data(
                data=context["data"],
                source_schema_id=context["source_schema"],
                target_schema_id=context["target_schema"],
                mapping_id=context.get("mapping_id"),
            )
        elif task == "check_compatibility":
            return await self.check_compatibility(
                schema1_id=context["schema1"], schema2_id=context["schema2"]
            )
        else:
            return await super().execute_task(task, context)
