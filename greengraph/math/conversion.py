# %%
from greengraph.utility.logging import logtimer
import networkx as nx
import numpy as np
import xarray as xr
from typing import Optional, Union, Type


def generate_matrix_from_graph(
    G: nx.MultiDiGraph,
    matrixformat: str,
    name_matrix: str,
    adjacency_amount_attribute: str,
    adjacency_dtype: Optional[Union[Type[np.generic], np.dtype, str]],
    name_coordinate_rows: str,
    name_coordinate_cols: str,
    list_nodes_rows: list[str],
    list_nodes_cols: list[str],
    sort_attributes_nodes_rows: Optional[list[str]] = None,
    sort_attributes_nodes_cols: Optional[list[str]] = None,
) -> xr.DataArray:
    r"""
    Given a graph, generate an xarray.DataArray containing a
    (bi-adjacency-)matrix from the nodes and their attributes.

    Notes
    -----
    The `lambdafunction_sort_keys` lambda functions are used to sort the nodes based on the specified attributes.

    For example, if graph `G` has nodes with attributes:

    ```python
    >>> [(node, attr) for node, attr in G.nodes(data=True)]
    [
        ('node1', {'type': 'production', 'name': 'process 22', 'production': 1.0}),
        ('node2', {'type': 'production', 'name': 'process 11', 'production': 2.0}),
    ]
    ```

    For sort keys `['name', 'production']` the lambda function will return for `node1`:
    
    ```python
    ('process 22', 1.0)
    ```

    and for `node2`:

    ```python
    ('process 11', 2.0)
    ```

    For sort keys `None`, the lambda function will return the node itself, e.g. `node1` and `node2`.

    See Also
    --------
    [`networkx.algorithms.bipartite.matrix.biadjacency_matrix`](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.bipartite.matrix.biadjacency_matrix.html)

    Parameters
    ----------
    G : nx.MultiDiGraph
        The graph from which the matrix is generated.
    matrixformat : str
        The format of the matrix, e.g., 'dense', 'sparse', etc.
        Can be any format accepted by the format parameter of [`networkx.algorithms.bipartite.matrix.biadjacency_matrix`](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.bipartite.matrix.biadjacency_matrix.html).
    name_matrix : str
        The name of the matrix, used for logging.  
        eg. `production`, `extension`, `indicator`, etc.
    adjacency_amount_attribute : str
        The attribute of the edges that contains the amount of the adjacency.  
        eg. `amount`, `weight`, etc.
    adjacency_dtype : Optional[Union[Type[np.generic], np.dtype, str]]
        The data type of the adjacency matrix. If None, the default data type is used.  
        Can be any [valid numpy data type](https://numpy.org/doc/stable/user/basics.types.html) or a string representation of it.  
        eg. `float`, `int`, etc.
    name_coordinate_rows : str
        The name of the coordinate for the rows of the xarray.DataArray.
    name_coordinate_cols : str
        The name of the coordinate for the columns of the xarray.DataArray.
    list_nodes_rows : list[str]
        A list of nodes for the rows of the matrix.
    list_nodes_cols : list[str]
        A list of nodes for the columns of the matrix.
    sort_attributes_nodes_rows : Optional[list[str]]
        A list of attributes to sort the nodes in the rows.
        eg. `['name', 'production']`, etc.
    sort_attributes_nodes_cols : Optional[list[str]]
        A list of attributes to sort the nodes in the columns.
        eg. `['name', 'production']`, etc.
    
    Returns
    -------
    xr.DataArray
        An xarray.DataArray containing the bi-adjacency matrix with the specified coordinates and attributes.

    Example
    -------
    ```python
    >>> generate_matrix_from_graph(
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
    ```
    """
    if sort_attributes_nodes_rows is None:
        lambdafunction_sort_keys_rows = lambda node: node
    else:
        lambdafunction_sort_keys_rows = lambda node: tuple(G.nodes[node].get(key, None) for key in sort_attributes_nodes_rows)
    list_sorted_nodes_rows = sorted(
        list_nodes_rows,
        key=lambdafunction_sort_keys_rows
    )
    if sort_attributes_nodes_cols is None:
        lambdafunction_sort_keys_cols = lambda node: node
    else:
        lambdafunction_sort_keys_cols = lambda node: tuple(G.nodes[node].get(key, None) for key in sort_attributes_nodes_cols)
    list_sorted_nodes_cols = sorted(
        list_nodes_cols,
        key=lambdafunction_sort_keys_cols
    )
    with logtimer(f"Generating {name_matrix} matrix from graph."):
        A = nx.algorithms.bipartite.biadjacency_matrix(
            G,
            row_order=list_sorted_nodes_rows,
            column_order=list_sorted_nodes_cols,
            dtype=adjacency_dtype,
            weight=adjacency_amount_attribute,
            format=matrixformat
        )
        A = xr.DataArray(
            A,
            dims=(name_coordinate_rows, name_coordinate_cols),
            coords={
                name_coordinate_rows: list_sorted_nodes_rows,
                name_coordinate_cols: list_sorted_nodes_cols,
            },
        )
    return A