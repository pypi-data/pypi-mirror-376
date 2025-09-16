"""
Graph Elements Library - Developer-Friendly API Demo

Example usage of the graph elements library with the NEW SHORTER GraphQuery API!

NEW SHORTER METHODS:
- query.classId('person') instead of query.filter_by_class_id('person')
- query.where('name', 'Alice') instead of query.filter_by_property('name', FilterOperator.EQ, 'Alice')
- query.where('age', '>', 30) or query.gt('age', 30) instead of filter_by_property with operators
- query.first(5) instead of query.take_first(5)
- query.order_by('age') instead of query.sort('age')
- query.avg('age') instead of query.mean('age')
- Much more readable chained queries!
"""

import sys
from pathlib import Path

# Add the parent directory to sys.path for importing graph_elements
sys.path.insert(0, str(Path(__file__).parent.parent))

from graph_elements.base_element import (
    BaseElement,
    ElementDetails,
    ElementProperties,
    NodeTypes,
)
from graph_elements.element_store import ElementStore
from graph_elements.graph_query import FilterOperator, GraphQuery


def main():
    """Demonstrate basic graph elements usage."""

    # Create an element store
    store = ElementStore()

    # Create some sample data
    sample_data = [
        {
            "id": "alice",
            "class_id": "person",
            "name": "Alice Smith",
            "age": 28,
            "department": "Engineering",
            "skills": ["python", "javascript"],
        },
        {
            "id": "bob",
            "class_id": "person",
            "name": "Bob Johnson",
            "age": 35,
            "department": "Engineering",
            "skills": ["java", "python"],
        },
        {
            "id": "carol",
            "class_id": "person",
            "name": "Carol White",
            "age": 32,
            "department": "Design",
            "skills": ["javascript", "css"],
        },
        {
            "id": "david",
            "class_id": "person",
            "name": "David Brown",
            "age": 29,
            "department": "Engineering",
            "skills": ["python", "golang"],
        },
        {
            "id": "eve",
            "class_id": "person",
            "name": "Eve Davis",
            "age": 41,
            "department": "Management",
            "skills": ["leadership", "strategy"],
        },
        {
            "id": "techcorp",
            "class_id": "company",
            "name": "TechCorp Inc",
            "industry": "Technology",
            "employees": 150,
        },
    ]

    # Add elements to store
    for item in sample_data:
        element_id = item.pop("id")
        class_id = item.pop("class_id")

        properties = ElementProperties(**item)
        details = ElementDetails(
            id=element_id, class_id=class_id, type=NodeTypes.NODE, properties=properties
        )

        element = BaseElement(details, store)
        store.elements[element_id] = element

    # Demonstrate query functionality
    GraphQuery(store)

    print("🧪 Graph Elements Library Demo")
    print("=" * 40)

    # Basic queries
    print(f"📊 Total elements: {GraphQuery(store).count()}")
    print(f"👥 Total people: {GraphQuery(store).classId('person').count()}")
    print(f"🏢 Total companies: {GraphQuery(store).classId('company').count()}")
    print()

    # Filter by department - NEW SHORTER API! 🎉
    engineers = (
        GraphQuery(store)
        .classId("person")
        .where("department", FilterOperator.EQ, "Engineering")
        .r()
    )
    print(f"👨‍💻 Engineers ({len(engineers)}):")
    for person in engineers:
        print(
            f"  • {person.properties.get('name')} (age {person.properties.get('age')})"
        )
    print()

    # Age-based queries - MUCH SHORTER!
    experienced = GraphQuery(store).classId("person").gte("age", 35).r()
    print(f"🧑‍🎓 Experienced workers (age >= 35): {len(experienced)}")
    for person in experienced:
        print(
            f"  • {person.properties.get('name')} - {person.properties.get('age')} years"
        )
    print()

    # Skills filtering - CLEANER!
    python_devs = GraphQuery(store).classId("person").contains("skills", "python").r()
    print(f"🐍 Python developers ({len(python_devs)}):")
    for person in python_devs:
        skills = person.properties.get("skills", [])
        print(f"  • {person.properties.get('name')} - Skills: {', '.join(skills)}")
    print()

    # Aggregations - NEW avg() alias!
    people_query = GraphQuery(store).type("person")
    avg_age = people_query.avg("age")
    min_age = GraphQuery(store).type("person").min("age")
    max_age = GraphQuery(store).type("person").max("age")

    print("📈 Age Statistics:")
    print(f"  • Average age: {avg_age:.1f}")
    print(f"  • Youngest: {min_age}")
    print(f"  • Oldest: {max_age}")
    print()

    # Sorted queries - order_by() and first()!
    by_age = GraphQuery(store).classId("person").order_by("age", "desc").first(3).r()

    print("🏆 Top 3 oldest employees:")
    for i, person in enumerate(by_age, 1):
        print(
            f"  {i}. {person.properties.get('name')} ({person.properties.get('age')} years)"
        )
    print()

    # Complex chained query - MUCH MORE READABLE! 🚀
    young_engineers = (
        GraphQuery(store)
        .classId("person")
        .where("department", FilterOperator.EQ, "Engineering")
        .lt("age", 35)
        .r()
    )

    print(f"🚀 Young Engineers (< 35 years in Engineering): {len(young_engineers)}")
    for person in young_engineers:
        print(f"  • {person.properties.get('name')} ({person.properties.get('age')})")
    print()

    # Alternative syntax examples
    print("🔍 Alternative syntax examples:")

    # Multiple syntax options for the same query
    alice_v1 = (
        GraphQuery(store)
        .classId("person")
        .where("name", FilterOperator.EQ, "Alice Smith")
        .r()
    )
    alice_v2 = GraphQuery(store).classId("person").prop("name", "Alice Smith").r()
    seniors_v1 = (
        GraphQuery(store).classId("person").where("age", FilterOperator.GTE, 30).r()
    )
    seniors_v2 = GraphQuery(store).classId("person").gte("age", 30).r()

    print(f"  • Alice (method 1): {len(alice_v1)} found")
    print(f"  • Alice (method 2): {len(alice_v2)} found")
    print(f"  • Seniors >=30 (method 1): {len(seniors_v1)} found")
    print(f"  • Seniors >=30 (method 2): {len(seniors_v2)} found")
    print()

    # Query serialization example - SHORTER!
    complex_query = GraphQuery(store).classId("person").gte("age", 30)

    json_data = complex_query.to_json()
    print(f"🔗 Query Operations: {len(json_data['operations'])} recorded")
    print("Query can be serialized and deserialized for later replay!")
    print()
    print("🎉 SUMMARY: The new shorter API makes queries much more readable!")
    print("Compare:")
    print(
        "  OLD: query.filter_by_class_id('person').filter_by_property('age', FilterOperator.GTE, 30)"
    )
    print("  NEW: query.classId('person').gte('age', 30)")
    print("  Much cleaner! 🚀")


if __name__ == "__main__":
    main()
