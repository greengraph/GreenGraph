import networkx as nx
import numpy as np

def from_biadjacency_matrix(
    matrix: np.ndarray,
    nodes_axis_0: list | np.ndarray,
    nodes_axis_1: list | np.ndarray,
    attributes_nodes_axis_0: dict,
    attributes_nodes_axis_1: dict,
    create_using: type = nx.MultiDiGraph,
) -> nx.MultiDiGraph:
    """
    Given a biadjacency matrix, two lists of nodes
    and two dictionaries of metadata attributes to be applied to all nodes, creates a bipartite graph.

    Example
    -------
    ```python
    >>> from greengraph.utility.graph import from_biadjacency_matrix
    >>> from_biadjacency_matrix(
    ...     matrix=B,
    ...     nodes_axis_0=[1, 2, 3],
    ...     nodes_axis_1=[A, B, C],
    ...     attributes_nodes_axis_0={"type": "process"},
    ...     attributes_nodes_axis_1={"type": "sector"},
    ...     create_using=nx.MultiDiGraph,
    ... )
    ```

    See Also
    --------
    - [`networkx.algorithms.bipartite.from_biadjacency_matrix`](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.bipartite.matrix.from_biadjacency_matrix.html)
    - ["Add `nodelist` to `from_biadjacency_matrix`"](https://github.com/networkx/networkx/discussions/7960) discussion on GitHub

    Warnings
    --------
    To be replaced with updated NetworkX function in future versions.

    Parameters
    ----------
    matrix : np.ndarray
        A 2D numpy array representing the biadjacency matrix.
    nodes_axis_0 : list | np.ndarray
        A list or array of nodes corresponding to the rows of the matrix.
    nodes_axis_1 : list | np.ndarray
        A list or array of nodes corresponding to the columns of the matrix.
    attributes_nodes_axis_0 : dict
        A dictionary of attributes to be applied to all nodes in axis 0.
    attributes_nodes_axis_1 : dict
        A dictionary of attributes to be applied to all nodes in axis 1.
    create_using : type, optional
        The type of graph to create. Default is `nx.MultiDiGraph`.
        Other options include [`nx.Graph`, `nx.DiGraph`, etc.](https://networkx.org/documentation/stable/reference/classes/index.html)
    
    Returns
    -------
    nx.MultiDiGraph
        A bipartite graph created from the biadjacency matrix.
    """
    G = nx.empty_graph(n=0, create_using=create_using)
    G.add_nodes_from(nodes_axis_0, attr=attributes_nodes_axis_0)
    G.add_nodes_from(nodes_axis_1, attr=attributes_nodes_axis_1)

    row_indices_nonzero, col_indices_nonzero = np.nonzero(matrix)
    row_labels_nonzero = np.array(nodes_axis_0)[row_indices_nonzero]
    col_labels_nonzero = np.array(nodes_axis_1)[col_indices_nonzero]
    
    values = matrix[row_indices_nonzero, col_indices_nonzero]
    edges = [(row, col, {'flow': val}) for row, col, val in zip(row_labels_nonzero, col_labels_nonzero, values)]

    G.add_edges_from(edges)

    return G