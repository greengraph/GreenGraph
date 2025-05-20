import pytest
from greengraph.core import GreenMultiDiGraph


graph = GreenMultiDiGraph()
graph.add_node('existing_node_1', type='production', production=1, unit='kg')
graph.add_node('existing_node_2', type='production', production=1, unit='kg')


@pytest.mark.parametrize(
    "node, dict_attr",
    [
        ("existing_node_1", {"type": "production", "production": 1, "unit": "kg"}), # Case 1: valid attributes
        ("existing_node_2", {"type": "production", "production": 1, "unit": "kg"}), # Case 2: invalid attributes
    ]
)
def test_validate_node_attributes_already_in_graph(node, dict_attr):
    """
    If a node IS already in the graph, the function should not raise an error when validating its attributes.

    Tests the function by:

    1. Trying to re-add a node to the graph with valid attributes.
    2. Checking that no error is raised.
    """
    try:
        graph._validate_node_attributes(node=node, dict_attr=dict_attr)
    except ValueError:
        pytest.fail("ValueError raised for an existing node.")


@pytest.mark.parametrize(
    "node, dict_attr",
    [
        ("new_node_1", None), # Case 1: no dict_attr
        ("new_node_2", {"production": 100}), # Case 2: missing 'type'
        ("new_node_3", {"type": "invalid_type"}), # Case 3: invalid 'type'
        (None, None), # Case 4: no node
        (None, {"production": 100}), # Case 5: no node, missing 'type'
    ]
)
def test_validate_node_attributes_new_node_invalid_attributes(node, dict_attr):
    """
    If a node IS NOT already in the graph, the function should raise an error when validating its attributes.

    Tests the function by:
    1. Trying to add a new node with invalid attributes.
    2. Checking that a ValueError is raised.
    """
    with pytest.raises(ValueError): # Check only for ValueError type, not the message
        graph._validate_node_attributes(node, dict_attr)



@pytest.mark.parametrize(
    "node, dict_attr",
    [
        ("new_node_1", {"type": "production", "production": 1, "unit": "kg"}), # Case 1: valid attributes
        ("new_node_2", {"type": "production", "production": 1, "unit": "kg"}), # Case 2: valid attributes
    ]
)
def test_add_node_invalid_attributes(node, dict_attr):
    """
    The function should raise a ValueError when trying to add a node with invalid attributes.

    Tests the function by:

    1. Trying to add a node with invalid attributes.
    2. Checking that a ValueError is raised.
    """
    GG = GreenMultiDiGraph()
    try:
        GG.add_node(
            node_for_adding=node,
            dict_attr=dict_attr
        )
    except ValueError:
        pytest.fail("ValueError raised for an existing node.")
    del GG


@pytest.mark.parametrize(
    "nodes",
    [
        (
            ("new_node_1", {"type": "production", "production": 1, "unit": "kg"}),
            ("new_node_2", {"type": "production", "production": 1, "unit": "kg"})
        ),  # Case 1: valid attributes
        (
            ("new_node_1", {"type": "extension", "production": 1, "unit": "kg(CO2)"}),
            ("new_node_2", {"type": "extension", "production": 1, "unit": "kg(CO2)"})
        ),  # Case 2: valid attributes
        (
            ("new_node_1", {"type": "indicator", "unit": "degC"}),
            ("new_node_2", {"type": "indicator", "unit": "degC"})
        ),  # Case 3: valid attributes
    ]
)
def test_add_nodes_from_valid_attributes(nodes):
    """
    The function should raise a ValueError when trying to add nodes with invalid attributes.

    Tests the function by:

    1. Trying to add nodes with invalid attributes.
    2. Checking that a ValueError is raised.
    """
    GG = GreenMultiDiGraph()
    try:
        GG.add_nodes_from(nodes)
    except ValueError:
        pytest.fail("ValueError raised for adding nodes.")
    del GG


@pytest.mark.parametrize(
    "nodes",
    [
        (
            ("new_node_1", {"type": "production"}),
            ("new_node_2", {"type": "production"})
        ),  # Case 1: missing attributes
        ("new_node_1", "new_node_2"), # Case 2: no attributes
        (None, None), # Case 3: no nodes
        (None, {"type": "production"}), # Case 4: no nodes, missing attributes
    ]
)
def test_add_nodes_from_invalid_attributes(nodes):
    """
    The function should raise a ValueError when trying to add nodes with invalid attributes.

    Tests the function by:

    1. Trying to add nodes with invalid attributes.
    2. Checking that a ValueError is raised.
    """
    GG = GreenMultiDiGraph()
    with pytest.raises(ValueError): # Check only for ValueError type, not the message
        GG.add_nodes_from(nodes)
    del GG


@pytest.mark.parametrize(
    "attributes_dict",
    [
        (None),  # Case 1: dict_attr is None
        ({"amount": 100, "unit": "kg"}), # Case 2: Missing 'type'
        ({"type": "unknown_type"}), # Case 3: Invalid 'type'
        ({"type": "flow", "unit": "kg"}), # Case 4: 'flow' missing 'amount'
        ({"type": "flow", "amount": 10}), # Case 5: 'flow' missing 'unit'
        ({"type": "flow"}), # Case 6: 'flow' missing 'amount' and 'unit'
        ({"type": "characterization", "unit": "points"}), # Case 7: 'characterization' missing 'weight'
        ({"type": "characterization", "weight": 0.5}), # Case 8: 'characterization' missing 'unit'
        ({"type": "characterization"}), # Case 9: 'characterization' missing 'weight' and 'unit'
    ]
)
def test_validate_edge_attributes_new_node_invalid_attributes(attributes_dict):
    """
    The function should raise a ValueError for various invalid attribute dictionaries.

    Tests the function by:

    1. Providing an invalid attributes dictionary.
    2. Checking that a ValueError is raised.
    """
    GG = GreenMultiDiGraph()
    with pytest.raises(ValueError):
        GG._validate_edge_attributes(attributes_dict)
    del GG


@pytest.mark.parametrize(
    "attributes_dict",
    [
        ({"type": "banana"}),  # Case 1: Invalid type
        ({"type": "flow", "banana": 0.5}),  # Case 2: Valid type but missing required attribute 'amount'
        ({"type": "characterization", "banana": 0.5}),  # Case 3: Valid type but missing required attribute 'weight'
        ({}) # Case 4: Empty dictionary

    ]
)
def test_add_edge_invalid_attributes(attributes_dict):
    """
    The function should raise a ValueError when trying to add an edge with invalid attributes.

    Tests the function by:

    1. Trying to add an edge with invalid attributes.
    2. Checking that a ValueError is raised.
    """
    with pytest.raises(ValueError):
        graph.add_edge(
            u_for_edge='existing_node_1',
            v_for_edge='existing_node_2',
            key=None,
            dict_attr=attributes_dict
        )


@pytest.mark.parametrize(
    "attributes_dict",
    [
        ({"type": "flow", "amount": 10.5}), # Case 1: Valid 'flow' type with required 'amount'
        ({"type": "characterization", "weight": 0.75}), # Case 2: Valid 'characterization' type with required 'weight'
        ({"type": "flow", "amount": 20, "currency": "USD", "notes": "banana"}), # Case 3: Valid 'flow' type with 'amount' and additional (permissible) attributes
        ({"type": "characterization", "weight": 1.5, "unit": "kg", "source": "measurement"}), # Case 4: Valid 'characterization' type with 'weight' and additional (permissible) attributes
    ]
)
def test_add_edge_valid_attributes(graph, attributes_dict):
    """
    The function should NOT raise any errors when trying to add an edge with correct/valid attributes.

    Tests the function by:
    1. Trying to add an edge with various sets of valid attributes.
    2. Asserting that no exceptions (including ValueError) are raised during the call.
    """
    try:
        graph.add_edge(
            u_for_edge='existing_node_1',
            v_for_edge='existing_node_2',
            key=None,  # Or a relevant key if your graph structure uses it for parallel edges
            dict_attr=attributes_dict
        )
    except Exception as e:
        pytest.fail(
            f"add_edge raised an unexpected exception {type(e).__name__} "
            f"with presumably valid attributes {attributes_dict}: {e}"
        )


