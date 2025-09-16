"""
Very Simple Person Creation Example

Shows the minimal code needed to create a person with name and age.
"""

from graph_elements.base_element import Props
from graph_elements.element_store import ElementStore


def main():
    print("🧪 SIMPLE PERSON WITH NAME AND AGE")
    print("=" * 40)

    # Create a person with just name and age
    person = Props(name="John Doe", age=30)

    # Access the properties
    print(f"Name: {person['name']}")
    print(f"Age: {person['age']}")

    # Add more properties dynamically
    person["city"] = "Boston"
    person["job"] = "Engineer"

    print(f"City: {person['city']}")
    print(f"Job: {person['job']}")

    # Show it works like a regular dict
    print(f"\nAll properties: {dict(person)}")

    # Show total property count
    print(f"Total properties: {len(person)}")

    print("\n" + "=" * 40)
    print("🏪 ADDING PERSON TO ELEMENTSTORE AS NODE")

    # Create an ElementStore
    store = ElementStore()
    print(f"Created ElementStore with {len(store.elements)} elements")

    # 🚀 SINGLE LINE: Create and add node directly with kwargs - sync by default!
    person_node = store.addNode(
        "person", name="John Doe", age=30, city="Boston", job="Engineer"
    )

    print("✅ Created and added node in ONE line with kwargs!")
    print(f"  ID: {person_node.id}")
    print(f"  Class: {person_node.class_id}")
    print(f"  Name: {person_node.properties['name']}")
    print(f"  Age: {person_node.properties['age']}")
    print(f"  City: {person_node.properties['city']}")
    print(f"  Job: {person_node.properties['job']}")
    print(f"ElementStore now contains {len(store.elements)} elements")

    # Test the createNode method (renamed from create_new_element)
    print("\n--- Testing createNode method ---")
    another_person = Props(name="Alice Smith", age=28, job="Designer")
    existing_node = store.createNode("person", another_person)
    print(f"Created node with createNode(): {existing_node.properties['name']}")

    # Add the existing node using addNode (sync by default)
    added_node = store.addNode(existing_node)
    print(f"Added existing node: {added_node.properties['name']}")
    print(f"ElementStore now contains {len(store.elements)} elements")

    # Test addNode with Props object too
    print("\n--- Testing addNode with Props ---")
    props_person = Props(name="Charlie Brown", age=35, city="Paris")
    props_node = store.addNode("person", props_person)
    print(
        f"Added with Props: {props_node.properties['name']} from {props_node.properties['city']}"
    )
    print(f"ElementStore now contains {len(store.elements)} elements")

    # Retrieve the node from the store to verify
    retrieved_node = store.get_element_by_id(person_node.id)
    if retrieved_node:
        print(f"✅ Retrieved from store: {retrieved_node.properties['name']}")
    else:
        print("❌ Could not retrieve node from store")

    print("\n" + "=" * 40)
    print("🔗 TESTING EDGE API (Coming Soon!)")
    print("Edge API is being implemented - will work like:")
    print("# Create two nodes")
    print("alice = store.addNode('person', name='Alice', age=25)")
    print("bob = store.addNode('person', name='Bob', age=30)")
    print("")
    print("# Add edge between them")
    print("edge = store.addEdge('friendship', alice, bob, type='friend')")
    print("✅ Edge API design complete - implementation in progress")

    print("\n✅ Person created successfully!")

    print("\n" + "=" * 50)
    print("🚀 ULTIMATE SINGLE-LINE API (SYNC BY DEFAULT!):")
    print("# Node operations:")
    print("store = ElementStore()")
    print("")
    print("# Method 1: Single line with kwargs (CLEANEST!)")
    print("node = store.addNode('person', name='John', age=30)")
    print("")
    print("# Method 2: With Props object")
    print("props = Props(name='John', age=30)")
    print("node = store.addNode('person', props)")
    print("")
    print("# Method 3: Create then add")
    print("node = store.createNode('person', props)")
    print("store.addNode(node)")
    print("")
    print("# Edge operations (same pattern):")
    print("alice = store.addNode('person', name='Alice')")
    print("bob = store.addNode('person', name='Bob')")
    print("edge = store.addEdge('friendship', alice, bob, type='friend')")
    print("")
    print("# For async use: store.addNodeAsync(...) or store.addEdgeAsync(...)")
    print("=" * 50)


if __name__ == "__main__":
    main()
