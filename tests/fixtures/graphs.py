# %%
import pytest
import numpy as np

from greengraph.importers.databases.generic import graph_system_from_input_output_matrices

@pytest.fixture(scope='function')
def example_graph_system_from_input_output_matrices():
    """
    Example of how to create a graph system from input-output matrices.
    This is a simple example with dummy data.
    """
    A = np.array(
        [
            [1, 2, 3], 
            [4, 1, 6],
            [7, 8, 1]
        ]
    )

    B = np.array(
        [
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6],
        ]
    )

    C = np.array(
        [
            [0.01, 0.02],
        ]
    )

    A_metadata = [
        {'name': 'Production 1', 'index': 0, 'unit': 'kg', 'production': 1.0},
        {'name': 'Production 2', 'index': 1, 'unit': 'kg', 'production': 1.0},
        {'name': 'Production 3', 'index': 2, 'unit': 'kg', 'production': 1.0}
    ]

    B_metadata = [
        {'name': 'Extension 1', 'index': 0, 'unit': 'kg', 'production': 1.0},
        {'name': 'Extension 2', 'index': 1, 'unit': 'kg', 'production': 1.0}
    ]

    C_metadata = [
        {'name': 'Indicator 1', 'index': 0, 'unit': 'degC',}
    ]

    G = graph_system_from_input_output_matrices(
        name_system='test_graph',
        assign_new_uuids=True,
        str_extension_nodes_uuid=None,
        str_production_nodes_uuid=None,
        str_indicator_nodes_uuid=None,
        matrix_convention='I-A',
        array_production=A,
        array_extension=B,
        array_indicator=C,
        list_dicts_production_node_metadata=A_metadata,
        list_dicts_extension_node_metadata=B_metadata,
        list_dicts_indicator_node_metadata=C_metadata,
    )

    return {
        'graph': G,
        'A': A,
        'B': B,
        'C': C,
        'A_metadata': A_metadata,
        'B_metadata': B_metadata,
        'C_metadata': C_metadata
    }

