r"""
This module contains functions to turn properly prepared dataframes/etc.
into a greengraph graph class.
"""

# %%
import networkx as nx
import xarray as xr
import pandas as pd
import numpy as np
import scipy as sp
import logging
from pathlib import Path
import uuid
from datetime import datetime
from greengraph.utility.logging import logtimer
import uuid

from greengraph.utility.graph import from_biadjacency_matrix


def graph_system_from_input_output_matrices(
    name_system: str,
    convention: str,
    ignore_matrix_dimension_errors: bool,
    matrix_production: np.ndarray,
    matrix_extension: np.ndarray,
    matrix_characterization: np.ndarray,
    list_dicts_production_node_metadata: list[dict],
    list_dicts_extension_node_metadata: list[dict],
    list_dicts_characterization_node_metadata: list[dict],
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

    
    Warnings
    --------
    This function assumes that

    order or rows....


    Parameters
    ----------
    matrix_production : np.ndarray
        Technosphere matrix.
    matrix_extension : np.ndarray
        Biosphere matrix.
    list_metadata_technosphere : list[dict]
        List of metadata for technosphere nodes.
    list_metadata_biosphere : list[dict]
        List of metadata for biosphere nodes.

    Returns
    -------
    nx.MultiDiGraph
        The created MultiDiGraph.
    """
    
    if ignore_matrix_dimension_errors == False:
        if matrix_production.shape[0] != matrix_production.shape[1]:
            raise ValueError("Production matrix must be square.")
        if matrix_extension.shape[0] != matrix_characterization.shape[1]:
            raise ValueError("Dimension mismatch between extension matrix and characterization matrix.")

    for matrix, metadata, name in [
        (matrix_production, list_dicts_production_node_metadata, "production"),
        (matrix_extension, list_dicts_extension_node_metadata,  "biosphere"),
        (matrix_characterization, list_dicts_characterization_node_metadata, "characterization")
    ]:
        if not np.issubdtype(matrix.dtype, np.number):
            raise TypeError(f"All entries in the {name} matrix must be numeric.")
        if matrix.shape[0] != len(metadata):
            raise ValueError(f"Dimensions of the {name} matrix does not match metadata dictionary length.")
    
    for node_metadata in list_dicts_production_node_metadata:
        for key in ['name', 'unit']:
            if key not in node_metadata:
                raise ValueError(f"Metadata dictionary for every node must contain a '{key}' key.")

    if not convention in ['I-A', 'A']:
        raise ValueError("Convention must be 'I-A' or 'A'.")
    if convention == 'A':
        np.fill_diagonal(matrix_production, 0)
    elif convention == 'I-A':
        if not (matrix_production >= 0).all():
            raise ValueError("All entries in the technosphere matrix must be non-negative.")

    # Production Metadata Parsing
    for idx, dict_node_metadata in enumerate(list_dicts_production_node_metadata):
        dict_node_metadata['uuid'] = str(uuid.uuid4())
        dict_node_metadata['index'] = idx
        dict_node_metadata['type'] = 'production'
        dict_node_metadata['system'] = name_system
        if convention == 'I-A':
            dict_node_metadata['production'] = 1.0
        elif convention == 'A':
            dict_node_metadata['production'] = matrix_production[idx, idx]

    # Extension Metadata Parsing
    for idx, dict_node_metadata in enumerate(list_dicts_extension_node_metadata):
        dict_node_metadata['uuid'] = str(uuid.uuid4())
        dict_node_metadata['index'] = idx       
        dict_node_metadata['type'] = 'extension'
        dict_node_metadata['system'] = name_system

    # Characterization Metadata Parsing
    for idx, dict_node_metadata in enumerate(list_dicts_characterization_node_metadata):
        dict_node_metadata['uuid'] = str(uuid.uuid4())
        dict_node_metadata['index'] = idx
        dict_node_metadata['type'] = 'characterization'
        dict_node_metadata['system'] = name_system

    
    matrix_production = xr.DataArray(
        np.abs(matrix_production),
        dims=['rows', 'cols'],
        coords={
            'rows': [node_metadata['uuid'] for node_metadata in list_dicts_production_node_metadata],
            'cols': [node_metadata['uuid'] for node_metadata in list_dicts_production_node_metadata]
        }
    )
    matrix_extension = xr.DataArray(
        matrix_extension,
        dims=['rows', 'cols'],
        coords={
            'rows': [node_metadata['uuid'] for node_metadata in list_dicts_extension_node_metadata],
            'cols': [node_metadata['uuid'] for node_metadata in list_dicts_production_node_metadata]
        }
    )
    matrix_characterization = xr.DataArray(
        matrix_characterization,
        dims=['rows', 'cols'],
        coords={
            'rows': [node_metadata['uuid'] for node_metadata in list_dicts_characterization_node_metadata],
            'cols': [node_metadata['uuid'] for node_metadata in list_dicts_extension_node_metadata]
        }
    )
    
    with logtimer("creating MultiDiGraph from technosphere matrix."):
        logging.info(
            f"# of nodes: {len(matrix_production.coords['rows'])}, # of edges: {(np.count_nonzero(~np.isnan(matrix_production) & (matrix_production != 0))):,}"
        )
        G = nx.from_numpy_array(
            matrix_production.values,
            create_using=nx.MultiDiGraph,
            parallel_edges=False,
            edge_attr='flow',
            nodelist=matrix_production.coords['rows'].values.tolist(),
        )

    with logtimer("creating MultiDiGraph from biosphere matrix."):
        logging.info(
            f"# of nodes: {len(matrix_extension.coords['rows'])}, # of edges: {(np.count_nonzero(~np.isnan(matrix_extension) & (matrix_extension != 0))):,}"
        )
        B = from_biadjacency_matrix(
            matrix=matrix_extension.values,
            nodes_axis_0=matrix_extension.coords['rows'].values.tolist(),
            nodes_axis_1=matrix_extension.coords['cols'].values.tolist(),
            attributes_nodes_axis_0={'type': 'biosphere'},
            attributes_nodes_axis_1={'type': 'technosphere'},
            create_using=nx.MultiDiGraph
        )

    with logtimer("creating MultiDiGraph from characterization matrix."):
        logging.info(
            f"# of nodes: {len(matrix_characterization.coords['rows'])}, # of edges: {(np.count_nonzero(~np.isnan(matrix_characterization) & (matrix_characterization != 0))):,}"
        )
        Q = from_biadjacency_matrix(
            matrix=matrix_characterization.values,
            nodes_axis_0=matrix_characterization.coords['rows'].values.tolist(),
            nodes_axis_1=matrix_characterization.coords['cols'].values.tolist(),
            attributes_nodes_axis_0={'type': 'impact'},
            attributes_nodes_axis_1={'type': 'biosphere'},
            create_using=nx.MultiDiGraph
        )

    with logtimer("setting node attributes."):
        for node_metadata in list_dicts_production_node_metadata:
            for key, value in node_metadata.items():
                G.nodes[node_metadata['uuid']][key] = value
        for node_metadata in list_dicts_extension_node_metadata:
            for key, value in node_metadata.items():
                B.nodes[node_metadata['uuid']][key] = value
        for node_metadata in list_dicts_characterization_node_metadata:
            for key, value in node_metadata.items():
                Q.nodes[node_metadata['uuid']][key] = value

    with logtimer("merging production and extension graphs."):
        GcomposeB = nx.compose(B, G)
        del G
        del B
    with logtimer("merging production+extension and characterization graphs."):
        GBcomposeQ = nx.compose(Q, GcomposeB)
        del GcomposeB

    return GBcomposeQ


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

    Create a MultiDiGraph from technosphere and biosphere matrices.
    """
    for node_metadata in list_dicts_production_nodes_metadata:
        node_metadata['type'] = 'production'
        node_metadata['system'] = name_system
    for node_metadata in list_dicts_extension_nodes_metadata:
        node_metadata['type'] = 'extension'
        node_metadata['system'] = name_system

    A = nx.MultiDiGraph(None)
    for node in list_dicts_production_nodes_metadata:
        A.add_node(node[str_production_nodes_uuid], **node)
    
    B = nx.MultiDiGraph(None)
    for node in list_dicts_extension_nodes_metadata:
        B.add_node(node[str_extension_nodes_uuid], **node)
                   
    A.add_edges_from(list_tuples_production_edges)
    B.add_edges_from(list_tuples_extension_edges)
    G = nx.compose(A, B)

    if assign_new_uuids:
        G = G.relabel_nodes(
            G=G,
            mapping={node: str(uuid.uuid4()) for node in G.nodes()}
        )
    
    return G