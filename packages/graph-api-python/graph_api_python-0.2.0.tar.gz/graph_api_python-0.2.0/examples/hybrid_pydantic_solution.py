"""
Concrete Example: Hybrid Pydantic + Dynamic Properties Solution

This shows how to maintain the current inheritance system and dynamic properties
while adding Pydantic validation for core fields.
"""

import re
import time
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Dict, List, Optional

print("=== HYBRID SOLUTION: PYDANTIC + DYNAMIC PROPERTIES ===")
print()

# =============================================================================
# CURRENT SYSTEM SIMULATION
# =============================================================================


class PropValueType(StrEnum):
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ELEMENT_ARRAY = "elementarray"


@dataclass
class MetaPropertyType:
    """Simplified MetaPropertyType for demonstration."""

    type: PropValueType
    key: str
    required: bool = True
    default: Any = None


class MetaNode:
    """Simplified MetaNode showing inheritance resolution."""

    def __init__(
        self,
        id: str,
        inherits_from: List[str] = None,
        property_types: Dict[str, MetaPropertyType] = None,
    ):
        self.id = id
        self.inherits_from = inherits_from or []
        self.property_types = property_types or {}
        self._registry = {}  # Global registry simulation

    def get_all_property_types(
        self, registry: Dict[str, "MetaNode"]
    ) -> Dict[str, MetaPropertyType]:
        """Simulate inheritance resolution."""
        result = {}

        # Collect from inheritance chain
        for parent_id in self.inherits_from:
            if parent_id in registry:
                parent_props = registry[parent_id].get_all_property_types(registry)
                result.update(parent_props)

        # Override with own properties
        result.update(self.property_types)
        return result


# =============================================================================
# HYBRID PYDANTIC SOLUTION
# =============================================================================

try:
    from pydantic import BaseModel, Field, root_validator, validator
    from pydantic.config import ConfigDict

    PYDANTIC_AVAILABLE = True
    print("Pydantic available - showing working implementation")
except ImportError:
    # Fallback for demonstration
    BaseModel = object

    def Field(*args, **kwargs):
        return None

    def validator(*args, **kwargs):
        return lambda f: f

    def root_validator(*args, **kwargs):
        return lambda f: f

    ConfigDict = dict
    PYDANTIC_AVAILABLE = False
    print("Pydantic not available - showing conceptual structure")

print()

if PYDANTIC_AVAILABLE:

    class HybridElementProperties(BaseModel):
        """Hybrid approach: Pydantic validation + dynamic properties."""

        model_config = ConfigDict(
            extra="allow",  # Allow dynamic properties
            validate_assignment=True,  # Validate on property changes
            str_strip_whitespace=True,  # Auto-clean strings
        )

        # CORE VALIDATED FIELDS
        name: Optional[str] = Field(None, min_length=1, max_length=200)
        description: Optional[str] = Field(None, max_length=2000)
        created_time: int = Field(default_factory=lambda: int(time.time() * 1000))
        updated_time: int = Field(default_factory=lambda: int(time.time() * 1000))
        tags: List[str] = Field(default_factory=list)

        # COMMON OPTIONAL FIELDS (validated when present)
        age: Optional[int] = Field(None, ge=0, le=150)
        email: Optional[str] = None
        occupation: Optional[str] = Field(None, min_length=1, max_length=100)
        city: Optional[str] = Field(None, min_length=1, max_length=100)

        @validator("email")
        def validate_email(cls, v):
            """Validate email format."""
            if v is None:
                return v
            email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            if not re.match(email_pattern, v):
                raise ValueError("Invalid email format")
            return v.lower()

        @validator("tags", pre=True)
        def normalize_tags(cls, v):
            """Normalize tags input."""
            if isinstance(v, str):
                return [v]
            if isinstance(v, list):
                return [str(tag).strip() for tag in v if str(tag).strip()]
            return v or []

        @root_validator(pre=True)
        def validate_dynamic_fields(cls, values):
            """Custom validation for dynamic fields."""
            # Validate salary if present
            if "salary" in values:
                salary = values["salary"]
                if isinstance(salary, (int, float)) and salary < 0:
                    raise ValueError("Salary cannot be negative")

            # Validate skills array if present
            if "skills" in values:
                skills = values["skills"]
                if not isinstance(skills, list):
                    values["skills"] = [skills] if skills else []

            return values

        # BACKWARD COMPATIBILITY METHODS
        def get(self, key: str, default=None):
            """Get property value (maintains current API)."""
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

        def get_all_properties(self) -> Dict[str, Any]:
            """Get all properties including dynamic ones."""
            result = {}

            # Add defined fields that have values
            for field_name, _field_info in self.__fields__.items():
                value = getattr(self, field_name)
                if value is not None:
                    result[field_name] = value

            # Add dynamic properties
            result.update(self.__pydantic_extra__)
            return result

    class MetaNodeCompatibleProperties(HybridElementProperties):
        """Properties that work with MetaNode inheritance."""

        def __init__(
            self,
            meta_node: Optional[MetaNode] = None,
            registry: Dict[str, MetaNode] = None,
            **data,
        ):
            """Initialize with MetaNode inheritance resolution."""
            if meta_node and registry:
                resolved_data = self._resolve_inheritance(meta_node, registry, data)
                super().__init__(**resolved_data)
            else:
                super().__init__(**data)

        def _resolve_inheritance(
            self,
            meta_node: MetaNode,
            registry: Dict[str, MetaNode],
            data: Dict[str, Any],
        ) -> Dict[str, Any]:
            """Resolve MetaNode inheritance before Pydantic validation."""
            all_property_types = meta_node.get_all_property_types(registry)
            resolved_data = data.copy()

            # Apply defaults from MetaNode property types
            for key, prop_type in all_property_types.items():
                if key not in resolved_data and prop_type.default is not None:
                    resolved_data[key] = prop_type.default

            return resolved_data

    def demonstrate_hybrid_solution():
        """Show the hybrid solution in action."""
        print("1. BASIC USAGE WITH VALIDATION")
        print("-" * 35)

        try:
            # Create properties with validation
            props = HybridElementProperties(
                name="Alice Johnson",
                age=28,
                email="alice@company.com",
                occupation="Software Engineer",
                tags=["python", "backend"],
                # Dynamic properties
                employee_id="EMP001",
                department="Engineering",
                skills=["Python", "Docker", "Kubernetes"],
                salary=95000,
            )

            print(f"✅ Created properties for: {props.name}")
            print(f"   Email: {props.email}")
            print(f"   Age: {props.age} (validated: 0 <= age <= 150)")
            print(f"   Dynamic - Employee ID: {props.get('employee_id')}")
            print(f"   Dynamic - Skills: {props.get('skills')}")
            print(f"   All properties: {len(props.get_all_properties())} fields")

        except Exception as e:
            print(f"❌ Validation error: {e}")

        print("\n2. VALIDATION IN ACTION")
        print("-" * 25)

        try:
            # This should fail validation
            HybridElementProperties(
                name="",  # Too short
                age=-5,  # Negative age
                email="not-an-email",  # Invalid format
                salary=-1000,  # Negative salary (custom validation)
            )
        except Exception as e:
            print("✅ Validation caught multiple errors:")
            print(f"   {type(e).__name__}: {str(e)[:100]}...")

        print("\n3. DYNAMIC PROPERTIES WORK")
        print("-" * 30)

        # Create with dynamic properties
        flexible_props = HybridElementProperties(
            name="Bob",
            # Any dynamic properties
            custom_field="custom value",
            metadata={"source": "import", "confidence": 0.95},
            scores=[85, 92, 78],
            is_verified=True,
        )

        print("✅ Dynamic properties preserved:")
        print(f"   custom_field: {flexible_props.get('custom_field')}")
        print(f"   metadata: {flexible_props.get('metadata')}")
        print(f"   scores: {flexible_props.get('scores')}")

        # Modify dynamic properties
        flexible_props.set_dynamic("new_field", "new value")
        print(f"   new_field: {flexible_props.get('new_field')}")

        print("\n4. METANODE INHERITANCE")
        print("-" * 25)

        # Setup MetaNode inheritance
        registry = {}

        # Base person MetaNode
        person_meta = MetaNode(
            id="person",
            property_types={
                "name": MetaPropertyType(
                    type=PropValueType.STRING, key="name", required=True
                ),
                "age": MetaPropertyType(
                    type=PropValueType.NUMBER, key="age", required=False, default=0
                ),
            },
        )
        registry["person"] = person_meta

        # Employee extends person
        employee_meta = MetaNode(
            id="employee",
            inherits_from=["person"],
            property_types={
                "employee_id": MetaPropertyType(
                    type=PropValueType.STRING, key="employee_id", required=True
                ),
                "salary": MetaPropertyType(
                    type=PropValueType.NUMBER,
                    key="salary",
                    required=False,
                    default=50000,
                ),
            },
        )
        registry["employee"] = employee_meta

        # Create properties with inheritance
        employee_props = MetaNodeCompatibleProperties(
            meta_node=employee_meta,
            registry=registry,
            name="Charlie Brown",
            employee_id="EMP002",
            # age and salary will get defaults from MetaNode
        )

        print("✅ Employee created with inheritance:")
        print(f"   Name: {employee_props.name}")
        print(f"   Age: {employee_props.age} (default from person MetaNode)")
        print(f"   Employee ID: {employee_props.get('employee_id')}")
        print(
            f"   Salary: {employee_props.get('salary')} (default from employee MetaNode)"
        )

        print("\n5. JSON SERIALIZATION")
        print("-" * 20)

        # Serialize to JSON (includes all fields)
        json_str = props.model_dump_json(indent=2)
        print("JSON output (first 300 chars):")
        print(json_str[:300] + "..." if len(json_str) > 300 else json_str)

        # Parse from JSON
        props_copy = HybridElementProperties.model_validate_json(json_str)
        print(
            f"✅ Parsed from JSON: {props_copy.name} with {len(props_copy.get_all_properties())} properties"
        )

        return props

    # Run demonstration
    if __name__ == "__main__":
        result = demonstrate_hybrid_solution()

else:
    print("CONCEPTUAL STRUCTURE (Pydantic not installed):")
    print(
        """
    class HybridElementProperties(BaseModel):
        model_config = ConfigDict(extra='allow', validate_assignment=True)

        # VALIDATED CORE FIELDS
        name: Optional[str] = Field(None, min_length=1, max_length=200)
        age: Optional[int] = Field(None, ge=0, le=150)
        email: Optional[str] = None

        # DYNAMIC PROPERTIES AUTOMATICALLY STORED IN __pydantic_extra__

        @validator('email')
        def validate_email(cls, v):
            # Email validation logic
            return v

        @root_validator(pre=True)
        def validate_dynamic_fields(cls, values):
            # Custom validation for dynamic fields
            return values

        def get(self, key: str, default=None):
            # Backward compatibility with current API
            if hasattr(self, key):
                return getattr(self, key)
            return self.__pydantic_extra__.get(key, default)

    USAGE:
    props = HybridElementProperties(
        name="Alice",           # Validated
        age=28,                 # Validated (0 <= age <= 150)
        custom_field="value"    # Dynamic property (stored in __pydantic_extra__)
    )

    print(props.name)                    # Alice
    print(props.get('custom_field'))     # value
    print(props.model_dump_json())       # Includes all fields
    """
    )

print("\n" + "=" * 60)
print("HYBRID SOLUTION BENEFITS")
print("=" * 60)

benefits = [
    "✅ VALIDATION: Core fields get full Pydantic validation",
    "✅ FLEXIBILITY: Dynamic properties work exactly like current system",
    "✅ COMPATIBILITY: Maintains current API (get/set methods)",
    "✅ SERIALIZATION: JSON in/out includes all fields automatically",
    "✅ INHERITANCE: MetaNode inheritance resolution preserved",
    "✅ TYPE SAFETY: IDE support and type checking for core fields",
    "✅ PERFORMANCE: Validation only where needed, dynamic fields are fast",
    "✅ MIGRATION: Can migrate incrementally field by field",
]

for benefit in benefits:
    print(f"  {benefit}")

print("\nCHALLENGES ADDRESSED:")
challenges = [
    "🔧 Runtime inheritance → Keep current MetaNode resolution, apply before Pydantic",
    "🔧 Dynamic properties → Use extra='allow' + __pydantic_extra__",
    "🔧 Complex merging → Keep existing inheritance logic in custom __init__",
    "🔧 Backward compatibility → Add get/set methods that work with both systems",
    "🔧 Validation flexibility → Custom validators for dynamic fields",
]

for challenge in challenges:
    print(f"  {challenge}")

print("\nRECOMMENDATION:")
print("This hybrid approach provides the best of both worlds:")
print("• Pydantic validation and serialization for core, well-known fields")
print("• Complete flexibility for dynamic, user-defined properties")
print("• Maintains all current functionality and APIs")
print("• Enables gradual migration without breaking changes")
