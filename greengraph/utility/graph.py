import networkx as nx
import numpy as np

def from_biadjacency_matrix(
    matrix: np.ndarray,
    nodes_axis_0: list,
    nodes_axis_1: list,
    attributes_nodes_axis_0: dict,
    attributes_nodes_axis_1: dict,
    create_using: type = nx.MultiDiGraph,
) -> nx.MultiDiGraph:
    """

    See Also
    --------
    - [Add `nodelist` to `from_biadjacency_matrix`](https://github.com/networkx/networkx/discussions/7960)

    Warnings
    --------
    To be replaced with updated NetworkX function in future versions.
    """
    G = nx.empty_graph(n=0, create_using=create_using)
    G.add_nodes_from(nodes_axis_0, attr=attributes_nodes_axis_0)
    G.add_nodes_from(nodes_axis_1, attr=attributes_nodes_axis_1)

    row_indices, col_indices = np.nonzero(matrix)
    row_labels_nonzero = nodes_axis_0[row_indices]
    col_labels_nonzero = nodes_axis_1[col_indices]
    values = matrix[row_indices, col_indices]
    edges = [(row, col, {'flow': val}) for row, col, val in zip(row_labels_nonzero, col_labels_nonzero, values)]

    G.add_edges_from(edges)

    return G