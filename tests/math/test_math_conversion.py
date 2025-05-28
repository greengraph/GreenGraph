# %%
import pytest
from numpy.testing import assert_array_almost_equal

from greengraph.math.conversion import (
    generate_matrix_from_graph,
)
from tests.fixtures.graphs import example_graph_system_from_input_output_matrices


def test_generate_matrices_from_graph_A_and_B(example_graph_system_from_input_output_matrices):
    """
    Test the _generate_matrices_from_graph function with a simple example graph.
    """
    G=example_graph_system_from_input_output_matrices['graph']
    generated_matrix_A = generate_matrix_from_graph(
        G=G,
        matrixformat='dense',
        name_matrix='production',
        adjacency_amount_attribute='amount',
        adjacency_dtype=float,
        name_coordinate_rows='production nodes (rows)',
        name_coordinate_cols='production nodes (cols)',
        list_nodes_rows=[node for node, attr in G.nodes(data=True) if attr['type'] == 'production'],
        list_nodes_cols=[node for node, attr in G.nodes(data=True) if attr['type'] == 'production'],
        sort_attributes_nodes_rows=['index'],
        sort_attributes_nodes_cols=['index']
    )
    assert_array_almost_equal(
        example_graph_system_from_input_output_matrices['A'],
        generated_matrix_A.values
    )
    assert "production nodes (rows)" in generated_matrix_A.coords
    assert "production nodes (cols)" in generated_matrix_A.coords
    assert generated_matrix_A.coords["production nodes (rows)"].size == 3
    assert generated_matrix_A.coords["production nodes (cols)"].size == 3

    generated_matrix_B = generate_matrix_from_graph(
        G=G,
        matrixformat='dense',
        name_matrix='extension',
        adjacency_amount_attribute='amount',
        adjacency_dtype=float,
        name_coordinate_rows='extension nodes (rows)',
        name_coordinate_cols='production nodes (cols)',
        list_nodes_rows=[node for node, attr in G.nodes(data=True) if attr['type'] == 'extension'],
        list_nodes_cols=[node for node, attr in G.nodes(data=True) if attr['type'] == 'production'],
        sort_attributes_nodes_rows=['index'],
        sort_attributes_nodes_cols=['index']
    )
    assert_array_almost_equal(
        example_graph_system_from_input_output_matrices['B'],
        generated_matrix_B.values
    )
    assert "extension nodes (rows)" in generated_matrix_B.coords
    assert "production nodes (cols)" in generated_matrix_B.coords
    assert generated_matrix_B.coords["extension nodes (rows)"].size == 2
    assert generated_matrix_B.coords["production nodes (cols)"].size == 3

    generated_matrix_C = generate_matrix_from_graph(
        G=G,
        matrixformat='dense',
        name_matrix='indicator',
        adjacency_amount_attribute='weight',
        adjacency_dtype=float,
        name_coordinate_rows='indicator nodes (rows)',
        name_coordinate_cols='extension nodes (cols)',
        list_nodes_rows=[node for node, attr in G.nodes(data=True) if attr['type'] == 'indicator'],
        list_nodes_cols=[node for node, attr in G.nodes(data=True) if attr['type'] == 'extension'],
        sort_attributes_nodes_rows=['index'],
        sort_attributes_nodes_cols=['index']
    )
    assert_array_almost_equal(
        example_graph_system_from_input_output_matrices['C'],
        generated_matrix_C.values
    )
    assert "indicator nodes (rows)" in generated_matrix_C.coords
    assert "extension nodes (cols)" in generated_matrix_C.coords
    assert generated_matrix_C.coords["indicator nodes (rows)"].size == 1
    assert generated_matrix_C.coords["extension nodes (cols)"].size == 2