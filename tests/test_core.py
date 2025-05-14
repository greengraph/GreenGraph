import pytest
from greengraph.core import GreenMultiDiGraph


graph = GreenMultiDiGraph()
graph.add_node('existing_node', type='production', production=1, unit='kg')


def test_node_already_in_graph_no_error():
    """
    If a node is already in the graph, the function should not raise an error when validating its attributes.
    """
    try:
        graph._validate_node_attributes('existing_node', {'type': 'production', 'production': 1, 'unit': 'kg'})
        graph._validate_node_attributes('existing_node', None) # Should also pass
    except ValueError:
        pytest.fail("ValueError raised for an existing node.")


@pytest.mark.parametrize(
    "node_name, attributes",
    [
        ("new_node_1", None), # no attributes
        ("new_node_2", {"production": 100}), # missing 'type'
        ("new_node_3", {"type": "invalid_type"}), # invalid 'type'
        (None, None), # no node
        (None, {"production": 100}), # no node, missing 'type'
    ]
)
def test_initial_validation_errors_for_new_node(node_name, attributes):
    """
    If a node is not already in the graph, the function should raise an error when validating its attributes.
    """
    with pytest.raises(ValueError): # Check only for ValueError type, not the message
        graph._validate_node_attributes(node_name, attributes)


@pytest.mark.parametrize(
    "attributes_dict",
    [
        (None),  # Case 1: dict_attr is None
        ({"amount": 100, "unit": "kg"}),  # Case 2: Missing 'type'
        ({"type": "unknown_type"}),  # Case 3: Invalid 'type'
        ({"type": "flow", "unit": "kg"}),  # Case 4: 'flow' missing 'amount'
        ({"type": "flow", "amount": 10}),  # Case 5: 'flow' missing 'unit'
        ({"type": "flow"}), # Case 6: 'flow' missing 'amount' and 'unit'
        ({"type": "characterization", "unit": "points"}),  # Case 7: 'characterization' missing 'weight'
        ({"type": "characterization", "weight": 0.5}),  # Case 8: 'characterization' missing 'unit'
        ({"type": "characterization"}), # Case 9: 'characterization' missing 'weight' and 'unit'
    ]
)
def test_edge_attributes_invalid_raises_value_error(attributes_dict):
    """
    Test that _validate_edge_attributes raises ValueError for various invalid attribute dictionaries.
    """
    validator = GreenMultiDiGraph() # Create an instance to call the method
    with pytest.raises(ValueError):
        validator._validate_edge_attributes(attributes_dict)