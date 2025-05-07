r"""
This module contains functions to turn properly prepared dataframes/etc.
into a greengraph graph class.
"""

# %%
import networkx as nx
import xarray as xr
import numpy as np
import logging
import uuid
from greengraph.utility.logging import logtimer
import uuid

from greengraph.utility.graph import from_biadjacency_matrix


def graph_system_from_input_output_matrices(
    name_system: str,
    assign_new_uuids: bool,
    str_production_nodes_uuid: str,
    str_extension_nodes_uuid: str,
    str_indicator_nodes_uuid: str,
    matrix_convention: str,
    array_production: np.ndarray,
    array_extension: np.ndarray,
    array_indicator: np.ndarray,
    list_dicts_production_node_metadata: list[dict],
    list_dicts_extension_node_metadata: list[dict],
    list_dicts_indicator_node_metadata: list[dict],
) -> nx.MultiDiGraph:
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
        A = np.abs(A)
    elif matrix_convention == 'I-A':
        if not (array_production >= 0).all():
            raise ValueError("All entries in the technosphere matrix must be non-negative.")

    # Production Metadata Parsing
    for idx, dict_node_metadata in enumerate(list_dicts_production_node_metadata):
        if assign_new_uuids:
            dict_node_metadata['uuid'] = str(uuid.uuid4())
        else:
            dict_node_metadata['uuid'] = dict_node_metadata[str_production_nodes_uuid]
        dict_node_metadata['index'] = idx
        dict_node_metadata['type'] = 'production'
        dict_node_metadata['system'] = name_system
        if matrix_convention == 'I-A':
            dict_node_metadata['production'] = 1.0
        elif matrix_convention == 'A':
            dict_node_metadata['production'] = array_production[idx, idx]

    # Extension Metadata Parsing
    for idx, dict_node_metadata in enumerate(list_dicts_extension_node_metadata):
        if assign_new_uuids:
            dict_node_metadata['uuid'] = str(uuid.uuid4())
        else:
            dict_node_metadata['uuid'] = dict_node_metadata[str_extension_nodes_uuid]
        dict_node_metadata['index'] = idx       
        dict_node_metadata['type'] = 'extension'
        dict_node_metadata['system'] = name_system

    # Indicator Metadata Parsing
    if array_indicator is not None:
        for idx, dict_node_metadata in enumerate(list_dicts_indicator_node_metadata):
            if assign_new_uuids:
                dict_node_metadata['uuid'] = str(uuid.uuid4())
            else:
                dict_node_metadata['uuid'] = dict_node_metadata[str_indicator_nodes_uuid]
            dict_node_metadata['index'] = idx
            dict_node_metadata['type'] = 'indicator'
            dict_node_metadata['system'] = name_system
    
    array_production = xr.DataArray(
        np.abs(array_production),
        dims=['rows', 'cols'],
        coords={
            'rows': [node_metadata['uuid'] for node_metadata in list_dicts_production_node_metadata],
            'cols': [node_metadata['uuid'] for node_metadata in list_dicts_production_node_metadata]
        }
    )
    array_extension = xr.DataArray(
        array_extension,
        dims=['rows', 'cols'],
        coords={
            'rows': [node_metadata['uuid'] for node_metadata in list_dicts_extension_node_metadata],
            'cols': [node_metadata['uuid'] for node_metadata in list_dicts_production_node_metadata]
        }
    )

    if array_indicator is not None:
        array_indicator = xr.DataArray(
            array_indicator,
            dims=['rows', 'cols'],
            coords={
                'rows': [node_metadata['uuid'] for node_metadata in list_dicts_indicator_node_metadata],
                'cols': [node_metadata['uuid'] for node_metadata in list_dicts_extension_node_metadata]
            }
        )
    
    with logtimer("creating MultiDiGraph from technosphere matrix."):
        logging.info(
            f"# of nodes: {len(array_production.coords['rows'])}, # of edges: {(np.count_nonzero(~np.isnan(array_production) & (array_production != 0))):,}"
        )
        A = nx.from_numpy_array(
            array_production.values,
            create_using=nx.MultiDiGraph,
            parallel_edges=False,
            edge_attr='flow',
            nodelist=array_production.coords['rows'].values.tolist(),
        )

    with logtimer("creating MultiDiGraph from biosphere matrix."):
        logging.info(
            f"# of nodes: {len(array_extension.coords['rows'])}, # of edges: {(np.count_nonzero(~np.isnan(array_extension) & (array_extension != 0))):,}"
        )
        B = from_biadjacency_matrix(
            matrix=array_extension.values,
            nodes_axis_0=array_extension.coords['rows'].values.tolist(),
            nodes_axis_1=array_extension.coords['cols'].values.tolist(),
            attributes_nodes_axis_0={'type': 'extension'},
            attributes_nodes_axis_1={'type': 'production'},
            amount_attribute='flow',
            dict_attributes={
                'type_origin': 'production',
                'type_destination': 'extension',
            },
            create_using=nx.MultiDiGraph
        )

    if array_indicator is not None:
        with logtimer("creating MultiDiGraph from indicator matrix."):
            logging.info(
                f"# of nodes: {len(array_indicator.coords['rows'])}, # of edges: {(np.count_nonzero(~np.isnan(array_indicator) & (array_indicator != 0))):,}"
            )
            Q = from_biadjacency_matrix(
                matrix=array_indicator.values,
                nodes_axis_0=array_indicator.coords['rows'].values.tolist(),
                nodes_axis_1=array_indicator.coords['cols'].values.tolist(),
                attributes_nodes_axis_0={'type': 'indicator'},
                attributes_nodes_axis_1={'type': 'extension'},
                amount_attribute='weight',
                dict_attributes={
                    'type_origin': 'extension',
                    'type_destination': 'indicator',
                },
                create_using=nx.MultiDiGraph
            )

    with logtimer("setting node attributes."):
        for node_metadata in list_dicts_production_node_metadata:
            for key, value in node_metadata.items():
                A.nodes[node_metadata['uuid']][key] = value
        for node_metadata in list_dicts_extension_node_metadata:
            for key, value in node_metadata.items():
                B.nodes[node_metadata['uuid']][key] = value
        if array_indicator is not None:
            for node_metadata in list_dicts_indicator_node_metadata:
                for key, value in node_metadata.items():
                    Q.nodes[node_metadata['uuid']][key] = value

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


def graph_system_from_node_and_edge_lists(
    name_system: str,
    assign_new_uuids: bool,
    str_production_nodes_uuid: str,
    str_extension_nodes_uuid: str,
    list_dicts_production_nodes_metadata: list[dict],
    list_dicts_extension_nodes_metadata: list[dict],
    list_tuples_production_edges: list[dict],
    list_tuples_extension_edges: list[dict],
) -> nx.MultiDiGraph:
    r"""
    Given a list of nodes and edges of production and extension types,
    create a MultiDiGraph.

    Notes
    -----
    This function is best suited for importing Ecoinvent/Ecospold data.

    Warnings
    --------
    This function expects that:

    1. Unless an attribute `production` is specified for a node, production is set to 1.

    Example
    -------
    Note that this example uses the same example system as
    [`greengraph.importers.databases.generic.graph_system_from_input_output_matrices`][].
    ```python
    list_dicts_production_nodes_metadata = [
        {'name': 'A', 'unit': 'kg'},
        {'name': 'B', 'unit': 'kg'},
        {'name': 'C', 'unit': 'kg'}
    ]
    list_dicts_extension_nodes_metadata = [
        {'name': 'alpha', 'unit': 'kg(CO2)'},
    ]
    list_tuples_production_edges = [
        ('B', 'A', 1),
        ('C', 'B', 2),
        ('C', 'A', 3)
    ]
    list_tuples_extension_edges = [
        ('A', 'alpha', 4),
        ('B', 'alpha', 3),
        ('C', 'alpha', 2)
    ]
    G = graph_system_from_node_and_edge_lists(
        name_system='example_system',
        assign_new_uuids=False,
        str_production_nodes_uuid='name',
        str_extension_nodes_uuid='name',
        list_dicts_production_nodes_metadata=list_dicts_production_nodes_metadata,
        list_dicts_extension_nodes_metadata=list_dicts_extension_nodes_metadata,
        list_tuples_production_edges=list_tuples_production_edges,
        list_tuples_extension_edges=list_tuples_extension_edges
    )
    ```

    Parameters
    ----------
    name_system : str
        Name of the system.
    assign_new_uuids : bool
        Whether to assign new UUIDs to the nodes.  
        If True, new UUIDs (`uuid.uuid4()`) will be assigned.  
        If False, the UUIDs in the metadata dictionaries will be used.
    str_production_nodes_uuid : str
        The key in the metadata dictionaries that contains the UUIDs for production nodes.
    str_extension_nodes_uuid : str
        The key in the metadata dictionaries that contains the UUIDs for extension nodes.
    list_dicts_production_nodes_metadata : list[dict]
        List of metadata dictionaries for production nodes.  
        Must contain at least the keys `['name', 'unit']`.
    list_dicts_extension_nodes_metadata : list[dict]
        List of metadata dictionaries for extension nodes.  
        Must contain at least the keys `['name', 'unit']`.
    list_tuples_production_edges : list[tuple]
        List of tuples representing edges for production nodes.  
        Must be in the form: `(source_uuid, target_uuid, amount)`.
    list_tuples_extension_edges : list[tuple]
        List of tuples representing edges for extension nodes.  
        Must be in the form: `(source_uuid, target_uuid, amount)`.
    
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

    A = nx.MultiDiGraph(None)
    for node in list_dicts_production_nodes_metadata:
        if set(['name', 'unit']).issubset(node.keys()) == False:
            raise ValueError("At least 'name' and 'unit' attributes must be present for every node.")
        node['type'] = 'production'
        node['system'] = name_system
        if 'production' not in node:
            node['production'] = 1.0
        A.add_node(node[str_production_nodes_uuid], **node)
    
    B = nx.MultiDiGraph(None)
    for node in list_dicts_extension_nodes_metadata:
        if set(['name', 'unit']).issubset(node.keys()) == False:
            raise ValueError("At least 'name' and 'unit' attributes must be present for every node.")
        node['type'] = 'extension'
        node['system'] = name_system
        B.add_node(node[str_extension_nodes_uuid], **node)
                   
    A.add_edges_from(list_tuples_production_edges, weight='flow')
    B.add_edges_from(list_tuples_extension_edges, weight='flow')
    G = nx.compose(A, B)

    if len(A.nodes) != len(list_dicts_production_nodes_metadata):
        raise ValueError("Number of nodes in production graph does not match number of metadata dictionaries.")
    # some ecoinvent versions have more metadata dictionaries than nodes
    # if len(B.nodes) != (len(list_dicts_extension_nodes_metadata) + len(list_tuples_production_edges)):
    #     raise ValueError("Number of nodes in extension graph does not match number of metadata dictionaries.")
    # if len(G.nodes) != (len(list_dicts_production_nodes_metadata) + len(list_dicts_extension_nodes_metadata)):
    #     raise ValueError("Number of nodes in combined graph does not match number of metadata dictionaries.")

    if assign_new_uuids:
        G = nx.relabel_nodes(
            G=G,
            mapping={node: str(uuid.uuid4()) for node in G.nodes()}
        )
    
    return G