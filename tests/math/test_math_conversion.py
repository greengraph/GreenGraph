import pytest

from greengraph.math.conversion import (
    _generate_matrices_from_graph,
)
from tests.fixtures.graphs import example_graph_system_from_input_output_matrices

from tests.importers.databases.test_inputoutput import test_useeio_matrices_to_graph


def test_generate_matrices_from_graph_A_and_B(example_graph_system_from_input_output_matrices):
    """
    Test the _generate_matrices_from_graph function with a simple example graph.
    """
    generated_matrices = _generate_matrices_from_graph(
        example_graph_system_from_input_output_matrices['graph'],
        matrixformat='dense',
        generate_A=True,
        generate_B=True,
        generate_Q=False,
        A_sort_attributes=['index'],
        B_sort_attributes=['index'],
    )

    assert generated_matrices['A'] == example_graph_system_from_input_output_matrices['A']
    assert generated_matrices['B'] == example_graph_system_from_input_output_matrices['B']
    assert generated_matrices['Q'] is None


def test_generate_matrices_from_graph_A_and_B_and_Q(example_graph_system_from_input_output_matrices):
    """
    Test the _generate_matrices_from_graph function with a simple example graph.
    """
    generated_matrices = _generate_matrices_from_graph(
        example_graph_system_from_input_output_matrices['graph'],
        matrixformat='dense',
        generate_A=True,
        generate_B=True,
        generate_Q=True,
        A_sort_attributes=['index'],
        B_sort_attributes=['index'],
        Q_sort_attributes=['index'],
    )

    assert generated_matrices['A'] == example_graph_system_from_input_output_matrices['A']
    assert generated_matrices['B'] == example_graph_system_from_input_output_matrices['B']
    assert generated_matrices['Q'] == example_graph_system_from_input_output_matrices['C']