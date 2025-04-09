
# %%
import networkx as nx
import pandas as pd
import numpy as np
import scipy as sp
import logging
from pathlib import Path
import uuid
from datetime import datetime
from ecograph.utility.logging import logtimer


def generic_system_from_matrices(
    name_system: str,
    matrix_technosphere: np.ndarray,
    matrix_biosphere: np.ndarray,
    list_metadata_technosphere: list[dict],
    list_metadata_biosphere: list[dict],
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
    if matrix_technosphere.shape[0] != len(list_metadata_technosphere):
        raise ValueError("Matrix technosphere shape does not match metadata length.")
    if matrix_biosphere.shape[0] != len(list_metadata_biosphere):
        raise ValueError("Matrix biosphere shape does not match metadata length.")
    if not np.issubdtype(matrix_technosphere.dtype, np.number):
        raise TypeError("All entries in the technosphere matrix must be numeric.")
    if not np.issubdtype(matrix_biosphere.dtype, np.number):
        raise TypeError("All entries in the biosphere matrix must be numeric.")
    if not (matrix_technosphere >= 0).all():
        raise ValueError("All entries in the technosphere matrix must be non-negative.")
    if not (matrix_biosphere >= 0).all():
        raise ValueError("All entries in the biosphere matrix must be non-negative.")
    
    nodelist_technosphere = [str(uuid.uuid4()) for _ in range(len(list_metadata_technosphere))]
    nodelist_biosphere = [str(uuid.uuid4()) for _ in range(len(list_metadata_biosphere))]
    
    with logtimer("Creating MultiDiGraph from technosphere matrix."):
        G = nx.from_numpy_array(
            matrix_technosphere,
            create_using=nx.MultiDiGraph,
            parallel_edges=False,
            edge_attr='flow',
            nodelist=nodelist_technosphere,
        )

    with logtimer("Creating MultiDiGraph from biosphere matrix."):
        B = nx.empty_graph(0)
        B.add_nodes_from(nodelist_biosphere, type='biosphere')
        B.add_nodes_from(nodelist_technosphere, type='technosphere')
        B.add_edges_from(
            [(i, j) for i, j in zip(*np.nonzero(matrix_biosphere))],
            flow=matrix_biosphere[i, j],
        )

    with logtimer("Setting node attributes."):
        for idx, metadata in enumerate(list_metadata_technosphere):
            G.nodes[G.nodes[idx]]['index'] = idx
            G.nodes[G.nodes[idx]]['name'] = metadata['name']
            G.nodes[G.nodes[idx]]['type'] = 'technosphere'
            G.nodes[G.nodes[idx]]['system'] = name_system
            G.nodes[G.nodes[idx]]['unit'] = metadata['unit']
        for idx, metadata in enumerate(list_metadata_biosphere):
            B.nodes[B.nodes[idx]]['index'] = idx
            B.nodes[B.nodes[idx]]['name'] = metadata['name']
            B.nodes[B.nodes[idx]]['type'] = 'biosphere'
            B.nodes[B.nodes[idx]]['system'] = name_system
            B.nodes[B.nodes[idx]]['unit'] = metadata['unit']

    with logtimer("Merging technosphere and biosphere graphs."):
        GcomposeB = nx.compose(B, G)
        del G
        del B

    return GcomposeB