"""
Initialization Comparison: Current vs Pydantic Implementation

This example demonstrates how creating Person nodes and relationships would work
with both the current dataclass implementation and a proposed Pydantic version.
"""

import time
from dataclasses import dataclass
from enum import StrEnum

# =============================================================================
# CURRENT IMPLEMENTATION SIMPLIFIED
# =============================================================================


class NodeTypes(StrEnum):
    NODE = "node"
    EDGE = "edge"


class CurrentElementProperties:
    """Current implementation using slots and manual validation."""

    def __init__(self, **kwargs):
        # Set properties from kwargs
        self.name = kwargs.get("name")
        self.age = kwargs.get("age")
        self.occupation = kwargs.get("occupation")
        self.city = kwargs.get("city")
        self.tags = kwargs.get("tags", [])
        self.created_time = kwargs.get("created_time", int(time.time() * 1000))
        self.updated_time = kwargs.get("updated_time", int(time.time() * 1000))

        # Store extra properties
        self._extra = {
            k: v
            for k, v in kwargs.items()
            if k
            not in [
                "name",
                "age",
                "occupation",
                "city",
                "tags",
                "created_time",
                "updated_time",
            ]
        }

    def get(self, key: str, default=None):
        return getattr(self, key, self._extra.get(key, default))


@dataclass
class CurrentNodeData:
    """Current node data structure."""

    id: str
    class_id: str
    type: NodeTypes
    properties: CurrentElementProperties

    def __post_init__(self):
        # Manual validation
        if not self.id:
            raise ValueError("Node ID is required")
        if not self.class_id:
            raise ValueError("Node class_id is required")


@dataclass
class CurrentEdgeData:
    """Current edge data structure."""

    id: str
    class_id: str
    type: NodeTypes
    from_id: str
    to_id: str
    properties: CurrentElementProperties

    def __post_init__(self):
        # Manual validation
        if not self.from_id or not self.to_id:
            raise ValueError("Edge must have both from_id and to_id")
        if self.from_id == self.to_id:
            raise ValueError("Edge cannot be self-referencing")


# =============================================================================
# PROPOSED PYDANTIC IMPLEMENTATION (CONCEPTUAL)
# =============================================================================

# This shows what the Pydantic version would look like structurally
# (actual Pydantic import would be needed for real implementation)


class PydanticElementPropertiesStructure:
    """
    Conceptual Pydantic structure - shows what validation would look like:

    class PydanticElementProperties(BaseModel):
        model_config = ConfigDict(extra='allow', validate_assignment=True)

        # Validated fields with constraints
        name: Optional[str] = Field(None, min_length=1, max_length=200)
        age: Optional[int] = Field(None, ge=0, le=150, description="Age in years")
        occupation: Optional[str] = Field(None, min_length=1, max_length=100)
        city: Optional[str] = Field(None, min_length=1, max_length=100)
        tags: List[str] = Field(default_factory=list)
        created_time: int = Field(default_factory=lambda: int(time.time() * 1000))
        updated_time: int = Field(default_factory=lambda: int(time.time() * 1000))

        @validator('name')
        def validate_name(cls, v):
            if v and not v.strip():
                raise ValueError('Name cannot be empty')
            return v.strip() if v else v

        @validator('tags', pre=True)
        def validate_tags(cls, v):
            if isinstance(v, str):
                return [v]
            return v or []
    """

    pass


class PydanticNodeDataStructure:
    """
    Conceptual Pydantic node structure:

    class PydanticNodeData(BaseModel):
        model_config = ConfigDict(validate_assignment=True)

        id: str = Field(..., min_length=1, description="Unique identifier")
        class_id: str = Field(..., min_length=1, description="Node class")
        type: NodeTypes = Field(default=NodeTypes.NODE, const=True)
        properties: PydanticElementProperties

        @validator('id', 'class_id')
        def validate_required_fields(cls, v):
            if not v.strip():
                raise ValueError('Field cannot be empty')
            return v.strip()
    """

    pass


class PydanticEdgeDataStructure:
    """
    Conceptual Pydantic edge structure:

    class PydanticEdgeData(BaseModel):
        id: str = Field(..., min_length=1)
        class_id: str = Field(..., min_length=1)
        type: NodeTypes = Field(default=NodeTypes.EDGE, const=True)
        from_id: str = Field(..., min_length=1, description="Source node")
        to_id: str = Field(..., min_length=1, description="Target node")
        properties: PydanticElementProperties

        @root_validator
        def validate_edge_connections(cls, values):
            from_id = values.get('from_id')
            to_id = values.get('to_id')
            if from_id == to_id:
                raise ValueError('Edge cannot be self-referencing')
            return values
    """

    pass


# =============================================================================
# USAGE EXAMPLES
# =============================================================================


def current_implementation_example():
    """Show how to create nodes and edges with current implementation."""
    print("=== CURRENT DATACLASS IMPLEMENTATION ===")

    # Create Alice
    alice_props = CurrentElementProperties(
        name="Alice Johnson",
        age=28,
        occupation="Software Engineer",
        city="San Francisco",
        tags=["tech", "python"],
        department="Engineering",  # Dynamic property
    )

    alice = CurrentNodeData(
        id="person-alice-001",
        class_id="person",
        type=NodeTypes.NODE,
        properties=alice_props,
    )

    # Create Bob
    bob_props = CurrentElementProperties(
        name="Bob Smith",
        age=32,
        occupation="Product Manager",
        city="New York",
        tags=["product", "strategy"],
    )

    bob = CurrentNodeData(
        id="person-bob-001",
        class_id="person",
        type=NodeTypes.NODE,
        properties=bob_props,
    )

    # Create relationship
    colleague_props = CurrentElementProperties(
        name="colleagues",
        relationship_type="professional",
        strength=8,  # Dynamic property
    )

    relationship = CurrentEdgeData(
        id="edge-colleague-001",
        class_id="colleague_relationship",
        type=NodeTypes.EDGE,
        from_id=alice.id,
        to_id=bob.id,
        properties=colleague_props,
    )

    print(f"✅ Created: {alice.properties.name} ({alice.properties.age})")
    print(f"✅ Created: {bob.properties.name} ({bob.properties.age})")
    print(
        f"✅ Relationship: {alice.properties.name} -> {colleague_props.name} -> {bob.properties.name}"
    )

    # Show current limitations
    print("\n--- Current Limitations ---")

    # No automatic validation
    invalid_props = CurrentElementProperties(
        name="", age=-5  # Empty name - not caught  # Invalid age - not caught
    )
    CurrentNodeData(
        id="invalid-node",
        class_id="person",
        type=NodeTypes.NODE,
        properties=invalid_props,
    )
    print("❌ Invalid data created without validation errors")

    # Manual serialization needed
    def to_dict(obj):
        if hasattr(obj, "__dict__"):
            return {
                k: to_dict(v) for k, v in obj.__dict__.items() if not k.startswith("_")
            }
        return obj

    alice_dict = to_dict(alice)
    print(f"Manual serialization required: {type(alice_dict)}")

    return alice, bob, relationship


def pydantic_implementation_example():
    """Show how the same example would work with Pydantic (conceptual)."""
    print("\n=== PROPOSED PYDANTIC IMPLEMENTATION ===")

    print("With Pydantic, the same creation would look like:")
    print(
        """
    # Automatic validation and parsing
    alice = PydanticNodeData(
        id="person-alice-001",
        class_id="person",
        properties={  # Can pass dict directly!
            "name": "Alice Johnson",
            "age": 28,
            "occupation": "Software Engineer",
            "city": "San Francisco",
            "tags": ["tech", "python"],
            "department": "Engineering"  # Dynamic property allowed
        }
    )

    # Or from JSON directly:
    alice = PydanticNodeData.model_validate_json('''
        {
            "id": "person-alice-001",
            "class_id": "person",
            "properties": {
                "name": "Alice Johnson",
                "age": 28,
                "occupation": "Software Engineer"
            }
        }
    ''')
    """
    )

    print("\n--- Pydantic Benefits ---")
    print("✅ Automatic validation on creation")
    print("✅ Built-in JSON serialization: alice.model_dump_json()")
    print("✅ Schema generation: PydanticNodeData.model_json_schema()")
    print("✅ Validation on property changes")
    print("✅ Clear error messages with field paths")
    print("✅ Type coercion (string '28' -> int 28)")

    print("\n--- Validation Examples ---")
    print("These would raise ValidationError with Pydantic:")
    print("• Empty name: ValidationError for field 'name'")
    print("• Negative age: ValidationError for field 'age' (must be >= 0)")
    print("• Self-referencing edge: ValidationError in root validator")
    print("• Missing required fields: ValidationError with missing field names")

    print("\n--- Advanced Features ---")
    print("• Custom validators for business logic")
    print("• Computed fields for derived properties")
    print("• Field aliases for API compatibility")
    print("• Discriminated unions for polymorphic types")
    print("• Integration with FastAPI for automatic API docs")


def initialization_pattern_comparison():
    """Compare initialization patterns between approaches."""
    print("\n=== INITIALIZATION PATTERN COMPARISON ===")

    print("\n1. BASIC CREATION")
    print("Current:")
    print("  props = CurrentElementProperties(name='Alice', age=28)")
    print(
        "  node = CurrentNodeData(id='alice', class_id='person', type=NodeTypes.NODE, properties=props)"
    )

    print("\nPydantic:")
    print(
        "  node = PydanticNodeData(id='alice', class_id='person', properties={'name': 'Alice', 'age': 28})"
    )

    print("\n2. FROM JSON")
    print("Current:")
    print("  # Manual JSON parsing required")
    print("  import json")
    print("  data = json.loads(json_string)")
    print("  props = CurrentElementProperties(**data['properties'])")
    print("  node = CurrentNodeData(**data, properties=props)")

    print("\nPydantic:")
    print("  node = PydanticNodeData.model_validate_json(json_string)")

    print("\n3. VALIDATION")
    print("Current:")
    print("  # Manual validation in __post_init__ or separate functions")
    print("  if not props.name or props.age < 0:")
    print("      raise ValueError('Invalid data')")

    print("\nPydantic:")
    print("  # Automatic validation with detailed error messages")
    print("  # ValidationError raised automatically with field-specific errors")

    print("\n4. SERIALIZATION")
    print("Current:")
    print("  # Manual to_dict implementation")
    print("  def to_dict(obj): ...")
    print("  json.dumps(to_dict(node))")

    print("\nPydantic:")
    print("  json_str = node.model_dump_json()")
    print("  dict_data = node.model_dump()")


def performance_considerations():
    """Discuss performance implications."""
    print("\n=== PERFORMANCE CONSIDERATIONS ===")

    print("Current Implementation:")
    print("✅ Very fast initialization (dataclasses + slots)")
    print("✅ Low memory overhead")
    print("✅ No validation overhead in production")
    print("❌ Manual validation code needed")
    print("❌ Manual serialization overhead")

    print("\nPydantic Implementation:")
    print("✅ Fast validation (Rust-based in v2)")
    print("✅ Fast serialization (built-in)")
    print("✅ Memory efficient (comparable to dataclasses)")
    print("⚠️ Small validation overhead on creation")
    print("⚠️ Slightly larger memory footprint")

    print("\nRecommendation:")
    print("For most use cases, Pydantic overhead is negligible compared to benefits.")
    print("For high-frequency creation scenarios, benchmarking is recommended.")


def migration_strategy():
    """Discuss migration approach."""
    print("\n=== MIGRATION STRATEGY ===")

    print("Phase 1 - Gradual Introduction:")
    print("• Keep current classes")
    print("• Add Pydantic models for new features")
    print("• Create conversion utilities")

    print("\nPhase 2 - Compatibility Layer:")
    print("• Implement adapter pattern")
    print("• Support both initialization methods")
    print("• Gradual deprecation of old patterns")

    print("\nPhase 3 - Full Migration:")
    print("• Replace internal implementations")
    print("• Maintain public API compatibility")
    print("• Performance optimization")


if __name__ == "__main__":
    print("Graph Elements Library - Initialization Pattern Comparison")
    print("=" * 60)

    # Show current implementation
    current_alice, current_bob, current_edge = current_implementation_example()

    # Show proposed Pydantic approach
    pydantic_implementation_example()

    # Compare patterns
    initialization_pattern_comparison()

    # Performance discussion
    performance_considerations()

    # Migration strategy
    migration_strategy()
