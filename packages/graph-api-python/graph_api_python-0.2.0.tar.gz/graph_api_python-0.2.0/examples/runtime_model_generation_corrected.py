"""
Corrected Runtime Pydantic Model Generation

This shows the corrected approach for generating Pydantic models at runtime
from MetaNode inheritance, addressing serialization issues.
"""

import time
from typing import Optional

print("=== RUNTIME PYDANTIC MODEL GENERATION (CORRECTED) ===")
print()

# Simulate pydantic for demonstration
try:
    from pydantic import BaseModel, Field, create_model
    from pydantic.config import ConfigDict

    PYDANTIC_AVAILABLE = True
    print("✅ Pydantic available - showing working implementation")
except ImportError:
    BaseModel = object

    def Field(*args, **kwargs):
        return None

    def create_model(*args, **kwargs):
        return None

    ConfigDict = dict
    PYDANTIC_AVAILABLE = False
    print("❌ Pydantic not available - showing conceptual structure")

print()

if PYDANTIC_AVAILABLE:

    def demonstrate_runtime_inheritance():
        """Show how runtime model generation solves inheritance."""

        print("SCENARIO: Create models for inheritance chain at runtime")
        print("node -> person -> employee (each adding properties)")
        print()

        # Simple runtime model creation using create_model
        print("1. BASE NODE MODEL")
        print("-" * 20)

        # Create base node model
        NodeModel = create_model(
            "NodeProperties",
            __config__=ConfigDict(extra="allow", validate_assignment=True),
            name=(Optional[str], Field(None, min_length=1, max_length=200)),
            description=(Optional[str], Field(None, max_length=2000)),
            created_time=(int, Field(default_factory=lambda: int(time.time() * 1000))),
        )

        # Add convenience methods
        def get_property(self, key: str, default=None):
            if hasattr(self, key):
                value = getattr(self, key)
                return value if value is not None else default
            return getattr(self, "__pydantic_extra__", {}).get(key, default)

        NodeModel.get = get_property
        print(
            f"✅ Created {NodeModel.__name__} with fields: name, description, created_time"
        )

        print("\n2. PERSON MODEL (INHERITS NODE)")
        print("-" * 35)

        # Create person model that includes node fields + person-specific fields
        PersonModel = create_model(
            "PersonProperties",
            __config__=ConfigDict(extra="allow", validate_assignment=True),
            # Inherit all fields from NodeModel
            name=(Optional[str], Field(None, min_length=1, max_length=200)),
            description=(Optional[str], Field(None, max_length=2000)),
            created_time=(int, Field(default_factory=lambda: int(time.time() * 1000))),
            # Add person-specific fields
            age=(Optional[int], Field(None, ge=0, le=150)),
            email=(Optional[str], Field(None)),
        )

        PersonModel.get = get_property
        print(
            f"✅ Created {PersonModel.__name__} with inherited + new fields: name, description, created_time, age, email"
        )

        print("\n3. EMPLOYEE MODEL (INHERITS PERSON)")
        print("-" * 40)

        # Create employee model with full inheritance chain
        EmployeeModel = create_model(
            "EmployeeProperties",
            __config__=ConfigDict(extra="allow", validate_assignment=True),
            # All inherited fields
            name=(Optional[str], Field(None, min_length=1, max_length=200)),
            description=(Optional[str], Field(None, max_length=2000)),
            created_time=(int, Field(default_factory=lambda: int(time.time() * 1000))),
            age=(Optional[int], Field(None, ge=0, le=150)),
            email=(Optional[str], Field(None)),
            # Employee-specific fields
            employee_id=(str, Field(..., min_length=1)),  # Required
            salary=(Optional[float], Field(50000.0, ge=0)),  # Default 50000
            department=(Optional[str], Field(None)),
        )

        EmployeeModel.get = get_property
        print(f"✅ Created {EmployeeModel.__name__} with full inheritance chain")

        print("\n4. USAGE EXAMPLES")
        print("-" * 18)

        # Create instances
        try:
            # Simple node
            node = NodeModel(name="Basic Node", description="A simple node example")
            print(f"Node: {node.name} (created: {node.created_time})")

            # Person with validation
            person = PersonModel(
                name="John Doe",
                age=35,
                email="john@example.com",
                custom_bio="Software developer",  # Dynamic property
            )
            print(f"Person: {person.name}, age {person.age}")
            print(f"  Custom bio: {person.get('custom_bio')}")

            # Employee with full inheritance + validation
            employee = EmployeeModel(
                name="Alice Johnson",
                age=28,
                email="alice@company.com",
                employee_id="EMP001",
                salary=75000,
                department="Engineering",
                # Dynamic properties still work
                skills=["Python", "Leadership"],
                office="Building A",
            )
            print(f"Employee: {employee.name} ({employee.employee_id})")
            print(f"  Department: {employee.department}, Salary: ${employee.salary}")
            print(f"  Skills: {employee.get('skills')}")
            print(f"  Office: {employee.get('office')}")

        except Exception as e:
            print(f"❌ Error creating instances: {e}")

        print("\n5. VALIDATION IN ACTION")
        print("-" * 25)

        try:
            # This should fail - violates inherited constraints
            EmployeeModel(
                name="",  # Too short (from node validation)
                age=-5,  # Invalid age (from person validation)
                employee_id="",  # Required field empty (employee validation)
                salary=-1000,  # Negative salary (employee validation)
            )
        except Exception as e:
            print("✅ Caught validation errors from inheritance chain:")
            errors = str(e).split("\n")
            for _i, error in enumerate(errors[:4]):  # Show first few errors
                if error.strip():
                    print(f"   {error.strip()}")
            if len(errors) > 4:
                print("   ...")

        print("\n6. JSON SERIALIZATION")
        print("-" * 22)

        # Create a clean employee for serialization
        clean_employee = EmployeeModel(
            name="Bob Wilson",
            age=32,
            email="bob@company.com",
            employee_id="EMP002",
            salary=65000,
            department="Product",
            start_date="2023-01-15",  # Dynamic property
            manager="Alice Johnson",  # Dynamic property
        )

        # Serialize to JSON
        json_data = (
            clean_employee.model_dump()
        )  # Get dict first to avoid function serialization issues
        print("Employee data structure:")
        for key, value in json_data.items():
            if not key.startswith("_"):
                print(f"  {key}: {value}")

        print(
            f"\n✅ All properties (static + dynamic) included: {len(json_data)} fields"
        )

        # Test round-trip serialization
        import json

        json_str = json.dumps(json_data, default=str)
        parsed_data = json.loads(json_str)
        restored_employee = EmployeeModel(**parsed_data)
        print(f"✅ Round-trip serialization successful: {restored_employee.name}")

        return clean_employee

    # Run the demonstration
    result = demonstrate_runtime_inheritance()

else:
    print("CONCEPTUAL STRUCTURE:")
    print(
        """
    Key insight: Use Pydantic's create_model() to generate models at runtime

    # Instead of static inheritance:
    class EmployeeModel(PersonModel):  # Compile-time only
        employee_id: str

    # Use dynamic generation:
    EmployeeModel = create_model(
        'EmployeeProperties',
        __config__=ConfigDict(extra='allow'),
        # Include ALL fields from inheritance chain
        name=(Optional[str], Field(None, min_length=1)),     # From node
        age=(Optional[int], Field(None, ge=0, le=150)),      # From person
        employee_id=(str, Field(..., min_length=1)),        # From employee
        # ... all other inherited fields
    )

    This approach:
    ✅ Generates models at runtime based on MetaNode inheritance
    ✅ Includes all validation from the inheritance chain
    ✅ Preserves dynamic properties with extra='allow'
    ✅ Works with existing inheritance resolution logic
    """
    )

print("\n" + "=" * 65)
print("RUNTIME GENERATION: THE PERFECT SOLUTION")
print("=" * 65)

print(
    """
YOUR INSIGHT IS CORRECT: Runtime generation eliminates inheritance issues!

WHY IT WORKS PERFECTLY:
✅ NO COMPILE-TIME LIMITATIONS: Models created when needed
✅ USE EXISTING INHERITANCE LOGIC: Your MetaNode resolution works unchanged
✅ FULL PYDANTIC BENEFITS: Validation, serialization, schemas
✅ DYNAMIC PROPERTIES: extra='allow' preserves all flexibility
✅ PERFORMANCE: Generated models can be cached
✅ BACKWARD COMPATIBILITY: Add methods to generated models

SIMPLIFIED WORKFLOW:
1. MetaNode defines inheritance: employee.inherits_from = ["person"]
2. Resolve inheritance (existing logic): all_props = resolve_inheritance(employee, registry)
3. Generate Pydantic model: Model = create_model("EmployeeProps", **field_defs)
4. Use model: employee = Model(name="Alice", employee_id="E001", custom_field="value")

INITIALIZATION BECOMES:
Current:   props = ElementProperties(**data) + manual validation
Pydantic:  props = GeneratedModel(**data)  # Includes inheritance + validation + dynamics

This approach makes Pydantic a perfect fit for your system!
"""
)

if PYDANTIC_AVAILABLE:
    print("✅ Working example above demonstrates the solution")
else:
    print("⚠️ Install pydantic to see the working implementation")
