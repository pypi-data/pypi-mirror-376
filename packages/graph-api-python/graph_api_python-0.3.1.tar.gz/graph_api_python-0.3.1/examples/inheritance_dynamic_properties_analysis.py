"""
Analysis: Pydantic Inheritance and Dynamic Properties Challenges

This examines the specific issues with converting the current inheritance system
and dynamic property handling to Pydantic models.
"""

print("=== PYDANTIC INHERITANCE & DYNAMIC PROPERTIES ANALYSIS ===")
print()

# =============================================================================
# CURRENT INHERITANCE SYSTEM COMPLEXITY
# =============================================================================

print("1. CURRENT INHERITANCE SYSTEM COMPLEXITY")
print("-" * 50)

print("The current system has multi-layered inheritance:")
print(
    """
CURRENT INHERITANCE PATTERNS:

1. CLASS INHERITANCE (Python classes)
   ElementProperties
   ├── NodeProperties (inherits from ElementProperties)
   ├── EdgeProperties (inherits from ElementProperties)
   └── MetaNodeProperties (inherits from ElementProperties)

2. META-NODE INHERITANCE (Runtime configuration)
   person (MetaNode)
   ├── inherits_from: ["node"]
   ├── property_types: {age: {...}, name: {...}}
   └── attributes: {card:variant: "outlined"}

   employee (MetaNode)
   ├── inherits_from: ["person"]  # Inherits person's properties
   ├── property_types: {employee_id: {...}, salary: {...}}
   └── attributes: {card:sections: [...]}

3. DYNAMIC PROPERTY RESOLUTION
   - Properties defined in MetaNode.property_types
   - Inherited from parent MetaNodes (recursive)
   - Runtime property validation based on inheritance chain
   - Dynamic attributes merging with conflict resolution
"""
)

print("CURRENT INHERITANCE RESOLUTION:")
print(
    """
# Complex runtime inheritance resolution
class MetaNode:
    @property
    def all_prop_types(self) -> Dict[str, MetaPropertyType]:
        # Recursively gather from inheritance chain
        all_nodes = list(self.inherited_meta_nodes) + [self]
        result = {}
        for meta_node in all_nodes:
            if meta_node.properties.property_types:
                result.update(meta_node.properties.property_types)  # Later overrides earlier
        return result

    def _gather_inherited_attributes(self) -> Dict[str, Any]:
        # Complex merging logic for attributes like card:sections
        inherited_attributes = {}
        all_nodes = list(self.inherited_meta_nodes) + [self]

        for meta_node in all_nodes:
            for key, value in meta_node.attributes.items():
                if key == 'card:sections':  # Special merging logic
                    # Merge sections by type, handle property arrays
                    ...complex merging logic...
                else:
                    inherited_attributes[key] = value  # Simple override
        return inherited_attributes
"""
)

# =============================================================================
# DYNAMIC PROPERTIES SYSTEM
# =============================================================================

print("\n2. CURRENT DYNAMIC PROPERTIES SYSTEM")
print("-" * 45)

print("The current system supports multiple types of dynamic properties:")
print(
    """
DYNAMIC PROPERTY TYPES:

1. KNOWN PROPERTIES (Predefined slots)
   class ElementProperties:
       __slots__ = ('name', 'description', 'tags', 'created_time', ...)

       def __setitem__(self, key, value):
           if key in self._KNOWN_ATTRS:
               setattr(self, key, value)  # Set on slots
           else:
               self.extra_properties[key] = value  # Dynamic storage

2. EXTRA PROPERTIES (Completely dynamic)
   props = ElementProperties()
   props['custom_field'] = "any value"          # Stored in extra_properties
   props['user_metadata'] = {"complex": "data"} # Any structure
   props['computed_score'] = 95.5               # Any type

3. META-DEFINED PROPERTIES (Schema-driven dynamic)
   # MetaNode defines available properties
   person_meta = MetaNode(properties={
       "property_types": {
           "age": MetaPropertyType(type="number", required=True),
           "skills": MetaPropertyType(type="elementarray"),
           "bio": MetaPropertyType(type="string", required=False)
       }
   })

   # Elements use these dynamically
   person = Node(properties={"age": 28, "skills": ["python"], "bio": "Developer"})

4. INHERITANCE-BASED PROPERTIES (Runtime resolution)
   # Parent MetaNode
   person_meta.property_types = {"name": ..., "age": ...}

   # Child MetaNode inherits and extends
   employee_meta.inherits_from = ["person"]
   employee_meta.property_types = {"employee_id": ..., "salary": ...}

   # Final element gets merged properties: name, age, employee_id, salary
"""
)

# =============================================================================
# PYDANTIC CHALLENGES WITH INHERITANCE
# =============================================================================

print("\n3. PYDANTIC INHERITANCE CHALLENGES")
print("-" * 40)

print("Pydantic has several limitations with this inheritance pattern:")

print(
    """
CHALLENGE 1: STATIC FIELD DEFINITION
❌ Problem: Pydantic requires fields to be defined at class definition time

Current (Dynamic):
    class ElementProperties:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                if key in known_attrs:
                    setattr(self, key, value)
                else:
                    self.extra_properties[key] = value  # Any field accepted

Pydantic (Static):
    class PydanticElementProperties(BaseModel):
        name: Optional[str] = None
        age: Optional[int] = None  # Must pre-define all fields
        # Cannot add arbitrary fields without extra='allow'

CHALLENGE 2: RUNTIME INHERITANCE RESOLUTION
❌ Problem: Pydantic inheritance is Python class-based, not runtime-configurable

Current (Runtime):
    # MetaNode defines inheritance at runtime
    employee_meta.inherits_from = ["person"]  # String reference

    # Properties resolved dynamically
    all_properties = resolve_inherited_properties(employee_meta)

Pydantic (Compile-time):
    class PersonModel(BaseModel):
        name: str
        age: int

    class EmployeeModel(PersonModel):  # Must inherit at class definition
        employee_id: str
        salary: float

    # Cannot change inheritance at runtime

CHALLENGE 3: COMPLEX MERGING LOGIC
❌ Problem: Pydantic doesn't support custom inheritance merging

Current (Custom merging):
    def _gather_inherited_attributes(self):
        for meta_node in inheritance_chain:
            if key == 'card:sections':
                # Custom merging logic for array fields
                merge_sections_by_type(existing, new)
            else:
                # Simple override
                result[key] = value

Pydantic (Simple override):
    # No built-in support for complex field merging
    # Would need custom __init_subclass__ or metaclass hacks
"""
)

# =============================================================================
# DYNAMIC PROPERTIES SOLUTIONS
# =============================================================================

print("\n4. PYDANTIC DYNAMIC PROPERTIES SOLUTIONS")
print("-" * 45)

print("Pydantic DOES support dynamic properties, but with trade-offs:")

print(
    """
SOLUTION 1: EXTRA='ALLOW' (Closest to current system)
✅ Pros: Accepts any additional fields
❌ Cons: No validation on extra fields

    class FlexibleProperties(BaseModel):
        model_config = ConfigDict(extra='allow')

        # Predefined fields with validation
        name: Optional[str] = Field(None, min_length=1)
        age: Optional[int] = Field(None, ge=0, le=150)

        # Any other fields stored in __pydantic_extra__

    props = FlexibleProperties(
        name="Alice",
        age=28,
        custom_field="any value",      # Allowed but not validated
        user_data={"key": "value"}     # Allowed but not validated
    )

    print(props.custom_field)          # Works
    print(props.__pydantic_extra__)    # Access extra fields

SOLUTION 2: DISCRIMINATED UNIONS (Type-based routing)
✅ Pros: Maintains validation for known types
❌ Cons: Requires pre-defining all possible property schemas

    from pydantic import BaseModel, Field, discriminator
    from typing import Union

    class PersonProperties(BaseModel):
        type: Literal["person"] = "person"
        name: str
        age: int
        occupation: Optional[str] = None

    class CompanyProperties(BaseModel):
        type: Literal["company"] = "company"
        name: str
        founded_year: int
        employees: Optional[int] = None

    class DynamicProperties(BaseModel):
        type: Literal["dynamic"] = "dynamic"
        data: Dict[str, Any]  # Fallback for unknown structures

    PropertyUnion = Union[PersonProperties, CompanyProperties, DynamicProperties]

    class Node(BaseModel):
        id: str
        properties: PropertyUnion = Field(discriminator='type')

SOLUTION 3: FLEXIBLE DICT WITH VALIDATION
✅ Pros: Maximum flexibility
❌ Cons: Loses type safety on dynamic fields

    from pydantic import BaseModel, validator, root_validator

    class DictBasedProperties(BaseModel):
        properties: Dict[str, Any] = Field(default_factory=dict)

        @validator('properties')
        def validate_known_fields(cls, v):
            # Custom validation for known fields
            if 'age' in v and (not isinstance(v['age'], int) or v['age'] < 0):
                raise ValueError('Age must be positive integer')
            if 'email' in v and '@' not in str(v['email']):
                raise ValueError('Invalid email format')
            return v

        def __getattr__(self, name: str) -> Any:
            if name in self.properties:
                return self.properties[name]
            raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'")
"""
)

# =============================================================================
# HYBRID APPROACH RECOMMENDATION
# =============================================================================

print("\n5. RECOMMENDED HYBRID APPROACH")
print("-" * 35)

print("Best solution: Combine Pydantic validation with flexible dynamic properties:")

print(
    r"""
HYBRID SOLUTION STRUCTURE:

class PydanticElementProperties(BaseModel):
    model_config = ConfigDict(extra='allow', validate_assignment=True)

    # CORE FIELDS (Always validated)
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    created_time: int = Field(default_factory=lambda: int(time.time() * 1000))
    updated_time: int = Field(default_factory=lambda: int(time.time() * 1000))
    tags: List[str] = Field(default_factory=list)

    # COMMON OPTIONAL FIELDS (Validated when present)
    age: Optional[int] = Field(None, ge=0, le=150)
    email: Optional[str] = Field(None, regex=r'^[^@]+@[^@]+\.[^@]+$')
    phone: Optional[str] = None

    # DYNAMIC FIELDS (Any additional properties)
    # Stored in __pydantic_extra__ automatically with extra='allow'

    @validator('tags', pre=True)
    def normalize_tags(cls, v):
        if isinstance(v, str):
            return [v]
        return v or []

    # Custom validation for dynamic fields
    @root_validator(pre=True)
    def validate_dynamic_fields(cls, values):
        # Apply business rules to dynamic fields
        if 'salary' in values and isinstance(values['salary'], (int, float)) and values['salary'] < 0:
            raise ValueError('Salary cannot be negative')
        return values

    # Backward compatibility methods
    def get(self, key: str, default=None):
        if hasattr(self, key):
            return getattr(self, key)
        return self.__pydantic_extra__.get(key, default)

    def set_extra(self, key: str, value: Any):
        # For setting dynamic properties
        if hasattr(self.__class__, key):
            setattr(self, key, value)
        else:
            self.__pydantic_extra__[key] = value

BENEFITS:
✅ Core fields get full Pydantic validation
✅ Dynamic fields are preserved and accessible
✅ Backward compatibility with current API
✅ Type safety where it matters most
✅ Runtime validation on both static and dynamic fields
✅ JSON serialization includes all fields (static + dynamic)

ADDRESSING INHERITANCE:
For the MetaNode inheritance system, keep current runtime resolution:

class MetaNodeCompatibleProperties(PydanticElementProperties):
    def __init__(self, meta_node: Optional[MetaNode] = None, **data):
        # Resolve inheritance before Pydantic validation
        if meta_node:
            resolved_data = self._resolve_meta_inheritance(meta_node, data)
            super().__init__(**resolved_data)
        else:
            super().__init__(**data)

    def _resolve_meta_inheritance(self, meta_node: MetaNode, data: Dict[str, Any]) -> Dict[str, Any]:
        # Use existing inheritance resolution logic
        all_prop_types = meta_node.all_prop_types
        resolved_data = data.copy()

        # Apply defaults from MetaNode
        for key, prop_type in all_prop_types.items():
            if key not in resolved_data and prop_type.default is not None:
                resolved_data[key] = prop_type.default

        return resolved_data
"""
)

print("\n" + "=" * 60)
print("SUMMARY: INHERITANCE & DYNAMIC PROPERTIES")
print("=" * 60)

print("CHALLENGES:")
print("❌ Pydantic inheritance is compile-time, current system is runtime")
print("❌ Complex inheritance merging logic not directly supported")
print("❌ MetaNode-based property resolution needs custom handling")

print("\nSOLUTIONS:")
print("✅ Use extra='allow' for dynamic properties (like current extra_properties)")
print("✅ Keep runtime MetaNode inheritance resolution, apply before Pydantic")
print("✅ Validate core fields with Pydantic, preserve flexibility for dynamic fields")
print("✅ Maintain backward compatibility with get/set methods")
print("✅ Use custom __init__ to bridge MetaNode system with Pydantic validation")

print("\nRECOMMENDATION:")
print(
    "Hybrid approach preserves all current functionality while adding Pydantic benefits"
)
print(
    "where they provide the most value (core field validation, serialization, schemas)."
)
