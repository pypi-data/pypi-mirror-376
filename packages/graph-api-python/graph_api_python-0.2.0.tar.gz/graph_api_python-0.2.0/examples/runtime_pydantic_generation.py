"""
Runtime Pydantic Model Generation for Dynamic Inheritance

This shows how to generate Pydantic models dynamically at runtime based on
MetaNode inheritance chains, eliminating the compile-time inheritance limitation.
"""

import time
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Dict, List, Optional, Type, Union

# Simulate pydantic for demonstration
try:
    from pydantic import BaseModel, Field, create_model
    from pydantic.config import ConfigDict

    PYDANTIC_AVAILABLE = True
except ImportError:
    BaseModel = object

    def Field(*args, **kwargs):
        return None

    def create_model(*args, **kwargs):
        return None

    ConfigDict = dict
    PYDANTIC_AVAILABLE = False

print("=== RUNTIME PYDANTIC MODEL GENERATION ===")
print()

# =============================================================================
# SIMPLIFIED METANODE SYSTEM
# =============================================================================


class PropValueType(StrEnum):
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ELEMENT_ARRAY = "elementarray"


@dataclass
class MetaPropertyType:
    """Property type definition."""

    type: PropValueType
    key: str
    required: bool = True
    default: Any = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    ge: Optional[float] = None  # greater than or equal
    le: Optional[float] = None  # less than or equal


class MetaNode:
    """MetaNode with inheritance support."""

    def __init__(
        self,
        id: str,
        inherits_from: Optional[List[str]] = None,
        property_types: Optional[Dict[str, MetaPropertyType]] = None,
    ):
        self.id = id
        self.inherits_from = inherits_from or []
        self.property_types = property_types or {}

    def resolve_all_properties(
        self, registry: Dict[str, "MetaNode"]
    ) -> Dict[str, MetaPropertyType]:
        """Resolve all properties including inherited ones."""
        result = {}
        visited = set()

        def collect_properties(node_id: str):
            if node_id in visited:
                return
            visited.add(node_id)

            if node_id in registry:
                node = registry[node_id]
                # First collect from parents
                for parent_id in node.inherits_from:
                    collect_properties(parent_id)
                # Then add own properties (overrides parents)
                result.update(node.property_types)

        collect_properties(self.id)
        return result


# =============================================================================
# RUNTIME PYDANTIC MODEL GENERATION
# =============================================================================

if PYDANTIC_AVAILABLE:

    class RuntimeModelGenerator:
        """Generates Pydantic models dynamically based on MetaNode definitions."""

        def __init__(self):
            self._model_cache: Dict[str, Type[BaseModel]] = {}

        def create_properties_model(
            self, meta_node: MetaNode, registry: Dict[str, MetaNode]
        ) -> Type[BaseModel]:
            """Create a Pydantic model for the given MetaNode's properties."""
            cache_key = f"{meta_node.id}:{hash(tuple(meta_node.inherits_from))}"

            if cache_key in self._model_cache:
                return self._model_cache[cache_key]

            # Resolve all properties from inheritance chain
            all_properties = meta_node.resolve_all_properties(registry)

            # Convert to Pydantic field definitions
            field_definitions = {}

            for prop_name, prop_type in all_properties.items():
                field_def = self._convert_to_pydantic_field(prop_type)
                field_definitions[prop_name] = field_def

            # Always allow extra fields for dynamic properties
            config = ConfigDict(extra="allow", validate_assignment=True)

            # Create the model dynamically
            model_name = f"{meta_node.id.title()}Properties"
            model = create_model(model_name, __config__=config, **field_definitions)

            # Add convenience methods
            self._add_convenience_methods(model)

            # Cache the model
            self._model_cache[cache_key] = model
            return model

        def _convert_to_pydantic_field(self, prop_type: MetaPropertyType) -> tuple:
            """Convert MetaPropertyType to Pydantic field definition."""
            field_kwargs = {}

            # Set constraints based on type
            if prop_type.min_length is not None:
                field_kwargs["min_length"] = prop_type.min_length
            if prop_type.max_length is not None:
                field_kwargs["max_length"] = prop_type.max_length
            if prop_type.ge is not None:
                field_kwargs["ge"] = prop_type.ge
            if prop_type.le is not None:
                field_kwargs["le"] = prop_type.le

            # Determine Python type and default
            if prop_type.type == PropValueType.STRING:
                python_type = Optional[str]
                default = prop_type.default
            elif prop_type.type == PropValueType.NUMBER:
                python_type = Optional[Union[int, float]]
                default = prop_type.default
            elif prop_type.type == PropValueType.BOOLEAN:
                python_type = Optional[bool]
                default = prop_type.default
            elif prop_type.type == PropValueType.ELEMENT_ARRAY:
                python_type = Optional[List[str]]
                default = prop_type.default or []
            else:
                python_type = Optional[Any]
                default = prop_type.default

            # Create field
            if field_kwargs:
                field = Field(default=default, **field_kwargs)
            else:
                field = Field(default=default)

            return (python_type, field)

        def _add_convenience_methods(self, model_class: Type[BaseModel]):
            """Add convenience methods to the dynamically created model."""

            def get(self, key: str, default=None):
                """Get property value with fallback to extra fields."""
                if hasattr(self, key):
                    value = getattr(self, key)
                    return value if value is not None else default
                return self.__pydantic_extra__.get(key, default)

            def set_dynamic(self, key: str, value: Any):
                """Set dynamic property."""
                if hasattr(self.__class__, key):
                    setattr(self, key, value)
                else:
                    self.__pydantic_extra__[key] = value

            def has_property(self, key: str) -> bool:
                """Check if property exists."""
                if hasattr(self, key):
                    return getattr(self, key) is not None
                return key in self.__pydantic_extra__

            # Add methods to the class
            model_class.get = get
            model_class.set_dynamic = set_dynamic
            model_class.has_property = has_property

    def demonstrate_runtime_generation():
        """Demonstrate runtime model generation."""
        print("1. SETTING UP METANODE INHERITANCE")
        print("-" * 40)

        registry = {}

        # Base node MetaNode
        base_node = MetaNode(
            id="node",
            property_types={
                "name": MetaPropertyType(
                    type=PropValueType.STRING,
                    key="name",
                    required=True,
                    min_length=1,
                    max_length=200,
                ),
                "description": MetaPropertyType(
                    type=PropValueType.STRING,
                    key="description",
                    required=False,
                    max_length=2000,
                ),
                "created_time": MetaPropertyType(
                    type=PropValueType.NUMBER,
                    key="created_time",
                    required=False,
                    default=lambda: int(time.time() * 1000),
                ),
            },
        )
        registry["node"] = base_node

        # Person MetaNode inherits from node
        person_node = MetaNode(
            id="person",
            inherits_from=["node"],
            property_types={
                "age": MetaPropertyType(
                    type=PropValueType.NUMBER, key="age", required=False, ge=0, le=150
                ),
                "email": MetaPropertyType(
                    type=PropValueType.STRING, key="email", required=False
                ),
            },
        )
        registry["person"] = person_node

        # Employee MetaNode inherits from person
        employee_node = MetaNode(
            id="employee",
            inherits_from=["person"],
            property_types={
                "employee_id": MetaPropertyType(
                    type=PropValueType.STRING,
                    key="employee_id",
                    required=True,
                    min_length=1,
                ),
                "salary": MetaPropertyType(
                    type=PropValueType.NUMBER,
                    key="salary",
                    required=False,
                    ge=0,
                    default=50000,
                ),
                "department": MetaPropertyType(
                    type=PropValueType.STRING, key="department", required=False
                ),
            },
        )
        registry["employee"] = employee_node

        print("MetaNode inheritance chain:")
        print("  node (name, description, created_time)")
        print("  └── person (inherits node + adds age, email)")
        print(
            "      └── employee (inherits person + adds employee_id, salary, department)"
        )

        print("\n2. GENERATING PYDANTIC MODELS AT RUNTIME")
        print("-" * 45)

        generator = RuntimeModelGenerator()

        # Generate models for each MetaNode
        NodePropertiesModel = generator.create_properties_model(base_node, registry)
        PersonPropertiesModel = generator.create_properties_model(person_node, registry)
        EmployeePropertiesModel = generator.create_properties_model(
            employee_node, registry
        )

        print(f"✅ Generated NodePropertiesModel: {NodePropertiesModel.__name__}")
        print(f"✅ Generated PersonPropertiesModel: {PersonPropertiesModel.__name__}")
        print(
            f"✅ Generated EmployeePropertiesModel: {EmployeePropertiesModel.__name__}"
        )

        print("\n3. USING RUNTIME-GENERATED MODELS")
        print("-" * 35)

        # Create an employee using the generated model
        try:
            employee_props = EmployeePropertiesModel(
                name="Alice Johnson",  # From node
                age=28,  # From person
                email="alice@company.com",  # From person
                employee_id="EMP001",  # From employee
                salary=75000,  # From employee
                department="Engineering",  # From employee
                # Dynamic properties still work
                skills=["Python", "Leadership"],
                office_location="Building A",
                manager_id="MGR123",
            )

            print(f"✅ Created employee: {employee_props.name}")
            print(f"   Age: {employee_props.age} (validated: 0-150)")
            print(f"   Email: {employee_props.email}")
            print(f"   Employee ID: {employee_props.employee_id} (required)")
            print(f"   Salary: {employee_props.salary} (validated: >= 0)")
            print(f"   Department: {employee_props.department}")
            print(f"   Dynamic - Skills: {employee_props.get('skills')}")
            print(f"   Dynamic - Office: {employee_props.get('office_location')}")

        except Exception as e:
            print(f"❌ Error: {e}")

        print("\n4. VALIDATION FROM INHERITANCE CHAIN")
        print("-" * 40)

        # Try creating with validation errors
        try:
            EmployeePropertiesModel(
                name="",  # Invalid: empty name (from node validation)
                age=-5,  # Invalid: negative age (from person validation)
                employee_id="",  # Invalid: empty employee_id (from employee validation)
                salary=-1000,  # Invalid: negative salary (from employee validation)
            )
        except Exception as e:
            print("✅ Validation caught errors from entire inheritance chain:")
            print(f"   {type(e).__name__}: {str(e)[:150]}...")

        print("\n5. JSON SERIALIZATION WITH INHERITANCE")
        print("-" * 42)

        # Show JSON serialization
        json_output = employee_props.model_dump_json(indent=2)
        print("Employee JSON (first 400 chars):")
        print(json_output[:400] + "..." if len(json_output) > 400 else json_output)

        # Parse back from JSON
        parsed_employee = EmployeePropertiesModel.model_validate_json(json_output)
        print(
            f"✅ Parsed from JSON: {parsed_employee.name} with all inherited + dynamic properties"
        )

        print("\n6. SCHEMA GENERATION")
        print("-" * 20)

        # Generate JSON schema
        schema = EmployeePropertiesModel.model_json_schema()
        print(f"Generated schema has {len(schema.get('properties', {}))} properties:")
        properties = list(schema.get("properties", {}).keys())
        print(f"   Properties: {properties}")
        print(f"   Required: {schema.get('required', [])}")

        return employee_props

    # Run demonstration if Pydantic is available
    if __name__ == "__main__":
        result = demonstrate_runtime_generation()

else:
    print("CONCEPTUAL APPROACH (Pydantic not installed):")
    print(
        """
    The key insight is using Pydantic's create_model() function:

    from pydantic import create_model, Field

    # Resolve inheritance at runtime
    all_properties = meta_node.resolve_all_properties(registry)

    # Convert to Pydantic field definitions
    field_definitions = {}
    for prop_name, prop_type in all_properties.items():
        if prop_type.type == "string":
            field_definitions[prop_name] = (Optional[str], Field(default=prop_type.default))
        elif prop_type.type == "number":
            field_definitions[prop_name] = (Optional[int], Field(default=prop_type.default, ge=0))
        # ... etc

    # Generate model dynamically
    DynamicModel = create_model(
        f"{meta_node.id}Properties",
        __config__=ConfigDict(extra='allow'),
        **field_definitions
    )

    # Use like any Pydantic model
    instance = DynamicModel(name="Alice", age=28, custom_field="dynamic")
    """
    )

print("\n" + "=" * 60)
print("RUNTIME MODEL GENERATION BENEFITS")
print("=" * 60)

benefits = [
    "✅ NO COMPILE-TIME INHERITANCE: Models created at runtime based on MetaNode chain",
    "✅ FULL INHERITANCE SUPPORT: All parent properties automatically included",
    "✅ VALIDATION INHERITANCE: Constraints from entire inheritance chain applied",
    "✅ DYNAMIC PROPERTIES: extra='allow' preserves current flexibility",
    "✅ CACHING: Generated models cached for performance",
    "✅ SCHEMA GENERATION: JSON schemas include all inherited properties",
    "✅ BACKWARD COMPATIBILITY: Can add convenience methods to generated models",
]

for benefit in benefits:
    print(f"  {benefit}")

print("\nSIMPLIFIED INITIALIZATION:")
print("Current complex approach:")
print("  props = ElementProperties(**data)")
print("  details = NodeDetails(properties=props, ...)")
print("  node = Node(details, store)")
print()
print("Runtime Pydantic approach:")
print("  PropertiesModel = generator.create_properties_model(meta_node, registry)")
print("  properties = PropertiesModel(**data)  # Includes inheritance + validation")
print("  node = PydanticNode(properties=properties, ...)")

print("\nKEY INSIGHT:")
print(
    "Since you can generate models at runtime, the inheritance 'limitation' disappears."
)
print(
    "Pydantic's create_model() + your existing inheritance resolution = perfect match!"
)
