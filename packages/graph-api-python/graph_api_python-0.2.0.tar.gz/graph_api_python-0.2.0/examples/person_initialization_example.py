"""
Real-world initialization examples showing how Person nodes and relationships
would be created with both current and Pydantic implementations.

This demonstrates the practical differences in code patterns.
"""

import json
import time
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Dict

# =============================================================================
# CURRENT IMPLEMENTATION - WORKING CODE
# =============================================================================


class NodeTypes(StrEnum):
    NODE = "node"
    EDGE = "edge"
    META = "meta"


class ElementProperties:
    """Current properties implementation with manual handling."""

    def __init__(self, **kwargs):
        # Core properties
        self.name = kwargs.get("name")
        self.description = kwargs.get("description")
        self.created_time = kwargs.get("created_time", int(time.time() * 1000))
        self.updated_time = kwargs.get("updated_time", int(time.time() * 1000))
        self.tags = kwargs.get("tags", [])

        # Person-specific properties
        self.age = kwargs.get("age")
        self.email = kwargs.get("email")
        self.occupation = kwargs.get("occupation")
        self.city = kwargs.get("city")
        self.phone = kwargs.get("phone")
        self.department = kwargs.get("department")

        # Relationship properties
        self.relationship_type = kwargs.get("relationship_type")
        self.strength = kwargs.get("strength")
        self.since_date = kwargs.get("since_date")

        # Store any additional properties
        known_props = {
            "name",
            "description",
            "created_time",
            "updated_time",
            "tags",
            "age",
            "email",
            "occupation",
            "city",
            "phone",
            "department",
            "relationship_type",
            "strength",
            "since_date",
        }
        self.extra = {k: v for k, v in kwargs.items() if k not in known_props}

    def get(self, key: str, default=None):
        """Get property value with fallback."""
        if hasattr(self, key):
            return getattr(self, key)
        return self.extra.get(key, default)

    def set(self, key: str, value: Any):
        """Set property value."""
        if hasattr(self, key):
            setattr(self, key, value)
        else:
            self.extra[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {}
        for attr in dir(self):
            if not attr.startswith("_") and not callable(getattr(self, attr)):
                value = getattr(self, attr)
                if value is not None:
                    result[attr] = value
        result.update(self.extra)
        return result


@dataclass
class NodeData:
    """Current node data structure."""

    id: str
    class_id: str
    type: NodeTypes
    properties: ElementProperties

    def __post_init__(self):
        """Manual validation."""
        if not self.id or not self.id.strip():
            raise ValueError("Node ID cannot be empty")
        if not self.class_id or not self.class_id.strip():
            raise ValueError("Node class_id cannot be empty")

        # Clean up IDs
        self.id = self.id.strip()
        self.class_id = self.class_id.strip()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "class_id": self.class_id,
            "type": self.type.value,
            "properties": self.properties.to_dict(),
        }


@dataclass
class EdgeData:
    """Current edge data structure."""

    id: str
    class_id: str
    type: NodeTypes
    from_id: str
    to_id: str
    properties: ElementProperties

    def __post_init__(self):
        """Manual validation."""
        if not all([self.id, self.class_id, self.from_id, self.to_id]):
            raise ValueError("All edge fields are required")

        if self.from_id.strip() == self.to_id.strip():
            raise ValueError("Edge cannot connect node to itself")

        # Clean up
        self.id = self.id.strip()
        self.class_id = self.class_id.strip()
        self.from_id = self.from_id.strip()
        self.to_id = self.to_id.strip()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "class_id": self.class_id,
            "type": self.type.value,
            "from_id": self.from_id,
            "to_id": self.to_id,
            "properties": self.properties.to_dict(),
        }


# =============================================================================
# DEMONSTRATION FUNCTIONS
# =============================================================================


def create_person_current_way():
    """Create person nodes and relationship using current implementation."""
    print("=== CURRENT IMPLEMENTATION EXAMPLE ===")

    try:
        # Create Alice - Software Engineer
        alice_props = ElementProperties(
            name="Alice Johnson",
            age=28,
            email="alice.johnson@techcorp.com",
            occupation="Software Engineer",
            city="San Francisco",
            department="Engineering",
            phone="+1-555-0123",
            tags=["python", "backend", "microservices"],
            skills=["Python", "Docker", "Kubernetes"],  # Dynamic property
            years_experience=5,  # Dynamic property
        )

        alice = NodeData(
            id="person-alice-001",
            class_id="person",
            type=NodeTypes.NODE,
            properties=alice_props,
        )

        print(f"✅ Created Alice: {alice.properties.name}")
        print(f"   Age: {alice.properties.age}, Role: {alice.properties.occupation}")
        print(f"   Skills: {alice.properties.get('skills')}")

        # Create Bob - Product Manager
        bob_props = ElementProperties(
            name="Bob Smith",
            age=32,
            email="bob.smith@techcorp.com",
            occupation="Product Manager",
            city="New York",
            department="Product",
            phone="+1-555-0124",
            tags=["product", "strategy", "roadmap"],
            years_experience=8,
            certifications=["PMP", "Scrum Master"],  # Dynamic property
        )

        bob = NodeData(
            id="person-bob-001",
            class_id="person",
            type=NodeTypes.NODE,
            properties=bob_props,
        )

        print(f"✅ Created Bob: {bob.properties.name}")
        print(f"   Age: {bob.properties.age}, Role: {bob.properties.occupation}")
        print(f"   Certifications: {bob.properties.get('certifications')}")

        # Create colleague relationship
        colleague_props = ElementProperties(
            name="colleagues",
            description="Professional work relationship",
            relationship_type="professional",
            strength=7,  # Scale of 1-10
            since_date="2023-01-15",
            interaction_frequency="daily",  # Dynamic property
            projects_together=[
                "Project Alpha",
                "Dashboard Redesign",
            ],  # Dynamic property
        )

        relationship = EdgeData(
            id="edge-colleague-alice-bob-001",
            class_id="colleague_relationship",
            type=NodeTypes.EDGE,
            from_id=alice.id,
            to_id=bob.id,
            properties=colleague_props,
        )

        print(
            f"✅ Created relationship: {alice.properties.name} -> {colleague_props.name} -> {bob.properties.name}"
        )
        print(
            f"   Strength: {colleague_props.strength}/10, Since: {colleague_props.since_date}"
        )

        # Demonstrate serialization
        print("\n--- Serialization ---")
        alice_json = json.dumps(alice.to_dict(), indent=2)
        print("Alice as JSON (first 200 chars):")
        print(alice_json[:200] + "..." if len(alice_json) > 200 else alice_json)

        # Demonstrate current limitations
        print("\n--- Current Limitations ---")

        # 1. No automatic validation on property changes
        alice.properties.age = -5  # Invalid but not caught
        print(
            f"❌ Set invalid age (-5) without validation error: {alice.properties.age}"
        )

        # 2. No type coercion
        alice.properties.age = "30"  # String instead of int
        print(
            f"❌ Age is now string: {type(alice.properties.age).__name__}: {alice.properties.age}"
        )

        # 3. Manual JSON parsing required
        print("❌ JSON deserialization requires manual parsing and reconstruction")

        return alice, bob, relationship

    except Exception as e:
        print(f"❌ Error: {e}")
        return None, None, None


def show_pydantic_equivalent():
    """Show what the same creation would look like with Pydantic."""
    print("\n=== PYDANTIC EQUIVALENT (CONCEPTUAL) ===")

    print("With Pydantic, the same person creation would look like:")
    print(
        """
# 1. Simple creation with validation
alice = PydanticPersonNode(
    id="person-alice-001",
    class_id="person",
    properties={
        "name": "Alice Johnson",
        "age": 28,
        "email": "alice.johnson@techcorp.com",
        "occupation": "Software Engineer",
        "city": "San Francisco",
        "department": "Engineering",
        "phone": "+1-555-0123",
        "tags": ["python", "backend", "microservices"],
        "skills": ["Python", "Docker", "Kubernetes"],  # Dynamic properties work
        "years_experience": 5
    }
)

# 2. From JSON string directly
alice = PydanticPersonNode.model_validate_json('''
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

# 3. Relationship with validation
relationship = PydanticEdge(
    id="edge-colleague-alice-bob-001",
    class_id="colleague_relationship",
    from_id="person-alice-001",
    to_id="person-bob-001",
    properties={
        "name": "colleagues",
        "relationship_type": "professional",
        "strength": 7,
        "since_date": "2023-01-15"
    }
)
"""
    )

    print("\n--- Pydantic Advantages ---")
    advantages = [
        "✅ Automatic validation: alice.properties.age = -5 → ValidationError",
        "✅ Type coercion: age='28' → automatically converted to int 28",
        "✅ Built-in serialization: alice.model_dump_json()",
        "✅ Schema generation: PydanticPersonNode.model_json_schema()",
        "✅ Field validation: email format, phone format, etc.",
        "✅ Business rule validation: age restrictions, required field combinations",
        "✅ Clear error messages: 'age: ensure this value is greater than 0'",
        "✅ IDE support: full type hints and autocompletion",
        "✅ API integration: direct FastAPI/OpenAPI support",
    ]

    for advantage in advantages:
        print(f"   {advantage}")


def demonstrate_validation_differences():
    """Show validation differences between approaches."""
    print("\n=== VALIDATION COMPARISON ===")

    print("Current Implementation:")

    # Current - no validation on creation
    try:
        bad_props = ElementProperties(
            name="",  # Empty name
            age=-5,  # Invalid age
            email="not-an-email",  # Invalid email format
        )
        NodeData(
            id="",  # Empty ID - this WILL be caught in __post_init__
            class_id="person",
            type=NodeTypes.NODE,
            properties=bad_props,
        )
    except ValueError as e:
        print(f"❌ Only caught empty ID: {e}")
        print("❌ Empty name and invalid age/email not validated")

    print("\nWith Pydantic (conceptual):")
    print("ValidationError would be raised with details:")
    print(
        """
    ValidationError: 3 validation errors for PersonNode
    id
      ensure this value has at least 1 character (type=value_error.any_str.min_length; limit_value=1)
    properties.name
      ensure this value has at least 1 character (type=value_error.any_str.min_length; limit_value=1)
    properties.age
      ensure this value is greater than or equal to 0 (type=value_error.number.not_ge; limit_value=0)
    properties.email
      field required to be a valid email address (type=value_error.email)
    """
    )


def show_serialization_differences():
    """Show serialization differences."""
    print("\n=== SERIALIZATION COMPARISON ===")

    # Current approach
    alice_props = ElementProperties(name="Alice", age=28, skills=["Python", "Docker"])
    alice = NodeData("alice-001", "person", NodeTypes.NODE, alice_props)

    print("Current Implementation:")
    current_dict = alice.to_dict()
    current_json = json.dumps(current_dict, indent=2)
    print("Manual to_dict() + json.dumps():")
    print(current_json[:150] + "..." if len(current_json) > 150 else current_json)

    print("\nPydantic Implementation (conceptual):")
    print("Built-in serialization methods:")
    print("• alice.model_dump() → dict")
    print("• alice.model_dump_json() → JSON string")
    print("• alice.model_dump(exclude={'internal_field'}) → filtered dict")
    print("• alice.model_dump(by_alias=True) → use field aliases")
    print("• Custom serializers for complex types")


def main():
    """Run the complete demonstration."""
    print("Graph Elements - Initialization Patterns Demonstration")
    print("=" * 60)

    # Show current implementation
    alice, bob, relationship = create_person_current_way()

    # Show Pydantic equivalent
    show_pydantic_equivalent()

    # Compare validation
    demonstrate_validation_differences()

    # Compare serialization
    show_serialization_differences()

    print("\n" + "=" * 60)
    print("SUMMARY: Pydantic provides significant improvements in:")
    print("• Data validation (automatic, comprehensive)")
    print("• Serialization/deserialization (built-in, efficient)")
    print("• Developer experience (type safety, IDE support)")
    print("• API integration (OpenAPI/FastAPI compatibility)")
    print("• Error handling (clear, detailed error messages)")


if __name__ == "__main__":
    main()
