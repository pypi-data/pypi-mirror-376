#!/usr/bin/env python3
"""
Example usage of the graph_elements package with GraphQuery functionality.
This demonstrates creating schemas, adding data, creating relationships, and querying the graph.

Updated to use the CURRENT GraphQuery API:
- query.classId('person') instead of query.filter_by_class_id('person')
- query.where('name', FilterOperator.EQ, 'Alice') instead of query.filter_by_property()
- query.first(2) instead of query.take_first(2)
"""

import asyncio
import sys
from pathlib import Path

# Add the parent directory to sys.path for importing graph_elements
sys.path.insert(0, str(Path(__file__).parent.parent))

from graph_elements.base_element import NodeTypes, generate_guid
from graph_elements.edge import Edge, EdgeDetails, EdgeProperties
from graph_elements.element_store import (
    ElementStore,
    ElementStoreConfig,
    MemoryDataStorage,
)
from graph_elements.graph_query import FilterOperator, IFluentOptions
from graph_elements.meta import (
    MetaNode,
    MetaNodeDetails,
    MetaNodeProperties,
    MetaPropertyType,
)
from graph_elements.node import Node, NodeDetails, NodeProperties


async def main():
    """Main example function demonstrating GraphQuery usage."""
    print("=== OSINT Pipeline Graph Elements with GraphQuery Example ===")

    # Initialize the element store with memory storage
    storage = MemoryDataStorage()
    config = ElementStoreConfig(operation=storage)
    store = ElementStore(config=config)
    await store.load_elements()

    print("✓ Element store initialized")

    # Create schema definitions (meta nodes)
    person_props = MetaNodeProperties(
        name="Person", description="A person in the OSINT system"
    )
    person_meta_details = MetaNodeDetails(
        id=generate_guid(),
        class_id="person",
        type=NodeTypes.META,
        properties=person_props,
    )
    person_meta = MetaNode(person_meta_details, store)

    # Add properties to person schema
    person_meta.properties.property_types = {}
    person_meta.properties.property_types["name"] = MetaPropertyType(
        key="name", type="string", label="Full Name", required=True
    )
    person_meta.properties.property_types["age"] = MetaPropertyType(
        key="age", type="number", label="Age"
    )
    person_meta.properties.property_types["location"] = MetaPropertyType(
        key="location", type="string", label="Location"
    )
    person_meta.properties.property_types["worksFor"] = MetaPropertyType(
        key="worksFor", type="relation", label="Works For"
    )

    org_props = MetaNodeProperties(
        name="Organization", description="An organization in the OSINT system"
    )
    org_meta_details = MetaNodeDetails(
        id=generate_guid(),
        class_id="organization",
        type=NodeTypes.META,
        properties=org_props,
    )
    org_meta = MetaNode(org_meta_details, store)

    org_meta.properties.property_types = {}
    org_meta.properties.property_types["name"] = MetaPropertyType(
        key="name", type="string", label="Organization Name", required=True
    )
    org_meta.properties.property_types["industry"] = MetaPropertyType(
        key="industry", type="string", label="Industry"
    )

    # Add schemas to store
    await store.add_elements([person_meta, org_meta])

    print("✓ Schema definitions created")

    # Create person nodes
    alice_props = NodeProperties(name="Alice Smith", age=30, location="New York")
    alice_details = NodeDetails(
        id=generate_guid(),
        class_id="person",
        type=NodeTypes.NODE,
        properties=alice_props,
        source="manual_entry",
    )
    alice = Node(alice_details, store)

    bob_props = NodeProperties(name="Bob Johnson", age=35, location="San Francisco")
    bob_details = NodeDetails(
        id=generate_guid(),
        class_id="person",
        type=NodeTypes.NODE,
        properties=bob_props,
        source="manual_entry",
    )
    bob = Node(bob_details, store)

    # Create organization node
    tech_corp_props = NodeProperties(name="TechCorp Inc", industry="Technology")
    tech_corp_details = NodeDetails(
        id=generate_guid(),
        class_id="organization",
        type=NodeTypes.NODE,
        properties=tech_corp_props,
        source="manual_entry",
    )
    tech_corp = Node(tech_corp_details, store)

    # Add nodes to store
    await store.add_elements([alice, bob, tech_corp])

    print("✓ Sample data created")

    # Create employment relationship edges
    alice_employment_props = EdgeProperties(
        role="Software Engineer", start_date="2022-01-15"
    )
    alice_employment_details = EdgeDetails(
        id=generate_guid(),
        class_id="employment",
        type=NodeTypes.EDGE,
        properties=alice_employment_props,
        from_id=alice.id,
        to_id=tech_corp.id,
        source="manual_entry",
    )
    alice_employment = Edge(alice_employment_details, store)

    bob_employment_props = EdgeProperties(
        role="Product Manager", start_date="2021-06-01"
    )
    bob_employment_details = EdgeDetails(
        id=generate_guid(),
        class_id="employment",
        type=NodeTypes.EDGE,
        properties=bob_employment_props,
        from_id=bob.id,
        to_id=tech_corp.id,
        source="manual_entry",
    )
    bob_employment = Edge(bob_employment_details, store)

    # Add edges to store
    await store.add_elements([alice_employment, bob_employment])

    print("✓ Relationships created")

    # Now demonstrate GraphQuery functionality
    print("\n=== GraphQuery Demonstrations ===")

    # Query 1: Find all people
    print("\n1. Finding all people:")
    people_query = store.query().classId("person")
    people = people_query.r()
    print(f"   Found {len(people)} people:")
    for person in people:
        print(
            f"   - {person.properties.get('name')} (age: {person.properties.get('age')})"
        )

    # Query 2: Find all organizations
    print("\n2. Finding all organizations:")
    org_query = store.query().classId("organization")
    orgs = org_query.r()
    print(f"   Found {len(orgs)} organizations:")
    for org in orgs:
        print(
            f"   - {org.properties.get('name')} (industry: {org.properties.get('industry')})"
        )

    # Query 3: Filter by property
    print("\n3. Finding people over 32:")
    older_people = store.query().classId("person").where("age", FilterOperator.GT, 32)
    for person in older_people.r():
        print(
            f"   - {person.properties.get('name')} (age: {person.properties.get('age')})"
        )

    # Query 4: Search by name property
    print("\n4. Search for 'Alice':")
    alice_search = store.query().where("name", FilterOperator.CONTAINS, "Alice")
    for person in alice_search.r():
        print(f"   - Found: {person.properties.get('name')}")

    # Query 5: Count results
    print("\n5. Counting elements:")
    total_people = store.query().classId("person").count()
    total_orgs = store.query().classId("organization").count()
    print(f"   - Total people: {total_people}")
    print(f"   - Total organizations: {total_orgs}")

    # Query 6: Focus query (relationship traversal)
    print("\n6. Focus query - finding elements related to Alice:")
    focus_query = store.query().filter_by_focus(
        [alice.id], IFluentOptions(levels=1, include_self=True)
    )
    related_elements = focus_query.r()
    print(f"   Found {len(related_elements)} related elements:")
    for element in related_elements:
        if hasattr(element, "properties") and "name" in element.properties:
            print(f"   - {element.properties.get('name')} ({element.class_id})")

    # Query 7: Sorting
    print("\n7. People sorted by age:")
    sorted_people = store.query().classId("person").sort("age", "desc")
    for person in sorted_people.r():
        print(
            f"   - {person.properties.get('name')} (age: {person.properties.get('age')})"
        )

    # Query 8: Taking first/last
    print("\n8. Taking first 2 elements:")
    first_two = store.query().classId("person").first(2)
    for person in first_two.r():
        print(f"   - {person.properties.get('name')}")

    # Query 9: Combining multiple filters
    print("\n9. Complex query - people in New York over 25:")
    complex_query = (
        store.query()
        .classId("person")
        .where("location", FilterOperator.EQ, "New York")
        .where("age", FilterOperator.GT, 25)
    )

    for person in complex_query.r():
        print(
            f"   - {person.properties.get('name')} in {person.properties.get('location')}"
        )

    # Query 10: Statistics
    print("\n10. Age statistics:")
    ages_query = store.query().classId("person")
    if ages_query.r():
        print(f"   - Mean age: {ages_query.mean('age'):.1f}")
        print(f"   - Sum of ages: {ages_query.sum('age')}")
        print(f"   - Median age: {ages_query.median('age'):.1f}")

    print("\n✓ GraphQuery example completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
