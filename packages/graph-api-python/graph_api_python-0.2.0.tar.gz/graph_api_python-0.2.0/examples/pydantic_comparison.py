"""
Comparison of current dataclass implementation vs proposed Pydantic implementation
for creating Person nodes and relationship edges.

This example shows how initialization would work with both approaches.
Note: Pydantic imports will fail unless pydantic is installed - this is just for demonstration.
"""

import time
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Dict, List, Optional

# Pydantic imports (would need: pip install pydantic)
try:
    from pydantic import BaseModel, Field, root_validator, validator
    from pydantic.config import ConfigDict

    PYDANTIC_AVAILABLE = True
except ImportError:
    # Fallback classes for demonstration
    BaseModel = object

    def Field(*args, **kwargs):
        return None

    def validator(*args, **kwargs):
        return lambda f: f

    def root_validator(*args, **kwargs):
        return lambda f: f

    ConfigDict = dict
    PYDANTIC_AVAILABLE = False

# =============================================================================
# CURRENT IMPLEMENTATION (Dataclasses)
# =============================================================================


class NodeTypes(StrEnum):
    NODE = "node"
    META = "meta"
    EDGE = "edge"


@dataclass(frozen=True, slots=True)
class CurrentDataContext:
    property: Optional[str] = None
    source_id: Optional[str] = None
    legend: Optional[Dict[str, Any]] = None
    dv: Optional[Any] = None
    extra_data: Dict[str, Any] = field(default_factory=dict)


class CurrentElementProperties:
    __slots__ = (
        "name",
        "description",
        "tags",
        "created_time",
        "created_by",
        "updated_time",
        "age",
        "occupation",
        "city",
        "extra_properties",
    )

    def __init__(self, **kwargs):
        # Core properties
        self.name: Optional[str] = None
        self.description: Optional[str] = None
        self.tags: Optional[List[str]] = None
        self.created_time: Optional[int] = None
        self.created_by: Optional[str] = None
        self.updated_time: Optional[int] = None

        # Person-specific properties
        self.age: Optional[int] = None
        self.occupation: Optional[str] = None
        self.city: Optional[str] = None

        # Dynamic properties
        self.extra_properties: Dict[str, Any] = {}

        # Set from kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                self.extra_properties[key] = value

    def __getitem__(self, key: str) -> Any:
        if hasattr(self, key):
            return getattr(self, key)
        return self.extra_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        if hasattr(self, key):
            setattr(self, key, value)
        else:
            self.extra_properties[key] = value


@dataclass(slots=True)
class CurrentElementDetails:
    id: str
    class_id: str
    type: NodeTypes
    properties: CurrentElementProperties
    to_id: Optional[str] = None
    from_id: Optional[str] = None
    source: Optional[str] = None


@dataclass(slots=True)
class CurrentNodeDetails(CurrentElementDetails):
    def __post_init__(self):
        if not self.id:
            raise ValueError("Node ID is required")
        if not self.class_id:
            raise ValueError("Node class_id is required")
        self.type = NodeTypes.NODE


@dataclass(slots=True)
class CurrentEdgeDetails(CurrentElementDetails):
    from_id: str
    to_id: str

    def __post_init__(self):
        if not self.from_id:
            raise ValueError("Edge from_id is required")
        if not self.to_id:
            raise ValueError("Edge to_id is required")
        if not self.id:
            raise ValueError("Edge ID is required")
        if not self.class_id:
            raise ValueError("Edge class_id is required")
        self.type = NodeTypes.EDGE


# =============================================================================
# PROPOSED PYDANTIC IMPLEMENTATION
# =============================================================================

from pydantic import BaseModel, Field, root_validator, validator
from pydantic.config import ConfigDict


class PydanticDataContext(BaseModel):
    """Pydantic version of DataContext with automatic validation."""

    model_config = ConfigDict(frozen=True, extra="allow")

    property: Optional[str] = None
    source_id: Optional[str] = None
    legend: Optional[Dict[str, Any]] = None
    dv: Optional[Any] = None
    extra_data: Dict[str, Any] = Field(default_factory=dict)


class PydanticElementProperties(BaseModel):
    """Pydantic version with automatic validation and serialization."""

    model_config = ConfigDict(
        extra="allow",  # Allow dynamic properties
        validate_assignment=True,  # Validate on property changes
        arbitrary_types_allowed=True,
    )

    # Core properties with validation
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = Field(default_factory=list)
    created_time: Optional[int] = Field(default_factory=lambda: int(time.time() * 1000))
    created_by: Optional[str] = None
    updated_time: Optional[int] = Field(default_factory=lambda: int(time.time() * 1000))

    # Person-specific properties with validation
    age: Optional[int] = Field(None, ge=0, le=150, description="Person's age in years")
    occupation: Optional[str] = Field(None, min_length=1, max_length=100)
    city: Optional[str] = Field(None, min_length=1, max_length=100)

    @validator("tags", pre=True)
    def validate_tags(cls, v):
        """Ensure tags is a list of strings."""
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        if isinstance(v, list):
            return [str(tag) for tag in v]
        return v

    @validator("name")
    def validate_name(cls, v):
        """Validate name is not just whitespace."""
        if v and not v.strip():
            raise ValueError("Name cannot be empty or just whitespace")
        return v.strip() if v else v


class PydanticElementDetails(BaseModel):
    """Base element details with Pydantic validation."""

    model_config = ConfigDict(validate_assignment=True)

    id: str = Field(..., min_length=1, description="Unique element identifier")
    class_id: str = Field(..., min_length=1, description="Element class identifier")
    type: NodeTypes
    properties: PydanticElementProperties
    to_id: Optional[str] = None
    from_id: Optional[str] = None
    source: Optional[str] = None

    @validator("id", "class_id")
    def validate_required_strings(cls, v):
        """Ensure required string fields are not empty."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()


class PydanticNodeDetails(PydanticElementDetails):
    """Node-specific details with automatic type setting."""

    type: NodeTypes = Field(default=NodeTypes.NODE, const=True)

    # Nodes shouldn't have from_id/to_id
    from_id: None = Field(default=None, const=True)
    to_id: None = Field(default=None, const=True)


class PydanticEdgeDetails(PydanticElementDetails):
    """Edge-specific details with required from/to relationships."""

    type: NodeTypes = Field(default=NodeTypes.EDGE, const=True)
    from_id: str = Field(..., min_length=1, description="Source node ID")
    to_id: str = Field(..., min_length=1, description="Target node ID")

    @validator("from_id", "to_id")
    def validate_edge_connections(cls, v):
        """Validate edge connection IDs."""
        if not v or not v.strip():
            raise ValueError("Edge connections cannot be empty")
        return v.strip()

    @root_validator
    def validate_edge_not_self_referencing(cls, values):
        """Ensure edge doesn't connect node to itself."""
        from_id = values.get("from_id")
        to_id = values.get("to_id")
        if from_id and to_id and from_id == to_id:
            raise ValueError("Edge cannot connect a node to itself")
        return values


# =============================================================================
# USAGE EXAMPLES
# =============================================================================


def current_implementation_example():
    """Example using current dataclass implementation."""
    print("=== CURRENT DATACLASS IMPLEMENTATION ===")

    # Create person properties
    alice_props = CurrentElementProperties(
        name="Alice Johnson",
        age=28,
        occupation="Software Engineer",
        city="San Francisco",
        tags=["tech", "python"],
        created_by="system",
    )

    bob_props = CurrentElementProperties(
        name="Bob Smith",
        age=32,
        occupation="Product Manager",
        city="New York",
        tags=["product", "management"],
    )

    # Create person nodes
    alice_details = CurrentNodeDetails(
        id="person-alice-001",
        class_id="person",
        type=NodeTypes.NODE,
        properties=alice_props,
    )

    bob_details = CurrentNodeDetails(
        id="person-bob-001",
        class_id="person",
        type=NodeTypes.NODE,
        properties=bob_props,
    )

    print(
        f"Alice: {alice_details.properties.name}, {alice_details.properties.age} years old"
    )
    print(f"Bob: {bob_details.properties.name}, {bob_details.properties.age} years old")

    # Create relationship edge
    relationship_props = CurrentElementProperties(
        name="colleagues",
        description="Work colleagues at the same company",
        relationship_type="professional",
    )

    edge_details = CurrentEdgeDetails(
        id="edge-colleague-001",
        class_id="colleague_relationship",
        type=NodeTypes.EDGE,
        from_id=alice_details.id,
        to_id=bob_details.id,
        properties=relationship_props,
    )

    print(
        f"Relationship: {alice_details.properties.name} -> {relationship_props.name} -> {bob_details.properties.name}"
    )

    # Manual validation required
    try:
        # This would pass without validation
        CurrentElementProperties(age=-5)  # Invalid age
        print("❌ Invalid age passed without validation!")
    except:
        print("✅ Validation caught invalid age")

    return alice_details, bob_details, edge_details


def pydantic_implementation_example():
    """Example using proposed Pydantic implementation."""
    print("\n=== PROPOSED PYDANTIC IMPLEMENTATION ===")

    # Create person nodes - automatic validation
    try:
        alice_details = PydanticNodeDetails(
            id="person-alice-001",
            class_id="person",
            properties=PydanticElementProperties(
                name="Alice Johnson",
                age=28,
                occupation="Software Engineer",
                city="San Francisco",
                tags=["tech", "python"],
                created_by="system",
            ),
        )

        bob_details = PydanticNodeDetails(
            id="person-bob-001",
            class_id="person",
            properties=PydanticElementProperties(
                name="Bob Smith",
                age=32,
                occupation="Product Manager",
                city="New York",
                tags=["product", "management"],
            ),
        )

        print(
            f"✅ Alice: {alice_details.properties.name}, {alice_details.properties.age} years old"
        )
        print(
            f"✅ Bob: {bob_details.properties.name}, {bob_details.properties.age} years old"
        )

        # Create relationship edge with validation
        edge_details = PydanticEdgeDetails(
            id="edge-colleague-001",
            class_id="colleague_relationship",
            from_id=alice_details.id,
            to_id=bob_details.id,
            properties=PydanticElementProperties(
                name="colleagues",
                description="Work colleagues at the same company",
                relationship_type="professional",  # Dynamic property
            ),
        )

        print(
            f"✅ Relationship: {alice_details.properties.name} -> {edge_details.properties.name} -> {bob_details.properties.name}"
        )

    except Exception as e:
        print(f"❌ Validation error: {e}")

    # Demonstrate automatic validation
    print("\n--- Validation Examples ---")

    # Invalid age validation
    try:
        PydanticNodeDetails(
            id="person-invalid",
            class_id="person",
            properties=PydanticElementProperties(
                name="Invalid Person", age=-5  # Invalid age
            ),
        )
    except ValueError as e:
        print(f"✅ Age validation caught: {e}")

    # Empty name validation
    try:
        PydanticNodeDetails(
            id="person-empty",
            class_id="person",
            properties=PydanticElementProperties(name="   ", age=25),  # Empty name
        )
    except ValueError as e:
        print(f"✅ Name validation caught: {e}")

    # Self-referencing edge validation
    try:
        PydanticEdgeDetails(
            id="edge-self",
            class_id="self_relationship",
            from_id="person-alice-001",
            to_id="person-alice-001",  # Same as from_id
            properties=PydanticElementProperties(name="self-reference"),
        )
    except ValueError as e:
        print(f"✅ Self-reference validation caught: {e}")

    # JSON serialization example
    print("\n--- Serialization Examples ---")
    alice_json = alice_details.model_dump_json(indent=2)
    print("Alice as JSON:")
    print(alice_json)

    # Schema generation
    print("\n--- Schema Generation ---")
    schema = PydanticNodeDetails.model_json_schema()
    print("Node schema keys:", list(schema.keys()))

    return alice_details, bob_details, edge_details


# =============================================================================
# PERFORMANCE AND USAGE COMPARISON
# =============================================================================


def compare_initialization_patterns():
    """Compare initialization patterns between implementations."""
    print("\n=== INITIALIZATION PATTERN COMPARISON ===")

    print("\n1. CURRENT - Manual property creation:")
    print(
        """
    props = CurrentElementProperties(
        name="Alice",
        age=28,
        occupation="Engineer"
    )
    node = CurrentNodeDetails(
        id="alice-001",
        class_id="person",
        type=NodeTypes.NODE,
        properties=props
    )
    # Manual validation in __post_init__
    """
    )

    print("2. PYDANTIC - Automatic validation and parsing:")
    print(
        """
    node = PydanticNodeDetails(
        id="alice-001",
        class_id="person",
        properties={  # Can pass dict directly!
            "name": "Alice",
            "age": 28,
            "occupation": "Engineer"
        }
    )
    # Automatic validation, parsing, and type conversion
    """
    )

    print("3. PYDANTIC - From JSON:")
    print(
        """
    json_data = '{"id": "alice-001", "class_id": "person", "properties": {...}}'
    node = PydanticNodeDetails.model_validate_json(json_data)
    # Direct JSON parsing with validation
    """
    )

    print("4. PYDANTIC - Partial updates:")
    print(
        """
    # Update with validation
    node.properties.age = 29  # Validates automatically

    # Bulk update
    updates = {"age": 30, "city": "Boston"}
    updated_props = node.properties.model_copy(update=updates)
    """
    )


def demonstrate_advanced_pydantic_features():
    """Show advanced Pydantic features that would benefit the library."""
    print("\n=== ADVANCED PYDANTIC FEATURES ===")

    # Custom validators
    class PersonProperties(PydanticElementProperties):
        email: Optional[str] = None

        @validator("email")
        def validate_email(cls, v):
            if v and "@" not in v:
                raise ValueError("Invalid email format")
            return v

        @root_validator
        def validate_person_business_rules(cls, values):
            age = values.get("age")
            occupation = values.get("occupation")

            # Business rule: minors can't have certain occupations
            if age and age < 18 and occupation in ["CEO", "Manager"]:
                raise ValueError(f"Person under 18 cannot be {occupation}")
            return values

    # Demonstrate usage
    try:
        PersonProperties(
            name="Young CEO",
            age=16,
            occupation="CEO",  # This should fail validation
            email="young@company.com",
        )
    except ValueError as e:
        print(f"✅ Business rule validation: {e}")

    # Config-driven validation
    print("\n--- Config-driven features ---")
    print("- Field aliases for API compatibility")
    print("- Custom serializers for complex types")
    print("- Computed fields for derived properties")
    print("- Discriminated unions for polymorphic types")


if __name__ == "__main__":
    # Run examples
    current_alice, current_bob, current_edge = current_implementation_example()
    pydantic_alice, pydantic_bob, pydantic_edge = pydantic_implementation_example()

    compare_initialization_patterns()
    demonstrate_advanced_pydantic_features()
