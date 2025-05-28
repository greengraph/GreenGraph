r"""
This module contains functions to turn properly formatted 
arrays, dataframe, metadata lists, etc. into a greengraph graph.
"""

import networkx as nx
import xarray as xr
import numpy as np
import logging
import uuid
from greengraph.core import GreenMultiDiGraph
from greengraph.utility.logging import logtimer
from greengraph.utility.graph import graph_from_matrix


def graph_system_from_input_output_matrices(
    name_system: str,
    assign_new_uuids: bool,
    str_production_nodes_uuid: str,
    str_extension_nodes_uuid: str,
    str_indicator_nodes_uuid: str | None,
    matrix_convention: str,
    array_production: np.ndarray,
    array_extension: np.ndarray,
    array_indicator: np.ndarray | None,
    list_dicts_production_node_metadata: list[dict],
    list_dicts_extension_node_metadata: list[dict],
    list_dicts_indicator_node_metadata: list[dict] | None,
) -> GreenMultiDiGraph:
    r"""
    Create a MultiDiGraph from technosphere and biosphere matrices.

    
    $$
    \mathbf{A} = \begin{bmatrix}
        a_{11} & a_{12} & a_{13} \\
        a_{21} & a_{22} & a_{23} \\
        a_{31} & a_{32} & a_{33}
    \end{bmatrix}
    $$

    $$
    \mathbf{B} = \begin{bmatrix}
        b_{11} & b_{12} & b_{13} \\
        b_{21} & b_{22} & b_{23} \\
    \end{bmatrix}
    $$

    and metadata lists:

    | index | name | unit | production |
    |-------|------|------|-----------|
    | 0     | A    | kg   | 1         |
    | 1     | B    | kg   | 1         |
    | 2     | C    | kg   | 1         |

    Notes
    -----
    This function is best suited for importing input-output data.

      A B C
    A 0 0 0
    B 1 0 0
    C 2 3 0

    Example
    -------
    Note that this example uses the same example system as
    [`greengraph.importers.databases.generic.graph_system_from_node_and_edge_lists`][].
    ```python
    list_dicts_production_nodes_metadata = [
        {'name': 'A', 'unit': 'kg'},
        {'name': 'B', 'unit': 'kg'},
        {'name': 'C', 'unit': 'kg'}
    ]
    list_dicts_extension_nodes_metadata = [
        {'name': 'alpha', 'unit': 'kg(CO2)'},
    ]
    array_production = np.array([
        [0, 0, 0],
        [-1, 0, 0],
        [-2, -3, 0]
    ])
    array_extension = np.array([
        [4, 3, 2]
    ])
    G = graph_system_from_input_output_matrices(
        name_system='example_system',
        normalized_production=True,
        array_production=array_production,
        array_extension=array_extension,
        list_dicts_production_node_metadata=list_dicts_production_nodes_metadata,
        list_dicts_extension_node_metadata=list_dicts_extension_nodes_metadata
    )
    ```
    
    Warnings
    --------
    This function expects that:
    
    1. Unless an attribute `production` is specified for a node, production is set to 1.
    2. The production matrix is square.
    3. The order of rows/columns in the production matrix
    corresponds to the order of nodes in the production node metadata list.
    4. The order of rows in the extension matrix corresponds to the order of nodes in the extension node metadata list.
    5. The order of colums in the extension matrix corresponds to the order of nodes in the production node metadata list.

    See Also
    --------
    [I-A]...

    Parameters
    ----------
    name_system : str
        Name of the system.
    matrix_convention : str
        The convention used for the production matrix.  
        Must be either 'I-A' (technology matrix convention) or 'A' (process-based inventory convention).
    array_production : np.ndarray
        Technosphere matrix.
    array_extension : np.ndarray
        Biosphere matrix.
    list_dicts_production_node_metadata : list[dict]
        List of metadata dictionaries for production nodes.
        Must contain at least the keys `['name', 'unit']`.
    list_dicts_extension_node_metadata : list[dict]
        List of metadata dictionaries for extension nodes.
        Must contain at least the keys `['name', 'unit']`.

    Returns
    -------
    nx.MultiDiGraph
        The created MultiDiGraph.

    Raises
    ------
    ValueError
        - If the input data is not in the correct format.
        - If the number of nodes in the production graph does not match the number of metadata dictionaries.
        - If the number of nodes in the extension graph does not match the number of metadata dictionaries.
        - If the number of nodes in the combined graph does not match the number of metadata dictionaries.

    """
    if (
        array_production is None or
        list_dicts_production_node_metadata is None or
        array_extension is None or
        list_dicts_extension_node_metadata is None
    ):
        raise ValueError("At least a production matrix+metadata and extension matrix+metadata must be provided.")
    if array_indicator is None and list_dicts_indicator_node_metadata is not None: # '== None' would perform NumPy element-wise check
        raise ValueError("If an indicator matrix is provided, metadata must also also be provided.")
    if array_indicator is not None and list_dicts_indicator_node_metadata is None:
        raise ValueError("If an indicator metadata list is provided, a matrix must also also be provided.")

    if array_production.shape[0] != array_production.shape[1]:
        raise ValueError("Production matrix must be square.")
    if array_extension.shape[1] != array_production.shape[0]:
        raise ValueError("Dimension mismatch between production and extension matrices.")
    if array_indicator is not None:
        if array_indicator.shape[1] != array_extension.shape[0]:
            raise ValueError("Dimension mismatch between indicator and extension matrices.")
    
    list_arrays_for_check = [
        (array_production, list_dicts_production_node_metadata, 'production'),
        (array_extension, list_dicts_extension_node_metadata, 'extension')
    ]

    if array_indicator is not None:
        list_arrays_for_check.append((array_indicator, list_dicts_indicator_node_metadata, 'indicator'))
    
    for matrix, metadata, name in list_arrays_for_check:
        if not np.issubdtype(matrix.dtype, np.number):
            raise TypeError(f"All entries in the {name} matrix must be numeric.")
        if matrix.shape[0] != len(metadata):
            raise ValueError(f"Dimensions of the {name} matrix ({matrix.shape[0]}) does not match metadata dictionary length ({len(metadata)}).")
        
    for node_metadata in list_dicts_production_node_metadata:
        for key in ['name', 'unit']:
            if key not in node_metadata:
                raise ValueError(f"Metadata dictionary of every node must contain at least a 'name and 'unit' key.")

    if not matrix_convention in ['I-A', 'A']:
        raise ValueError("matrix_convention must be 'I-A' or 'A'.")
    if matrix_convention == 'A':
        np.fill_diagonal(array_production, 0)
        array_production = np.abs(array_production)
    elif matrix_convention == 'I-A':
        if not (array_production >= 0).all():
            raise ValueError("All entries in the technosphere matrix must be non-negative.")
    
    # Production Metadata Parsing
    for idx, dict_node_metadata in enumerate(list_dicts_production_node_metadata):
        dict_node_metadata.update({
            'uuid': str(uuid.uuid4()) if assign_new_uuids else dict_node_metadata[str_production_nodes_uuid],
            'index': idx,
            'type': 'production',
            'system': name_system,
            'production': 1.0 if matrix_convention == 'I-A' else array_production[idx, idx]
        })
    list_tuples_production_node_metadata = [(d['uuid'], d) for d in list_dicts_production_node_metadata]

    # Extension Metadata Parsing
    for idx, dict_node_metadata in enumerate(list_dicts_extension_node_metadata):
        dict_node_metadata.update({
            'uuid': str(uuid.uuid4()) if assign_new_uuids else dict_node_metadata[str_extension_nodes_uuid],
            'index': idx,
            'type': 'extension',
            'system': name_system,
            'production': 1.0
        })
    list_tuples_extension_node_metadata = [(d['uuid'], d) for d in list_dicts_extension_node_metadata]

    # Indicator Metadata Parsing
    if array_indicator is not None and list_dicts_indicator_node_metadata is not None:
        for idx, dict_node_metadata in enumerate(list_dicts_indicator_node_metadata):
            dict_node_metadata.update({
                'uuid': str(uuid.uuid4()) if assign_new_uuids else dict_node_metadata[str_indicator_nodes_uuid],
                'index': idx,
                'type': 'indicator',
                'system': name_system
            })
        list_tuples_indicator_node_metadata = [(d['uuid'], d) for d in list_dicts_indicator_node_metadata]
    else:
        list_tuples_indicator_node_metadata = None
    
    with logtimer("creating MultiDiGraph from technosphere matrix."):
        logging.info(
            f"# of nodes: {len(array_production)}, # of edges: {(np.count_nonzero(~np.isnan(array_production) & (array_production != 0))):,}"
        )
        A = graph_from_matrix(
            matrix=array_production,
            nodes_axis_0=list_tuples_production_node_metadata,
            nodes_axis_1=None,
            common_attributes_nodes_axis_0=None,
            common_attributes_nodes_axis_1=None,
            name_amount_attribute='amount',
            common_attributes_edges={'type': 'flow'},
            create_using=GreenMultiDiGraph,
        )

    with logtimer("creating MultiDiGraph from biosphere matrix."):
        logging.info(
            f"# of nodes: {len(array_extension)}, # of edges: {(np.count_nonzero(~np.isnan(array_extension) & (array_extension != 0))):,}"
        )
        B = graph_from_matrix(
            matrix=array_extension,
            nodes_axis_0=list_tuples_extension_node_metadata,
            nodes_axis_1=list_tuples_production_node_metadata,
            common_attributes_nodes_axis_0=None,
            common_attributes_nodes_axis_1=None,
            name_amount_attribute='amount',
            common_attributes_edges={'type': 'flow'},
            create_using=GreenMultiDiGraph,
        )

    if list_tuples_indicator_node_metadata is not None:
        with logtimer("creating MultiDiGraph from indicator matrix."):
            logging.info(
                f"# of nodes: {len(array_indicator)}, # of edges: {(np.count_nonzero(~np.isnan(array_indicator) & (array_indicator != 0))):,}"
            )
            Q = graph_from_matrix(
                matrix=array_indicator,
                nodes_axis_0=list_tuples_indicator_node_metadata,
                nodes_axis_1=list_tuples_extension_node_metadata,
                common_attributes_nodes_axis_0=None,
                common_attributes_nodes_axis_1=None,
                name_amount_attribute='weight',
                common_attributes_edges={'type': 'characterization'},
                create_using=GreenMultiDiGraph,
            )

    with logtimer("merging production and extension graphs. Whoop-whoop!"):
        if array_indicator is None:
            BcomposeA = nx.compose(B, A)
            del A
            del B
            return BcomposeA
        elif array_indicator is not None:
            BcomposeA = nx.compose(B, A)
            del A
            del B
            QcomposeBA = nx.compose(Q, BcomposeA)
            del Q
            del BcomposeA
            return QcomposeBA
