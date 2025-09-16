from collections.abc import Iterable
from typing import Any, Optional
import networkx as nx
import numpy as np
from greengraph.utility.log import logtimer
from greengraph.core import GreenMultiDiGraph


def _get_nodes_from_node_container(
    node_container: Any | tuple[Any, dict]
) -> list:
    r"""
    Given a container of nodes, returns a list of nodes (without the attributes).

    In NetworkX, a container of nodes can be:

    1. A list of nodes (list, dict, set, etc.)
    2. A container of (node, attribute dict) tuples

    Warnings
    --------

    
    See Also
    --------
    [networkx.Graph.add_nodes_from](https://networkx.org/documentation/stable/reference/classes/generated/networkx.Graph.add_nodes_from.html)

    Example
    -------
    ```python
    >>> from greengraph.utility.graph import get_nodes_from_node_container
    >>> node_container = [
        ('N1', {'type': 'production', 'unit': 'kg', 'production': 1.0}),
        ('N2', {'type': 'production', 'unit': 'kg', 'production': 1.0})
    ]
    >>> get_nodes_from_node_container(node_container)
    ['N1', 'N2']
    ```

    Parameters
    ----------
    node_container : list | np.ndarray
        A container of nodes, which can be a list, dict, set, etc.
        Each element can be a node or a tuple of (node, attribute dict).
    
    Returns
    -------
    list
        A list of nodes without the attributes.
    """
    list_nodes = []
    for item in node_container:
        if isinstance(item, Iterable) and isinstance(item[-1], dict):
            list_nodes.append(item[0])
        else:
            list_nodes.append(item)
    return list_nodes


def graph_from_matrix(
    matrix: np.ndarray,
    validate: bool,
    nodes_axis_0: Iterable[Any | tuple[Any, dict[str, Any]]],
    nodes_axis_1: Iterable[Any | tuple[Any, dict[str, Any]]],
    common_attributes_nodes_axis_0: Optional[dict] | None,
    common_attributes_nodes_axis_1: Optional[dict] | None,
    name_amount_attribute: str,
    common_attributes_edges: dict,
    create_using: type,
) -> nx.MultiDiGraph:
    """
    Given an array and one-two lists of nodes and additional attributes, creates a graph.
    
    This function can create a graph from either an adjacency matrix or a biadjacency matrix.
    
    Example
    -------
    ```python
    >>> from greengraph.utility.graph import from_biadjacency_matrix
    >>> from_biadjacency_matrix(
    ...     matrix=B,
    ...     nodes_axis_0=[1, 2, 3],
    ...     nodes_axis_1=[A, B],
    ...     common_attributes_nodes_axis_0={"type": "process", 'unit': "kg"},
    ...     common_attributes_nodes_axis_1={"type": "sector", 'unit': "USD"},
    ...     create_using=nx.MultiDiGraph,
    ... )
    ```

    See Also
    --------
    - [`networkx.algorithms.bipartite.from_biadjacency_matrix`](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.bipartite.matrix.from_biadjacency_matrix.html)

    Warnings
    --------
    When using `create_using=gg.GreenMultiDiGraph`,
    ensure that you pass the required node and/or edge attributes.

    Parameters
    ----------
    matrix : np.ndarray
        A 2D numpy array representing the biadjacency matrix.
    nodes_axis_0 : list | np.ndarray
        A list or array of nodes corresponding to the rows of the matrix.
    nodes_axis_1 : list | np.ndarray
        A list or array of nodes corresponding to the columns of the matrix.
    common_attributes_nodes_axis_0 : dict
        A dictionary of attributes to be applied to all nodes in axis 0.
    common_attributes_nodes_axis_1 : dict
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

    if nodes_axis_0 is None:
        raise ValueError("Some nodes must be provided.")
    else:
        with logtimer('creating graph from bi-adjacency matrix.'):
            G.add_nodes_from(nodes_axis_0, **(common_attributes_nodes_axis_0 or {}), validate=validate)
            if nodes_axis_1 is not None:
                G.add_nodes_from(nodes_axis_1, **(common_attributes_nodes_axis_1 or {}), validate=validate)

    with logtimer('adding edges to the graph from adjacency matrix.'):
        row_indices_nonzero, col_indices_nonzero = np.nonzero(matrix)
        row_labels_nonzero = np.array(_get_nodes_from_node_container(nodes_axis_0))[row_indices_nonzero]
        if nodes_axis_1 is None:
            col_labels_nonzero = row_labels_nonzero
        else:
            col_labels_nonzero = np.array(_get_nodes_from_node_container(nodes_axis_1))[col_indices_nonzero]
        values = matrix[row_indices_nonzero, col_indices_nonzero]
        
        generator_edges = (
            (
                str(row),
                str(col),
                {
                    name_amount_attribute: float(val),
                    **(common_attributes_edges or {})
                }
            )
            for row, col, val in zip(row_labels_nonzero, col_labels_nonzero, values)
        )
        if create_using == GreenMultiDiGraph:
            G.add_edges_from(generator_edges, validate=validate)
        else:
            G.add_edges_from(generator_edges)

    return G