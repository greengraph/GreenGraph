# %%
import pytest
import numpy as np
from greengraph.core import GreenMultiDiGraph
from greengraph.utility.graph import (
    get_nodes_from_node_container,
    graph_from_matrix,
)


@pytest.mark.parametrize(
    "container_input, expected_output_nodes",
    [
        # case 0: List of tuples with attributes
        (
            [
                ('N1', {'attr': 1, 'color': 'red'}),
                (2, {'attr': 'value'}),
                (('tuple_node',), {'complex': True})
            ],
            ['N1', 2, ('tuple_node',)]
        ),
        # case 1: List of nodes without attributes
        (
            ['N1', 'N2', 'N3'],
            ['N1', 'N2', 'N3']
        ),
        # case 2: List of nodes with attributes
        (
            (('T1', {'a': 1}), ('T2', {'b': 2})),
            ['T1', 'T2']
        ),
        # case 3: List of nodes, only some with attributes
        ( 
            ['N1', ('N2', {'attr': 2}), 3, None, (4.0, {'f': 'val'})],
            ['N1', 'N2', 3, None, 4.0]
        ),
        # case 4: list of nodes, only some with attributes
        (
            ('T_N1', ('T_N2', {'attr': 't_val'}), 100),
            ['T_N1', 'T_N2', 100]
        )
    ]
)
def test_containers_of_node_attr_tuples(container_input, expected_output_nodes):
    """
    For different containers of nodes, the function should return a list of nodes without the attributes.
    """
    assert get_nodes_from_node_container(container_input) == expected_output_nodes


def test_graph_from_matrix_adjacency():
    """
    For a simple adjacency matrix, the function should create a graph with the correct nodes and edges.
    """
    data = np.array([
        [0, 1, 0],
        [1, 0, 5],
        [0, 0, 0]
    ])

    nodelist = (
        ('N1', {'type': 'production', 'unit': 'kg', 'production': 1.0}),
        ('N2', {'type': 'production', 'unit': 'kg', 'production': 1.0}),
        ('N3', {'type': 'production', 'unit': 'kg', 'production': 1.0})
    )

    G = graph_from_matrix(
        matrix=data,
        nodes_axis_0=nodelist,
        nodes_axis_1=None,
        common_attributes_nodes_axis_0=None,
        common_attributes_nodes_axis_1=None,
        name_amount_attribute='amount',
        common_attributes_edges={'type': 'flow', 'unit': 'kg'},
        create_using=GreenMultiDiGraph,
    )

    assert list(G.nodes(data=True)) == [
        ('N1', {'type': 'production', 'unit': 'kg', 'production': 1.0}),
        ('N2', {'type': 'production', 'unit': 'kg', 'production': 1.0}),
        ('N3', {'type': 'production', 'unit': 'kg', 'production': 1.0})
    ]

    assert list(G.edges(data=True)) == [
        ('N1', 'N2', {'amount': 1.0, 'type': 'flow', 'unit': 'kg'}),
        ('N2', 'N1', {'amount': 1.0, 'type': 'flow', 'unit': 'kg'}),
        ('N2', 'N3', {'amount': 5.0, 'type': 'flow', 'unit': 'kg'})
    ]


def test_graph_from_matrix_biadjacency():
    """
    For a bi-adjacency matrix, the function should create a graph with the correct nodes and edges.
    """
    data = np.array([
        [0, 1, 0],
        [1, 0, 5],
    ])

    nodelist_axis_0 = (
        ('N1', {'type': 'production', 'unit': 'kg', 'production': 1.0}),
        ('N2', {'type': 'production', 'unit': 'kg', 'production': 1.0}),
    )
    nodelist_axis_1 = (
        ('A', {'type': 'extension', 'unit': 'kg', 'production': 1.0}),
        ('B', {'type': 'extension', 'unit': 'kg', 'production': 1.0}),
        ('C', {'type': 'extension', 'unit': 'kg', 'production': 1.0})
    )

    G = graph_from_matrix(
        matrix=data,
        nodes_axis_0=nodelist_axis_0,
        nodes_axis_1=nodelist_axis_1,
        common_attributes_nodes_axis_0=None,
        common_attributes_nodes_axis_1=None,
        name_amount_attribute='amount',
        common_attributes_edges={'type': 'flow', 'unit': 'kg'},
        create_using=GreenMultiDiGraph,
    )

    assert list(G.nodes(data=True)) == [
        ('N1', {'type': 'production', 'unit': 'kg', 'production': 1.0}),
        ('N2', {'type': 'production', 'unit': 'kg', 'production': 1.0}),
        ('A', {'type': 'extension', 'unit': 'kg', 'production': 1.0}),
        ('B', {'type': 'extension', 'unit': 'kg', 'production': 1.0}),
        ('C', {'type': 'extension', 'unit': 'kg', 'production': 1.0})
    ]

    assert list(G.edges(data=True)) == [
        ('N1', 'B', {'amount': 1.0, 'type': 'flow', 'unit': 'kg'}),
        ('N2', 'A', {'amount': 1.0, 'type': 'flow', 'unit': 'kg'}),
        ('N2', 'C', {'amount': 5.0, 'type': 'flow', 'unit': 'kg'})
    ]