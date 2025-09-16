import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Union

from .base_element import BaseElement, ElementDetails, PropertyValue
from .fluent_query import FluentQuery

if TYPE_CHECKING:
    from .edge import Edge
    from .element_store import ElementStore
    from .meta import MetaNode, MetaPropertyType
    from .node import Node

# Type alias for elements
Element = Union["Node", "Edge"]

logger = logging.getLogger(__name__)


class FilterOperator(str, Enum):
    """Filter operators for graph queries."""

    EQ = "eq"
    NOT = "not"
    GT = "gt"
    LT = "lt"
    GTE = "gte"
    LTE = "lte"
    IN = "in"
    BETWEEN = "between"
    CONTAINS = "contains"
    STARTS_WITH = "startsWith"
    ENDS_WITH = "endsWith"
    REGEX = "regex"


class QueryOperations(str, Enum):
    """Available query operations."""

    COMBINE = "combine"
    FILTER_BY_ORIGIN = "filterByOrigin"
    FILTER_BY_SOURCE = "filterBySource"
    FILTER_BY_CLASS_ID = "filterByClassId"
    FILTER_BY_ELEMENTS = "filterByElements"
    FILTER_BY_ELEMENT = "filterByElement"
    FILTER_BY_RELATED_TO = "filterByRelatedTo"
    FILTER_BY_CLASS_IDS = "filterByClassIds"
    EXCLUDE_BY_CLASS_IDS = "excludeByClassIds"
    FILTER_BY_BOUNDING_BOX = "filterByBoundingBox"
    FILTER_BY_TEXT = "filterByText"
    FILTER_BY_CONTEXT = "filterByContext"
    FILTER_BY_PROPERTY = "filterByProperty"
    FILTER_BY_LINK_ELEMENT = "filterByLinkElement"
    FILTER_BY_ID = "filterById"
    FILTER_BY = "filterBy"
    FILTER_BY_FOCUS = "filterByFocus"
    SORT = "sort"
    TAKE_FIRST = "takeFirst"
    TAKE_LAST = "takeLast"
    SEARCH_BY_PROPERTY = "searchByProperty"


@dataclass
class IFluentOptions:
    """Options for fluent query operations."""

    inherit: Optional[bool] = None
    skip_serialization: Optional[bool] = None
    conditions: Optional[Dict[str, Any]] = None
    is_live: Optional[bool] = None
    link_element: Optional[Union[bool, BaseElement]] = None
    property_type: Optional[str] = None
    all: Optional[bool] = None
    include_self: Optional[bool] = None
    levels: Optional[int] = None
    direction: Optional[str] = None  # 'incoming' | 'outgoing' | 'both'
    include_property_edges: Optional[bool] = None


@dataclass
class IFluentOperation:
    """Interface for fluent operation records."""

    method: QueryOperations
    args: Optional[List[Any]] = None
    params: Optional[Dict[str, Any]] = None
    options: Optional[IFluentOptions] = None
    _property_type: Optional["MetaPropertyType"] = None


class ElementFilter(IFluentOperation):
    """Element filter with additional properties."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.enabled: Optional[bool] = kwargs.get("enabled")
        self.name: Optional[str] = kwargs.get("name")
        self.query: Optional[Callable[[GraphQuery], GraphQuery]] = kwargs.get("query")
        self._meta_node: Optional[MetaNode] = kwargs.get("_meta_node")


@dataclass
class ElementFilters:
    """Set of filters that can be applied to elements."""

    text: Optional[str] = None
    properties: Optional[List[Union[str, Dict[str, str]]]] = None
    post_filters: Optional[List[ElementFilter]] = None
    enabled: Optional[bool] = None
    focus_filter: Optional[bool] = None
    bounding_box_enabled: Optional[bool] = None
    bounding_box: Optional[List[float]] = None
    _bounding_box_filter: Optional[ElementFilter] = None
    visible_classes_filters: Optional[bool] = None
    timeline_filter: Optional[bool] = None
    map_filter: Optional[bool] = None
    timeline_filter_property: Optional[str] = None


class GraphQuery(FluentQuery):
    """Graph query implementation similar to TypeScript version."""

    def __init__(self, store: "ElementStore"):
        super().__init__(store)
        self.query_operations: List[IFluentOperation] = []

    def get_element_property(
        self,
        link_element: BaseElement,
        element_id: str,
        key: str,
        default_value: Any = None,
    ) -> Any:
        """Get element property from link element."""
        element_details = getattr(link_element.properties, "element_details", {})
        if element_id in element_details:
            return element_details[element_id].get(key, default_value)
        return default_value

    def check_conditions(
        self, element: BaseElement, options: Optional[IFluentOptions] = None
    ) -> bool:
        """Check if element meets filter conditions."""
        if not options or not options.conditions:
            return False

        if (
            options.conditions.get("class_id")
            and options.conditions["class_id"] != element.class_id
        ):
            return True
        return bool(
            options.conditions.get("class_ids")
            and element.class_id not in options.conditions["class_ids"]
        )

    def filter_by_origin(self, origin: str) -> "GraphQuery":
        """Filter elements by origin."""
        self.result = self.r()

        # Record operation
        self.query_operations.append(
            IFluentOperation(
                method=QueryOperations.FILTER_BY_ORIGIN, params={"origin": origin}
            )
        )

        return self

    def id(self, element_id: str) -> "GraphQuery":
        """Filter elements by ID."""
        self.result = [el for el in self.r() if el.id == element_id]

        # Record operation
        self.query_operations.append(
            IFluentOperation(
                method=QueryOperations.FILTER_BY_ID, params={"id": element_id}
            )
        )

        return self

    def filter_by(self, filters: ElementFilters) -> "GraphQuery":
        """Apply element filters."""
        if filters.text:
            self.filter_by_text(filters.text, IFluentOptions())
        if filters.post_filters:
            # Could implement post_filters here
            pass

        # Record operation
        self.query_operations.append(
            IFluentOperation(
                method=QueryOperations.FILTER_BY, params={"filter": filters}
            )
        )

        return self

    def combine(
        self,
        filters: List[Callable[["GraphQuery"], "GraphQuery"]],
        options: Optional[IFluentOptions] = None,
    ) -> "GraphQuery":
        """Combine multiple filter functions."""
        results = []

        for filter_func in filters:
            query = filter_func(GraphQuery(self.store))
            results.extend(query.result)

        self.result = results

        # Record operation
        self.query_operations.append(
            IFluentOperation(
                method=QueryOperations.COMBINE,
                params={"filters": filters},
                options=options,
            )
        )

        return self

    def filter_by_source(
        self, source: str, options: Optional[IFluentOptions] = None
    ) -> "GraphQuery":
        """Filter elements by source."""
        if options and options.is_live:
            # Handle live filtering if needed
            pass
        else:
            self.result = [el for el in self.r() if el.source == source]

        # Record operation
        self.query_operations.append(
            IFluentOperation(
                method=QueryOperations.FILTER_BY_SOURCE,
                params={"source": source},
                args=[source, options.is_live if options else False],
            )
        )

        return self

    def filter_by_element(
        self, element: Union[ElementDetails, List[ElementDetails]]
    ) -> "GraphQuery":
        """Filter by specific element(s)."""
        params = {}
        if isinstance(element, list) and len(element) > 0:
            params["elements"] = element
        else:
            params["element"] = element

        # Record operation
        self.query_operations.append(
            IFluentOperation(method=QueryOperations.FILTER_BY_ELEMENT, params=params)
        )

        return self

    def filter_by_bounding_box(
        self, bounding_box: List[float], options: Optional[IFluentOptions] = None
    ) -> "GraphQuery":
        """Filter elements by spatial bounding box."""
        if bounding_box and len(bounding_box) == 4:
            west, south, east, north = bounding_box

            filtered_results = []
            for el in self.result:
                center = None

                # Check if _flat.center is available
                if hasattr(el, "_flat") and el.flat and "center" in el.flat:
                    center = el.flat["center"]
                elif hasattr(el, "get_geometry") and callable(el.get_geometry):
                    # Call getGeometry to populate _flat.center
                    el.get_geometry()
                    if hasattr(el, "flat") and el.flat and "center" in el.flat:
                        center = el.flat["center"]
                else:
                    # Fallback: check for direct lat/lon properties
                    lat = el.properties.get("lat")
                    lon = el.properties.get("lon")

                    if lat is not None and lon is not None:
                        try:
                            lat_val = (
                                float(lat) if not isinstance(lat, (int, float)) else lat
                            )
                            lon_val = (
                                float(lon) if not isinstance(lon, (int, float)) else lon
                            )
                            center = [lon_val, lat_val]
                        except (ValueError, TypeError):
                            continue

                # Check if element is within bounds
                if center and len(center) >= 2:
                    lon_val, lat_val = center[0], center[1]
                    if west <= lon_val <= east and south <= lat_val <= north:
                        filtered_results.append(el)

            self.result = filtered_results
        self._operations_performed = True

        # Record operation
        self.query_operations.append(
            IFluentOperation(
                method=QueryOperations.FILTER_BY_BOUNDING_BOX,
                params={"box": bounding_box},
            )
        )

        return self

    def filter_by_context(
        self, element_id: str, options: Optional[IFluentOptions] = None
    ) -> "GraphQuery":
        """Filter by context element."""
        element = self.store.get_element(element_id)
        if element and hasattr(element.properties, "context"):
            context = getattr(element.properties, "context", [])
            if isinstance(context, list):
                self.result = context
            else:
                self.result = []
        else:
            self.result = []

        # Record operation
        self.query_operations.append(
            IFluentOperation(
                method=QueryOperations.FILTER_BY_CONTEXT,
                params={"element_id": element_id, "options": options},
                options=options,
                args=[element_id, options],
            )
        )

        return self

    def filter_by_class_ids(
        self,
        class_ids: Optional[List[str]] = None,
        options: Optional[IFluentOptions] = None,
    ) -> "GraphQuery":
        """Filter by multiple class IDs."""
        if not class_ids:
            self.result = []
            return self

        logger.info(
            f"filter by class ids: {class_ids}, inherit: {options.inherit if options else False}"
        )

        if options and options.inherit:
            self.result = [
                el
                for el in self.result
                if (
                    el.class_id in class_ids
                    or (
                        hasattr(el, "meta_node")
                        and el.meta_node
                        and hasattr(el.meta_node, "inherited_meta_nodes_names")
                        and any(
                            name in class_ids
                            for name in el.meta_node.inherited_meta_nodes_names
                        )
                    )
                )
            ]
        else:
            self.result = [el for el in self.result if el.class_id in class_ids]

        # Record operation
        self.query_operations.append(
            IFluentOperation(
                method=QueryOperations.FILTER_BY_CLASS_IDS,
                params={"class_ids": class_ids, "options": options},
                options=options,
            )
        )

        return self

    def exclude_by_class_ids(
        self,
        class_ids: Optional[List[str]] = None,
        options: Optional[IFluentOptions] = None,
    ) -> "GraphQuery":
        """Exclude elements by class IDs."""
        if not class_ids:
            return self

        logger.info(
            f"exclude by class ids: {class_ids}, inherit: {options.inherit if options else False}"
        )

        if options and options.inherit:
            self.result = [
                el
                for el in self.result
                if not (
                    el.class_id in class_ids
                    or (
                        hasattr(el, "meta_node")
                        and el.meta_node
                        and hasattr(el.meta_node, "inherited_meta_nodes_names")
                        and any(
                            name in class_ids
                            for name in el.meta_node.inherited_meta_nodes_names
                        )
                    )
                )
            ]
        else:
            self.result = [el for el in self.result if el.class_id not in class_ids]

        # Record operation
        self.query_operations.append(
            IFluentOperation(
                method=QueryOperations.EXCLUDE_BY_CLASS_IDS,
                params={"class_ids": class_ids, "options": options},
                options=options,
            )
        )

        return self

    def filter_by_elements(
        self, elements: List[BaseElement], options: Optional[IFluentOptions] = None
    ) -> "GraphQuery":
        """Filter by specific elements."""
        if not elements:
            self.result = []
            return self

        self.result = elements

        # Record operation
        self.query_operations.append(
            IFluentOperation(method=QueryOperations.FILTER_BY_ELEMENTS, options=options)
        )

        return self

    def classId(
        self, class_id: str, options: Optional[Dict[str, Any]] = None
    ) -> "GraphQuery":
        """Filter by single class ID - semantic method name."""
        inherit = options.get("inherit", False) if options else False

        # Start with current result set or all elements if empty
        base_elements = self.r()

        if inherit:
            self.result = [
                el
                for el in base_elements
                if (
                    el.class_id == class_id
                    or (
                        hasattr(el, "meta_node")
                        and el.meta_node
                        and hasattr(el.meta_node, "inherited_meta_nodes_names")
                        and class_id in el.meta_node.inherited_meta_nodes_names
                    )
                )
            ]
        else:
            self.result = [el for el in base_elements if el.class_id == class_id]

        # Record this operation
        self.query_operations.append(
            IFluentOperation(
                method=QueryOperations.FILTER_BY_CLASS_ID,
                params={"class_id": class_id, "options": options},
                options=IFluentOptions(**options) if options else None,
            )
        )

        return self

    def class_(
        self, class_id: str, options: Optional[Dict[str, Any]] = None
    ) -> "GraphQuery":
        """
        @deprecated Use classId() instead for better semantic clarity.
        Filter by single class ID - Python-compatible method name.
        """
        import warnings

        warnings.warn(
            "class_() method is deprecated. Use classId() instead for filtering by class ID.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.classId(class_id, options)

    def type(
        self, class_id: str, options: Optional[Dict[str, Any]] = None
    ) -> "GraphQuery":
        """
        @deprecated Use classId() instead for better semantic clarity.
        Filter by single class ID (type).
        """
        import warnings

        warnings.warn(
            "type() method is deprecated. Use classId() instead for filtering by class ID.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.classId(class_id, options)

    def filter_by_related_to(
        self, element_id: str, options: Optional[Dict[str, Any]] = None
    ) -> "GraphQuery":
        """Filter by elements related to given element."""
        element = self.store.get_element(element_id)
        if not element or not hasattr(element, "edges"):
            self.result = []
            return self

        include_self = options.get("include_self", False) if options else False

        filtered_results = []
        for el in self.result:
            if include_self and el.id == element_id:
                filtered_results.append(el)
                continue

            # Check if element is connected via edges
            if hasattr(element, "edges"):
                for edge in element.edges:
                    if edge.from_id == el.id or edge.to_id == el.id:
                        filtered_results.append(el)
                        break

        self.result = filtered_results
        self._operations_performed = True

        # Record operation
        self.query_operations.append(
            IFluentOperation(
                method=QueryOperations.FILTER_BY_RELATED_TO,
                params={"element_id": element_id, "options": options},
                options=IFluentOptions(**options) if options else None,
            )
        )

        return self

    def filter_by_focus(
        self,
        seeds: List[Union[str, Dict[str, Any]]],
        options: Optional[IFluentOptions] = None,
    ) -> "GraphQuery":
        """Filter by focus elements with configurable levels and direction."""
        # Normalize seeds to objects with explicit settings
        default_levels = options.levels if options else 1
        default_direction = options.direction if options else "both"
        default_include_self = options.include_self if options else True
        default_include_property_edges = (
            options.include_property_edges if options else True
        )

        normalized_seeds = []
        for seed in seeds or []:
            if isinstance(seed, str):
                normalized_seeds.append(
                    {
                        "id": seed,
                        "levels": default_levels,
                        "direction": default_direction,
                        "include_self": default_include_self,
                        "include_property_edges": default_include_property_edges,
                    }
                )
            elif isinstance(seed, dict) and "id" in seed:
                normalized_seeds.append(
                    {
                        "id": seed["id"],
                        "levels": seed.get("levels", default_levels),
                        "direction": seed.get("direction", default_direction),
                        "include_self": seed.get("include_self", default_include_self),
                        "include_property_edges": seed.get(
                            "include_property_edges", default_include_property_edges
                        ),
                    }
                )

        # BFS per seed up to configured levels
        neighbor_ids = set()
        focus_node_ids = set()

        def enqueue_neighbors(node, push_func, direction, include_property_edges):
            """Helper to enqueue neighbors based on direction."""
            # Graph edges
            if direction in ("outgoing", "both") and hasattr(node, "outgoing_edges"):
                for edge in node.outgoing_edges:
                    if edge.to_id:
                        push_func(edge.to_id)

            if direction in ("incoming", "both") and hasattr(node, "incoming_edges"):
                for edge in node.incoming_edges:
                    if edge.from_id:
                        push_func(edge.from_id)

            # Property-based relations if enabled
            if include_property_edges and hasattr(node, "meta_node") and node.meta_node:
                meta_prop_types = getattr(node.meta_node, "all_prop_types", {})
                if hasattr(node, "get_property_elements"):
                    for prop_name, prop_type in meta_prop_types.items():
                        if (
                            hasattr(prop_type, "type")
                            and prop_type.type in ("element", "relation")
                            or getattr(prop_type, "label", "") == "inheritsFrom"
                        ):
                            try:
                                elements = node.get_property_elements(prop_name)
                                for el in elements:
                                    if el and el.id:
                                        push_func(el.id)
                            except (AttributeError, KeyError, TypeError):
                                # Ignore errors when getting property elements fails
                                # This can happen when properties are not properly configured
                                continue

        # Process each seed
        for seed in normalized_seeds:
            start_node = self.store.get_element(seed["id"])
            if not start_node:
                continue

            focus_node_ids.add(seed["id"])

            # Include seed if requested
            if seed["include_self"]:
                neighbor_ids.add(seed["id"])

            if seed["levels"] <= 0:
                continue

            visited = {seed["id"]}
            queue = []

            # Seed initial neighbors
            def add_to_queue(node_id):
                if node_id not in visited:
                    visited.add(node_id)
                    queue.append({"id": node_id, "depth": 1})

            enqueue_neighbors(
                start_node,
                add_to_queue,
                seed["direction"],
                seed["include_property_edges"],
            )

            # BFS traversal
            while queue:
                current = queue.pop(0)
                neighbor_ids.add(current["id"])

                if current["depth"] >= seed["levels"]:
                    continue

                node = self.store.get_element(current["id"])
                if not node:
                    continue

                def add_next_level(node_id):
                    if node_id not in visited:
                        visited.add(node_id)
                        queue.append({"id": node_id, "depth": current["depth"] + 1})

                enqueue_neighbors(
                    node,
                    add_next_level,
                    seed["direction"],
                    seed["include_property_edges"],
                )

        # Build result elements
        result_elements = []
        seen = set()

        for node_id in neighbor_ids:
            element = self.store.get_element(node_id)
            if element and element.id not in seen:
                seen.add(element.id)
                result_elements.append(element)

        self.result = result_elements

        # Record operation
        recorded_seeds = [
            {
                "id": s["id"],
                "levels": s["levels"],
                "direction": s["direction"],
                "include_self": s["include_self"],
                "include_property_edges": s["include_property_edges"],
            }
            for s in normalized_seeds
        ]

        self.query_operations.append(
            IFluentOperation(
                method=QueryOperations.FILTER_BY_FOCUS,
                params={"seeds": recorded_seeds, "element_ids": list(focus_node_ids)},
                options=options,
            )
        )

        return self

    def text(
        self, text: Optional[str] = None, options: Optional[IFluentOptions] = None
    ) -> "GraphQuery":
        """Filter elements by text in name property."""
        if not text:
            return self

        # Start with current result set or all elements if empty
        base_elements = self.r()
        text_lower = text.lower()

        self.result = [
            el
            for el in base_elements
            if (
                hasattr(el.properties, "name")
                and el.properties.name
                and isinstance(el.properties.name, str)
                and len(el.properties.name) > 0
                and text_lower in el.properties.name.lower()
            )
        ]

        # Record operation
        self.query_operations.append(
            IFluentOperation(
                method=QueryOperations.FILTER_BY_TEXT,
                params={"text": text, "options": options},
                options=options,
            )
        )

        return self

    def search_by_property(
        self, key: str, search_term: str, options: Optional[IFluentOptions] = None
    ) -> "GraphQuery":
        """Search property using regex."""
        # Create regex pattern
        regex_pattern = re.compile(search_term, re.IGNORECASE)

        # Record operation
        self.query_operations.append(
            IFluentOperation(
                method=QueryOperations.SEARCH_BY_PROPERTY,
                params={"key": key, "search_term": search_term},
            )
        )

        # Use filter_by_property with regex operator
        skip_options = IFluentOptions(**(vars(options) if options else {}))
        skip_options.skip_serialization = True

        return self.filter_by_property(
            key, FilterOperator.REGEX, regex_pattern, skip_options
        )

    def filter_by_link_element(
        self, link_element: BaseElement, options: Optional[IFluentOptions] = None
    ) -> "GraphQuery":
        """Filter by link element."""
        element_details = getattr(link_element.properties, "element_details", {})
        if element_details:
            self.result = [el for el in self.result if el.id in element_details]

        return self

    def where(
        self,
        key: str,
        operator: FilterOperator,
        value: PropertyValue,
        options: Optional[IFluentOptions] = None,
    ) -> "GraphQuery":
        """Filter elements by property with various operators (primary where method)."""
        # Log relation property filtering
        if options and options.property_type == "relation":
            logger.info(
                f"Starting relation property filter: key={key}, operator={operator}, value={value}, propertyType={options.property_type}, totalElements={len(self.r())}"
            )

        # Start with current result set or all elements if empty
        base_elements = self.r()
        filtered_results = []

        for el in base_elements:
            # Check conditions
            if self.check_conditions(el, options):
                filtered_results.append(el)
                continue

            # Handle empty values
            prop_exists = key in el.properties
            prop_value = el.properties.get(key) if prop_exists else None
            is_empty_array = isinstance(prop_value, list) and len(prop_value) == 0
            is_empty_value = not value or (isinstance(value, list) and len(value) == 0)

            if (not prop_exists or is_empty_array) and is_empty_value:
                filtered_results.append(el)
                continue

            if not prop_exists:
                continue

            # Get property value (considering link elements)
            if (
                options
                and options.link_element
                and not isinstance(options.link_element, bool)
            ):
                prop_value = self.get_element_property(options.link_element, el.id, key)
            else:
                prop_value = el.properties.get(key)

            "array" if isinstance(prop_value, list) else type(prop_value).__name__

            # Apply operator
            result = False

            if operator == FilterOperator.EQ:
                if options and options.property_type == "relation":
                    result = self._handle_relation_filter(el, key, value, "eq", options)
                else:
                    result = prop_value == value

            elif operator == FilterOperator.NOT:
                if options and options.property_type == "relation":
                    result = self._handle_relation_filter(
                        el, key, value, "not", options
                    )
                else:
                    result = prop_value != value

            elif operator == FilterOperator.GT:
                result = isinstance(prop_value, (int, float)) and prop_value > value

            elif operator == FilterOperator.LT:
                result = isinstance(prop_value, (int, float)) and prop_value < value

            elif operator == FilterOperator.GTE:
                result = isinstance(prop_value, (int, float)) and prop_value >= value

            elif operator == FilterOperator.LTE:
                result = isinstance(prop_value, (int, float)) and prop_value <= value

            elif operator == FilterOperator.BETWEEN:
                result = (
                    isinstance(prop_value, (int, float))
                    and isinstance(value, list)
                    and len(value) >= 2
                    and value[0] <= prop_value <= value[1]
                )

            elif operator == FilterOperator.IN:
                if not isinstance(value, list) or len(value) == 0:
                    result = True
                else:
                    if options and options.property_type == "tags":
                        result = (
                            all(val in prop_value for val in value)
                            if isinstance(prop_value, list)
                            else False
                        )
                    elif options and options.property_type == "options":
                        result = prop_value in value
                    else:
                        result = True

            elif operator == FilterOperator.CONTAINS:
                result = self._handle_contains_filter(
                    el, key, prop_value, value, options
                )

            elif operator == FilterOperator.STARTS_WITH:
                result = isinstance(prop_value, str) and prop_value.startswith(
                    str(value)
                )

            elif operator == FilterOperator.ENDS_WITH:
                result = isinstance(prop_value, str) and prop_value.endswith(str(value))

            elif operator == FilterOperator.REGEX:
                if isinstance(value, re.Pattern):
                    result = (
                        bool(value.search(str(prop_value))) if prop_value else False
                    )
                else:
                    try:
                        pattern = re.compile(str(value))
                        result = (
                            bool(pattern.search(str(prop_value)))
                            if prop_value
                            else False
                        )
                    except re.error:
                        result = False

            if result:
                filtered_results.append(el)

        self.result = filtered_results
        self._operations_performed = True

        # Log relation property filtering results
        if options and options.property_type == "relation":
            logger.info(
                f"Completed relation property filter: key={key}, operator={operator}, value={value}, remainingElements={len(self.result)}"
            )

        if not (options and options.skip_serialization):
            # Record operation
            self.query_operations.append(
                IFluentOperation(
                    method=QueryOperations.FILTER_BY_PROPERTY,  # Keep for serialization compatibility
                    params={"key": key, "operator": operator, "value": value},
                    options=options,
                )
            )

        return self

    def _handle_relation_filter(
        self,
        element: BaseElement,
        key: str,
        value: Any,
        operator_type: str,
        options: IFluentOptions,
    ) -> bool:
        """Handle relation property filtering."""
        logger.info(
            f"Filtering relation property with {operator_type} operator: key={key}, value={value}, elementId={element.id}, propertyType={options.property_type}"
        )

        if not hasattr(element, "outgoing_edges"):
            logger.info(f"No outgoing edges found for element: {element.id}")
            return (
                operator_type == "not"
            )  # Return True for 'not' operator when no edges exist

        outgoing_edges = getattr(element, "outgoing_edges", [])
        logger.info(
            f'Element outgoing edges: {[{"id": e.id, "class_id": e.class_id, "to_id": e.to_id} for e in outgoing_edges]}'
        )

        # Get expected relation type from meta node
        expected_relation_type = None
        if (
            hasattr(element, "meta_node")
            and element.meta_node
            and hasattr(element.meta_node, "all_prop_types")
        ):
            prop_type = element.meta_node.all_prop_types.get(key)
            if prop_type and hasattr(prop_type, "relation") and prop_type.relation:
                expected_relation_type = getattr(prop_type.relation, "type", None)

        logger.info(f"Expected relation type: {expected_relation_type}")

        # Find related element IDs for this relation type
        related_element_ids = [
            edge.to_id
            for edge in outgoing_edges
            if edge.class_id == expected_relation_type and edge.to_id
        ]

        logger.info(
            f"Related element IDs for this relation type: {related_element_ids}"
        )

        # Apply operator
        if operator_type == "eq":
            result = value in related_element_ids
        else:  # 'not'
            result = value not in related_element_ids

        logger.info(f"Relation filter result ({operator_type}): {result}")
        return result

    def _handle_contains_filter(
        self,
        element: BaseElement,
        key: str,
        prop_value: Any,
        value: Any,
        options: Optional[IFluentOptions],
    ) -> bool:
        """Handle contains operator filtering."""
        if options and options.property_type == "options":
            return prop_value in value if isinstance(value, list) else False
        elif options and options.property_type == "string":
            if value is None or prop_value is None:
                return False
            if isinstance(value, str) and len(value) == 0:
                return True
            return (
                isinstance(prop_value, str) and str(value).lower() in prop_value.lower()
            )
        elif options and options.property_type == "tags":
            if not isinstance(prop_value, list):
                return False
            if not isinstance(value, list) or len(value) == 0:
                return True
            return all(v in prop_value for v in value)
        elif options and options.property_type == "relation":
            return self._handle_relation_filter(
                element, key, value, "contains", options
            )
        else:
            # Default behavior - check if we're searching in an array property
            if isinstance(prop_value, list):
                # If searching in an array, check if the search value is contained
                if isinstance(value, str):
                    return value in prop_value
                elif isinstance(value, list):
                    return all(v in prop_value for v in value)
                else:
                    return value in prop_value
            elif (
                isinstance(prop_value, str)
                and prop_value is not None
                and value is not None
            ):
                if len(str(value)) == 0:
                    return True
                return str(value).lower() in prop_value.lower()
            return False

    # Aggregation methods
    def select_property(self, property_name: str) -> List[PropertyValue]:
        """Select property values from all elements."""
        return [
            el.properties.get(property_name)
            for el in self.result
            if property_name in el.properties
        ]

    def _calculate_aggregation(
        self,
        property_name: str,
        aggregator: Callable[[float, float], float],
        initial_value: float,
    ) -> float:
        """Helper for aggregation calculations."""
        result = initial_value
        for el in self.result:
            value = el.properties.get(property_name)
            if isinstance(value, (int, float)):
                result = aggregator(result, value)
        return result

    def count(self) -> int:
        """Count elements in result."""
        return len(self.r())

    def avg(self, property_name: str) -> float:
        """Calculate average (mean) of numeric property."""
        total = self._calculate_aggregation(property_name, lambda a, b: a + b, 0)
        elements = self.r()
        return total / len(elements) if elements else 0

    def mean(self, property_name: str) -> float:
        """Alias for avg() - calculate average of numeric property."""
        return self.avg(property_name)

    def sum(self, property_name: str) -> float:
        """Sum numeric property values."""
        return self._calculate_aggregation(property_name, lambda a, b: a + b, 0)

    def product(self, property_name: str) -> float:
        """Calculate product of numeric property values."""
        return self._calculate_aggregation(property_name, lambda a, b: a * b, 1)

    def min(self, property_name: str) -> float:
        """Find minimum value of numeric property."""
        values = [
            el.properties.get(property_name)
            for el in self.result
            if isinstance(el.properties.get(property_name), (int, float))
        ]
        return min(values) if values else 0

    def max(self, property_name: str) -> float:
        """Find maximum value of numeric property."""
        values = [
            el.properties.get(property_name)
            for el in self.result
            if isinstance(el.properties.get(property_name), (int, float))
        ]
        return max(values) if values else 0

    def median(self, property_name: str) -> float:
        """Calculate median of numeric property."""
        values = [
            el.properties.get(property_name)
            for el in self.result
            if isinstance(el.properties.get(property_name), (int, float))
        ]
        values.sort()

        if not values:
            return 0

        mid = len(values) // 2
        if len(values) % 2 == 0:
            return (values[mid - 1] + values[mid]) / 2
        else:
            return values[mid]

    def sort(self, property_name: str, direction: str = "asc") -> "GraphQuery":
        """Sort elements by property."""
        reverse = direction == "desc"

        def sort_key(el):
            value = el.properties.get(property_name)
            # Handle None values by putting them at the end
            return (value is None, value)

        self.result.sort(key=sort_key, reverse=reverse)

        # Record operation
        self.query_operations.append(
            IFluentOperation(
                method=QueryOperations.SORT,
                params={"property_name": property_name, "direction": direction},
            )
        )

        return self

    def first(self, n: int = 1) -> "GraphQuery":
        """Take first n elements."""
        self.result = self.r()[:n]
        self._operations_performed = True

        # Record operation
        self.query_operations.append(
            IFluentOperation(method=QueryOperations.TAKE_FIRST, params={"n": n})
        )

        return self

    def last(self, n: int = 1) -> "GraphQuery":
        """Take last n elements."""
        self.result = self.r()[-n:]
        self._operations_performed = True

        # Record operation
        self.query_operations.append(
            IFluentOperation(method=QueryOperations.TAKE_LAST, params={"n": n})
        )

        return self

    # ===== SHORTER, DEVELOPER-FRIENDLY ALIASES =====

    def of_type(self, class_id: str, **options) -> "GraphQuery":
        """Alternative alias for type()."""
        return self.type(class_id, options)

    # Flexible where method - supports multiple syntaxes
    def prop(self, property_name: str, value) -> "GraphQuery":
        """Shorter alias for property equality filter."""
        return self.where(property_name, FilterOperator.EQ, value)

    # Comparison shortcuts
    def gt(self, property_name: str, value) -> "GraphQuery":
        """Greater than filter."""
        return self.where(property_name, FilterOperator.GT, value)

    def lt(self, property_name: str, value) -> "GraphQuery":
        """Less than filter."""
        return self.where(property_name, FilterOperator.LT, value)

    def gte(self, property_name: str, value) -> "GraphQuery":
        """Greater than or equal filter."""
        return self.where(property_name, FilterOperator.GTE, value)

    def lte(self, property_name: str, value) -> "GraphQuery":
        """Less than or equal filter."""
        return self.where(property_name, FilterOperator.LTE, value)

    def contains(self, property_name: str, value) -> "GraphQuery":
        """Contains filter for arrays and strings."""
        return self.where(property_name, FilterOperator.CONTAINS, value)

    def matches(self, property_name: str, pattern) -> "GraphQuery":
        """Regex pattern matching."""
        return self.where(property_name, FilterOperator.REGEX, pattern)

    def search(self, search_term: str) -> "GraphQuery":
        """Alternative alias for text search."""
        return self.text(search_term)

    def by_id(self, element_id: str) -> "GraphQuery":
        """Alternative alias for id()."""
        return self.id(element_id)

    # Collection operations
    def limit(self, n: int) -> "GraphQuery":
        """Alias for first() - common in query builders."""
        return self.first(n)

    def order_by(self, property_name: str, direction: str = "asc") -> "GraphQuery":
        """Shorter alias for sort."""
        return self.sort(property_name, direction)

    # Relationship and spatial shortcuts
    def focus(self, seeds, **options) -> "GraphQuery":
        """Shorter alias for filter_by_focus."""
        return self.filter_by_focus(
            seeds, IFluentOptions(**options) if options else None
        )

    def expand(self, seeds, **options) -> "GraphQuery":
        """Alternative shorter alias for filter_by_focus."""
        return self.filter_by_focus(
            seeds, IFluentOptions(**options) if options else None
        )

    def related_to(self, element_id: str, **options) -> "GraphQuery":
        """Shorter alias for filter_by_related_to."""
        return self.filter_by_related_to(element_id, options)

    def connected_to(self, element_id: str, **options) -> "GraphQuery":
        """Alternative shorter alias for filter_by_related_to."""
        return self.filter_by_related_to(element_id, options)

    def bbox(self, bounds: List[float], **options) -> "GraphQuery":
        """Shorter alias for filter_by_bounding_box."""
        return self.filter_by_bounding_box(
            bounds, IFluentOptions(**options) if options else None
        )

    def bounds(self, bounds: List[float], **options) -> "GraphQuery":
        """Alternative shorter alias for filter_by_bounding_box."""
        return self.filter_by_bounding_box(
            bounds, IFluentOptions(**options) if options else None
        )

    def construct_query(
        self,
        operations: List[IFluentOperation],
        elements: Optional[List[BaseElement]] = None,
    ) -> None:
        """Reconstruct query from operations."""
        if elements:
            self.result = elements

        for op in operations:
            if not op.args:
                op.args = []
            if not op.params:
                op.params = {}
            if not op.options:
                op.options = IFluentOptions()

            op.method.value.replace("_", "").lower()  # Convert to method name

            if op.method == QueryOperations.FILTER_BY_ELEMENT:
                self.filter_by_element(op.params.get("element"))
            elif op.method == QueryOperations.FILTER_BY_ORIGIN:
                self.filter_by_origin(op.params.get("origin"))
            elif op.method == QueryOperations.FILTER_BY_SOURCE:
                self.filter_by_source(op.params.get("source"), op.options)
            elif op.method == QueryOperations.FILTER_BY_ID:
                self.filter_by_id(op.params.get("id"))
            elif op.method == QueryOperations.FILTER_BY_CLASS_ID:
                self.type(
                    op.params.get("class_id"), vars(op.options) if op.options else None
                )
            elif op.method == QueryOperations.FILTER_BY_ELEMENTS:
                self.filter_by_elements(op.params.get("elements", []), op.options)
            elif op.method == QueryOperations.FILTER_BY_FOCUS:
                seeds = op.params.get(
                    "seeds", op.params.get("element_ids", op.args[0] if op.args else [])
                )
                self.filter_by_focus(seeds, op.options)
            elif op.method == QueryOperations.FILTER_BY_CLASS_IDS:
                self.filter_by_class_ids(op.params.get("class_ids"), op.options)
            elif op.method == QueryOperations.EXCLUDE_BY_CLASS_IDS:
                self.exclude_by_class_ids(op.params.get("class_ids"), op.options)
            elif op.method == QueryOperations.FILTER_BY_RELATED_TO:
                self.filter_by_related_to(
                    op.params.get("element_id"),
                    vars(op.options) if op.options else None,
                )
            elif op.method == QueryOperations.FILTER_BY_BOUNDING_BOX:
                self.filter_by_bounding_box(op.params.get("box"), op.options)
            elif op.method == QueryOperations.FILTER_BY_CONTEXT:
                self.filter_by_context(op.params.get("element_id"), op.options)
            elif op.method == QueryOperations.COMBINE:
                self.combine(op.params.get("filters", []), op.options)
            elif op.method == QueryOperations.FILTER_BY_TEXT:
                self.filter_by_text(op.params.get("text"), op.options)
            elif op.method == QueryOperations.FILTER_BY_LINK_ELEMENT:
                self.filter_by_link_element(op.params.get("link_element"), op.options)
            elif op.method == QueryOperations.FILTER_BY_PROPERTY:
                if op._property_type:
                    op.options.property_type = getattr(op._property_type, "type", None)
                self.where(
                    op.params.get("key"),
                    op.params.get("operator"),
                    op.params.get("value"),
                    op.options,
                )
            elif op.method == QueryOperations.SORT:
                self.sort(
                    op.params.get("property_name"), op.params.get("direction", "asc")
                )
            elif op.method == QueryOperations.TAKE_FIRST:
                self.first(op.params.get("n", 1))
            elif op.method == QueryOperations.TAKE_LAST:
                self.last(op.params.get("n", 1))
            elif op.method == QueryOperations.SEARCH_BY_PROPERTY:
                self.search_by_property(
                    op.params.get("key"), op.params.get("search_term")
                )

    @staticmethod
    def deserialize_query(
        operations: List[IFluentOperation], store: "ElementStore"
    ) -> "GraphQuery":
        """Deserialize query operations."""
        query = GraphQuery(store)
        query.construct_query(operations)
        return query

    def to_json(self) -> Dict[str, Any]:
        """Serialize query operations to JSON."""
        operations = []
        for op in self.query_operations:
            operations.append(
                {
                    "method": op.method.value,
                    "params": op.params,
                    "options": vars(op.options) if op.options else None,
                }
            )
        return {"operations": operations}
