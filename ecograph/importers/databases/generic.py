
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
from ecograph.utility.logging import logtimer

from ecograph.utility.graph import from_biadjacency_matrix


def _generic_graph_system_from_matrices(
    name_system: str,
    convention: str,
    matrix_technosphere: np.ndarray,
    matrix_biosphere: np.ndarray,
    matrix_characterization: np.ndarray,
    list_dicts_technosphere_node_metadata: list[dict],
    list_dicts_biosphere_node_metadata: list[dict],
) -> nx.MultiDiGraph:
    """
    Create a MultiDiGraph from technosphere and biosphere matrices.

    Parameters
    ----------
    matrix_technosphere : np.ndarray
        Technosphere matrix.
    matrix_biosphere : np.ndarray
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
    
    if matrix_technosphere.shape[0] != matrix_technosphere.shape[1]:
        raise ValueError("Technosphere matrix must be square.")
    if matrix_technosphere.shape[0] != len(list_dicts_technosphere_node_metadata):
        raise ValueError("Matrix technosphere shape does not match metadata length.")
    if matrix_biosphere.shape[0] != len(list_dicts_biosphere_node_metadata):
        raise ValueError("Matrix biosphere shape does not match metadata length.")
    if not np.issubdtype(matrix_technosphere.dtype, np.number):
        raise TypeError("All entries in the technosphere matrix must be numeric.")
    if not np.issubdtype(matrix_biosphere.dtype, np.number):
        raise TypeError("All entries in the biosphere matrix must be numeric.")
    if not (matrix_technosphere >= 0).all():
        raise ValueError("All entries in the technosphere matrix must be non-negative.")
    if not (matrix_biosphere >= 0).all():
        raise ValueError("All entries in the biosphere matrix must be non-negative.")
    if not convention in ['I-A', 'A']:
        raise ValueError("Convention must be 'I-A' or 'A'.")

    for idx, dict_node_metadata in enumerate(list_dicts_technosphere_node_metadata):
        dict_node_metadata['uuid'] = str(uuid.uuid4())
        dict_node_metadata['index'] = idx
        if convention == 'I-A':
            dict_node_metadata['production'] = 1.0
        elif convention == 'A':
            dict_node_metadata['production'] = matrix_technosphere[idx, idx]

    for idx, dict_node_metadata in enumerate(list_dicts_biosphere_node_metadata):
        dict_node_metadata['uuid'] = str(uuid.uuid4())
        dict_node_metadata['index'] = idx        

    if convention == 'A':
        np.fill_diagonal(matrix_technosphere, 0)

    matrix_technosphere = xr.DataArray(
        np.abs(matrix_technosphere),
        dims=['rows', 'cols'],
        coords={
            'rows': [node_metadata['uuid'] for node_metadata in list_dicts_technosphere_node_metadata],
            'cols': [node_metadata['uuid'] for node_metadata in list_dicts_technosphere_node_metadata]
        }
    )
    matrix_biosphere = xr.DataArray(
        np.abs(matrix_biosphere),
        dims=['rows', 'cols'],
        coords={
            'rows': [node_metadata['uuid'] for node_metadata in list_dicts_biosphere_node_metadata],
            'cols': [node_metadata['uuid'] for node_metadata in list_dicts_technosphere_node_metadata]
        }
    )    
    
    with logtimer("Creating MultiDiGraph from technosphere matrix."):
        G = nx.from_numpy_array(
            matrix_technosphere.values,
            create_using=nx.MultiDiGraph,
            parallel_edges=False,
            edge_attr='flow',
            nodelist=matrix_technosphere.coords['rows'].values,
        )

    with logtimer("Creating MultiDiGraph from biosphere matrix."):
        B = from_biadjacency_matrix(
            matrix=matrix_biosphere.values,
            nodes_axis_0=matrix_biosphere.coords['rows'].values,
            nodes_axis_1=matrix_biosphere.coords['cols'].values,
            attributes_nodes_axis_0={'type': 'biosphere'},
            attributes_nodes_axis_1={'type': 'technosphere'},
            create_using=nx.MultiDiGraph
        )

    with logtimer("Setting node attributes."):
        for node_metadata in list_dicts_technosphere_node_metadata:
            node_uuid = node_metadata['uuid']
            G.nodes[node_uuid]['index'] = node_metadata['index']
            G.nodes[node_uuid]['name'] = node_metadata['name']
            G.nodes[node_uuid]['type'] = 'technosphere'
            G.nodes[node_uuid]['system'] = name_system
            G.nodes[node_uuid]['production'] = node_metadata['production']
            G.nodes[node_uuid]['unit'] = node_metadata['unit']
            explicitly_set_keys = {'uuid', 'index', 'name', 'production', 'unit'}
            for key, value in node_metadata.items():
                if key not in explicitly_set_keys:
                    G.nodes[node_uuid][key] = value
        for node_metadata in list_dicts_biosphere_node_metadata:
            node_uuid = node_metadata['uuid']
            B.nodes[node_uuid]['index'] = node_metadata['index']
            B.nodes[node_uuid]['name'] = node_metadata['name']
            B.nodes[node_uuid]['type'] = 'biosphere'
            B.nodes[node_uuid]['system'] = name_system
            B.nodes[node_uuid]['unit'] = node_metadata['unit']
            for key, value in node_metadata.items():
                if key not in explicitly_set_keys:
                    B.nodes[node_uuid][key] = value

    with logtimer("Merging technosphere and biosphere graphs."):
        GcomposeB = nx.compose(B, G)
        del G
        del B

    return GcomposeB